#!/usr/bin/env bash
# Active une ambiance météo à partir de meteo/<ambiance>/ :
# - cfgweather.xml et spawngear_survivant.json sont copiés à leur place dans la mission ;
# - gameplay.json (éclairage, températures) est reporté dans cfggameplay.json ;
# - message.txt devient le message affiché à la connexion dans db/messages.xml ;
# - mappings.txt (facultatif) : mappings ajoutés à objectSpawnersArr de cfggameplay.json ;
# - events.xml (facultatif) : blocs <event> qui remplacent ceux de db/events.xml ; hors de cette ambiance,
#   les blocs de events.origine.xml sont remis ;
# - zombie_territories.xml (facultatif) : zones ajoutées à env/zombie_territories.xml, entre deux marqueurs.
# Usage : tools/meteo.sh default|hiver|canicule|tempete|brouillard
set -euo pipefail

MISSION="$(dirname "$0")/../dayzxb_missions/dayzOffline.chernarusplus"
AMBIANCE="${1:-}"
PRESET="$MISSION/meteo/$AMBIANCE"

if [ -z "$AMBIANCE" ] || [ ! -f "$PRESET/cfgweather.xml" ]; then
	echo "Usage : $0 <ambiance>  (disponibles : $(ls "$MISSION/meteo" | tr '\n' ' '))" >&2
	exit 1
fi

cp "$PRESET/cfgweather.xml" "$MISSION/cfgweather.xml"
cp "$PRESET/spawngear_survivant.json" "$MISSION/custom/spawngear_survivant.json"

python3 -I - "$PRESET" "$MISSION" <<'EOF'
import json, re, sys
preset, mission = sys.argv[1], sys.argv[2]

# cfggameplay.json : on remplace les valeurs ligne par ligne pour garder la mise en forme du fichier
path = mission + "/cfggameplay.json"
text = open(path).read()
for key, value in json.load(open(preset + "/gameplay.json")).items():
	value = "[" + ", ".join(str(v) for v in value) + "]" if isinstance(value, list) else str(value)
	text, n = re.subn(r'("%s":\s*)(\[[^\]]*\]|[^,\n]+)' % key, lambda m: m.group(1) + value, text)
	if n != 1:
		sys.exit("%s introuvable dans %s" % (key, path))
# mappings propres à une ambiance (meteo/*/mappings.txt) : on retire ceux de toutes les ambiances,
# puis on ajoute ceux de l'ambiance choisie ; les autres mappings ne sont pas touchés
def mappings(folder):
	try:
		return [l.strip() for l in open(folder + "/mappings.txt") if l.strip() and not l.startswith("#")]
	except FileNotFoundError:
		return []
import glob, os
every = {m for folder in glob.glob(os.path.dirname(preset) + "/*") for m in mappings(folder)}
match = re.search(r'("objectSpawnersArr":\s*\[)(.*?)(\n\t*\])', text, re.S)
current = [m for m in re.findall(r'"([^"]+)"', match.group(2)) if m not in every] + mappings(preset)
text = text[:match.start(2)] + "".join("\n\t\t\t\"%s\"," % m for m in current).rstrip(",") + text[match.end(2):]
json.loads(text)
open(path, "w").write(text)

# db/messages.xml : le message d'ambiance est entre deux marqueurs, le reste du fichier n'est pas touché
path = mission + "/db/messages.xml"
text = open(path).read()
start, end = "<!-- AMBIANCE METEO (tools/meteo.sh) -->", "<!-- FIN AMBIANCE METEO -->"
text = re.sub(r"\n?[ \t]*" + re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
message = open(preset + "/message.txt").read().strip()
if message:
	message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
	block = ("\t%s\n\t<message>\n\t\t<delay>1</delay>\n\t\t<onconnect>1</onconnect>\n"
		"\t\t<text>%s</text>\n\t</message>\n\t%s\n" % (start, message, end))
	text = text.replace("</messages>", block + "</messages>")
open(path, "w").write(text)

# db/events.xml : remplacement de blocs <event> entiers, repérés par leur nom (même principe que fete.sh)
def blocks(path):
	if not os.path.isfile(path):
		return {}
	return {m.group(1): m.group(0) for m in re.finditer(r'^[ \t]*<event name="([^"]+)">.*?</event>', open(path).read(), re.M | re.S)}

known, origine = {}, {}
for folder in sorted(glob.glob(os.path.dirname(preset) + "/*")):
	for key, b in blocks(folder + "/events.xml").items():
		known.setdefault(key, set()).add(b)
	for key, b in blocks(folder + "/events.origine.xml").items():
		origine[key] = b
		known.setdefault(key, set()).add(b)
path = mission + "/db/events.xml"
text = open(path).read()

def swap(text, key, new):
	if text.count('<event name="%s">' % key) != 1:
		sys.exit("db/events.xml : bloc %s introuvable ou en double" % key)
	m = re.search(r'^[ \t]*<event name="%s">.*?</event>' % re.escape(key), text, re.M | re.S)
	if m.group(0) not in known[key]:
		sys.exit("db/events.xml : le bloc %s a été modifié à la main, mettre à jour meteo/*/events*.xml" % key)
	return text[:m.start()] + new + text[m.end():]

for key in known:
	if key not in origine:
		sys.exit("db/events.xml : pas de valeur d'origine pour %s (meteo/*/events.origine.xml)" % key)
	text = swap(text, key, origine[key])
for key, b in blocks(preset + "/events.xml").items():
	text = swap(text, key, b)
open(path, "w").write(text)

# env/zombie_territories.xml : zones propres à l'ambiance, dans un territoire à part entre deux marqueurs
path = mission + "/env/zombie_territories.xml"
text = open(path).read()
start, end = "<!-- ZOMBIES METEO (tools/meteo.sh) -->", "<!-- FIN ZOMBIES METEO -->"
text = re.sub(r"\n?[ \t]*" + re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
if os.path.isfile(preset + "/zombie_territories.xml"):
	zones = open(preset + "/zombie_territories.xml").read().rstrip("\n")
	block = '    %s\n    <territory color="4278255360">\n%s\n    </territory>\n    %s\n' % (start, zones, end)
	if text.count("</territory-type>") != 1:
		sys.exit("env/zombie_territories.xml : fin de fichier introuvable")
	text = text.replace("</territory-type>", block + "</territory-type>")
open(path, "w").write(text)
EOF

echo "Ambiance '$AMBIANCE' activée. Envoyer sur le FTP puis redémarrer :"
echo "  cfgweather.xml, cfggameplay.json, custom/spawngear_survivant.json, db/messages.xml,"
echo "  db/events.xml, env/zombie_territories.xml"
if [ -f "$PRESET/mappings.txt" ]; then
	echo "  et les mappings de l'ambiance (s'ils ne sont pas déjà sur le FTP) :"
	grep -v '^#' "$PRESET/mappings.txt" | sed 's|^\./|  |'
fi
