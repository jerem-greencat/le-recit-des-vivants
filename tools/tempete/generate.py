"""Génère le mapping des arbres tombés de l'ambiance tempête.

Usage : python3 tools/tempete/generate.py
Écrit custom/tempete_arbres.json et meteo/tempete/mappings.txt (chargé seulement en ambiance tempête).

Règles :
- les arbres ne tombent que là où il y a des arbres : au moins MIN_TREES arbres de la carte à moins de
  TREE_RADIUS m ;
- des arbres coupent les routes (goudron, gravier, terre), au moins CROSS_SPACING m entre deux coupures,
  sauf dans l'enceinte de Zelenogorsk (zone RP : les rues y restent praticables) ;
- d'autres sont couchés le long des routes, sans les couper, tous les ROADSIDE_SPACING m au plus ;
- jamais sur un pont, dans un bâtiment ou sur les gros objets de nos mappings ;
- les troncs suivent la pente : roulis = -pente le long du tronc (axe x du modèle), comme les murs posés
  en pente dans zeleno_enceinte.json ; tangage = pente en travers (positif = avant relevé) ;
- hauteur de pose : celle des mêmes arbres couchés placés par Bohemia sur la carte (médiane).
Les modèles sont des « plantes » (chemins DZ\\plants), que l'Object Spawner charge en objets statiques.
"""
import json
import math
import os
import random
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "neige"))
import gamedata  # noqa: E402
import generate as neige  # noqa: E402  (classement des bâtiments, objets de nos mappings)

MISSION = os.path.join(HERE, "..", "..", "dayzxb_missions", "dayzOffline.chernarusplus")

TREE_RADIUS = 25          # m autour du point de chute où l'on compte les arbres
MIN_TREES = 4             # arbres minimum dans ce rayon
CROSS_SPACING = 1200      # m minimum entre deux routes coupées
ROADSIDE_SPACING = 250    # m minimum entre deux arbres couchés au bord d'une même zone
MAX_GAP = 0.6             # écart maximal entre le tronc et le terrain (m)
MAX_TILT = 20             # pente maximale sous le tronc (degrés)
NO_CROSSING = ["zeleno_enceinte.json"]   # mappings dont l'emprise ne doit pas avoir de route coupée

# arbres entiers (longs) pour couper les routes, troncs plus courts pour les bas-côtés
LONG_TREES = [
	"DZ\\plants\\tree\\d_fagussylvatica_fallen.p3d",
	"DZ\\plants\\tree\\d_piceaabies_fallen.p3d",
	"DZ\\plants_bliss\\tree\\d_piceaabies_fallend.p3d",
	"DZ\\plants_bliss\\tree\\d_piceaabies_fallene.p3d",
	"DZ\\plants\\tree\\d_pinussylvestris_fallen.p3d",
	"DZ\\plants_bliss\\tree\\d_betulapendula_fallen.p3d",
]
SIDE_TREES = LONG_TREES + [
	"DZ\\plants\\tree\\d_piceaabies_fallenb.p3d",
	"DZ\\plants\\tree\\d_pinussylvestris_fallenb.p3d",
	"DZ\\plants\\tree\\d_fagussylvatica_fallenb.p3d",
]


def road_kind(path):
	p = path.lower()
	if "\\roads\\parts\\" not in p:
		return None
	name = p.rsplit("\\", 1)[-1]
	if name.startswith("kr_"):
		return None   # carrefours : forme irrégulière
	if name.startswith(("asf", "city", "grav", "mud")):
		return name
	return None


def axes(yaw_deg):
	r = math.radians(yaw_deg)
	return (math.cos(r), -math.sin(r)), (math.sin(r), math.cos(r))


def yaw_of(xaxis):
	return math.degrees(math.atan2(-xaxis[1], xaxis[0])) % 360


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


def main():
	rnd = random.Random("tempete")
	objects = gamedata.map_objects()

	# hauteur de pose de chaque modèle : médiane des placements de Bohemia (y - terrain)
	offsets = defaultdict(list)
	for path, xa, za, pos in objects:
		if "\\d_" in path and "fallen" in path:
			offsets[path.lower()].append(pos[1] - gamedata.height(pos[0], pos[2]))
	lift = {m: statistics.median(offsets[m.lower()]) if offsets[m.lower()] else -gamedata.model_bbox(m)[0][1] * 0.5
			for m in SIDE_TREES}
	length = {m: gamedata.model_bbox(m)[1][0] for m in SIDE_TREES}   # demi-longueur (axe x)

	trees = SpatialIndex(25)
	obstacles = SpatialIndex(50)   # (x, z, rayon) des bâtiments, ponts et gros objets de nos mappings
	roads = []
	for path, xa, za, pos in objects:
		p = path.lower()
		if p.startswith("dz\\plants\\tree\\t_"):
			trees.add(pos[0], pos[2], 1)
		elif neige.is_building(path) or "\\bridges\\" in p:
			box = gamedata.model_bbox(path)
			if box:
				obstacles.add(pos[0], pos[2], (pos[0], pos[2], math.hypot(box[1][0], box[1][2])))
		kind = road_kind(path)
		if kind and abs(pos[1] - gamedata.height(pos[0], pos[2])) < 1.0:   # pas les ponts
			box = gamedata.model_bbox(path)
			if box:
				roads.append((pos, xa, za, box[1][0]))
	for pos, xa, za, lo, hi in neige.own_mapping_objects():
		obstacles.add(pos[0], pos[1], (pos[0], pos[1], math.hypot(max(-lo[0], hi[0]), max(-lo[1], hi[1]))))
	rnd.shuffle(roads)
	no_cross = []
	for name in NO_CROSSING:
		pts = [o["pos"] for o in json.load(open(os.path.join(MISSION, "custom", name)))["Objects"]]
		no_cross.append((min(p[0] for p in pts), min(p[2] for p in pts), max(p[0] for p in pts), max(p[2] for p in pts)))

	def wooded(x, z):
		return sum(1 for _ in trees.near(x, z, TREE_RADIUS)) >= MIN_TREES

	def blocked(x, z, half_len, xaxis):
		"""Le tronc (segment) passe-t-il dans un obstacle ?"""
		for ox, oz, r in obstacles.near(x, z, half_len + 60):
			# distance du centre de l'obstacle au segment du tronc
			dx, dz = ox - x, oz - z
			t = max(-half_len, min(half_len, dx * xaxis[0] + dz * xaxis[1]))
			if math.hypot(dx - t * xaxis[0], dz - t * xaxis[1]) < r + 1.5:
				return True
		return False

	def place(model, x, z, yaw, kind):
		xa, za = axes(yaw)
		h = length[model]
		sx = (gamedata.height(x + h * xa[0], z + h * xa[1]) - gamedata.height(x - h * xa[0], z - h * xa[1])) / (2 * h)
		sz = (gamedata.height(x + 2 * za[0], z + 2 * za[1]) - gamedata.height(x - 2 * za[0], z - 2 * za[1])) / 4
		y0 = gamedata.height(x, z)
		gap = max(abs(gamedata.height(x + t * h * xa[0], z + t * h * xa[1]) - (y0 + t * h * sx)) for t in (-1, -0.5, 0.5, 1))
		roll, pitch = -math.degrees(math.atan(sx)), math.degrees(math.atan(sz))
		if gap > MAX_GAP or abs(roll) > MAX_TILT or abs(pitch) > MAX_TILT or blocked(x, z, h, xa):
			return None
		return {
			"name": model,
			"pos": [round(x, 3), round(y0 + lift[model], 3), round(z, 3)],
			"ypr": [round(yaw, 1), round(pitch, 2), round(roll, 2)],
			"scale": 1.0,
			"enableCEPersistency": 0,
			"customString": kind,
		}

	placed, crossings, sides = [], [], SpatialIndex(ROADSIDE_SPACING)
	for pos, xa, za, half_width in roads:
		x, z = pos[0], pos[2]
		if not wooded(x, z):
			continue
		# 1. arbre en travers de la route
		if (all(math.hypot(x - cx, z - cz) >= CROSS_SPACING for cx, cz in crossings)
				and not any(x0 <= x <= x1 and z0 <= z <= z1 for x0, z0, x1, z1 in no_cross)):
			models = [m for m in LONG_TREES if 2 * length[m] >= 2 * half_width + 3]
			if models:
				model = rnd.choice(models)
				# tronc à peu près perpendiculaire à la route, décalé pour dépasser plus d'un côté
				a = math.atan2(xa[1], xa[0]) + math.radians(rnd.uniform(-25, 25))
				tx, tz = math.cos(a), math.sin(a)
				shift = rnd.uniform(-1, 1) * max(0.0, length[model] - half_width - 1.5)
				along = rnd.uniform(-3, 3)
				px, pz = x + shift * tx + along * za[0], z + shift * tz + along * za[1]
				o = place(model, px, pz, yaw_of((tx, tz)), "travers")
				if o:
					placed.append(o)
					crossings.append((x, z))
					continue
		# 2. arbre couché au bord de la route, parallèle à elle
		if any(math.hypot(x - sx_, z - sz_) < ROADSIDE_SPACING for sx_, sz_ in sides.near(x, z, ROADSIDE_SPACING)):
			continue
		model = rnd.choice(SIDE_TREES)
		side = rnd.choice((-1, 1))
		dist = half_width + 2 + rnd.uniform(0, 4)
		px, pz = x + side * dist * xa[0], z + side * dist * xa[1]
		a = math.atan2(za[1], za[0]) + math.radians(rnd.uniform(-20, 20))
		o = place(model, px, pz, yaw_of((math.cos(a), math.sin(a))), "bord")
		if o:
			placed.append(o)
			sides.add(x, z, (x, z))

	out = os.path.join(MISSION, "custom", "tempete_arbres.json")
	with open(out, "w") as f:
		f.write(json.dumps({"Objects": placed}, indent=4) + "\n")
	with open(os.path.join(MISSION, "meteo", "tempete", "mappings.txt"), "w") as f:
		f.write("# Mappings chargés seulement avec cette ambiance (générés par tools/tempete/generate.py)\n")
		f.write("./custom/tempete_arbres.json\n")
	print("%d arbres tombés, dont %d en travers d'une route -> %s"
		  % (len(placed), len(crossings), os.path.relpath(out)))


if __name__ == "__main__":
	main()
