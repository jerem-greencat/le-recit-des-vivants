"""Génère les mappings et les zones de zombies de l'ambiance brouillard.

Usage : python3 tools/brouillard/generate.py
Écrit (chargés seulement en ambiance brouillard, par tools/meteo.sh) :
- custom/brouillard_carambolages.json : carambolages sur les routes, feux de détresse (piles de pneus en
  feu au bord de la route, parfois une voiture en feu) ;
- custom/brouillard_barrages.json : barrages abandonnés aux entrées des localités ;
- meteo/brouillard/zombie_territories.xml : zones de zombies le long des routes et autour des carambolages ;
- meteo/brouillard/mappings.txt.

Règles :
- rien dans la zone safe de Zelenogorsk ni à moins de SAFE_MARGIN m (zombies : bord de la zone), et pas de
  barrage à moins de BARRAGE_SAFE_MARGIN m ;
- carambolages sur les routes goudronnées ou en gravier, sur une portion droite hors des villes, au moins
  PILEUP_SPACING m entre deux ; chaque voiture doit rester sur la route, hors des bâtiments, des ponts et des
  gros objets de nos mappings, sur une pente faible ; les voitures suivent la pente ;
- hauteur de pose : médiane des mêmes épaves placées par Bohemia sur la carte (celles de nos mappings sont
  souvent posées sur des dalles), sinon mesurée sur nos mappings ;
- feu de voiture : un Bonfire réduit (0.3) et enterré sous l'épave (astuce de zeleno_police.json : origine
  1,78 m sous le sol, seules les flammes dépassent) ;
- zombies : zones dynamiques (dmin/dmax, rien de statique) au nom d'événements vanilla déjà actifs
  (InfectedSolitude, InfectedVillage), hors des villes et à plus de OWN_MARGIN m de nos mappings.
"""
import json
import math
import os
import random
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "neige"))
import gamedata  # noqa: E402
import generate as neige  # noqa: E402  (bâtiments, localités, objets de nos mappings)

MISSION = os.path.join(HERE, "..", "..", "dayzxb_missions", "dayzOffline.chernarusplus")

# zone safe de Zelenogorsk (README) : ville, gare / zone industrielle, zone militaire
SAFE = [(2480, 5060, 2960, 5640), (2180, 5140, 2520, 5320), (2360, 4980, 2640, 5220)]
SAFE_MARGIN = 250          # m entre la zone safe et un carambolage / le bord d'une zone de zombies
BARRAGE_SAFE_MARGIN = 2500 # m : pas de barrage autour de Zelenogorsk
OWN_MARGIN = 200           # m entre nos mappings et une zone de zombies

PILEUP_SPACING = 900       # m minimum entre deux carambolages
BURNING_CAR = 0.35         # part des carambolages avec une voiture en feu
MAX_TILT = 12              # pente maximale sous un objet (degrés)
TOWN_RADIUS = 60           # m : un morceau de route avec un bâtiment plus près est « en ville »

BARRAGES_PER_TOWN = 2      # barrages au plus par localité
BARRAGE_SPACING = 300      # m minimum entre deux barrages d'une même localité
TOWN_MIN_BUILDINGS = 40    # bâtiments minimum pour qu'une localité ait des barrages

ZOMBIE_SPACING = 600       # m minimum entre deux zones de zombies le long des routes
ZOMBIE_ROAD = (60, 2, 4)   # rayon, dmin, dmax des zones le long des routes
ZOMBIE_PILEUP = (50, 6, 10) # rayon, dmin, dmax des zones autour des carambolages
ZOMBIE_EVENTS = [("InfectedSolitude", 3), ("InfectedVillage", 2)]   # (événement, poids)

# hauteur de l'origine au-dessus du sol, par classe (voir docstring)
WRECKS = {
	"Land_Wreck_hb01_aban1_white": 1.06,
	"Land_Wreck_hb01_aban2_blue": 0.93,
	"Land_Wreck_hb01_aban2_green": 0.93,
	"Land_Wreck_hb02_aban1_black": 0.76,
	"Land_Wreck_hb02_aban1_red": 0.76,
	"Land_Wreck_sed01_aban1_white": 0.75,
	"Land_Wreck_sed01_aban1_black": 0.75,
	"Land_Wreck_sed02_aban1_red": 0.86,
	"Land_Wreck_sed02_aban1_yellow": 0.86,
	"Land_Wreck_sed02_aban2_grey": 0.66,
	"Land_Wreck_Lada_Red": 0.67,
}
BUS = ("Land_Wreck_Ikarus", 1.42)
BUS_CHANCE = 0.12
TIRE_FIRE = ("Misc_TirePile_Burning_DE", 0.04)
CAR_FIRE = ("Bonfire", -1.78, 0.3)
BLOCK = ("StaticObj_Roadblock_CncBlock", 0.34)
HEDGEHOG = ("StaticObj_Misc_Hedgehog_Iron", 0.6)
STOP = ("StaticObj_Sign_Roadblock_Stop", 0.53)
CONE = ("StaticObj_RoadCone", 0.41)
BARRICADE = ("StaticObj_Misc_Barricade", 0.67)

STRAIGHT = re.compile(r"^(asf[123]|grav)_(25|12|1 1000|0 2000)\.p3d$")
MAIN_ROAD = re.compile(r"^(asf[123]|grav|city)_")


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


def safe_distance(x, z):
	return min(math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1)) for x0, z0, x1, z1 in SAFE)


def yaw_towards(dx, dz):
	"""Lacet qui oriente l'axe z (l'avant) du modèle vers (dx, dz)."""
	return math.degrees(math.atan2(dx, dz)) % 360


def axes(yaw_deg):
	r = math.radians(yaw_deg)
	return (math.cos(r), -math.sin(r)), (math.sin(r), math.cos(r))


def main():
	rnd = random.Random("brouillard")
	objects = gamedata.map_objects()

	buildings = SpatialIndex(50)   # maisons d'au moins 40 m² : sert à savoir si l'on est en ville
	for x, z in neige.houses(objects):
		buildings.add(x, z, (x, z))
	obstacles = SpatialIndex(50)   # (x, z, rayon) : bâtiments, ponts, gros objets de nos mappings
	own = SpatialIndex(100)
	roads = []                     # (x, z, y, axe x, axe z, demi-largeur, demi-longueur, nom du modèle)
	for path, xa, za, pos in objects:
		p = path.lower()
		if neige.is_building(path) or "\\bridges\\" in p:
			box = gamedata.model_bbox(path)
			if box:
				obstacles.add(pos[0], pos[2], (pos[0], pos[2], math.hypot(box[1][0], box[1][2])))
		if "\\roads\\parts\\" in p:
			name = p.rsplit("\\", 1)[-1]
			if MAIN_ROAD.match(name) and abs(pos[1] - gamedata.height(pos[0], pos[2])) < 1.0:
				box = gamedata.model_bbox(path)
				if box:
					roads.append((pos[0], pos[2], xa, za, box[1][0], box[1][2], name))
	# nos mappings, sauf ceux des ambiances météo (jamais chargés en même temps que le brouillard)
	ambiance = set()
	for folder in os.listdir(os.path.join(MISSION, "meteo")):
		path = os.path.join(MISSION, "meteo", folder, "mappings.txt")
		if os.path.isfile(path):
			ambiance |= {os.path.basename(l.strip()) for l in open(path) if l.strip() and not l.startswith("#")}
	for pos, xa, za, lo, hi in neige.own_mapping_objects(exclude=ambiance):
		r = math.hypot(max(-lo[0], hi[0]), max(-lo[1], hi[1]))
		obstacles.add(pos[0], pos[1], (pos[0], pos[1], r))
		own.add(pos[0], pos[1], (pos[0], pos[1]))
	road_index = SpatialIndex(25)
	for r in roads:
		road_index.add(r[0], r[1], r)
	rnd.shuffle(roads)

	def count_near(index, x, z, r):
		return sum(1 for bx, bz in index.near(x, z, r) if math.hypot(bx - x, bz - z) < r)

	def blocked(x, z, radius):
		return any(math.hypot(ox - x, oz - z) < r + radius for ox, oz, r in obstacles.near(x, z, radius + 60))

	def on_road(x, z, margin=1.0):
		for rx, rz, xa, za, hw, hl, _ in road_index.near(x, z, 25):
			dx, dz = x - rx, z - rz
			if abs(dx * xa[0] + dz * xa[1]) <= hw + margin and abs(dx * za[0] + dz * za[1]) <= hl + 0.5:
				return True
		return False

	def obj(name, x, z, yaw, lift, kind, half=(1.0, 1.0), scale=1.0, flat=False, extra_ypr=(0, 0)):
		"""Objet posé sur le terrain, incliné selon la pente (sauf flat)."""
		xa, za = axes(yaw)
		hx, hz = max(half[0], 0.5), max(half[1], 0.5)
		sx = (gamedata.height(x + hx * xa[0], z + hx * xa[1]) - gamedata.height(x - hx * xa[0], z - hx * xa[1])) / (2 * hx)
		sz = (gamedata.height(x + hz * za[0], z + hz * za[1]) - gamedata.height(x - hz * za[0], z - hz * za[1])) / (2 * hz)
		pitch, roll = (0.0, 0.0) if flat else (math.degrees(math.atan(sz)), -math.degrees(math.atan(sx)))
		if abs(math.degrees(math.atan(sx))) > MAX_TILT or abs(math.degrees(math.atan(sz))) > MAX_TILT:
			return None
		return {
			"name": name,
			"pos": [round(x, 3), round(gamedata.height(x, z) + lift, 3), round(z, 3)],
			"ypr": [round(yaw % 360, 1), round(pitch + extra_ypr[0], 2), round(roll + extra_ypr[1], 2)],
			"scale": scale,
			"enableCEPersistency": 0,
			"customString": kind,
		}

	half_size = {}
	for c in list(WRECKS) + [BUS[0], TIRE_FIRE[0]]:
		box = gamedata.model_bbox(gamedata.class_model(c).lstrip("\\"))
		half_size[c] = (box[1][0], box[1][2])

	# --- carambolages ------------------------------------------------------------------------------
	pileups, pileup_objects, pileup_zones, burning = [], [], [], 0
	for rx, rz, xa, za, hw, hl, name in roads:
		if not STRAIGHT.match(name) or safe_distance(rx, rz) < SAFE_MARGIN:
			continue
		if any(math.hypot(rx - px, rz - pz) < PILEUP_SPACING for px, pz in pileups):
			continue
		if count_near(buildings, rx, rz, TOWN_RADIUS):
			continue
		sign = rnd.choice((-1, 1))
		u = (za[0] * sign, za[1] * sign)   # sens de la file
		v = (xa[0], xa[1])                # travers de la route
		n = rnd.choices((2, 3, 4, 5), weights=(2, 3, 3, 1))[0]
		cars = []
		if rnd.random() < BUS_CHANCE:
			cars.append(BUS)
		while len(cars) < n:
			c = rnd.choice(list(WRECKS))
			if c not in [k for k, _ in cars]:
				cars.append((c, WRECKS[c]))
		sideways = rnd.randrange(len(cars)) if rnd.random() < 0.4 else -1
		lengths = []
		for i, (c, lift) in enumerate(cars):
			w, l = half_size[c]
			if i == sideways:
				rel = rnd.choice((-1, 1)) * rnd.uniform(60, 100)
			else:
				rel = rnd.uniform(-25, 25) + (180 if rnd.random() < 0.3 else 0)
			t = math.radians(rel)
			along = abs(l * math.cos(t)) + abs(w * math.sin(t))
			across = abs(l * math.sin(t)) + abs(w * math.cos(t))
			lengths.append((rel, along, across))
		total = sum(a for _, a, _ in lengths) * 2
		s = -total / 2
		group, ok = [], True
		for (c, lift), (rel, along, across) in zip(cars, lengths):
			s += along
			room = max(0.0, hw + 0.8 - across)
			lat = rnd.uniform(-room, room)
			x, z = rx + s * u[0] + lat * v[0], rz + s * u[1] + lat * v[1]
			s += along + rnd.uniform(-0.6, 0.8)
			yaw = yaw_towards(*u) + rel
			o = obj(c, x, z, yaw, lift, "carambolage", half_size[c])
			if not o or not on_road(x, z) or blocked(x, z, 1.5):
				ok = False
				break
			group.append(o)
		if not ok:
			continue
		# feu de détresse : pile de pneus en feu sur le bas-côté, en amont de la file
		side = rnd.choice((-1, 1))
		d = -total / 2 - rnd.uniform(6, 12)
		lat = side * (hw + rnd.uniform(1.5, 3))
		fx, fz = rx + d * u[0] + lat * v[0], rz + d * u[1] + lat * v[1]
		fire = obj(TIRE_FIRE[0], fx, fz, rnd.uniform(0, 360), TIRE_FIRE[1], "feu", half_size[TIRE_FIRE[0]], flat=True)
		if fire and not blocked(fx, fz, 2):
			group.append(fire)
		if rnd.random() < BURNING_CAR:
			car = rnd.choice([o for o in group if o["name"] in WRECKS])
			x, z = car["pos"][0], car["pos"][2]
			group.append({
				"name": CAR_FIRE[0],
				"pos": [x, round(gamedata.height(x, z) + CAR_FIRE[1], 3), z],
				"ypr": [0.0, 0.0, 0.0],
				"scale": CAR_FIRE[2],
				"enableCEPersistency": 0,
				"customString": "feu",
			})
			burning += 1
		pileups.append((rx, rz))
		pileup_objects += group
		pileup_zones.append((rx, rz) + ZOMBIE_PILEUP)

	# --- barrages ----------------------------------------------------------------------------------
	towns = []
	for loc in neige.localities():
		if loc["buildings"] < TOWN_MIN_BUILDINGS:
			continue
		x0, z0, x1, z1 = loc["box"]
		cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
		if safe_distance(cx, cz) < BARRAGE_SAFE_MARGIN:
			continue
		towns.append((loc["name"], cx, cz, max(x1 - x0, z1 - z0) / 2 + 300))
	per_town = defaultdict(list)
	barrage_objects = []
	for rx, rz, xa, za, hw, hl, name in roads:
		if not name.startswith(("asf", "city")) or not STRAIGHT.match(name.replace("city", "asf1")):
			continue
		if safe_distance(rx, rz) < BARRAGE_SAFE_MARGIN or count_near(buildings, rx, rz, 35):
			continue
		if count_near(buildings, rx, rz, 300) < 12 or blocked(rx, rz, 8):
			continue
		town = min(towns, key=lambda t: math.hypot(t[1] - rx, t[2] - rz), default=None)
		if not town or math.hypot(town[1] - rx, town[2] - rz) > town[3]:
			continue
		placed = per_town[town[0]]
		if len(placed) >= BARRAGES_PER_TOWN or any(math.hypot(rx - px, rz - pz) < BARRAGE_SPACING for px, pz in placed):
			continue
		# entrée de ville : plus loin du centre que le reste de la localité qui l'entoure
		u = (za[0], za[1]) if (rx - town[1]) * za[0] + (rz - town[2]) * za[1] > 0 else (-za[0], -za[1])
		v = (xa[0], xa[1])
		road_yaw = yaw_towards(*u)

		def at(a, b):
			return rx + a * u[0] + b * v[0], rz + a * u[1] + b * v[1]

		group, ok = [], True
		gap_side = rnd.choice((-1, 1))
		for row, a in ((0, 0.0), (1, rnd.uniform(6, 9))):
			gs = gap_side if row == 0 else -gap_side
			# rangée de blocs jointifs en travers, laissant un passage d'environ 3 m du côté gs
			b = -gs * (hw + 0.3)
			stop = gs * (hw - 3.0)
			while (stop - b) * gs > 0.8:
				if row == 0 or rnd.random() > 0.15:   # dans la 2e rangée, un bloc manque de temps en temps
					x, z = at(a + rnd.uniform(-0.3, 0.3), b + gs * 1.33)
					o = obj(BLOCK[0], x, z, road_yaw + 90 + rnd.uniform(-15, 15), BLOCK[1], "barrage", (0.5, 1.3))
					if not o:
						ok = False
					group.append(o)
				b += gs * 2.7
		# côté campagne (a > 0) : hérissons sur les bas-côtés et panneau stop face aux arrivants
		for side in (-1, 1):
			x, z = at(rnd.uniform(10, 13), side * (hw + rnd.uniform(1.2, 2.0)))
			group.append(obj(HEDGEHOG[0], x, z, rnd.uniform(0, 360), HEDGEHOG[1], "barrage"))
		x, z = at(rnd.uniform(14, 17), gap_side * (hw + 0.8))
		group.append(obj(STOP[0], x, z, road_yaw + 90 + rnd.uniform(-10, 10), STOP[1], "barrage", (0.5, 0.5)))
		x, z = at(rnd.uniform(-2, 10), -gap_side * (hw + rnd.uniform(1.5, 3)))
		group.append(obj(BARRICADE[0], x, z, road_yaw + rnd.uniform(-40, 40), BARRICADE[1], "barrage"))
		for i in range(rnd.randint(4, 6)):
			x, z = at(rnd.uniform(-6, 12), rnd.uniform(-hw, hw))
			if i < 2 and rnd.random() < 0.6:   # cône renversé
				group.append(obj(CONE[0], x, z, rnd.uniform(0, 360), 0.2, "barrage", flat=True, extra_ypr=(0, 90)))
			else:
				group.append(obj(CONE[0], x, z, rnd.uniform(0, 360), CONE[1], "barrage", (0.5, 0.5)))
		if not ok or any(o is None for o in group):
			continue
		placed.append((rx, rz))
		barrage_objects += group

	# --- zombies -----------------------------------------------------------------------------------
	zones = list(pileup_zones)
	for rx, rz, xa, za, hw, hl, name in roads:
		r = ZOMBIE_ROAD[0]
		if any(math.hypot(rx - zx, rz - zz) < ZOMBIE_SPACING for zx, zz, *_ in zones):
			continue
		if count_near(buildings, rx, rz, 120):
			continue
		zones.append((rx, rz) + ZOMBIE_ROAD)
	names, weights = zip(*ZOMBIE_EVENTS)
	lines = []
	for x, z, r, dmin, dmax in zones:
		if safe_distance(x, z) - r < SAFE_MARGIN or count_near(own, x, z, OWN_MARGIN + r):
			continue
		lines.append('        <zone name="%s" smin="0" smax="0" dmin="%d" dmax="%d" x="%.1f" z="%.1f" r="%d"/>'
					 % (rnd.choices(names, weights)[0], dmin, dmax, x, z, r))

	# --- écriture ----------------------------------------------------------------------------------
	for fname, objs in (("brouillard_carambolages.json", pileup_objects), ("brouillard_barrages.json", barrage_objects)):
		with open(os.path.join(MISSION, "custom", fname), "w") as f:
			f.write(json.dumps({"Objects": objs}, indent=4) + "\n")
	preset = os.path.join(MISSION, "meteo", "brouillard")
	with open(os.path.join(preset, "zombie_territories.xml"), "w") as f:
		f.write("\n".join(lines) + "\n")
	with open(os.path.join(preset, "mappings.txt"), "w") as f:
		f.write("# Mappings chargés seulement avec cette ambiance (générés par tools/brouillard/generate.py)\n")
		f.write("./custom/brouillard_carambolages.json\n./custom/brouillard_barrages.json\n")
	print("%d carambolages (%d objets, %d voitures en feu), %d barrages dans %d localités (%d objets), %d zones de zombies"
		  % (len(pileups), len(pileup_objects), burning, sum(map(len, per_town.values())), len(per_town),
			 len(barrage_objects), len(lines)))


if __name__ == "__main__":
	main()
