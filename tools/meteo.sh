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
