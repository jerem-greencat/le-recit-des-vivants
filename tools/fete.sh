#!/usr/bin/env bash
# Active une fête à partir de fetes/<fete>/ ; tout ce qui appartient aux autres fêtes est d'abord retiré :
# - mappings.txt : mappings ajoutés à objectSpawnersArr de cfggameplay.json ;
# - events.xml / types.xml (facultatifs) : blocs <event>/<type> qui remplacent ceux de db/events.xml et
#   db/types.xml ; hors fête, les blocs de events.origine.xml / types.origine.xml sont remis ;
# - effectareas.json (facultatif) : zones ajoutées à la fin de "Areas" dans cfgEffectArea.json.
# Le reste de ces fichiers n'est pas touché.
# Usage : tools/fete.sh noel|halloween|aucune
set -euo pipefail

MISSION="$(dirname "$0")/../dayzxb_missions/dayzOffline.chernarusplus"
FETE="${1:-}"
PRESET="$MISSION/fetes/$FETE"

if [ -z "$FETE" ] || [ ! -f "$PRESET/mappings.txt" ]; then
	echo "Usage : $0 <fete>  (disponibles : $(ls "$MISSION/fetes" | tr '\n' ' '))" >&2
	exit 1
fi

python3 -I - "$PRESET" "$MISSION" <<'EOF'
import glob, json, os, re, sys
preset, mission = sys.argv[1], sys.argv[2]
fetes = sorted(glob.glob(os.path.dirname(preset) + "/*/"))
preset = preset.rstrip("/") + "/"
out = {}  # fichiers de la mission modifiés, écrits seulement si tout est valide


def read(rel):
	return out.get(rel) or open(os.path.join(mission, rel)).read()


def mappings(folder):
	return [l.strip() for l in open(folder + "mappings.txt") if l.strip() and not l.startswith("#")]


for m in mappings(preset):
	if not os.path.isfile(os.path.join(mission, m)):
		sys.exit("%s introuvable" % m)

# cfggameplay.json : seule la liste objectSpawnersArr est réécrite
text = read("cfggameplay.json")
every = {m for folder in fetes for m in mappings(folder)}
match = re.search(r'("objectSpawnersArr":\s*\[)(.*?)(\n\t*\])', text, re.S)
current = [m for m in re.findall(r'"([^"]+)"', match.group(2)) if m not in every] + mappings(preset)
text = text[:match.start(2)] + "".join("\n\t\t\t\"%s\"," % m for m in current).rstrip(",") + text[match.end(2):]
json.loads(text)
out["cfggameplay.json"] = text


# db/events.xml, db/types.xml : remplacement de blocs entiers, repérés par leur nom
def blocks(path, tag):
	if not os.path.isfile(path):
		return {}
	return {m.group(1): m.group(0) for m in re.finditer(r'^[ \t]*<%s name="([^"]+)">.*?</%s>' % (tag, tag), open(path).read(), re.M | re.S)}


for name, tag in (("events.xml", "event"), ("types.xml", "type")):
	rel = "db/" + name
	text = read(rel)

	def swap(text, key, new, allowed):
		if text.count('<%s name="%s">' % (tag, key)) != 1:
			sys.exit("%s : bloc %s introuvable ou en double" % (rel, key))
		m = re.search(r'^[ \t]*<%s name="%s">.*?</%s>' % (tag, re.escape(key), tag), text, re.M | re.S)
		if m.group(0) not in allowed:
			sys.exit("%s : le bloc %s a été modifié à la main, mettre à jour fetes/*/%s" % (rel, key, name))
		return text[:m.start()] + new + text[m.end():]

	active = {f: blocks(f + name, tag) for f in fetes}
	known = {}
	for f in fetes:
		for key, b in active[f].items():
			known.setdefault(key, set()).add(b)
	origine = {}
	for f in fetes:
		for key, b in blocks(f + name.replace(".xml", ".origine.xml"), tag).items():
			origine[key] = b
			known.setdefault(key, set()).add(b)
	for key in known:
		if key not in origine:
			sys.exit("%s : pas de valeur hors fête pour %s" % (rel, key))
		text = swap(text, key, origine[key], known[key])
	for key, b in active.get(preset, {}).items():
		text = swap(text, key, b, known[key])
	out[rel] = text


# cfgEffectArea.json : zones de fête ajoutées en fin de liste "Areas", texte généré à l'identique pour les retirer
def area_text(folder):
	if not os.path.isfile(folder + "effectareas.json"):
		return ""
	areas = json.load(open(folder + "effectareas.json"))["Areas"]
	return "".join(",\n" + "\n".join("\t\t" + l for l in json.dumps(a, indent="\t").split("\n")) for a in areas)


text = read("cfgEffectArea.json")
for f in fetes:
	t = area_text(f)
	if t:
		text = text.replace(t, "")
end = re.search(r'\n[ \t]*\],\s*"SafePositions"', text).start()
text = text[:end] + area_text(preset) + text[end:]
names = [a["AreaName"] for a in json.loads(text)["Areas"]]
if len(names) != len(set(names)):
	sys.exit("cfgEffectArea.json : zone en double")
out["cfgEffectArea.json"] = text

for rel, text in out.items():
	open(os.path.join(mission, rel), "w").write(text)
EOF

echo "Fête '$FETE' activée. Envoyer sur le FTP puis redémarrer :"
echo "  cfggameplay.json, db/events.xml, db/types.xml, cfgEffectArea.json"
if grep -qv '^#' "$PRESET/mappings.txt"; then
	echo "  et les mappings de la fête (s'ils ne sont pas déjà sur le FTP) :"
	grep -v '^#' "$PRESET/mappings.txt" | sed 's|^\./|  |'
fi
