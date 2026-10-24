"""Lecture des données du jeu installé sur le PC : pbo, config.bin, modèles (ODOL), terrain (wrp).

Les résultats lourds (relief, objets de la carte, classes) sont mis en cache dans tools/neige/cache/.
"""
import glob
import os
import pickle
import re
import struct
from array import array

DAYZ = os.environ.get("DAYZ_DIR", os.path.expanduser("~/snap/steam/common/.local/share/Steam/steamapps/common/DayZ"))
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

HEIGHT_GRID = 2048
HEIGHT_CELL = 7.5


def _cached(name, build):
	path = os.path.join(CACHE, name)
	if os.path.exists(path):
		return pickle.load(open(path, "rb"))
	os.makedirs(CACHE, exist_ok=True)
	data = build()
	pickle.dump(data, open(path, "wb"))
	return data


# --- pbo -------------------------------------------------------------------------------------

def _cstr(f):
	b = b""
	while (c := f.read(1)) != b"\0":
		b += c
	return b.decode("latin1")


def _build_pbo_index():
	"""Chemin complet en minuscules (préfixe du pbo inclus) -> (fichier pbo, offset, taille, compressé)."""
	index = {}
	paths = glob.glob(DAYZ + "/Addons/*.pbo") + glob.glob(DAYZ + "/*/Addons/*.pbo") + glob.glob(DAYZ + "/*/addons/*.pbo")
	for p in paths:
		f = open(p, "rb")
		entries, prefix = [], ""
		while True:
			name = _cstr(f)
			mime, orig, res, ts, size = struct.unpack("<5I", f.read(20))
			if name == "" and mime == 0x56657273:
				while (k := _cstr(f)):
					v = _cstr(f)
					if k.lower() == "prefix":
						prefix = v
				continue
			if name == "":
				break
			entries.append((name, mime, size))
		off = f.tell()
		for name, mime, size in entries:
			index[(prefix + "\\" + name).lower().replace("/", "\\")] = (p, off, size, mime != 0)
			off += size
	return index


_pbo_index = None


def pbo_read(path, length=None):
	global _pbo_index
	if _pbo_index is None:
		_pbo_index = _cached("pbo_index.pkl", _build_pbo_index)
	entry = _pbo_index.get(path.lower().replace("/", "\\").lstrip("\\"))
	if not entry or entry[3]:
		return None
	p, off, size, _ = entry
	with open(p, "rb") as f:
		f.seek(off)
		return f.read(size if length is None else min(size, length))


# --- config.bin (CfgVehicles) ------------------------------------------------------------------

def _rap_classes(b):
	res = {}

	def cint(o):
		v = s = 0
		while True:
			c = b[o]; o += 1; v |= (c & 0x7F) << s; s += 7
			if not c & 0x80:
				return v, o

	def cstr(o):
		e = b.index(b"\0", o)
		return b[o:e].decode("latin1"), e + 1

	def arr(o):
		n, o = cint(o)
		out = []
		for _ in range(n):
			t = b[o]; o += 1
			if t == 1:
				v = struct.unpack_from("<f", b, o)[0]; o += 4
			elif t == 2:
				v = struct.unpack_from("<i", b, o)[0]; o += 4
			elif t == 3:
				v, o = arr(o)
			else:
				v, o = cstr(o)
			out.append(v)
		return out, o

	def body(o, path):
		parent, o = cstr(o)
		n, o = cint(o)
		d = {"_parent": parent}
		res[path] = d
		for _ in range(n):
			t = b[o]; o += 1
			if t == 0:
				name, o = cstr(o)
				body(struct.unpack_from("<I", b, o)[0], path + "/" + name); o += 4
			elif t == 1:
				st = b[o]; o += 1
				name, o = cstr(o)
				if st in (1, 2):
					v = struct.unpack_from("<f" if st == 1 else "<i", b, o)[0]; o += 4
				else:
					v, o = cstr(o)
				d[name] = v
			elif t in (2, 5):
				if t == 5:
					o += 4
				name, o = cstr(o)
				d[name], o = arr(o)
			elif t in (3, 4):
				name, o = cstr(o)

	body(16, "")
	return res


def _build_models():
	"""Classe CfgVehicles (minuscules) -> modèle .p3d (héritage résolu)."""
	global _pbo_index
	if _pbo_index is None:
		_pbo_index = _cached("pbo_index.pkl", _build_pbo_index)
	classes = {}
	for path, entry in _pbo_index.items():
		if path.endswith("config.bin") and not entry[3]:
			try:
				for k, v in _rap_classes(pbo_read(path)).items():
					if k.lower().startswith("/cfgvehicles/"):
						classes[k.split("/")[-1].lower()] = v
			except Exception:
				pass
	models = {}
	for name in classes:
		c, seen = name, set()
		while c in classes and c not in seen:
			seen.add(c)
			if "model" in classes[c]:
				models[name] = classes[c]["model"]
				break
			c = classes[c]["_parent"].lower()
	return models


def class_model(name):
	return _cached("class_models.pkl", _build_models).get(name.lower())


# --- modèles ODOL --------------------------------------------------------------------------------

_bbox_cache = {}


def model_bbox(path):
	"""Boîte englobante (min xyz, max xyz) du modèle, dans ses coordonnées (origine = position de l'objet)."""
	key = path.lower().lstrip("\\")
	if not key.endswith(".p3d"):
		key += ".p3d"
	if key not in _bbox_cache:
		b = pbo_read(key, 400)
		box = None
		if b and b[:4] == b"ODOL":
			fl = struct.unpack_from("<%df" % ((len(b) - 12) // 4), b, 12)
			# la boîte apparaît deux fois de suite dans l'en-tête
			for i in range(len(fl) - 12):
				g = fl[i:i + 6]
				if g == fl[i + 6:i + 12] and all(g[k] <= g[k + 3] for k in range(3)) and g[3] - g[0] > 0.01:
					box = (g[:3], g[3:])
					break
		_bbox_cache[key] = box
	return _bbox_cache[key]


# --- terrain (wrp) --------------------------------------------------------------------------------

def _lzo(src, ip, out_len):
	out = bytearray()

	def run(t, base):
		nonlocal ip
		if t == 0:
			while src[ip] == 0:
				t += 255; ip += 1
			t += base + src[ip]; ip += 1
		return t

	state = 0
	if src[ip] > 17:
		t = src[ip] - 17; ip += 1
		out += src[ip:ip + t]; ip += t
		state = 4 if t >= 4 else t
	while len(out) < out_len:
		t = src[ip]; ip += 1
		if t < 16:
			if state == 0:
				t = run(t, 15) + 3
				out += src[ip:ip + t]; ip += t; state = 4
				continue
			if state == 4:
				d = 1 + 0x800 + (t >> 2) + (src[ip] << 2); ln = 3
			else:
				d = 1 + (t >> 2) + (src[ip] << 2); ln = 2
			ip += 1
		elif t >= 64:
			d = 1 + ((t >> 2) & 7) + (src[ip] << 3); ip += 1; ln = (t >> 5) + 1
		elif t >= 32:
			ln = run(t & 31, 31) + 2
			d = 1 + ((src[ip] | (src[ip + 1] << 8)) >> 2); ip += 2; t = src[ip - 2]
		else:
			ln = run(t & 7, 7) + 2
			d = ((t & 8) << 11) + ((src[ip] | (src[ip + 1] << 8)) >> 2); ip += 2; t = src[ip - 2]
			if d == 0:
				break
			d += 0x4000
		s = len(out) - d
		if s < 0:
			raise ValueError("référence avant le début du flux")
		if d >= ln:
			out += out[s:s + ln]
		else:
			for i in range(ln):
				out.append(out[s + i])
		if t & 3:
			out += src[ip:ip + (t & 3)]; ip += t & 3
		state = t & 3
	return bytes(out)


def _wrp():
	return pbo_read("dz\\worlds\\chernarusplus\\world\\chernarusplus.wrp")


def _smooth_heights(out):
	a = array("f"); a.frombytes(out[:len(out) // 4 * 4])
	return len(a) > 100 and all(-300 < v < 1000 for v in a) and all(abs(a[i] - a[i - 1]) < 20 for i in range(1, len(a)))


def _build_heights():
	src = _wrp()
	# début du flux LZO du relief : 1423002 pour la version OPRW 32 (mise à jour du 22/10/2026), sinon on le
	# cherche ; un départ en milieu de flux peut sembler valide, d'où la vérification de la taille complète
	size = HEIGHT_GRID * HEIGHT_GRID * 4
	for o in [1423002] + list(range(len(src) // 8, 0, -1)):
		try:
			if _smooth_heights(_lzo(src, o, 8192)):
				out = _lzo(src, o, size)
				if len(out) >= size:
					break
		except Exception:
			pass
	a = array("f"); a.frombytes(out[:len(out) // 4 * 4])
	return a


_heights = None


def height(x, z):
	global _heights
	if _heights is None:
		_heights = _cached("heights.pkl", _build_heights)
	gx = min(max(x / HEIGHT_CELL, 0.0), HEIGHT_GRID - 1.001)   # bords de la carte
	gz = min(max(z / HEIGHT_CELL, 0.0), HEIGHT_GRID - 1.001)
	i, j = int(gx), int(gz)
	fx, fz = gx - i, gz - j
	g = lambda c, r: _heights[r * HEIGHT_GRID + c]
	return (g(i, j) * (1 - fx) + g(i + 1, j) * fx) * (1 - fz) + (g(i, j + 1) * (1 - fx) + g(i + 1, j + 1) * fx) * fz


def _build_objects():
	"""Objets posés sur la carte : liste de (modèle, axe x, axe z, position)."""
	src = _wrp()
	o = src.find(b".p3d\0")
	while src[o - 1] != 0:
		o -= 1
	count = struct.unpack_from("<I", src, o - 4)[0]
	names = []
	for _ in range(count):
		e = src.index(b"\0", o)
		names.append(src[o:e].decode("latin1")); o = e + 1

	# enregistrements de 64 octets : id, index du modèle, matrice 3x3, position, 8 octets
	def valid(p):
		if p + 64 > len(src):
			return False
		mi = struct.unpack_from("<I", src, p + 4)[0]
		f = struct.unpack_from("<12f", src, p + 8)
		norm = f[0] * f[0] + f[1] * f[1] + f[2] * f[2]
		return mi < count and -100 < f[9] < 16000 and -100 < f[11] < 16000 and -500 < f[10] < 2000 and 0.01 < norm < 400

	# début du tableau : première suite de 1000 enregistrements valides ; quelques enregistrements
	# isolés (matrice nulle) sont invalides, on les saute ; fin : 1000 invalides d'affilée
	p = o
	while not all(valid(p + 64 * k) for k in range(1000)):
		p += 1
	objects, misses = [], 0
	while misses < 1000 and p + 64 <= len(src):
		if valid(p):
			mi = struct.unpack_from("<I", src, p + 4)[0]
			f = struct.unpack_from("<12f", src, p + 8)
			objects.append((names[mi], (f[0], f[2]), (f[6], f[8]), (f[9], f[10], f[11])))
			misses = 0
		else:
			misses += 1
		p += 64
	return objects


def map_objects():
	return _cached("objects.pkl", _build_objects)
