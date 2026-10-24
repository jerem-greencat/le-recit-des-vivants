"""Génère des mappings de plaques de neige (Sakhal) pour les localités de Chernarus.

Usage :
  python3 tools/neige/generate.py              toutes les localités d'au moins MIN_BUILDINGS bâtiments,
                                               et réécrit meteo/hiver/mappings.txt
  python3 tools/neige/generate.py zelenogorsk  une seule localité (nom en minuscules, voir --liste)
  python3 tools/neige/generate.py --liste      liste les localités détectées
Écrit custom/neige_<localité>.json. Ces mappings ne sont chargés qu'en ambiance hiver.

Les localités sont détectées automatiquement : zones d'un seul tenant à moins de TOWN_RADIUS m d'un
bâtiment d'au moins HOUSE_AREA m². Leur nom vient des lieux nommés de la config du jeu.

Règles :
- la neige couvre la localité ;
- pas de neige dans les bâtiments de la carte ni dans les gros objets de nos mappings ;
- en ville, les rues goudronnées restent dégagées (hors ville, les routes seront enneigées) ;
- les plaques sont plates : on les incline dans le sens de la pente (lacet tourné vers l'amont, tangage
  positif = avant relevé, comme les postes de garde posés en pente dans zeleno_enceinte.json), et on ne
  les pose que là où le terrain est assez régulier sous la plaque ;
- chaque plaque est un objet synchronisé avec les joueurs proches : trop de plaques au même endroit
  provoquent de la désynchronisation (3 572 à Zelenogorsk, c'était trop ; 1 680 réparties sur trois villes,
  aucun souci), d'où les grandes plaques seules et un plafond par localité.
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

MIN_BUILDINGS = 40        # bâtiments (d'au moins HOUSE_AREA m²) pour qu'une localité ait de la neige
MAX_PER_TOWN = 600        # plaques au plus par localité ; au-delà, on en retire au hasard (neige plus
						  # clairsemée mais répartie sur toute la localité)
NAME_DISTANCE = 1000      # distance maximale (m) au lieu nommé de la config du jeu

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


def houses(objects):
	"""Positions (x, z) des bâtiments d'au moins HOUSE_AREA m²."""
	out = []
	for path, xa, za, pos in objects:
		if is_building(path):
			box = gamedata.model_bbox(path)
			if box and (box[1][0] - box[0][0]) * (box[1][2] - box[0][2]) >= HOUSE_AREA:
				out.append((pos[0], pos[2]))
	return out


def localities():
	"""Localités de la carte, de la plus grande à la plus petite : dicts nom, graine, boîte, bâtiments."""
	step, size = 5, 15360
	n = size // step
	near = bytearray(n * n)
	count = Counter()
	r = TOWN_RADIUS // step + 1
	disk = [(di, dj) for dj in range(-r, r + 1) for di in range(-r, r + 1) if math.hypot(di * step, dj * step) <= TOWN_RADIUS]
	all_houses = houses(gamedata.map_objects())
	for x, z in all_houses:
		ci, cj = int(x / step), int(z / step)
		count[cj * n + ci] += 1
		for di, dj in disk:
			i, j = ci + di, cj + dj
			if 0 <= i < n and 0 <= j < n:
				near[j * n + i] = 1
	seen = bytearray(n * n)
	found = []
	for start in range(n * n):
		if not near[start] or seen[start]:
			continue
		seen[start] = 1
		stack, nb, box, seed = [start], 0, [n, n, 0, 0], None
		while stack:
			k = stack.pop()
			i, j = k % n, k // n
			if count[k]:
				nb += count[k]
				seed = seed or ((i + 0.5) * step, (j + 0.5) * step)
			box = [min(box[0], i), min(box[1], j), max(box[2], i), max(box[3], j)]
			for kk in (k + 1, k - 1, k + n, k - n):
				if 0 <= kk < n * n and near[kk] and not seen[kk]:
					seen[kk] = 1
					stack.append(kk)
		found.append({"buildings": nb, "seed": seed,
					  "box": (box[0] * step, box[1] * step, (box[2] + 1) * step, (box[3] + 1) * step)})
	found.sort(key=lambda t: -t["buildings"])

	# noms : lieu habité le plus proche du centre de la boîte et pas encore pris, sinon autre lieu nommé
	# (aérodrome, base, ruine…), sinon le plus proche avec un suffixe (berezino_2)
	config = gamedata._rap_classes(gamedata.pbo_read("dz\\worlds\\chernarusplus\\world\\config.bin"))
	places = [(k.rsplit("/", 1)[-1], v) for k, v in config.items() if "/names/" in k.lower() and "position" in v]
	towns = [(k.split("_", 1)[1].lower(), v["position"]) for k, v in places
			 if k.lower().startswith("settlement_") and v.get("type") in ("Capital", "City", "Village")]
	others = [(k.split("_", 1)[1].lower(), v["position"]) for k, v in places
			  if v.get("type") not in ("ViewPoint", "Hill") and "_" in k]
	used = Counter()
	for t in found:
		cx, cz = (t["box"][0] + t["box"][2]) / 2, (t["box"][1] + t["box"][3]) / 2
		dist = lambda p: math.hypot(p[1][0] - cx, p[1][1] - cz)
		name = None
		for pool in ([p for p in towns if not used[p[0]]], [p for p in others if not used[p[0]]], towns):
			best = min(pool, key=dist, default=None)
			if best and (dist(best) <= NAME_DISTANCE or pool is towns):
				name = best[0]
				break
		used[name] += 1
		t["name"] = name if used[name] == 1 else "%s_%d" % (name, used[name])
	return found


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
	# le centre donné peut tomber hors zone (place, parc) : on part de la cellule « ville » la plus proche
	si, sj = min(((i, j) for j in range(m) for i in range(m) if near[j * m + i]),
				 key=lambda c: (c[0] - si) ** 2 + (c[1] - sj) ** 2)
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


def generate(loc, budget=MAX_PER_TOWN):
	town = loc["name"]
	x0, z0, x1, z1 = loc["box"]
	rnd = random.Random(town)
	grid = Grid((x0 + x1) / 2, (z0 + z1) / 2, int(max(x1 - x0, z1 - z0) / 2) + 60)

	objects = [o for o in gamedata.map_objects()
			   if grid.x0 - 30 <= o[3][0] <= grid.x0 + grid.n + 30 and grid.z0 - 30 <= o[3][2] <= grid.z0 + grid.n + 30]
	town_mask(grid, houses(objects), loc["seed"])

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
	cores = []

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
		cores.append(core)
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

	if budget and len(placed) > budget:
		keep = sorted(rnd.sample(range(len(placed)), budget))
		placed = [placed[k] for k in keep]
		covered = bytearray(grid.n * grid.n)
		for k in keep:
			for i in cores[k]:
				covered[i] = 1
	free = sum(1 for c in grid.cells if c == FREE)
	done = sum(1 for i, c in enumerate(grid.cells) if c == FREE and covered[i])
	out = os.path.join(MISSION, "custom", "neige_%s.json" % town)
	with open(out, "w") as f:
		f.write(json.dumps({"Objects": placed}, indent=4) + "\n")
	print("%-20s %4d plaques, %2d %% de la surface libre couverte" % (town, len(placed), 100 * done // max(free, 1)))
	write_image(grid, covered, os.path.join(gamedata.CACHE, "neige_%s.png" % town))
	return len(placed)


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
	locs = localities()
	args = sys.argv[1:]
	if args == ["--liste"]:
		for t in locs:
			if t["buildings"] >= MIN_BUILDINGS:
				print("%-20s %4d bâtiments" % (t["name"], t["buildings"]))
		sys.exit()
	if args:
		chosen = [t for t in locs if t["name"] in args]
		if len(chosen) != len(args):
			sys.exit("Localité inconnue ; voir %s --liste" % sys.argv[0])
	else:
		chosen = [t for t in locs if t["buildings"] >= MIN_BUILDINGS]
	total = 0
	for t in chosen:
		t["plates"] = generate(t)
		total += t["plates"]
		if not t["plates"]:
			os.remove(os.path.join(MISSION, "custom", "neige_%s.json" % t["name"]))
	print("total : %d plaques" % total)
	if not args:
		with open(os.path.join(MISSION, "meteo", "hiver", "mappings.txt"), "w") as f:
			f.write("# Mappings chargés seulement avec cette ambiance (générés par tools/neige/generate.py)\n")
			for t in sorted(chosen, key=lambda t: t["name"]):
				if t["plates"]:
					f.write("./custom/neige_%s.json\n" % t["name"])
