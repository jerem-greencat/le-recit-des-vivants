"""Génère un mapping de plaques de neige (Sakhal) pour une ville de Chernarus.

Usage : python3 tools/neige/generate.py zelenogorsk
Écrit custom/neige_<ville>.json. Le mapping n'est chargé qu'en ambiance hiver (meteo/hiver/mappings.txt).

Règles :
- la neige couvre la ville (zone à moins de TOWN_RADIUS m d'un bâtiment, d'un seul tenant autour du centre) ;
- pas de neige dans les bâtiments de la carte ni dans les gros objets de nos mappings ;
- en ville, les rues goudronnées restent dégagées (hors ville, les routes seront enneigées) ;
- les plaques sont plates : on les incline dans le sens de la pente (lacet tourné vers l'amont, tangage
  positif = avant relevé, comme les postes de garde posés en pente dans zeleno_enceinte.json), et on ne
  les pose que là où le terrain est assez régulier sous la plaque ;
- chaque plaque est un objet synchronisé par le serveur : trop de plaques provoquent de la désynchronisation
  (3 572 à Zelenogorsk, c'était trop), d'où les grandes plaques seules (pas de bandes étroites).
"""
import glob
import json
import math
import os
import random
import struct
import sys
import zlib
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedata  # noqa: E402

MISSION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dayzxb_missions", "dayzOffline.chernarusplus")

TOWNS = {
	# nom : (x, z) d'un point au cœur de la ville, demi-largeur de la zone étudiée
	"zelenogorsk": ((2730.0, 5373.0), 900),
}

TOWN_RADIUS = 40          # m autour des bâtiments qui comptent comme « ville »
MAX_STREET = 0.03         # part maximale d'une plaque posée sur une rue goudronnée
MAX_BUILDING = 0.15       # part maximale sur un bâtiment (la plaque passe sous le plancher, surélevé)
HOUSE_AREA = 40           # emprise minimale (m²) d'un bâtiment pour définir la ville
MAX_OUTSIDE = 0.35        # part maximale d'une plaque qui déborde hors de la ville
MAX_GAP = 0.3             # enfoncement maximal de la plaque inclinée dans le terrain (m)
MAX_TILT = 12             # pente maximale (degrés)
MIN_NEW = 0.7             # part minimale de surface nouvellement couverte pour poser une plaque
CORE = 0.75               # part centrale d'une plaque réellement blanche (les bords sont fondus)

DECALS = [
	# classe (sans suffixe _noLC), demi-largeur x, demi-largeur z
	("StaticObj_Decal_Sakhal_Snow_01", 10.58, 10.58),
	("StaticObj_Decal_Sakhal_Snow_02", 10.58, 10.58),
	("StaticObj_Decal_Sakhal_Snow_03", 11.59, 11.59),
	("StaticObj_Decal_Sakhal_Snow_05", 8.17, 8.17),
	("StaticObj_Decal_Sakhal_Snow_06", 7.41, 7.41),
]
LONG = ("StaticObj_Decal_Sakhal_snow_long1", 4.83, 2.35)
USE_LONG = False          # bandes étroites entre les maisons : beaucoup d'objets pour peu de surface
SCALES = [1.0, 0.7]

BUILDING_DIRS = ("residential", "industrial", "military", "specific", "ruins", "farm", "houses")


def is_building(path):
	p = path.lower().split("\\")
	if len(p) < 3:
		return False
	if p[1] == "structures":
		return p[2] in BUILDING_DIRS
	return p[1].startswith("structures_") and p[2] not in ("roads", "walls", "signs", "rail", "wrecks")


def is_town_street(path):
	p = path.lower()
	if "\\roads\\parts\\" not in p:
		return False
	name = p.rsplit("\\", 1)[-1]
	return name.startswith("asf") or name.startswith("kr_")


class Grid:
	"""Grille de 1 m sur la zone étudiée."""

	def __init__(self, cx, cz, half):
		self.x0, self.z0, self.n = int(cx - half), int(cz - half), 2 * half
		self.cells = bytearray(self.n * self.n)

	def idx(self, x, z):
		i, j = int(x - self.x0), int(z - self.z0)
		if 0 <= i < self.n and 0 <= j < self.n:
			return j * self.n + i
		return None

	def fill_box(self, pos, xa, za, lo, hi, value, margin=0.0):
		"""Remplit la boîte orientée (axes xa, za ; limites lo/hi en x et z du modèle)."""
		ext = math.hypot(max(abs(lo[0]), abs(hi[0])), max(abs(lo[1]), abs(hi[1]))) + margin + 1
		for z in range(int(pos[1] - ext), int(pos[1] + ext) + 1):
			for x in range(int(pos[0] - ext), int(pos[0] + ext) + 1):
				dx, dz = x + 0.5 - pos[0], z + 0.5 - pos[1]
				mx, mz = dx * xa[0] + dz * xa[1], dx * za[0] + dz * za[1]
				if lo[0] - margin <= mx <= hi[0] + margin and lo[1] - margin <= mz <= hi[1] + margin:
					k = self.idx(x, z)
					if k is not None:
						self.cells[k] = value


FREE, BLOCKED, OUTSIDE, STREET = 0, 1, 2, 3


def yaw_axes(yaw_deg):
	r = math.radians(yaw_deg)
	return (math.cos(r), -math.sin(r)), (math.sin(r), math.cos(r))


def own_mapping_objects():
	"""Gros objets de nos mappings (bâtiments, dalles…) : pas de neige dessous."""
	out = []
	for f in glob.glob(os.path.join(MISSION, "custom", "*.json")):
		base = os.path.basename(f)
		if base.startswith("neige_") or base.startswith("test_neige") or base.startswith("spawngear"):
			continue
		try:
			data = json.load(open(f))
		except Exception:
			continue
		for o in data.get("Objects", []):
			name = o["name"]
			model = name if name.lower().endswith(".p3d") else gamedata.class_model(name)
			box = gamedata.model_bbox(model) if model else None
			if not box:
				continue
			(lx, ly, lz), (hx, hy, hz) = box
			s = o.get("scale", 1) or 1
			if (hx - lx) * (hz - lz) * s * s >= 10 and (hy - ly) * s >= 1.5:
				xa, za = yaw_axes(o["ypr"][0])
				out.append(((o["pos"][0], o["pos"][2]), xa, za, (lx * s, lz * s), (hx * s, hz * s)))
	return out


def town_mask(grid, buildings, seed):
	"""Zone à moins de TOWN_RADIUS m d'un bâtiment d'au moins HOUSE_AREA m², d'un seul tenant (grille de 5 m) autour du centre."""
	step = 5
	m = grid.n // step
	near = bytearray(m * m)
	r = TOWN_RADIUS // step + 1
	for (x, z) in buildings:
		ci, cj = int((x - grid.x0) / step), int((z - grid.z0) / step)
		for j in range(cj - r, cj + r + 1):
			for i in range(ci - r, ci + r + 1):
				if 0 <= i < m and 0 <= j < m and math.hypot((i - ci) * step, (j - cj) * step) <= TOWN_RADIUS:
					near[j * m + i] = 1
	si, sj = int((seed[0] - grid.x0) / step), int((seed[1] - grid.z0) / step)
	keep = bytearray(m * m)
	stack = [(si, sj)]
	while stack:
		i, j = stack.pop()
		if 0 <= i < m and 0 <= j < m and near[j * m + i] and not keep[j * m + i]:
			keep[j * m + i] = 1
			stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
	for j in range(grid.n):
		for i in range(grid.n):
			ii, jj = i // step, j // step
			if ii >= m or jj >= m or not keep[jj * m + ii]:
				grid.cells[j * grid.n + i] = OUTSIDE


def generate(town):
	(cx, cz), half = TOWNS[town]
	rnd = random.Random(town)
	grid = Grid(cx, cz, half)

	objects = [o for o in gamedata.map_objects()
			   if grid.x0 - 30 <= o[3][0] <= grid.x0 + grid.n + 30 and grid.z0 - 30 <= o[3][2] <= grid.z0 + grid.n + 30]
	buildings = [o for o in objects if is_building(o[0])]
	houses = []
	for o in buildings:
		box = gamedata.model_bbox(o[0])
		if box and (box[1][0] - box[0][0]) * (box[1][2] - box[0][2]) >= HOUSE_AREA:
			houses.append((o[3][0], o[3][2]))
	town_mask(grid, houses, (cx, cz))

	def block(path, pos, xa, za, value, margin):
		box = gamedata.model_bbox(path)
		if box:
			(lx, _, lz), (hx, _, hz) = box
			grid.fill_box(pos, xa, za, (lx, lz), (hx, hz), value, margin)

	for path, xa, za, pos in objects:
		if is_building(path):
			block(path, (pos[0], pos[2]), xa, za, BLOCKED, 0.5)
		elif is_town_street(path) or "\\water\\" in path.lower():
			k = grid.idx(pos[0], pos[2])
			if k is not None and grid.cells[k] != OUTSIDE:
				block(path, (pos[0], pos[2]), xa, za, STREET, 0.0)
	for pos, xa, za, lo, hi in own_mapping_objects():
		grid.fill_box(pos, xa, za, lo, hi, BLOCKED, 0.5)

	covered = bytearray(grid.n * grid.n)
	placed = []
	rejects = Counter()

	def footprint(x, z, hx, hz, xa, za, step):
		"""Cellules sous la plaque (échantillonnées tous les `step` m) : (indices, indices du cœur)."""
		cells, core = [], []
		ext = math.hypot(hx, hz)
		k = -ext
		while k <= ext:
			l = -ext
			while l <= ext:
				px, pz = x + k, z + l
				mx, mz = k * xa[0] + l * xa[1], k * za[0] + l * za[1]
				if abs(mx) <= hx and abs(mz) <= hz:
					i = grid.idx(px, pz)
					if i is None:
						return None, None
					cells.append(i)
					if abs(mx) <= hx * CORE and abs(mz) <= hz * CORE:
						core.append(i)
				l += step
			k += step
		return cells, core

	def allowed(cells):
		n = len(cells)
		return (sum(1 for i in cells if grid.cells[i] == STREET) <= MAX_STREET * n
				and sum(1 for i in cells if grid.cells[i] == BLOCKED) <= MAX_BUILDING * n)

	def try_place(name, hx, hz, scale, x, z):
		yaw = rnd.uniform(0, 360)
		xa, za = yaw_axes(yaw)
		hx, hz = hx * scale, hz * scale
		step = 1.0 if hx < 6 else 2.0
		cells, core = footprint(x, z, hx, hz, xa, za, step)
		if not cells or not core:
			rejects["bord de zone"] += 1
			return False
		n = len(cells)
		if not allowed(cells):
			rejects["bâtiment ou rue"] += 1
			return False
		if sum(1 for i in cells if grid.cells[i] == OUTSIDE) > MAX_OUTSIDE * n:
			rejects["hors ville"] += 1
			return False
		if sum(1 for i in core if grid.cells[i] == FREE and not covered[i]) < MIN_NEW * len(core):
			rejects["déjà couvert"] += 1
			return False
		# plan moyen du terrain sous la plaque : pente (gx, gz) et écart maximal au plan
		r = max(hx, hz)
		gx = (gamedata.height(x + r, z) - gamedata.height(x - r, z)) / (2 * r)
		gz = (gamedata.height(x, z + r) - gamedata.height(x, z - r)) / (2 * r)
		tilt = math.degrees(math.atan(math.hypot(gx, gz)))
		if tilt > MAX_TILT:
			rejects["terrain irrégulier"] += 1
			return False
		if tilt > 0.3:
			# avant de la plaque tourné vers l'amont, relevé de la pente
			yaw = math.degrees(math.atan2(gx, gz)) % 360
			xa, za = yaw_axes(yaw)
			cells, core = footprint(x, z, hx, hz, xa, za, step)
			if not cells or not allowed(cells):
				rejects["bâtiment ou rue"] += 1
				return False
		else:
			tilt, gx, gz = 0.0, 0.0, 0.0
		# terrain moins plan de la plaque, sur 11 x 11 points de la plaque : elle est abaissée pour ne flotter
		# nulle part, et refusée si elle s'enfonce trop ailleurs (partie cachée)
		y0 = gamedata.height(x, z)
		diffs = []
		for a in range(-5, 6):
			for b in range(-5, 6):
				dx = (a * hx * xa[0] + b * hz * za[0]) / 5
				dz = (a * hx * xa[1] + b * hz * za[1]) / 5
				diffs.append(gamedata.height(x + dx, z + dz) - (y0 + gx * dx + gz * dz))
		y0 += min(diffs)
		if max(diffs) - min(diffs) > MAX_GAP:
			rejects["terrain irrégulier"] += 1
			return False
		for i in core:
			covered[i] = 1
		suffix = "_noLC" if rnd.random() < 0.5 else ""
		placed.append({
			"name": name + suffix,
			"pos": [round(x, 3), round(y0 + 0.03, 3), round(z, 3)],
			"ypr": [round(yaw, 1), round(tilt, 2), 0.0],
			"scale": scale,
			"enableCEPersistency": 0,
			"customString": "",
		})
		return True

	# grandes plaques d'abord (toutes tailles), puis les bandes pour combler les espaces étroits
	for kind in ([DECALS, [LONG]] if USE_LONG else [DECALS]):
		for scale in SCALES:
			hmax = max(d[1] for d in kind) * scale
			step = max(2, int(hmax * 0.9))
			for z in range(grid.z0, grid.z0 + grid.n, step):
				for x in range(grid.x0, grid.x0 + grid.n, step):
					px, pz = x + rnd.uniform(0, step), z + rnd.uniform(0, step)
					k = grid.idx(px, pz)
					if k is None or grid.cells[k] != FREE or covered[k]:
						continue
					name, hx, hz = rnd.choice(kind)
					try_place(name, hx, hz, scale, px, pz)

	free = sum(1 for c in grid.cells if c == FREE)
	done = sum(1 for i, c in enumerate(grid.cells) if c == FREE and covered[i])
	out = os.path.join(MISSION, "custom", "neige_%s.json" % town)
	with open(out, "w") as f:
		f.write(json.dumps({"Objects": placed}, indent=4) + "\n")
	print("%s : %d plaques, %d %% de la surface libre de la ville couverte -> %s"
		  % (town, len(placed), 100 * done // max(free, 1), os.path.relpath(out)))
	print("plaques refusées :", dict(rejects))
	write_image(grid, covered, os.path.join(gamedata.CACHE, "neige_%s.png" % town))


def write_image(grid, covered, path):
	"""Image de contrôle (1 px = 2 m, nord en haut) : gris hors ville, rouge bâtiments, brun rues, vert libre, blanc enneigé."""
	colors = {OUTSIDE: b"\x30\x30\x30", BLOCKED: b"\xc0\x30\x30", STREET: b"\x90\x60\x30", FREE: b"\x40\x90\x40"}
	n = grid.n // 2
	rows = []
	for j in reversed(range(n)):
		row = bytearray(b"\0")
		for i in range(n):
			k = (2 * j) * grid.n + 2 * i
			row += b"\xf0\xf0\xff" if covered[k] else colors[grid.cells[k]]
		rows.append(bytes(row))
	chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
	png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
	png += chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")
	open(path, "wb").write(png)


if __name__ == "__main__":
	if len(sys.argv) != 2 or sys.argv[1] not in TOWNS:
		sys.exit("Usage : %s <ville>  (disponibles : %s)" % (sys.argv[0], ", ".join(TOWNS)))
	generate(sys.argv[1])
