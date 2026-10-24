#!/usr/bin/env bash
# Active une ambiance météo à partir de meteo/<ambiance>/ :
# - cfgweather.xml et spawngear_survivant.json sont copiés à leur place dans la mission ;
# - gameplay.json (éclairage, températures) est reporté dans cfggameplay.json ;
# - message.txt devient le message affiché à la connexion dans db/messages.xml.
# Usage : tools/meteo.sh default|hiver|canicule|tempete
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
EOF

echo "Ambiance '$AMBIANCE' activée. Envoyer sur le FTP puis redémarrer :"
echo "  cfgweather.xml, cfggameplay.json, custom/spawngear_survivant.json, db/messages.xml"
if [ -f "$PRESET/mappings.txt" ]; then
	echo "  et les mappings de l'ambiance (s'ils ne sont pas déjà sur le FTP) :"
	grep -v '^#' "$PRESET/mappings.txt" | sed 's|^\./|  |'
fi
