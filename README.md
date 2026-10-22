# Le Récit des Vivants

Serveur DayZ RP sur Xbox — map Chernarus, hébergé chez Nitrado.

Sur console, les mods ne sont pas disponibles : toute la personnalisation passe par les fichiers de mission.

## Origine des fichiers

Les fichiers sont une copie de ceux du serveur Nitrado, téléchargés par FTP le 29/09/2026
(fichiers vanilla générés par Nitrado). L'arborescence du dépôt reprend celle du FTP.

Les fichiers fournis par Nitrado étaient une variante console proche de DayZ 1.29 (certaines valeurs
de loot et d'événements diffèrent du vanilla). Le passage en 1.30 a été fait par fusion à trois voies
avec le dépôt officiel [BohemiaInteractive/DayZ-Central-Economy](https://github.com/BohemiaInteractive/DayZ-Central-Economy) :
base `DZ_129`, cible `DZ_130`. Seuls les changements de Bohemia entre ces deux tags ont été appliqués ;
les spécificités Nitrado et nos modifications sont conservées. Pour `db/types.xml` et `cfgspawnabletypes.xml`,
la fusion se fait par entrée `<type>` : les nouveaux types sont regroupés en fin de fichier, et une entrée
existante n'est mise à jour que si elle était encore identique à la 1.29. Seules différences côté Xbox :
pas d'`init.c`, de `env/fox_territories.xml` ni de `mapgroupdirt.xml`. Pour une prochaine mise à jour,
refaire la même fusion avec `DZ_130` comme base et le nouveau tag comme cible.

## Structure

| Dossier / fichier | Contenu |
| --- | --- |
| `dayzxb_missions/dayzOffline.chernarusplus/` | Mission : économie, loot, gameplay, mappings |
| `dayzxb/config/` | Profil serveur et logs (`.RPT`, `.ADM`, `script_*.log`) |
| `restart.log` | Log des démarrages/arrêts écrit par Nitrado |

Les logs (`.RPT`, `.ADM`, `.log`, `restart.log`, `stop`) sont ignorés par git : on peut les
télécharger en local pour diagnostiquer, ils ne sont pas versionnés.

## Fichiers de mission

| Fichier | Rôle |
| --- | --- |
| `db/types.xml` | Loot : quantités, durée de vie, zones de spawn de chaque objet |
| `db/events.xml` | Véhicules, hélicos crashés, animaux, zombies dynamiques |
| `db/globals.xml` | Paramètres globaux de l'économie (nettoyage, limites, etc.) |
| `db/economy.xml` | Persistance et activation des systèmes économiques |
| `db/messages.xml` | Messages serveur (annonces, redémarrages) |
| `cfggameplay.json` | Gameplay : stamina, construction, spawn gear, carte, mappings… |
| `cfgspawnabletypes.xml` | Attachements et cargo des objets qui spawnent |
| `cfgplayerspawnpoints.xml` | Points d'apparition des joueurs |
| `cfgeventspawns.xml` | Positions de spawn des événements |
| `cfgweather.xml` | Météo |
| `cfgEffectArea.json` | Zones contaminées |
| `env/*.xml` | Territoires des animaux et des zombies |
| `mapgroup*.xml`, `mapcluster*.xml` | Positions de loot des bâtiments (rarement modifiés) |
| `custom/*.json` | Mappings DayZ Editor (Object Spawner) et presets d'équipement de départ |
| `custom/spawngear_survivant.json` | Équipement de départ des joueurs (`PlayerData.spawnGearPresetFiles`) |
| `areaflags.map` | Carte des zones d'usage/valeur (binaire, ne pas modifier) |

### Pas d'`init.c`

Le serveur charge un `init.c`, mais Nitrado ne l'expose pas sur le FTP des serveurs console.
Tout ce qui passerait par `init.c` se fait via `cfggameplay.json` :

- équipement de départ : `PlayerData.spawnGearPresetFiles` ;
- objets / mappings : `WorldsData.objectSpawnersArr`.

## Mappings

Chaque mapping est un JSON dans `custom/`, déclaré dans `objectSpawnersArr` de `cfggameplay.json` :

```json
"objectSpawnersArr": ["./custom/PZero_SpawnTest_LordBionik.json", "./custom/zeleno_enceinte.json", "./custom/zeleno_garagiste.json", "./custom/zeleno_hospital.json"],
```

| Fichier | Description |
| --- | --- |
| `custom/PZero_SpawnTest_LordBionik.json` | Mapping de test, positionné volontairement au point zéro de la map |
| `custom/zeleno_enceinte.json` | Enceinte de la zone safe de Zelenogorsk : murs, poteaux, barrages, épaves |
| `custom/zeleno_garagiste_v2.json` | Zone RP du garagiste : en face de la station essence de Zelenogorsk, de l'autre côté de la route |
| `custom/zeleno_hospital.json` | Zone RP du médecin dans l'hôpital de Zelenogorsk (`Land_Village_HealthCare`) : matériel médical sur les étagères |

Les objets ramassables (armes, `UndergroundStash`…) d'un mapping sont recréés à chaque
redémarrage, même s'ils ont été pris : à éviter hors test.

## Zone safe de Zelenogorsk

Aucun zombie ne spawn dans la ville, la gare/zone industrielle et la zone militaire de
Zelenogorsk, ni à moins de 250 m autour (bord de la zone de spawn à moins de 250 m) :

| Zone | x | z |
| --- | --- | --- |
| Ville | 2480–2960 | 5060–5640 |
| Gare / zone industrielle | 2180–2520 | 5140–5320 |
| Zone militaire | 2360–2640 | 4980–5220 |

Les lignes désactivées sont commentées avec le marqueur `SafeZone Zelenogorsk` :

- `env/zombie_territories.xml` : zones de spawn des zombies (18 zones) ;
- `cfgeventspawns.xml` : positions des événements qui font apparaître des zombies (crash
  d'hélico, voitures de police, feu de camp, crash du père Noël, police situation : 12 positions) et
  les 2 zones de gaz dynamique de Zelenogorsk (`StaticContaminatedArea`, ville et zone militaire).

Pour rétablir une zone, décommenter sa ligne.

## Déploiement (FTP)

1. Arrêter le serveur depuis l'interface Nitrado (sinon il peut réécrire des fichiers à l'arrêt).
2. Envoyer les fichiers modifiés avec FileZilla en mode binaire, en respectant l'arborescence
   et la casse des noms.
3. Vérifier que l'utilisation de `cfggameplay.json` est activée dans les réglages Nitrado.
4. Démarrer le serveur, puis contrôler `restart.log` et le dernier `.RPT` de `dayzxb/config/`
   (erreurs de parsing XML/JSON, `No custom folder found`…).

Les JSON et XML doivent être en UTF-8 sans BOM.
