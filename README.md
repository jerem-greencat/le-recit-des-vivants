# Le Récit des Vivants

Serveur DayZ RP sur Xbox — map Chernarus.

## Structure

`dayzxb_missions/dayzOffline.chernarusplus/` reprend le chemin de la mission sur un serveur Xbox Nitrado.

Fichiers vanilla d'origine : dépôt officiel de Bohemia Interactive
[DayZ-Central-Economy](https://github.com/BohemiaInteractive/DayZ-Central-Economy),
commit `9a21bb9` (13/08/2026).

## Fichiers principaux

| Fichier | Rôle |
| --- | --- |
| `db/types.xml` | Loot : quantités, durée de vie, zones de spawn de chaque objet |
| `db/events.xml` | Véhicules, hélicos crashés, animaux, zombies dynamiques |
| `db/globals.xml` | Paramètres globaux de l'économie (nettoyage, limites, etc.) |
| `db/economy.xml` | Persistance et activation des systèmes économiques |
| `db/messages.xml` | Messages serveur (annonces, redémarrages) |
| `cfggameplay.json` | Gameplay : stamina, construction, spawn gear, carte… |
| `cfgspawnabletypes.xml` | Attachements et cargo des objets qui spawnent |
| `cfgplayerspawnpoints.xml` | Points d'apparition des joueurs |
| `cfgeventspawns.xml` | Positions de spawn des événements |
| `cfgweather.xml` | Météo |
| `cfgEffectArea.json` | Zones contaminées |
| `init.c` | Script de démarrage de la mission (équipement de départ, date/heure) |
| `env/*.xml` | Territoires des animaux et des zombies |
| `mapgroup*.xml`, `mapcluster*.xml` | Positions de loot des bâtiments (rarement modifiés) |
| `areaflags.map` | Carte des zones d'usage/valeur (binaire, 81 Mo, ne pas modifier) |

Sur console, les mods ne sont pas disponibles : toute la personnalisation passe par ces fichiers.
