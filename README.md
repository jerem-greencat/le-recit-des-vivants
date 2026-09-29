# Le Récit des Vivants

Serveur DayZ RP sur Xbox — map Chernarus, hébergé chez Nitrado.

Sur console, les mods ne sont pas disponibles : toute la personnalisation passe par les fichiers de mission.

## Origine des fichiers

Les fichiers sont une copie de ceux du serveur Nitrado, téléchargés par FTP le 29/09/2026
(DayZ 1.29, fichiers vanilla générés par Nitrado). L'arborescence du dépôt reprend celle du FTP.

## Structure

| Dossier / fichier | Contenu |
| --- | --- |
| `dayzxb_missions/dayzOffline.chernarusplus/` | Mission : économie, loot, gameplay, mappings |
| `dayzxb/config/` | Profil serveur et logs (`.RPT`, `.ADM`, `script_*.log`) |
| `restart.log` | Log des démarrages/arrêts écrit par Nitrado |

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
| `custom/*.json` | Mappings DayZ Editor (Object Spawner) |
| `areaflags.map` | Carte des zones d'usage/valeur (binaire, ne pas modifier) |

### Pas d'`init.c`

Le serveur charge un `init.c`, mais Nitrado ne l'expose pas sur le FTP des serveurs console.
Tout ce qui passerait par `init.c` se fait via `cfggameplay.json` :

- équipement de départ : `PlayerData.spawnGearPresetFiles` ;
- objets / mappings : `WorldsData.objectSpawnersArr`.

## Mappings

Chaque mapping est un JSON dans `custom/`, déclaré dans `objectSpawnersArr` de `cfggameplay.json` :

```json
"objectSpawnersArr": ["./custom/PZero_SpawnTest_LordBionik.json"],
```

| Fichier | Description |
| --- | --- |
| `custom/PZero_SpawnTest_LordBionik.json` | Mapping de test, positionné volontairement au point zéro de la map |

Les objets ramassables (armes, `UndergroundStash`…) d'un mapping sont recréés à chaque
redémarrage, même s'ils ont été pris : à éviter hors test.

## Déploiement (FTP)

1. Arrêter le serveur depuis l'interface Nitrado (sinon il peut réécrire des fichiers à l'arrêt).
2. Envoyer les fichiers modifiés avec FileZilla en mode binaire, en respectant l'arborescence
   et la casse des noms.
3. Vérifier que l'utilisation de `cfggameplay.json` est activée dans les réglages Nitrado.
4. Démarrer le serveur, puis contrôler `restart.log` et le dernier `.RPT` de `dayzxb/config/`
   (erreurs de parsing XML/JSON, `No custom folder found`…).

Les JSON et XML doivent être en UTF-8 sans BOM.
