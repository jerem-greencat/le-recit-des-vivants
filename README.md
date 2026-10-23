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
| `cfgweather.xml` | Météo (ambiance active, copiée depuis `meteo/`) |
| `meteo/<ambiance>/` | Ambiances météo : météo, éclairage, températures, équipement de départ, message (voir la section Météo) |
| `cfgEffectArea.json` | Zones contaminées |
| `env/*.xml` | Territoires des animaux et des zombies |
| `mapgroup*.xml`, `mapcluster*.xml` | Positions de loot des bâtiments (rarement modifiés) |
| `custom/*.json` | Mappings DayZ Editor (Object Spawner) et presets d'équipement de départ |
| `custom/spawngear_survivant.json` | Équipement de départ des joueurs (`PlayerData.spawnGearPresetFiles`), copié depuis `meteo/` |
| `areaflags.map` | Carte des zones d'usage/valeur (binaire, ne pas modifier) |

### Pas d'`init.c`

Le serveur charge un `init.c`, mais Nitrado ne l'expose pas sur le FTP des serveurs console.
Tout ce qui passerait par `init.c` se fait via `cfggameplay.json` :

- équipement de départ : `PlayerData.spawnGearPresetFiles` ;
- objets / mappings : `WorldsData.objectSpawnersArr`.

## Mappings

Chaque mapping est un JSON dans `custom/`, déclaré dans `objectSpawnersArr` de `cfggameplay.json` :

```json
"objectSpawnersArr": [
  "./custom/PZero_SpawnTest_LordBionik.json",
  "./custom/zeleno_enceinte.json",
  "./custom/zeleno_garagiste_v2.json",
  "./custom/zeleno_hospital.json",
  "./custom/zeleno_police.json",
  "./custom/zeleno_church.json",
  "./custom/zeleno_city_hall.json",
  "./custom/zeleno_builder.json",
  "./custom/zeleno_gunshop.json",
  "./custom/shop_admin.json"
],
```

| Fichier | Description |
| --- | --- |
| `custom/PZero_SpawnTest_LordBionik.json` | Mapping de test, positionné volontairement au point zéro de la map |
| `custom/zeleno_enceinte.json` | Enceinte de la zone safe de Zelenogorsk : murs, poteaux, barrages, épaves |
| `custom/zeleno_garagiste_v2.json` | Zone RP du garagiste : en face de la station essence de Zelenogorsk, de l'autre côté de la route |
| `custom/zeleno_hospital.json` | Zone RP du médecin dans l'hôpital de Zelenogorsk (`Land_Village_HealthCare`) : matériel médical sur les étagères |
| `custom/zeleno_police.json` | Commissariat de Zelenogorsk : munitions et chargeurs, lampes tactiques, piles, barbelés, tour de guet |
| `custom/zeleno_church.json` | Église de Zelenogorsk : décor (tombes, sarcophage, corps, pendus) et bibles |
| `custom/zeleno_city_hall.json` | Mairie de Zelenogorsk : mobilier de bureau (bureaux, PC, tapis, bancs), bougies, décor |
| `custom/zeleno_builder.json` | Zone RP du constructeur à Zelenogorsk : matériaux (rondins, tôles, fil, corde, filets de camouflage) et outils |
| `custom/zeleno_gunshop.json` | Armurerie de Zelenogorsk : boîtes de munitions de tous calibres et tableaux d'affichage |
| `custom/shop_admin.json` | Shop admin à l'aérodrome de Krasnostav : stock d'objets (matériaux de construction, conteneurs, munitions, explosifs…) |

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
  les 2 zones de gaz dynamique de Zelenogorsk (`StaticContaminatedArea`, ville et zone militaire) ;
- `env/wolf_territories.xml` : zones de loups dont le bord est à moins de 500 m de la zone safe
  (17 zones, dont un territoire entier qui n'avait plus de zone de repos).

Les hordes et les meutes de chiens sont placées à plus de 1,5 km de la zone safe.

Pour rétablir une zone, décommenter sa ligne.

## Danger

| Élément | Réglage | Fichier |
| --- | --- | --- |
| Zombies | `smin`/`smax`/`dmin`/`dmax` ×2 sur toutes les zones actives | `env/zombie_territories.xml` |
| Plafonds zombies | `ZombieMaxCount` 1000 → 1500, `max` des événements `Infected*` ×2 | `db/globals.xml`, `db/events.xml` |
| Hordes civiles | `StaticHorde` : 8 hordes de 25 à 35 zombies (`InfectedHorde`) autour d'une épave de voiture, dans les villes et villages | `db/events.xml`, `cfgeventspawns.xml` |
| Hordes militaires | `StaticHordeMilitary` : 4 hordes de 25 à 35 zombies militaires (`InfectedArmy`) autour d'une épave militaire, dans les bases | `db/events.xml`, `cfgeventspawns.xml` |
| Loups | 16 meutes de 5 à 8 (au lieu de 8 meutes de 4 à 6) | `db/events.xml` |
| Ours | 6 groupes de 1 ou 2 ours (au lieu de 2 ours seuls), `limit` passé de `custom` à `child` comme les loups | `db/events.xml` |
| Chiens | **Désactivé** (`active` 0, territoire commenté) : soupçonné de bloquer les zombies, voir plus bas. Prévu : `AnimalDog`, 15 meutes de 2 à 4 dobermans / bergers allemands, territoires `Dog` | `db/events.xml`, `cfgenvironment.xml`, `env/dog_territories.xml` |
| Animaux | `AnimalMaxCount` 200 → 300 | `db/globals.xml` |

Hordes : une position par point d'intérêt, soit 57 villes et villages et 18 bases militaires. Un point
d'intérêt regroupe des zones de zombies actives distantes de moins de 300 m ; seuls ceux qui comptent
au moins 40 zombies (somme des `smax` + `dmax`) sont retenus côté civil. Dans chacun, l'épave est posée sur
la position de spawn de véhicule (`Vehicle*`, `StaticPoliceCar`) la plus proche du centre : une route ou
un parking, jamais dans un bâtiment. Une horde disparaît au bout de 45 min si personne n'est à moins de 300 m, puis réapparaît ailleurs,
hors de vue des joueurs (500 m) : les hordes « se déplacent » d'un point à l'autre de la carte. Les
zombies ne marchent pas en groupe d'un point à un autre : ce n'est pas faisable sans `init.c`. La taille
d'une horde se règle dans la balise `<zone>` de `StaticHorde` (`cfgeventspawns.xml`).

Chiens : classes vanilla de la 1.30, utilisées par Bohemia sur Nasdara avec le comportement
`DZDogGroupBeh` (repris tel quel). Un territoire par camp de tentes militaires et par camp de chasse
(`Land_Camp_House_*`). Si `DZDogGroupBeh` est inconnu sur le serveur, le `.RPT` le signale au démarrage.
Après l'ajout des chiens, il n'y avait presque plus de zombies dans les zones de `env/zombie_territories.xml`.
Le `.RPT` de cette session contient une seule erreur de territoire :
`File "DZ\worlds\chernarusplus\ce\env/dog_territories.xml" does not exist`, alors que le fichier est bien
dans `env/` sur le FTP. Pourtant, les fichiers `env/` de la mission
qui existent en vanilla sont bien lus (les zombies retirés de Zelenogorsk n'y apparaissent pas). Sur Xbox, un fichier
`env/` de la mission ne fait que remplacer le fichier du même nom dans le jeu : un nouveau nom n'est pas trouvé, et
cette erreur a fait disparaître les zombies de zone. Ne jamais ajouter de nouveau fichier dans `env/`. Les chiens
restent désactivés.

## Loot restreint

Certains objets ne se trouvent plus dans le loot de la map (bâtiments, zombies, crashs, événements) :
on ne peut les obtenir que via les mappings (shop admin, armurerie, commissariat, futur black market).

| Catégorie | Objets retirés | Conservés |
| --- | --- | --- |
| Armes lourdes | Fusils d'assaut (AK101, AK74, AKM, AKS74U, AS VAL, AUG, FAL, FAMAS, M4A1, M16A2, M14, SCAR-H, Vikhr), snipers (SVD, SV98, VSS), lance-grenades M79 | SKS, armes de chasse, fusils à pompe, pistolets, SMG |
| Explosifs | Grenades M67 et RGD-5, grenades flash, mines (Claymore, mine terrestre), explosif plastique, détonateur, grenade PO-X, toutes les munitions 40 mm (explosives, PO-X, fumigènes) | Grenades fumigènes à main |
| Chargeurs | Chargeurs des armes retirées (AK, STANAG, CMAG, AUG, FAL, FAMAS, M14, SCAR-H, SVD, SV98, VSS/VAL/Vikhr) | Toutes les munitions, sauf le 40 mm |
| Accessoires d'armes | Crosses, garde-mains, silencieux AK, baïonnettes AK et M9A1 (exclusifs aux armes retirées) | Optiques et accessoires qui vont aussi sur une arme conservée (MP5K, UMP45, Scout, PP19, Saiga, arbalètes, pistolets), lunettes de chasse |
| Tenues militaires | BDU, Gorka, M65, TTsKO, USMC, chemises tactiques, pull militaire, rangers (combat, jungle, militaires), gants tactiques et OMNO, ceinture militaire | Sacs militaires, rangers `MilitaryBoots_Bluerock` / `_Redpunk` (loot civil) |
| Gilets | Plate carrier (et ses holsters/poches), gilet haute capacité, Smersh, UK Assault, chest rig | Gilet de chasse, gilet de presse, gilet anti-couteaux (`PoliceVest`) |
| Accessoires militaires | Casques (balistiques, Gorka, MICH, SSh-68, tankiste, pilote), bérets, casquettes et chapeaux militaires, cagoule BDU, lunettes tactiques, vision nocturne (lunettes et sangle), gourde | Masques à gaz, combinaisons NBC |
| Ghillies | Toutes les pièces ghillie | |

Modifications, toutes commentées avec le marqueur `Loot restreint` :

- `db/types.xml` : `nominal` et `min` à 0, valeur d'origine en commentaire. L'entrée est conservée :
  le `lifetime` s'applique toujours aux objets des mappings ;
- `cfgspawnabletypes.xml` et `cfgrandompresets.xml` : ces fichiers font apparaître les objets même avec
  un `nominal` à 0 (équipement des zombies, cargo des sacs et des caisses), les lignes concernées sont
  donc commentées. Les presets de zombies militaires devenus vides (`hatsArmy`, `vestsArmy`,
  `HeavyArmorArmy`, `HeavyHelmetArmy`, `OfficerHatArmy`) sont commentés avec leurs références. Les
  attachements des armes retirées sont laissés tels quels.

Gaz dynamique : à chaque largage, le script du jeu (`ContaminatedArea_Dynamic`) pose 2 à 5 grenades PO-X
(`Grenade_ChemGas`) à 5–15 m du centre de la zone, sans passer par le loot. Le `lifetime` de
`Grenade_ChemGas` est passé de 900 à 10 s : le serveur les supprime presque aussitôt. Limite : le serveur
ne supprime pas un objet tant qu'un joueur est à moins de 100 m (`CleanupAvoidance` de `db/globals.xml`).
Un joueur en tenue NBC déjà sur place au moment du largage pourrait donc les ramasser. Une grenade PO-X
posée au sol (par un joueur ou un mapping) disparaît aussi au bout de 10 s si personne n'est à proximité.

Pour rétablir un objet : remettre ses valeurs d'origine dans `db/types.xml` et décommenter ses lignes.

## Loot RP

Objets ajoutés au loot de la map pour le RP. Marqueur `Loot RP` dans `db/types.xml`. Les objets absents
du `types.xml` vanilla ont une entrée créée en fin de fichier. Les autres avaient un `nominal` à 0 : la
valeur d'origine est en commentaire, et les `usage` ajoutés sont marqués.

| Objet | Quantité (`nominal`/`min`) | Où | Remarque |
| --- | --- | --- | --- |
| Graines de cannabis (`CannabisSeedsPack`) | 8/4 | Fermes | 10 graines par sachet, à planter dans un potager. Chaque plant donne 7 têtes de `Cannabis` |
| Cannabis (`Cannabis`), graines (`CannabisSeeds`), plant (`Plant_Cannabis`) | 0/0 | Culture uniquement | Le cannabis se mange, sans effet particulier |
| Frigo (`Refridgerator`) | 4/2 | Zones industrielles, villes | Se pose au sol, 40 cases de stockage, se branche sur un générateur. Ne ralentit pas le pourrissement |
| Cigarettes (Chernamorka, Merkur, Partyzanka) | 10/6 chacune | Villes, villages, prison | Accessoire, pas d'action « fumer » |
| Champignons amanite et psilocybe | 6/3 chacun | Zones de chasse | Pas d'effet particulier |
| Livres (145 titres, dont la Bible) | 1/1 chacun | Emplacements « livres » des bâtiments (villes, villages, bureaux, écoles) | Accessoire, non lisible |
| Stylos (4 couleurs), papier | 8/4 chacun, 20/10 | Villes, bureaux, écoles | Le jeu ne permet pas d'écrire. `Paper` passe de `crafted="1"` à `crafted="0"` pour pouvoir apparaître |
| Valises d'armes (`GunCase_*`) | 2/1 chacune | Zones de chasse, police (au lieu de militaire) | Livrées ouvertes avec leur clé. Se ferment et s'ouvrent avec la clé de la même couleur, et n'importe quelle clé de cette couleur les ouvre |
| Mallette scientifique et clés | 2/1 chacune | Hôpitaux, bureaux | `lifetime` passé de 1800 à 14400 s. Les clés apparaissent séparément |
| Lance-fusées et fusées éclairantes | 5/2, 8/4 par couleur | Côte, police, pompiers, médical, militaire | |
| Matraque télescopique | 8/4 | Villes, police | |
| Vêtements : doudounes, blousons d'aviateur, gants et lunettes de ski, chapkas, ballerines, bandanas uni, gilet réfléchissant, lunettes anti-poussière | 3 à 10 | Villes, villages, zones industrielles | |
| Variantes de couleur : Mosin (noir, camo, vert), CZ527 (noir, camo, vert), Winchester 70 (noir, vert), B95 (noir, vert), Derringer (noir, rose) | 2 à 4 | Comme l'arme de base | Elles s'ajoutent aux armes de base |
| Nourriture : chair de crabe, sodas Takola et ZumZam, sarma, crackers, mélange salé, banane, orange, kiwi | 8 à 10 | Villes, villages, côte | |
| Pots en céramique (4 couleurs) | 3/2 chacun | Fermes, villes, villages, chasse | Ustensile de cuisine |

Laissés de côté : la radio (sa pile `BatteryD` n'existe pas dans le jeu) et les cassettes. Aussi la
matraque électrique, l'aiguillon électrique et le défibrillateur : `cfgignorelist.xml` les supprime
au démarrage.

## Météo

Quatre ambiances sont prêtes dans `meteo/` :

| Ambiance | Ciel | Pluie | Vent | Températures (min / max) | Nuits |
| --- | --- | --- | --- | --- | --- |
| `default` | Météo vanilla (fichier désactivé, `enable="0"`) | Normale | Normal | Vanilla, selon le mois | Claires |
| `hiver` | Gris (couverture 0.4 à 0.9), brume | Aucune | 2 m/s minimum | -10 / -3 °C toute l'année | Noires |
| `canicule` | Dégagé (couverture 0 à 0.25), pas de brume | Aucune | Normal | 22 / 38 °C toute l'année | Claires |
| `tempete` | Couvert (0.8 à 1.0) | Forte, orages | 10 m/s minimum | Vanilla, selon le mois | Noires |

Équipement de départ : les objets sont les mêmes partout (radio et pile, carte, bouteille d'eau pleine,
ouvre-boîte, confiture, spaghettis, 6 chiffons, boîte de clous), ainsi que la sacoche. Seuls les
vêtements changent :

| Ambiance | Haut | Bas | Chaussures | En plus |
| --- | --- | --- | --- | --- |
| `default` | Pull | Pantalon de toile | Baskets | |
| `hiver` | Doudoune | Jean | Chaussures de travail | Bonnet, gants en laine |
| `canicule` | T-shirt | Short en jean | Baskets | Casquette |
| `tempete` | Imperméable | Pantalon de toile | Bottes en caoutchouc | |

Chaque dossier `meteo/<ambiance>/` contient :

| Fichier | Rôle | Remplace |
| --- | --- | --- |
| `cfgweather.xml` | Météo | `cfgweather.xml` |
| `gameplay.json` | Éclairage des nuits (`lightingConfig` : 0 claires, 1 noires) et températures | Ces trois valeurs dans `cfggameplay.json` |
| `spawngear_survivant.json` | Équipement de départ | `custom/spawngear_survivant.json` |
| `message.txt` | Message affiché 1 min après la connexion (vide : pas de message) | Le bloc « AMBIANCE METEO » de `db/messages.xml` |
| `mappings.txt` (facultatif) | Mappings chargés seulement avec cette ambiance (la neige pour `hiver`) | Ajoutés à `objectSpawnersArr` de `cfggameplay.json` |

Pour changer d'ambiance, en local :

```sh
tools/meteo.sh hiver   # ou default, canicule, tempete
```

Le script met à jour les quatre fichiers de la colonne « Remplace ». Il reste à les envoyer sur le FTP
et à redémarrer. Dans `db/messages.xml`, il ne touche qu'au bloc entre les marqueurs `AMBIANCE METEO` :
les autres messages restent en place. De même, dans `objectSpawnersArr`, il ne retire que les mappings
listés dans un `mappings.txt` : les autres mappings ne bougent pas.

### Neige au sol (ambiance `hiver`)

La neige au sol est faite de plaques de neige de Sakhal (`StaticObj_Decal_Sakhal_Snow_*`, visibles même
sans le DLC), générées par ville dans `custom/neige_<ville>.json` :

```sh
python3 tools/neige/generate.py zelenogorsk
```

Le script lit le relief et les objets de la carte dans le jeu installé sur le PC (cache dans
`tools/neige/cache/`, non versionné), puis couvre la ville en évitant les bâtiments et les rues goudronnées.
Les plaques sont inclinées selon la pente, puis abaissées pour ne flotter nulle part (quelques
centimètres au plus) ; celles qui s'enfonceraient de plus de 30 cm ailleurs sont écartées. Chaque plaque est un objet synchronisé par le serveur : à
3 572 plaques pour Zelenogorsk, les joueurs avaient l'icône de désynchronisation en permanence. Le script
ne pose donc que des grandes plaques. Il écrit aussi une image de contrôle
`tools/neige/cache/neige_<ville>.png` (blanc : neige, rouge : bâtiments, brun : rues). Les réglages
(densité, pente maximale…) sont en tête du script. Pour une nouvelle ville, l'ajouter à `TOWNS` dans le
script et son fichier à `meteo/hiver/mappings.txt`.

| Ville | Plaques | Surface libre couverte |
| --- | --- | --- |
| Zelenogorsk | 580 | 17 % |

Les valeurs `lightingConfig` 2 et 3 chargent l'éclairage de Sakhal et de Nasdara. Elles ne sont pas
utilisées : ces fichiers font partie des DLC, et les joueurs qui ne les ont pas risquent de ne pas les avoir.

Ce que Chernarus permet (vérifié dans les scripts du jeu, `ChernarusPlus.c`) :

- **La météo reste pilotée par le script de Chernarus.** `cfgweather.xml` ne fait que borner les valeurs
  (`limits`). Le script réimpose aussi le seuil de pluie (couverture 0.6), celui des éclairs (0.9) et un
  vent maximum de 20 m/s : seul le minimum de vent est réglable.
- **Pas de chute de neige.** Le script remet la neige à 0 à chaque changement de météo. Il faudrait un
  `init.c`, non disponible sur console. La neige au sol passe par des mappings (voir plus haut).
- **Pas de tempête de sable.** Elle est gérée par le script de Nasdara, qui ne tourne pas sur Chernarus.
- **Le gel fonctionne.** Il ne dépend que de la température : avec l'ambiance `hiver`, l'eau et la
  nourriture gèlent comme sur Sakhal, et les joueurs ont froid.

Les ambiances `hiver`, `canicule` et `tempete` ont `reset="1"` : la météo sauvegardée est ignorée et
l'ambiance s'applique dès le redémarrage.

## Déploiement (FTP)

1. Arrêter le serveur depuis l'interface Nitrado (sinon il peut réécrire des fichiers à l'arrêt).
2. Envoyer les fichiers modifiés avec FileZilla en mode binaire, en respectant l'arborescence
   et la casse des noms.
3. Vérifier que l'utilisation de `cfggameplay.json` est activée dans les réglages Nitrado.
4. Démarrer le serveur, puis contrôler `restart.log` et le dernier `.RPT` de `dayzxb/config/`
   (erreurs de parsing XML/JSON, `No custom folder found`…).

Les JSON et XML doivent être en UTF-8 sans BOM.
