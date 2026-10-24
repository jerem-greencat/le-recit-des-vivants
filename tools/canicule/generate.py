"""Génère le mapping de l'ambiance canicule : traces de brûlé au sol.

Usage : python3 tools/canicule/generate.py
Écrit custom/canicule_brulis.json et meteo/canicule/mappings.txt (chargés seulement en ambiance canicule).

Traces de brûlé (décals de Nasdara, visibles sans le DLC comme les plaques de neige de Sakhal) :
- par groupes (une grande, quelques petites autour), en terrain dégagé en bordure des localités ;
- inclinées selon la pente comme les plaques de neige, et abaissées pour ne flotter nulle part.

Pas de lierre sec : il n'existe qu'en modèle (chemin DZ\\plants_bliss\\...), que l'Object Spawner crée en
objet local au serveur (createLocal), invisible pour les joueurs (constaté le 24/10/2026 avec les arbres
de la tempête).
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

SCORCH_GROUPS = 4         # groupes de traces de brûlé par tranche de 100 bâtiments (au moins 1)
SCORCH_LARGE = ("StaticObj_Decal_ScorchMark_01_large_f", 4.35, 2.85)
SCORCH_SMALL = ("StaticObj_Decal_ScorchMark_01_small_f", 1.5, 1.5)
MAX_GAP = 0.2             # enfoncement maximal d'une trace dans le terrain (m)


def entry(name, pos, ypr, scale, kind):
	return {"name": name, "pos": [round(v, 3) for v in pos], "ypr": [round(v, 2) for v in ypr],
			"scale": round(scale, 3), "enableCEPersistency": 0, "customString": kind}


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
	brulis = scorch(rnd, objects, neige.houses(objects), localities)
	with open(os.path.join(MISSION, "custom", "canicule_brulis.json"), "w") as f:
		f.write(json.dumps({"Objects": brulis}, indent=4) + "\n")
	with open(os.path.join(MISSION, "meteo", "canicule", "mappings.txt"), "w") as f:
		f.write("# Mappings chargés seulement avec cette ambiance (générés par tools/canicule/generate.py)\n")
		f.write("./custom/canicule_brulis.json\n")
	print("%d traces de brûlé" % len(brulis))


if __name__ == "__main__":
	main()
