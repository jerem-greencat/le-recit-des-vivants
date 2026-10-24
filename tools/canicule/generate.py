"""Génère les mappings de l'ambiance canicule : lierre sec sur les murs et traces de brûlé au sol.

Usage : python3 tools/canicule/generate.py
Écrit custom/canicule_lierre.json, custom/canicule_brulis.json et meteo/canicule/mappings.txt
(chargés seulement en ambiance canicule).

Lierre sec (modèles de Livonia, chemins DZ\\plants_bliss : objets statiques légers) :
- sur les murs et murets pleins (béton, brique, pierre, tôle, planches) des localités ayant de la neige en
  hiver, à moins de NEAR_HOUSE m d'un bâtiment, MAX_IVY brins au plus par localité (comme les plaques de
  neige, trop d'objets autour d'un joueur provoquent de la désynchronisation) ; pas sur les grillages,
  rambardes ni poteaux ;
- les maisons n'en ont pas : leur boîte englobante comprend les débords de toit, le lierre flotterait ;
- le brin est plaqué contre une face du mur et mis à l'échelle de sa hauteur visible (le haut du mur
  moins le terrain : certains murs sont en partie enterrés).

Traces de brûlé (décals de Nasdara, visibles sans le DLC comme les plaques de neige de Sakhal) :
- par groupes (une grande, quelques petites autour), en terrain dégagé en bordure des localités ;
- inclinées selon la pente comme les plaques de neige, et abaissées pour ne flotter nulle part.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "neige"))
import gamedata  # noqa: E402
import generate as neige  # noqa: E402
from importlib import util  # noqa: E402

_spec = util.spec_from_file_location("tempete", os.path.join(HERE, "..", "tempete", "generate.py"))
tempete = util.module_from_spec(_spec)
_spec.loader.exec_module(tempete)

MISSION = os.path.join(HERE, "..", "..", "dayzxb_missions", "dayzOffline.chernarusplus")

NEAR_HOUSE = 50           # m : murs pris en compte autour des bâtiments
MAX_IVY = 400             # brins de lierre au plus par localité
MIN_WALL = 0.6            # hauteur visible minimale d'un mur (m)
SOLID_WALLS = ("cnc", "cbrk", "cgry", "stone", "tin", "wood", "vilvar", "indvar")
NOT_WALLS = ("pole", "fen", "railing", "garb", "hole", "gate")
IVY = [
	"DZ\\plants_bliss\\building\\ivy_dry_%s.p3d" % k for k in "abcdefghij"
]

SCORCH_GROUPS = 4         # groupes de traces de brûlé par tranche de 100 bâtiments (au moins 1)
SCORCH_LARGE = ("StaticObj_Decal_ScorchMark_01_large_f", 4.35, 2.85)
SCORCH_SMALL = ("StaticObj_Decal_ScorchMark_01_small_f", 1.5, 1.5)
MAX_GAP = 0.2             # enfoncement maximal d'une trace dans le terrain (m)


def is_solid_wall(path):
	name = path.lower().rsplit("\\", 1)[-1]
	return ("\\walls\\" in path.lower() and name.startswith("wall_") and any(k in name for k in SOLID_WALLS)
			and not any(k in name for k in NOT_WALLS))


def entry(name, pos, ypr, scale, kind):
	return {"name": name, "pos": [round(v, 3) for v in pos], "ypr": [round(v, 2) for v in ypr],
			"scale": round(scale, 3), "enableCEPersistency": 0, "customString": kind}


def ivy(rnd, objects, houses, localities):
	boxes = {m: gamedata.model_bbox(m) for m in IVY}
	out = []
	walls = [o for o in objects if is_solid_wall(o[0]) and any(True for _ in houses.near(o[3][0], o[3][2], NEAR_HOUSE))]
	for loc in localities:
		x0, z0, x1, z1 = loc["box"]
		mine = [o for o in walls if x0 <= o[3][0] <= x1 and z0 <= o[3][2] <= z1]
		rnd.shuffle(mine)
		town = []
		for o in mine:
			if len(town) >= MAX_IVY:
				break
			town += ivy_on_wall(rnd, o, boxes)
		out += town[:MAX_IVY]
	return out


def ivy_on_wall(rnd, wall, boxes):
	"""1 ou 2 brins plaqués sur une face du pan de mur."""
	path, xa, za, pos = wall
	box = gamedata.model_bbox(path)
	if not box:
		return []
	(lx, ly, lz), (hx, hy, hz) = box
	if hx - lx < 1.5 or hz - lz > 2:   # pans de mur : longs en x, fins en z
		return []
	top = pos[1] + hy
	out = []
	for _ in range(rnd.choice((1, 1, 2))):
		t = rnd.uniform(lx + 0.4, hx - 0.4)
		side = rnd.choice((-1, 1))
		face = (hz if side > 0 else -lz) + 0.02
		x = pos[0] + t * xa[0] + side * face * za[0]
		z = pos[2] + t * xa[1] + side * face * za[1]
		ground = gamedata.height(x, z)
		visible = top - ground
		if visible < MIN_WALL:
			continue
		model = rnd.choice(IVY)
		(mlx, mly, mlz), (mhx, mhy, mhz) = boxes[model]
		scale = min(1.2, max(0.4, visible * rnd.uniform(0.6, 0.95) / (mhy - mly)))
		# axe z du lierre = normale sortante du mur (les feuilles partent vers +z)
		nx, nz = side * za[0], side * za[1]
		yaw = math.degrees(math.atan2(nx, nz)) % 360
		out.append(entry(model, (x, ground - mly * scale, z), (yaw, 0, 0), scale, "lierre"))
	return out


def scorch(rnd, objects, houses_list, localities):
	"""Groupes de traces de brûlé en terrain dégagé, en bordure de chaque localité."""
	obstacles = tempete.SpatialIndex(50)
	for path, xa, za, pos in objects:
		p = path.lower()
		if neige.is_building(path) or "\\roads\\" in p or "\\walls\\" in p or "\\water\\" in p:
			box = gamedata.model_bbox(path)
			if box:
				obstacles.add(pos[0], pos[2], (pos[0], pos[2], math.hypot(box[1][0], box[1][2])))
	for pos, xa, za, lo, hi in neige.own_mapping_objects():
		obstacles.add(pos[0], pos[1], (pos[0], pos[1], math.hypot(max(-lo[0], hi[0]), max(-lo[1], hi[1]))))

	def clear(x, z, r):
		return all(math.hypot(ox - x, oz - z) > orad + r for ox, oz, orad in obstacles.near(x, z, r + 60))

	def decal(name, hx, hz, x, z):
		# même pose que les plaques de neige : lacet vers l'amont, tangage = pente, abaissée sous le terrain
		r = max(hx, hz)
		gx = (gamedata.height(x + r, z) - gamedata.height(x - r, z)) / (2 * r)
		gz = (gamedata.height(x, z + r) - gamedata.height(x, z - r)) / (2 * r)
		tilt = math.degrees(math.atan(math.hypot(gx, gz)))
		if tilt > 12:
			return None
		yaw = math.degrees(math.atan2(gx, gz)) % 360 if tilt > 0.3 else rnd.uniform(0, 360)
		if tilt <= 0.3:
			tilt, gx, gz = 0.0, 0.0, 0.0
		xa, za = neige.yaw_axes(yaw)
		y0 = gamedata.height(x, z)
		diffs = []
		for a in range(-4, 5):
			for b in range(-4, 5):
				dx = (a * hx * xa[0] + b * hz * za[0]) / 4
				dz = (a * hx * xa[1] + b * hz * za[1]) / 4
				diffs.append(gamedata.height(x + dx, z + dz) - (y0 + gx * dx + gz * dz))
		if max(diffs) - min(diffs) > MAX_GAP:
			return None
		return entry(name, (x, y0 + min(diffs) + 0.03, z), (yaw, tilt, 0), 1.0, "brulis")

	out = []
	for loc in localities:
		groups = max(1, loc["buildings"] * SCORCH_GROUPS // 100)
		x0, z0, x1, z1 = loc["box"]
		members = [h for h in houses_list if x0 <= h[0] <= x1 and z0 <= h[1] <= z1]
		tries = 0
		while groups and tries < 300:
			tries += 1
			hx_, hz_ = rnd.choice(members)
			a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(20, 60)
			x, z = hx_ + d * math.cos(a), hz_ + d * math.sin(a)
			if not clear(x, z, 6):
				continue
			big = decal(*SCORCH_LARGE, x, z)
			if not big:
				continue
			group = [big]
			for _ in range(rnd.randint(2, 4)):
				a2, d2 = rnd.uniform(0, 2 * math.pi), rnd.uniform(4, 9)
				sx, sz = x + d2 * math.cos(a2), z + d2 * math.sin(a2)
				if clear(sx, sz, 2):
					small = decal(*SCORCH_SMALL, sx, sz)
					if small:
						group.append(small)
			out += group
			groups -= 1
	return out


def main():
	rnd = random.Random("canicule")
	objects = gamedata.map_objects()
	localities = [t for t in neige.localities() if t["buildings"] >= neige.MIN_BUILDINGS]
	houses_list = neige.houses(objects)
	houses = tempete.SpatialIndex(50)
	for x, z in houses_list:
		houses.add(x, z, (x, z))

	lierre = ivy(rnd, objects, houses, localities)
	brulis = scorch(rnd, objects, houses_list, localities)
	for name, objs in (("canicule_lierre", lierre), ("canicule_brulis", brulis)):
		with open(os.path.join(MISSION, "custom", name + ".json"), "w") as f:
			f.write(json.dumps({"Objects": objs}, indent=4) + "\n")
	with open(os.path.join(MISSION, "meteo", "canicule", "mappings.txt"), "w") as f:
		f.write("# Mappings chargés seulement avec cette ambiance (générés par tools/canicule/generate.py)\n")
		f.write("./custom/canicule_lierre.json\n./custom/canicule_brulis.json\n")
	print("%d brins de lierre sec, %d traces de brûlé" % (len(lierre), len(brulis)))


if __name__ == "__main__":
	main()
