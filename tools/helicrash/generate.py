#!/usr/bin/env python3
"""Crashs d'hélicoptère dynamiques : épave + cadavre du pilote (squelette, viande humaine, os).

Chaque position de StaticHeliCrash (cfgeventspawns.xml) reçoit son propre groupe dans
cfgeventgroups.xml (HeliCrash_NN) : l'épave au centre, orientation fixe tirée au hasard, et le
pilote éjecté à 11-13 m, sur un sol peu pentu, hors de l'eau, loin des arbres, rochers et murs.
Les enfants de groupe sans « y » sont posés au sol par le moteur (comme les convois vanilla).

Relançable : les groupes générés sont entre deux marqueurs et réécrits à chaque fois ; l'orientation
déjà choisie pour une position est conservée.
"""
import math
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "neige"))
import gamedata as g  # noqa: E402

MISSION = os.path.join(ROOT, "dayzxb_missions", "dayzOffline.chernarusplus")
SPAWNS = os.path.join(MISSION, "cfgeventspawns.xml")
GROUPS = os.path.join(MISSION, "cfgeventgroups.xml")
EVENTS = os.path.join(MISSION, "db", "events.xml")

BEGIN, END = "    <!-- HELICRASH PILOTE (tools/helicrash/generate.py) -->", "    <!-- /HELICRASH PILOTE -->"
WRECK = '<child type="Wreck_UH1Y" deloot="1" lootmax="15" lootmin="10" x="0" z="0" a="%.1f"/>'
SKELETON = "StaticObj_Forest_HumanSkeleton"

# demi-diagonale de l'épave UH-1Y (11,4 × 15,4 m) = 9,6 m : au-delà, on est dehors quelle que soit
# l'orientation
WRECK_CLEAR = 10.0
NEAR = 45.0           # rayon de recherche des obstacles autour d'une position
IGNORED = {"clutter", "decals", "parts", "sidewalks", "tracks"}   # plats : on peut se poser dessus
TRUNK = {"tree": 1.2, "bush": 1.4}                                # troncs / buissons : rayon fixe


def rnd_for(i):
	return random.Random(23100 + i)


def category(model):
	parts = model.lower().replace("/", "\\").split("\\")
	return parts[-2] if len(parts) > 1 else ""


def obstacles_near(points):
	"""Objets de la carte à moins de NEAR m d'une des positions, regroupés par position."""
	near = {k: [] for k in range(len(points))}
	cell = {}
	for k, (x, z) in enumerate(points):
		cell.setdefault((int(x // NEAR), int(z // NEAR)), []).append(k)
	for model, xa, za, (x, _, z) in g.map_objects():
		cat = category(model)
		if cat in IGNORED:
			continue
		cx, cz = int(x // NEAR), int(z // NEAR)
		for dx in (-1, 0, 1):
			for dz in (-1, 0, 1):
				for k in cell.get((cx + dx, cz + dz), ()):
					px, pz = points[k]
					if (x - px) ** 2 + (z - pz) ** 2 < NEAR * NEAR:
						near[k].append((model, cat, xa, za, x, z))
	return near


_box = {}


def blocked(px, pz, obstacles, margin):
	for model, cat, xa, za, x, z in obstacles:
		dx, dz = px - x, pz - z
		if cat in TRUNK:
			if dx * dx + dz * dz < (TRUNK[cat] + margin) ** 2:
				return True
			continue
		if model not in _box:
			_box[model] = g.model_bbox(model)
		box = _box[model]
		if box is None:
			if dx * dx + dz * dz < (1.5 + margin) ** 2:
				return True
			continue
		# coordonnées dans le repère du modèle (axes éventuellement mis à l'échelle)
		nx, nz = xa[0] ** 2 + xa[1] ** 2, za[0] ** 2 + za[1] ** 2
		lx, lz = (dx * xa[0] + dz * xa[1]) / nx, (dx * za[0] + dz * za[1]) / nz
		mx, mz = margin / math.sqrt(nx), margin / math.sqrt(nz)
		if box[0][0] - mx < lx < box[1][0] + mx and box[0][2] - mz < lz < box[1][2] + mz:
			return True
	return False


def slope(x, z, r=1.0):
	h = [g.height(x + dx, z + dz) for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r))]
	return max(abs(h[0] - h[1]), abs(h[2] - h[3])) / (2 * r)


def ok(x, z, cx, cz, obstacles, margin):
	return (math.hypot(x - cx, z - cz) >= WRECK_CLEAR and g.height(x, z) > 1.0
			and slope(x, z) < 0.25 and not blocked(x, z, obstacles, margin))


def layout(i, cx, cz, obstacles):
	"""Le pilote et ses restes, en décalages (x, z) par rapport à l'épave."""
	rnd = rnd_for(i)
	best = None
	for step in range(36):
		ang = math.radians(step * 10 + rnd.uniform(0, 10))
		for dist in (11.0, 12.0, 13.0):
			sx, sz = cx + dist * math.sin(ang), cz + dist * math.cos(ang)
			if not ok(sx, sz, cx, cz, obstacles, 1.0):
				continue
			s = slope(sx, sz, 1.5)
			if best is None or s < best[0]:
				best = (s, sx, sz)
	if best is None:
		return None
	_, sx, sz = best
	items = [(SKELETON, sx, sz, rnd.uniform(0, 360))]
	wanted = ["HumanSteakMeat"] * rnd.randint(2, 3) + ["Bone"] * rnd.randint(1, 2)
	for name in wanted:
		near = 0.6 if name == "HumanSteakMeat" else 1.2
		for _ in range(200):
			a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(near, near + 1.3)
			x, z = sx + d * math.sin(a), sz + d * math.cos(a)
			if ok(x, z, cx, cz, obstacles, 0.3) and all(math.hypot(x - ox, z - oz) > 0.45 for _, ox, oz, _ in items[1:]):
				items.append((name, x, z, rnd.uniform(0, 360)))
				break
	return [(n, x - cx, z - cz, a) for n, x, z, a in items]


def main():
	spawns = open(SPAWNS, encoding="utf-8").read()
	groups = open(GROUPS, encoding="utf-8").read()
	events = open(EVENTS, encoding="utf-8").read()

	m = re.search(r'(    <event name="StaticHeliCrash">\n)(.*?)(    </event>)', spawns, re.S)
	body = m.group(2)
	if "<!--" in body:
		sys.exit("StaticHeliCrash contient des positions commentées : le script les perdrait, à traiter à la main")
	zone = re.search(r"\t\t<zone [^\n]*\n", body).group(0)
	pos = re.findall(r"<pos ([^/]*)/>", body)

	old_yaw = {name: float(a) for name, a in re.findall(
		r'<group name="(HeliCrash_\d+)">\s*<child type="Wreck_UH1Y"[^>]* a="([-\d.]+)"', groups)}

	points, yaws = [], []
	for i, attrs in enumerate(pos):
		at = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
		x, z = float(at["x"]), float(at["z"])
		name = "HeliCrash_%02d" % (i + 1)
		if name in old_yaw:
			yaw = old_yaw[name]
		elif float(at.get("a", -1)) >= 0 and "group" not in at:
			yaw = float(at["a"]) % 360
		else:
			yaw = rnd_for(i).uniform(0, 360)
		points.append((x, z))
		yaws.append(yaw)

	print("obstacles…", file=sys.stderr)
	near = obstacles_near(points)

	out_groups, out_pos, missing = [], [], []
	for i, ((x, z), yaw) in enumerate(zip(points, yaws)):
		name = "HeliCrash_%02d" % (i + 1)
		y = g.height(x, z)
		out_pos.append('\t\t<pos x="%.3f" z="%.3f" a="0" y="%.3f" group="%s"/>\n' % (x, z, y, name))
		lines = ['    <group name="%s">' % name, "        " + WRECK % yaw]
		pilot = layout(i, x, z, near[i])
		if pilot is None:
			missing.append(name)
		else:
			for n, dx, dz, a in pilot:
				lines.append('        <child type="%s" spawnsecondary="false" x="%.3f" z="%.3f" a="%.1f"/>' % (n, dx, dz, a))
		lines.append("    </group>")
		out_groups.append("\n".join(lines))

	spawns = spawns[:m.start(2)] + zone + "".join(out_pos) + spawns[m.end(2):]
	block = BEGIN + "\n" + "\n".join(out_groups) + "\n" + END + "\n"
	if BEGIN in groups:
		groups = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", lambda _: block, groups, flags=re.S)
	else:
		groups = groups.replace("</eventgroupdef>", block + "</eventgroupdef>")
	# avec des groupes, l'événement n'a plus d'enfants propres (comme StaticMilitaryConvoy)
	events = re.sub(r'(<event name="StaticHeliCrash">(?:(?!</event>).)*?)<children>.*?</children>', r"\1<children/>", events, count=1, flags=re.S)

	for path, text in ((SPAWNS, spawns), (GROUPS, groups), (EVENTS, events)):
		with open(path, "w", encoding="utf-8", newline="") as f:
			f.write(text)
	print("%d crashs, sans pilote : %s" % (len(points), ", ".join(missing) or "aucun"))


if __name__ == "__main__":
	main()
