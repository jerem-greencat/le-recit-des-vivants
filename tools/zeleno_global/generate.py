"""Génère le mapping d'ambiance globale de Zelenogorsk : feux et lumières post-apocalyptiques dans la ville.

Usage : python3 tools/zeleno_global/generate.py
Écrit custom/zeleno_global.json (réécrit entièrement : retoucher les paramètres ci-dessous plutôt que le
fichier, ou ne plus relancer le script une fois le fichier retouché dans DayZ Editor).

Principe (repris des deux assemblages faits à la main dans custom/zeleno_police.json) : un feu de sorcière
(Bonfire) rapetissé et enterré sous un élément de décor, dont seules les flammes dépassent. Calibrage :
- le maillage du Bonfire (boîte ±4,23 m × échelle) reste à plus de FIRE_HIDDEN m sous le sol ;
- petites flammes (ordures de la police : Garbage_Pile6, Bonfire échelle 0,05) : origine du Bonfire à
  FLAME_SMALL m sous le haut de l'élément qui le cache ;
- véhicule en flammes (crash de la police : Bonfire échelle 0,3) : origine à FIRE_CAR m sous le sol, un peu
  moins enfoncé pour les bus et camions (FIRE_BIG).

Scènes (SCENES : nombre de chaque) :
- « crash » : deux véhicules accidentés, disposés comme le crash de la police, modèles tirés au hasard ;
- « voiture », « poids lourd » : un véhicule seul en feu au bord d'une rue ;
- « ordures » : tas d'ordures en feu, avec parfois une poubelle renversée ou des déchets au sol ;
- « benne » : benne à ordures qui brûle, souvent à côté d'une autre ;
- « gravats » : gravats de bois ou de briques qui se consument ;
- « pneus » : tas de pneus en feu (Misc_TirePile_Burning_DE), qui éclaire tout seul ;
- « brasero » : bidon de feu (Land_Misc_FireBarrel_*), qui éclaire tout seul.

Règles :
- uniquement dans l'enceinte (custom/zeleno_enceinte.json), à plus de WALL_MARGIN m du mur ;
- à plus de RP_MARGIN m des objets des zones RP (police, hôpital, église…) : elles ont leur propre décor ;
- pas dans un bâtiment, un mur, une clôture, un arbre ni sur les objets de nos mappings ;
- les rues restent praticables : un véhicule déborde au plus de ROAD_EDGE m sur la chaussée, le reste
  reste hors des routes ; les véhicules sont au bord d'une rue, ordures, bennes et braseros près d'une maison ;
- terrain assez plat sous la scène (les objets sont posés à plat) ;
- au moins MIN_SPACING m entre deux feux, et VEHICLE_SPACING m entre deux scènes de véhicules ;
- chaque objet est synchronisé avec les joueurs : ~2 600 entités de nos mappings sont déjà à moins de 1 km
  de la ville (neige d'hiver comprise), on reste sobre.
"""
import json
import math
import os
import random
import statistics
import sys
from collections import defaultdict, deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "neige"))
import gamedata  # noqa: E402
import generate as neige  # noqa: E402  (classement des bâtiments)

MISSION = os.path.join(HERE, "..", "..", "dayzxb_missions", "dayzOffline.chernarusplus")
CUSTOM = os.path.join(MISSION, "custom")

SCENES = {"crash": 3, "voiture": 4, "poids lourd": 1, "ordures": 8, "benne": 6, "gravats": 6, "pneus": 5,
		  "brasero": 7}
MIN_SPACING = 45          # m minimum entre deux feux
VEHICLE_SPACING = 150     # m minimum entre deux scènes de véhicules
WALL_MARGIN = 12          # m minimum entre un feu et le mur d'enceinte
RP_MARGIN = 20            # m minimum entre un feu et les objets d'une zone RP
ROAD_EDGE = 1.2           # m dont un véhicule peut déborder sur la chaussée
NEAR_ROAD = 4.0           # un véhicule est à moins de NEAR_ROAD m d'une route
NEAR_HOUSE = 8.0          # ordures, bennes et braseros à moins de NEAR_HOUSE m d'un bâtiment
MAX_BUMP = 0.35           # dénivelé maximal du terrain sous une scène (m)

BONFIRE_HALF = 4.23       # demi-hauteur du maillage du Bonfire à l'échelle 1
FIRE_HIDDEN = 0.3         # m minimum entre le haut du maillage du Bonfire et le sol
FLAME_SMALL = 6.48        # m entre le haut de l'élément et l'origine du Bonfire (ordures de la police)
FIRE_CAR = (-1.78, 0.3)   # origine sous le sol, échelle (crash de la police)
FIRE_BIG = (-1.0, 0.12)   # bus et camions : flammes plus hautes

RP_FILES = ["zeleno_police.json", "zeleno_hospital.json", "zeleno_church.json", "zeleno_city_hall.json",
			"zeleno_builder.json", "zeleno_gunshop.json", "zeleno_epicerie.json", "zeleno_garagiste_v2.json"]

CARS = (["Land_Wreck_hb01_aban1_%s_DE" % c for c in ("blue", "green", "white")]
		+ ["Land_Wreck_hb01_aban2_%s_DE" % c for c in ("blue", "green", "white")]
		+ ["Land_Wreck_hb02_aban%d_%s_DE" % (n, c) for n in (1, 2) for c in ("black", "blue", "red")]
		+ ["Land_Wreck_sed01_aban%d_%s_DE" % (n, c) for n in (1, 2) for c in ("black", "white", "wine")]
		+ ["Land_Wreck_sed02_aban%d_%s_DE" % (n, c) for n in (1, 2) for c in ("grey", "red", "yellow")]
		+ ["Land_Wreck_Volha_Blue", "Land_Wreck_Volha_Grey", "Land_Wreck_Lada_Green", "Land_Wreck_Lada_Red",
		   "Land_Wreck_S1023_Beige", "Land_Wreck_S1023_Blue", "Land_Wreck_Uaz", "Land_Wreck_offroad02_aban1_DE",
		   "Land_Wreck_offroad02_aban2_DE", "Land_Wreck_Uaz_TK", "Land_Wreck_LR_TK"]
		+ ["Land_Wreck_Pickup01_Aban_%s" % c for c in ("Blue", "Red", "White", "Yellow")])
BIG = (["Land_Wreck_Ikarus"]
	   + ["Land_wreck_truck01_aban%d_%s_DE" % (n, c) for n in (1, 2) for c in ("blue", "green", "orange")])
PILES = ["StaticObj_Garbage_Pile1", "StaticObj_Garbage_Pile2", "StaticObj_Garbage_Pile4",
		 "StaticObj_Garbage_Pile5", "StaticObj_Garbage_Pile6"]
DUMPSTERS = ["StaticObj_Garbage_Container", "StaticObj_Garbage_Container_Glass",
			 "StaticObj_Garbage_Container_Paper", "StaticObj_Garbage_Container_Plastic"]
RUBBLE = ["StaticObj_Rubble_Wood1", "StaticObj_Rubble_Wood2", "StaticObj_Rubble_Bricks1", "StaticObj_Rubble_Metal3"]
GROUND_TRASH = ["StaticObj_Garbage_GroundSq_3m_NoLC", "StaticObj_Garbage_GroundSq_5m_NoLC"]
TIRE_PILE = "Misc_TirePile_Burning_DE"
BARRELS = ["Land_Misc_FireBarrel_Red", "Land_Misc_FireBarrel_Blue", "Land_Misc_FireBarrel_Green",
		   "Land_Misc_FireBarrel_Yellow"]
# pose reprise telle quelle des assemblages de la police (y - terrain, tangage, roulis)
BIN_DOWN = (0.706, 0.0, 49.0)        # poubelle renversée
TIRE_DOWN = (0.562, 0.0, -32.0)      # pneu appuyé


def axes(yaw_deg):
	r = math.radians(yaw_deg)
	return (math.cos(r), -math.sin(r)), (math.sin(r), math.cos(r))


def load(name):
	return json.load(open(os.path.join(CUSTOM, name)))["Objects"]


def model_key(name):
	m = gamedata.class_model(name)
	return m.lstrip("\\").lower().removesuffix(".p3d") if m else None


class SpatialIndex:
	def __init__(self, cell):
		self.cell, self.data = cell, defaultdict(list)

	def add(self, x, z, item):
		self.data[(int(x // self.cell), int(z // self.cell))].append(item)

	def near(self, x, z, r):
		cx, cz, n = int(x // self.cell), int(z // self.cell), int(r // self.cell) + 1
		for i in range(cx - n, cx + n + 1):
			for j in range(cz - n, cz + n + 1):
				yield from self.data.get((i, j), ())


class Box:
	"""Boîte orientée au sol : centre, axes du modèle, limites en x et z (déjà à l'échelle)."""

	def __init__(self, x, z, xa, za, lo, hi):
		self.x, self.z, self.xa, self.za, self.lo, self.hi = x, z, xa, za, lo, hi
		self.r = math.hypot(max(-lo[0], hi[0]), max(-lo[1], hi[1]))

	def local(self, x, z):
		dx, dz = x - self.x, z - self.z
		return dx * self.xa[0] + dz * self.xa[1], dx * self.za[0] + dz * self.za[1]

	def distance(self, x, z):
		mx, mz = self.local(x, z)
		return math.hypot(max(self.lo[0] - mx, 0, mx - self.hi[0]), max(self.lo[1] - mz, 0, mz - self.hi[1]))

	def points(self, step=0.5):
		nx = max(1, int((self.hi[0] - self.lo[0]) / step))
		nz = max(1, int((self.hi[1] - self.lo[1]) / step))
		for i in range(nx + 1):
			for j in range(nz + 1):
				mx = self.lo[0] + (self.hi[0] - self.lo[0]) * i / nx
				mz = self.lo[1] + (self.hi[1] - self.lo[1]) * j / nz
				yield self.x + mx * self.xa[0] + mz * self.za[0], self.z + mx * self.xa[1] + mz * self.za[1]


def object_box(name, x, z, yaw, scale):
	model = gamedata.class_model(name)
	box = gamedata.model_bbox(model) if model else None
	if not box:
		return None
	(lx, _, lz), (hx, _, hz) = box
	xa, za = axes(yaw)
	return Box(x, z, xa, za, (lx * scale, lz * scale), (hx * scale, hz * scale))


def inside_mask():
	"""Cellules de 2 m à l'intérieur de l'enceinte, à plus de WALL_MARGIN m du mur : remplissage depuis
	l'extérieur, les objets de l'enceinte grossis de WALL_MARGIN (ce qui bouche aussi les portails)."""
	objs = [o for o in load("zeleno_enceinte.json") if not o["name"].lower().endswith(".p3d")]
	xs, zs = [o["pos"][0] for o in objs], [o["pos"][2] for o in objs]
	s, pad = 2, WALL_MARGIN + 30
	x0, z0 = int(min(xs) - pad), int(min(zs) - pad)
	w, h = int((max(xs) + pad - x0) / s), int((max(zs) + pad - z0) / s)
	wall = bytearray(w * h)
	for o in objs:
		b = object_box(o["name"], o["pos"][0], o["pos"][2], o["ypr"][0], o["scale"])
		if not b:
			continue
		ext = b.r + WALL_MARGIN
		for j in range(int((b.z - ext - z0) / s), int((b.z + ext - z0) / s) + 1):
			for i in range(int((b.x - ext - x0) / s), int((b.x + ext - x0) / s) + 1):
				if 0 <= i < w and 0 <= j < h and b.distance(x0 + (i + 0.5) * s, z0 + (j + 0.5) * s) <= WALL_MARGIN:
					wall[j * w + i] = 1
	outside = bytearray(w * h)
	outside[0], queue = 1, deque([0])
	while queue:
		k = queue.popleft()
		i, j = k % w, k // w
		for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
			n = b * w + a
			if 0 <= a < w and 0 <= b < h and not outside[n] and not wall[n]:
				outside[n] = 1
				queue.append(n)
	return [(x0 + (k % w + 0.5) * s, z0 + (k // w + 0.5) * s) for k in range(w * h) if not outside[k] and not wall[k]]


def ground_offsets(names):
	"""Hauteur de pose (y - terrain) de chaque classe : médiane de nos mappings faits à la main, sinon des
	placements de Bohemia sur la carte (même modèle), sinon celle d'une variante de couleur de même hauteur,
	sinon 0 si l'origine du modèle est au sol. Les classes sans hauteur fiable sont écartées."""
	keys = {n: model_key(n) for n in names}
	ours, theirs = defaultdict(list), defaultdict(list)
	for f in ("zeleno_enceinte.json", "zeleno_police.json"):
		for o in load(f):
			k = model_key(o["name"]) if not o["name"].lower().endswith(".p3d") else None
			if k and abs(o.get("scale", 1) - 1) < 0.01 and o["ypr"][1] == 0 and o["ypr"][2] == 0:
				ours[k].append(o["pos"][1] - gamedata.height(o["pos"][0], o["pos"][2]))
	wanted = set(keys.values())
	for path, xa, za, pos in gamedata.map_objects():
		k = path.lower().removesuffix(".p3d")
		if k in wanted:
			theirs[k].append(pos[1] - gamedata.height(pos[0], pos[2]))
	out = {}
	for n, k in keys.items():
		if not k:
			continue
		if ours[k]:
			out[n] = statistics.median(ours[k])
		elif len(theirs[k]) >= 5:
			out[n] = statistics.median(theirs[k])
	heights = {n: gamedata.model_bbox(gamedata.class_model(n)) for n, k in keys.items() if k}
	for n, box in heights.items():
		if n in out or not box:
			continue
		family = lambda c: c.removesuffix("_DE").rsplit("_", 1)[0]
		twin = [m for m in out if family(m) == family(n) and heights.get(m) and abs(heights[m][0][1] - box[0][1]) < 0.01]
		if twin:
			out[n] = out[twin[0]]
		elif box[0][1] > -0.15:
			out[n] = 0.0
	return out


def police_crash():
	"""Disposition du crash fait à la main près de la police : (dx, dz, lacet) de chaque véhicule autour du
	Bonfire, et décor (verre, ordures, pneu, poubelle) tel quel."""
	objs = load("zeleno_police.json")
	fires = [o for o in objs if o["name"] == "Bonfire"]
	for fire in fires:
		fx, fz = fire["pos"][0], fire["pos"][2]
		near = [o for o in objs if math.hypot(o["pos"][0] - fx, o["pos"][2] - fz) < 3.0 and o is not fire]
		cars = [o for o in near if o["name"].startswith("Land_Wreck_")]
		if len(cars) >= 2:
			deco = [o for o in near if o["name"] in ("StaticObj_Rubble_Glass", "StaticObj_Garbage_Pile3")]
			return ([(o["pos"][0] - fx, o["pos"][2] - fz, o["ypr"][0]) for o in cars],
					[(o["name"], o["pos"][0] - fx, o["pos"][2] - fz,
					  o["pos"][1] - gamedata.height(o["pos"][0], o["pos"][2]), o["ypr"]) for o in deco])
	raise SystemExit("crash modèle introuvable dans zeleno_police.json")


def main():
	rnd = random.Random("zeleno_global")
	every = CARS + BIG + PILES + DUMPSTERS + RUBBLE + GROUND_TRASH + BARRELS + [TIRE_PILE, "StaticObj_Garbage_Bin",
		"StaticObj_Misc_Tire", "StaticObj_Rubble_Glass", "StaticObj_Garbage_Pile3"]
	lift = ground_offsets(every)
	missing = [n for n in every if n not in lift]
	if missing:
		print("écartés (hauteur de pose inconnue) :", ", ".join(missing))
	cars = [c for c in CARS if c in lift]
	big = [c for c in BIG if c in lift]
	crash_cars, crash_deco = police_crash()

	def top(name, scale=1.0):
		return lift[name] + gamedata.model_bbox(gamedata.class_model(name))[1][1] * scale

	def fire(dx, dz, dy, scale):
		scale = min(scale, (-dy - FIRE_HIDDEN) / BONFIRE_HALF)
		return ("Bonfire", dx, dz, dy, [0.0, 0.0, 0.0], round(scale, 3))

	def part(name, dx=0.0, dz=0.0, yaw=0.0, pose=None):
		dy, pitch, roll = pose if pose else (lift[name], 0.0, 0.0)
		return (name, dx, dz, dy, [yaw, pitch, roll], 1.0)

	def ring(r0, r1):
		a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(r0, r1)
		return r * math.cos(a), r * math.sin(a)

	# chaque scène : liste de (classe, dx, dz, y - terrain, [lacet, tangage, roulis], échelle), repère de la
	# scène (axe z = sens de la rue pour les véhicules)
	def scene(kind):
		if kind == "crash":
			parts = [part(rnd.choice(cars), dx, dz, yaw + rnd.uniform(-10, 10)) for dx, dz, yaw in crash_cars]
			parts += [(n, dx, dz, dy, list(ypr), 1.0) for n, dx, dz, dy, ypr in crash_deco]
			return parts + [fire(0, 0, *FIRE_CAR)]
		if kind == "voiture":
			parts = [part(rnd.choice(cars), 0, 0, rnd.uniform(-20, 20) + rnd.choice((0, 180)))]
			if rnd.random() < 0.6:
				parts.append(part("StaticObj_Rubble_Glass", rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 360)))
			if rnd.random() < 0.5:
				parts.append(part("StaticObj_Misc_Tire", *ring(2.5, 3.5), rnd.uniform(0, 360), TIRE_DOWN))
			return parts + [fire(0, rnd.uniform(-0.8, 0.8), *FIRE_CAR)]
		if kind == "poids lourd":
			parts = [part(rnd.choice(big), 0, 0, rnd.uniform(-10, 10) + rnd.choice((0, 180)))]
			parts.append(part("StaticObj_Rubble_Glass", rnd.uniform(-1, 1), rnd.uniform(-2, 2), rnd.uniform(0, 360)))
			return parts + [fire(0, rnd.uniform(-1.5, 1.5), *FIRE_BIG)]
		if kind == "ordures":
			pile = rnd.choice(PILES)
			parts = [part(pile, 0, 0, rnd.uniform(0, 360))]
			if rnd.random() < 0.5:
				parts.append(part(rnd.choice(GROUND_TRASH), *ring(1.0, 2.0), rnd.uniform(0, 360)))
			if rnd.random() < 0.5:
				parts.append(part("StaticObj_Garbage_Bin", *ring(2.5, 3.5), rnd.uniform(0, 360), BIN_DOWN))
			return parts + [fire(0, 0, top(pile) - FLAME_SMALL, 0.05)]
		if kind == "benne":
			yaw = rnd.uniform(0, 360)
			parts = [part(rnd.choice(DUMPSTERS), 0, 0, yaw)]
			if rnd.random() < 0.6:   # une deuxième benne à côté (axe x du modèle = largeur 1,2 m)
				xa, _ = axes(yaw)
				parts.append(part(rnd.choice(DUMPSTERS), 1.5 * xa[0], 1.5 * xa[1], yaw + rnd.uniform(-8, 8)))
			if rnd.random() < 0.5:
				parts.append(part("StaticObj_Garbage_Pile3", *ring(1.8, 2.5), rnd.uniform(0, 360)))
			return parts + [fire(0, 0, top(parts[0][0]) - FLAME_SMALL, 0.05)]
		if kind == "gravats":
			rubble = rnd.choice(RUBBLE)
			parts = [part(rubble, 0, 0, rnd.uniform(0, 360))]
			if rnd.random() < 0.4:
				parts.append(part(rnd.choice(GROUND_TRASH), *ring(1.5, 2.5), rnd.uniform(0, 360)))
			return parts + [fire(0, 0, top(rubble) - FLAME_SMALL, 0.05)]
		if kind == "pneus":
			parts = [part(TIRE_PILE, 0, 0, rnd.uniform(0, 360))]
			for _ in range(rnd.randint(1, 3)):
				parts.append(part("StaticObj_Misc_Tire", *ring(2.2, 3.5), rnd.uniform(0, 360),
								  TIRE_DOWN if rnd.random() < 0.5 else None))
			return parts
		if kind == "brasero":
			parts = [part(rnd.choice(BARRELS), 0, 0, rnd.uniform(0, 360))]
			if rnd.random() < 0.4:
				parts.append(part(rnd.choice(GROUND_TRASH), *ring(1.5, 2.0), rnd.uniform(0, 360)))
			return parts
		raise ValueError(kind)

	cells = inside_mask()
	area = (min(c[0] for c in cells) - 60, min(c[1] for c in cells) - 60,
			max(c[0] for c in cells) + 60, max(c[1] for c in cells) + 60)

	def in_area(x, z):
		return area[0] <= x <= area[2] and area[1] <= z <= area[3]

	obstacles, roads, houses = SpatialIndex(20), SpatialIndex(20), SpatialIndex(20)
	for path, xa, za, pos in gamedata.map_objects():
		if not in_area(pos[0], pos[2]):
			continue
		p = path.lower()
		if "\\tree\\" in p:   # tronc
			obstacles.add(pos[0], pos[2], Box(pos[0], pos[2], xa, za, (-1.2, -1.2), (1.2, 1.2)))
			continue
		if "\\plants" in p or "\\clutter\\" in p or "\\sidewalks\\" in p or "\\decals\\" in p:
			continue
		box = gamedata.model_bbox(path)
		if not box:
			continue
		b = Box(pos[0], pos[2], xa, za, (box[0][0], box[0][2]), (box[1][0], box[1][2]))
		if "\\roads\\parts\\" in p:
			roads.add(pos[0], pos[2], b)
		elif box[1][1] - box[0][1] >= 0.3:   # objets plats (dalles, marquages) : on peut poser dessus
			obstacles.add(pos[0], pos[2], b)
			# vraies maisons seulement (is_building compte aussi poteaux, cabanes, lignes de stade…)
			if neige.is_building(path) and (box[1][0] - box[0][0]) * (box[1][2] - box[0][2]) >= neige.HOUSE_AREA \
					and box[1][1] - box[0][1] >= 3:
				houses.add(pos[0], pos[2], b)
	for name in os.listdir(CUSTOM):
		if not name.endswith(".json") or name.startswith(("neige_", "spawngear", "zeleno_global")):
			continue
		try:
			objs = json.load(open(os.path.join(CUSTOM, name))).get("Objects", [])
		except Exception:
			continue
		for o in objs:
			if o["name"].lower().endswith(".p3d") or not in_area(o["pos"][0], o["pos"][2]):
				continue
			b = object_box(o["name"], o["pos"][0], o["pos"][2], o["ypr"][0], o.get("scale", 1) or 1)
			if b:
				obstacles.add(b.x, b.z, b)
	rp = SpatialIndex(25)
	for name in RP_FILES:
		for o in load(name):
			rp.add(o["pos"][0], o["pos"][2], (o["pos"][0], o["pos"][2]))

	def on_roadway(x, z, edge):
		"""Le point est-il sur une chaussée, à plus de edge m de son bord (axe x des routes = largeur) ?"""
		for r in roads.near(x, z, 30):
			mx, mz = r.local(x, z)
			if r.lo[0] + edge <= mx <= r.hi[0] - edge and r.lo[1] <= mz <= r.hi[1]:
				return True
		return False

	def road_yaw(x, z):
		"""Lacet de la route la plus proche (axe z du modèle = sens de la route)."""
		best = min(roads.near(x, z, 30), key=lambda r: r.distance(x, z), default=None)
		return math.degrees(math.atan2(-best.xa[1], best.xa[0])) if best else rnd.uniform(0, 360)

	def build(kind, x, z, yaw):
		"""Objets de la scène posée en (x, z), repère tourné de yaw, ou None si elle ne rentre pas."""
		xa, za = axes(yaw)
		vehicle = kind in ("crash", "voiture", "poids lourd")
		out, ground = [], []
		for name, dx, dz, dy, ypr, scale in scene(kind):
			px = x + dx * xa[0] + dz * za[0]
			pz = z + dx * xa[1] + dz * za[1]
			oyaw = (ypr[0] + yaw + 180) % 360 - 180
			if name != "Bonfire":
				b = object_box(name, px, pz, oyaw, scale)
				flat = gamedata.model_bbox(gamedata.class_model(name))[1][1] < 0.15   # verre, déchets au sol
				for qx, qz in b.points():
					if not flat:
						if any(o.distance(qx, qz) < 0.3 for o in obstacles.near(qx, qz, 30)):
							return None
						if on_roadway(qx, qz, ROAD_EDGE if vehicle else -0.5):
							return None
					ground.append(gamedata.height(qx, qz))
			out.append({
				"name": name,
				"pos": [round(px, 4), round(gamedata.height(px, pz) + dy, 4), round(pz, 4)],
				"ypr": [round(oyaw, 3), round(ypr[1], 3), round(ypr[2], 3)],
				"scale": scale,
				"enableCEPersistency": 0,
				"customString": "",
			})
		if ground and max(ground) - min(ground) > MAX_BUMP:
			return None
		return out

	def suits(kind, x, z):
		if any(math.hypot(px - x, pz - z) < RP_MARGIN for px, pz in rp.near(x, z, RP_MARGIN)):
			return False
		if kind in ("crash", "voiture", "poids lourd"):
			return (not any(math.hypot(vx - x, vz - z) < VEHICLE_SPACING for vx, vz in vehicles.near(x, z, VEHICLE_SPACING))
					and any(r.distance(x, z) < NEAR_ROAD for r in roads.near(x, z, 30)))
		near_house = any(h.distance(x, z) < NEAR_HOUSE for h in houses.near(x, z, 40))
		if kind in ("ordures", "benne", "brasero"):
			return near_house
		# pneus, gravats : en ville aussi, pas au milieu des champs
		return near_house or any(r.distance(x, z) < 2 * NEAR_ROAD for r in roads.near(x, z, 30))

	fires, vehicles = SpatialIndex(MIN_SPACING), SpatialIndex(VEHICLE_SPACING)
	placed, done = [], defaultdict(int)
	pending = {}
	for kind in SCENES:
		rnd.shuffle(cells)
		pending[kind] = iter(list(cells))
	progress = True
	while progress and any(done[k] < n for k, n in SCENES.items()):
		progress = False
		for kind, n in SCENES.items():   # tour à tour, pour mélanger les scènes dans toute la ville
			if done[kind] >= n:
				continue
			for x, z in pending[kind]:
				x, z = x + rnd.uniform(-1, 1), z + rnd.uniform(-1, 1)
				if any(math.hypot(fx - x, fz - z) < MIN_SPACING for fx, fz in fires.near(x, z, MIN_SPACING)):
					continue
				if not suits(kind, x, z):
					continue
				objs = None
				for _ in range(6):
					yaw = road_yaw(x, z) if kind in ("voiture", "poids lourd") else rnd.uniform(-180, 180)
					objs = build(kind, x, z, yaw)
					if objs:
						break
				if objs:
					placed += objs
					fires.add(x, z, (x, z))
					if kind in ("crash", "voiture", "poids lourd"):
						vehicles.add(x, z, (x, z))
					done[kind] += 1
					progress = True
					break

	out = os.path.join(CUSTOM, "zeleno_global.json")
	with open(out, "w") as f:
		f.write(json.dumps({"Objects": placed}, indent=4) + "\n")
	print("%d objets, %d feux (%s) -> %s" % (len(placed), sum(done.values()),
										   ", ".join("%d %s" % (done[k], k) for k in SCENES), os.path.relpath(out)))


if __name__ == "__main__":
	main()
