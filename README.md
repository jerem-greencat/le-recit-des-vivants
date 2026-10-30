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

La 1.30 apporte les motos (`Motorbike_01`, `Motorbike_02`) : événement `VehicleMotorbike` dans `db/events.xml`
(97 positions dans `cfgeventspawns.xml`), classe `MotorbikeScript` déclarée dans `cfgeconomycore.xml`.
Le crash du père Noël (`ZmbM_Santa`) a été désactivé (`active` 0) au même moment.

## Structure

| Dossier / fichier | Contenu |
| --- | --- |
| `dayzxb_missions/dayzOffline.chernarusplus/` | Mission : économie, loot, gameplay, mappings |
| `dayzxb/config/` | Profil serveur (`Users/Server/DayZ.cfg`, `Users/Survivor/*.DayZProfile`) et logs (`.RPT`, `.ADM`, `script_*.log`) |
| `tools/` | Scripts locaux : changement d'ambiance météo et génération des mappings d'ambiance (voir Outils) |
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
| `db/messages.xml` | Messages serveur (bienvenue à la connexion, avertissements de redémarrage calés sur le redémarrage planifié Nitrado toutes les 4 h) |
| `cfggameplay.json` | Gameplay : stamina, construction, spawn gear, carte, mappings… |
| `cfgspawnabletypes.xml` | Attachements et cargo des objets qui spawnent |
| `cfgplayerspawnpoints.xml` | Points d'apparition des joueurs |
| `cfgeventspawns.xml` | Positions de spawn des événements |
| `cfgweather.xml` | Météo (ambiance active, copiée depuis `meteo/`) |
| `meteo/<ambiance>/` | Ambiances météo : météo, éclairage, températures, équipement de départ, message (voir la section Météo) |
| `fetes/<fete>/` | Fêtes (Noël, Halloween) : mappings, événements, loot et zones hantées, activés par `tools/fete.sh` (voir la section Fêtes) |
| `cfgrandompresets.xml` | Presets aléatoires de cargo et d'équipement (zombies, sacs, caisses) |
| `cfgignorelist.xml` | Objets supprimés au démarrage |
| `cfgeconomycore.xml` | Classes gérées par l'économie (dont les motos) |
| `cfgenvironment.xml` | Déclaration des territoires (`env/`) |
| `cfgeventgroups.xml` | Groupes d'objets des événements (trains, épaves…) |
| `cfglimitsdefinition.xml`, `cfglimitsdefinitionuser.xml` | Catégories, usages, valeurs et tags utilisables dans `types.xml` |
| `cfgundergroundtriggers.json` | Zones souterraines (bunker) |
| `cfgEffectArea.json` | Zones contaminées |
| `env/*.xml` | Territoires des animaux et des zombies |
| `mapgroup*.xml`, `mapcluster*.xml` | Positions de loot des bâtiments (rarement modifiés) |
| `custom/*.json` | Mappings DayZ Editor (Object Spawner) et presets d'équipement de départ |
| `custom/neige_*.json`, `tempete_arbres.json`, `canicule_brulis.json` | Mappings d'ambiance générés par les scripts de `tools/` (ne pas modifier à la main) |
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
  "./custom/zeleno_admin.json",
  "./custom/zeleno_enceinte.json",
  "./custom/zeleno_garagiste_v2.json",
  "./custom/zeleno_hospital.json",
  "./custom/zeleno_police.json",
  "./custom/zeleno_church.json",
  "./custom/zeleno_city_hall.json",
  "./custom/zeleno_builder.json",
  "./custom/zeleno_builder_mobile.json",
  "./custom/zeleno_gunshop.json",
  "./custom/zeleno_epicerie.json",
  "./custom/zeleno_reporter.json",
  "./custom/zeleno_ghetto.json",
  "./custom/zeleno_market_place.json",
  "./custom/zeleno_global.json",
  "./custom/shop_admin.json",
  "./custom/vybor_shop_bm.json",
  "./custom/novaya_overgrown.json",
  "./custom/tishina_barrage_overgrown.json",
  "./custom/prison_bridge.json",
  "./custom/devils_castle_secte.json",
  "./custom/vyshnoye_plane_base.json",
  "./custom/junkyard_base.json",
  "./custom/pustoshka_survivor_camp.json"
],
```

S'y ajoutent les mappings de l'ambiance météo active, ajoutés et retirés par `tools/meteo.sh` : ne pas
les gérer à la main (voir la section Météo). De même pour les mappings de fête, gérés par
`tools/fete.sh` (voir la section Fêtes).

| Fichier | Description |
| --- | --- |
| `custom/PZero_SpawnTest_LordBionik.json` | Mapping de test, positionné volontairement au point zéro de la map |
| `custom/zeleno_admin.json` | Espace admin à l'ouest de la gare routière de Zelenogorsk : tenues admin (bob et brassard orange, voir Loot restreint), crochets de serrure, jerrican |
| `custom/zeleno_enceinte.json` | Enceinte de la zone safe de Zelenogorsk : murs, poteaux, barrages, épaves |
| `custom/zeleno_garagiste_v2.json` | Zone RP du garagiste : en face de la station essence de Zelenogorsk, de l'autre côté de la route |
| `custom/zeleno_hospital.json` | Zone RP du médecin dans l'hôpital de Zelenogorsk (`Land_Village_HealthCare`) : matériel médical sur les étagères |
| `custom/zeleno_police.json` | Commissariat de Zelenogorsk : munitions et chargeurs, lampes tactiques, piles, barbelés, tour de guet |
| `custom/zeleno_church.json` | Église de Zelenogorsk : décor (tombes, sarcophage, corps, pendus) et bibles |
| `custom/zeleno_city_hall.json` | Mairie de Zelenogorsk : mobilier de bureau (bureaux, PC, tapis, bancs), bougies, décor |
| `custom/zeleno_builder.json` | Zone RP du constructeur à Zelenogorsk : matériaux (rondins, tôles, fil, corde, filets de camouflage) et outils |
| `custom/zeleno_builder_mobile.json` | Stocks du constructeur mobile, en 4 points de Zelenogorsk : rondins, bâtons, tôles, fil, corde, barbelés, filets de camouflage, outils, cadenas et serrures à code |
| `custom/zeleno_gunshop.json` | Armurerie de Zelenogorsk : boîtes de munitions de tous calibres et tableaux d'affichage |
| `custom/zeleno_epicerie.json` | Zone RP de l'épicier dans le supermarché à l'ouest de la fontaine de Zelenogorsk (`Land_City_Store_WithStairs`) : nourriture, boissons et matériel de cuisine (Chernarus, Livonia, Sakhal, Badlands, sans fruits ni légumes) sur les rayons, viande et poisson dans les congélateurs, papier et stylos sur les caisses, stock et cartons dans la réserve |
| `custom/zeleno_reporter.json` | Maison du journaliste à l'est de Zelenogorsk (`Land_House_2B04`) : bureau radio (radio de base, talkie-walkie, mégaphone), gilet presse, jumelles, bibliothèque, papier |
| `custom/zeleno_ghetto.json` | Cité derrière l'hôpital de Zelenogorsk : route en dalles de béton qui relie les deux impasses, tour et barre d'immeubles, box, check-point et QG du gang, squat dans un bus, aire de jeux abandonnée, graffitis, épaves et feux |
| `custom/zeleno_market_place.json` | Place du marché de Zelenogorsk (place pavée au sud-est de la gare routière), pour le marché hebdomadaire : halles, boucherie, poissonnerie, rangée de stands, brocante, buvette, cabane du placier. Une boucle de voies reste libre pour les véhicules, et 6 emplacements de 8 × 9 m (coins marqués par des cônes) sont laissés aux tentes des joueurs |
| `custom/zeleno_global.json` | Ambiance post-apo dans toute la ville safe : feux cachés sous des poubelles, gravats et pneus, quelques épaves en feu, fosse commune. Fait à la main (plus de générateur) |
| `custom/shop_admin.json` | Shop admin à l'aérodrome de Krasnostav : stock d'objets (matériaux de construction, conteneurs, munitions, explosifs…) |
| `custom/vybor_shop_bm.json` | Black market à l'est de Vybor : conteneurs et caisses, objets du loot restreint (armes lourdes, explosifs, munitions 40 mm et RPG, casques, ghillies, vision nocturne), cigarettes, cannabis, matériel, le seul bob orange accessible aux joueurs |
| `custom/novaya_overgrown.json` | Novaya Petrovka envahie par la végétation : souches, herbes et buissons, arbres couchés, barricades, épaves (véhicules civils et militaires, hélico crashé). Camp de gitans (tabor) dans un terrain vague clos : caravanes autour du feu, tente commune, charrette, poulailler, étal de tapis |
| `custom/tishina_barrage_overgrown.json` | Barrage de Tishina : base fermée (murs, palissades en tôle, portails), atelier (étaux, établis, étagères), tuyaux, végétation |
| `custom/prison_bridge.json` | Pont de pierre vers l'île de la prison |
| `custom/devils_castle_secte.json` | Base de la secte au château du diable : remparts, tentes, tour, escaliers, tombes, têtes coupées, bougies |
| `custom/vyshnoye_plane_base.json` | Base autour d'une carcasse d'avion près de Vyshnoye : MiG-21, stand de tir, dortoir (lits de camp, casiers), cratères, arbres couchés |
| `custom/junkyard_base.json` | Casse auto au nord de la route de Berezino : dalle de béton à plat (sol 118,70) avec rampe d'accès depuis la route, des centaines d'épaves, piles de pneus, conteneurs, talus de rochers |
| `custom/pustoshka_survivor_camp.json` | Camp de survivants à Pustoshka : enceinte d'épaves (bus, Volga, UAZ, camions), barbelés, bungalows, conteneurs |
| `custom/comete.json` | Épaves du traîneau du père Noël au centre de Zelenogorsk. N'est plus chargé (retiré de `objectSpawnersArr`) |

Les objets ramassables (armes, `UndergroundStash`…) d'un mapping sont recréés à chaque
redémarrage, même s'ils ont été pris : à éviter hors test et hors zones RP. Dans les bases (secte,
avion…), seuls les objets de décor sont gardés (bougies, objets agrandis ou réduits, bois dans les
cheminées).

Règles pour les mappings sur console :

- uniquement des classes vanilla (`StaticObj_*`, `Land_*`…) : les classes `bldr_*` de DayZ Editor
  (mod BuilderItems) n'existent pas sur Xbox, et un chemin `.p3d` n'est accepté que pour les plantes et
  les rochers, qui restent invisibles pour les joueurs (voir Météo) ;
- les morceaux de route posés par mapping scintillent : utiliser des dalles de béton
  (`StaticObj_Panel_Concrete_*`) pour une chaussée ;
- un décor plat posé au ras du sol ou sur un autre (plaques de neige, décalcomanies) scintille :
  le surélever de quelques centimètres et décaler les hauteurs.

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

### Bâtiments RP sans loot

Le jeu ne fait plus spawn de loot au sol dans les bâtiments des zones RP de Zelenogorsk. Leurs
lignes ont été supprimées de `mapgrouppos.xml`. Les objets des fichiers de mapping restent :

| Zone RP | Bâtiment | Position (x, z) |
| --- | --- | --- |
| Commissariat | `Land_City_PoliceStation` | 2730, 5374 |
| Hôpital | `Land_Village_HealthCare` | 2739, 5181 |
| Mairie | `Land_HouseBlock_2F4` | 2734, 5320 |
| Armurerie | `Land_HouseBlock_1F2` | 2696, 5354 |
| Builder | `Land_Barn_Wood2` | 2585, 5360 |
| Épicerie | `Land_City_Store_WithStairs` | 2673, 5281 |

Pour rétablir le loot d'un bâtiment, remettre sa ligne `<group>` d'origine (historique git).

### Véhicules réduits de moitié

Le garagiste a son propre spawn de véhicules (`VehicleZelenoParking`). Les autres spawns de
véhicules terrestres de la map sont réduits de moitié dans `db/events.xml` (marqueur
`Vehicules reduits de moitie`). Les bateaux (`VehicleBoat`) et le Humvee ne changent pas :

| Événement | nominal / min / max | Par variante (min–max) |
| --- | --- | --- |
| `VehicleCivilianSedan`, `VehicleHatchback02`, `VehicleOffroadHatchback`, `VehicleSedan02`, `VehicleTruck01` | 8 / 5 / 11 (avant 16 / 10 / 22) | 2–3 (avant 3–5) |
| `VehicleMotorbike` | 12 / 3 / 6 (avant 25 / 5 / 11) | 5–10 (avant 10–20) |

Humvee (`VehicleOffroad02`, marqueur `Humvee`) : 4 sur la map (4 / 3 / 4), 2 verts
(`Offroad_02`) et 2 en version désert de Badlands (`Offroad_02_Beige`).

## Apparition des joueurs

Tous les joueurs apparaissent au même endroit, à l'est de Zelenogorsk (x 3073, z 5207.9), pour une
première connexion comme après une mort ou un changement de serveur (`fresh`, `hop` et `travel` dans
`cfgplayerspawnpoints.xml`). Garder `grid_density` au-dessus de 0 : à 0, il n'y a aucun point candidat
et les joueurs apparaissent au point (0, 0) de la carte.

## Construction

Les vérifications de placement sont assouplies dans `cfggameplay.json` (`BaseBuildingData`) pour
construire librement en RP : collisions, toit, pente, hauteur, terrain, plot de base et zones froides
(`disableIs…Check` à `true`, ainsi que `disablePerformRoofCheck` et `disableIsCollidingCheck` pour la
construction). Restent actives : la collision avec les joueurs, l'interdiction de construire sous l'eau
ou dans les zones interdites, et la distance de construction. Les bases et les conteneurs ne prennent
pas de dégâts (`disableBaseDamage`, `disableContainerDamage`).

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
on ne peut les obtenir que via les mappings (shop admin, armurerie, commissariat, black market de Vybor).

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
| Tenue admin | Bob orange (`BoonieHat_Orange`), imperméable orange (`Raincoat_Orange`, qui sert à fabriquer le brassard orange : la recette ne peut pas être désactivée sur console). L'imperméable orange est aussi retiré de l'équipement de départ `tempete` | Le bob orange du black market de Vybor, voulu |

Les admins se reconnaissent au bob et au brassard orange (`custom/zeleno_admin.json`).

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
| Vêtements civils de Sakhal (froid) : budionovka grise, bob et gilet de chasse d'hiver, veste et pantalon de chasse de printemps, veste matelassée de police (`BushlatPoliceJacket_Blue`) | 4/2 chacun | Fermes, villes, villages (budionovka), chasse, police et prison | Utiles en ambiance `hiver` |
| Uniforme de marine de Sakhal (veste, pantalon) | 4/2 chacun | Côte | |
| Combinaison NBC blanche (veste, pantalon, cagoule, bottes) | 2/1 chacune | Militaire, comme les NBC grise et jaune | |
| Gourde filtrante (`FilteringBottle`) | 5/2 | Médical, chasse | Purifie l'eau bue. Catégorie `tools` ajoutée (absente du fichier) |
| Piolet (`Iceaxe`) | 6/3 | Villes, villages | |
| Nourriture et boissons de Badlands : ayran (brique et bouteille), lassi (mangue, masala, menthe), sirops afza et jallab, halva | 8/4 chacun | Fermes, villes, villages, chasse (côte pour les lassi et sirops) | |
| Lames de Badlands : akinaka, couteau à kebab (`DonerKnife`), jambiya, cimeterre, baïonnette P1907 | 6/3 (akinaka, couteau à kebab), 4/2 | Villes, villages, chasse ; militaire et villages pour la baïonnette | La baïonnette se fixe sur le Lee-Enfield |
| Armes de Badlands : Lee-Enfield et son chargeur 10 coups, MP18 et son chargeur tambour 32 coups | 5/2 et 8/4, 4/2 et 6/3 | Chasse, fermes, villages (Lee-Enfield) ; fermes, villes, villages (MP18) | Munitions déjà au loot : 7.62x54 (Lee-Enfield), 9x19 (MP18) |
| Vêtements civils de Badlands (chaleur) : kamiz (14 couleurs), shalwars homme (7) et femme (6), pakols (5), turbans (12), keffiehs (8), gilets longs (`RobeVest`, 5), sandales (4), chemises à vagues et hawaïennes (3), chemisette de police, tenue de chasse désert (veste, pantalon, gilet) | 2 à 6 | Villes, villages, côte (chemises hawaïennes, au lieu de militaire), police, chasse | Utiles en ambiance `canicule` |
| Variantes de couleur : Mosin (noir, camo, vert), CZ527 (noir, camo, vert), Winchester 70 (noir, vert), B95 (noir, vert), Derringer (noir, rose) | 2 à 4 | Comme l'arme de base | Elles s'ajoutent aux armes de base |
| Nourriture : chair de crabe, sodas Takola et ZumZam, sarma, crackers, mélange salé, banane, orange, kiwi | 8 à 10 | Villes, villages, côte | |
| Pots en céramique (4 couleurs) | 3/2 chacun | Fermes, villes, villages, chasse | Ustensile de cuisine |

Laissés de côté : la radio (sa pile `BatteryD` n'existe pas dans le jeu) et les cassettes. Aussi la
matraque électrique, l'aiguillon électrique et le défibrillateur : `cfgignorelist.xml` les supprime
au démarrage.

## Météo

Quatre ambiances sont prêtes dans `meteo/` :

| Ambiance | Ciel | Pluie | Vent | Températures (min / max) | Éclairage |
| --- | --- | --- | --- | --- | --- |
| `default` | Météo vanilla (fichier désactivé, `enable="0"`) | Normale | Normal | Vanilla, selon le mois | Vanilla (nuits claires) |
| `hiver` | Gris (couverture 0.4 à 0.9), brume | Aucune | 6 à 12 m/s, pour des changements moins brusques | -10 / -3 °C toute l'année | Sakhal |
| `canicule` | Dégagé (couverture 0 à 0.25), pas de brume | Aucune | Normal | 22 / 38 °C toute l'année | Nasdara |
| `tempete` | Couvert (0.8 à 1.0) | Continue (0.2 minimum), forte, orages | 10 m/s minimum | Vanilla, selon le mois | Nuits noires |

Équipement de départ : les objets sont les mêmes partout (radio et pile, carte, bouteille d'eau pleine,
ouvre-boîte, confiture, spaghettis, 6 chiffons, boîte de clous), ainsi que la sacoche. Seuls les
vêtements changent :

| Ambiance | Haut | Bas | Chaussures | En plus |
| --- | --- | --- | --- | --- |
| `default` | Pull | Pantalon de toile | Baskets | |
| `hiver` | Doudoune | Jean | Chaussures de travail | Bonnet, gants en laine |
| `canicule` | T-shirt | Short en jean | Baskets | Casquette |
| `tempete` | Imperméable | Pantalon de toile | Bottes en caoutchouc | Lampe frontale avec pile 9V |

Chaque dossier `meteo/<ambiance>/` contient :

| Fichier | Rôle | Remplace |
| --- | --- | --- |
| `cfgweather.xml` | Météo | `cfgweather.xml` |
| `gameplay.json` | Éclairage (`lightingConfig` : 0 vanilla, 1 nuits noires, 2 Sakhal, 3 Nasdara) et températures | Ces trois valeurs dans `cfggameplay.json` |
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
sans le DLC), générées par localité dans `custom/neige_<localité>.json` :

```sh
python3 tools/neige/generate.py              # toutes les localités (une dizaine de minutes)
python3 tools/neige/generate.py zelenogorsk  # une seule
python3 tools/neige/generate.py --liste      # localités détectées
```

Le script lit le relief et les objets de la carte dans le jeu installé sur le PC (cache dans
`tools/neige/cache/`, non versionné). Il détecte les localités (zones bâties d'au moins 40 bâtiments,
nommées d'après les lieux de la config du jeu) et les couvre en évitant les bâtiments et les gros objets
de nos mappings. Les rues sont enneigées comme le reste (`CLEAR_STREETS = True` dans le script pour les
dégager). Les plaques sont inclinées selon la pente, puis abaissées pour ne
flotter nulle part (quelques centimètres au plus) ; celles qui s'enfonceraient de plus de 30 cm ailleurs
sont écartées. Sans argument, il réécrit aussi `meteo/hiver/mappings.txt`.

Chaque plaque est un objet synchronisé avec les joueurs proches. Avec 3 572 plaques à Zelenogorsk, les
joueurs avaient l'icône de désynchronisation en permanence ; avec 1 680 réparties sur trois villes, aucun
souci : c'est le nombre de plaques autour du joueur qui compte. Le script ne pose donc que des grandes
plaques, 600 au plus par localité (au-delà, il en retire au hasard). Il écrit une image de contrôle par
localité dans `tools/neige/cache/neige_<localité>.png` (blanc : neige, rouge : bâtiments, brun : rues dégagées).
Les réglages (seuil de bâtiments, plafond, pente maximale…) sont en tête du script.

État actuel : 48 localités, 17 265 plaques, au plus environ 1 450 dans un rayon de 1 km (Berezino, en
trois localités voisines). Les grandes villes sont plafonnées, donc plus clairsemées (Chernogorsk : 3 % de
la surface libre couverte) ; les villages sont couverts de 10 à 35 %. Les routes hors des localités
n'ont pas de neige : elles demanderaient trop de plaques.

### Arbres tombés (ambiance `tempete`)

`custom/tempete_arbres.json`, généré par `python3 tools/tempete/generate.py` (il réutilise les données du
jeu lues par `tools/neige/`), est chargé seulement en tempête (`meteo/tempete/mappings.txt`). Ce sont des
hêtres couchés (`StaticObj_d_FagusSylvatica_fallen`, arbre entier de 19 m, et `_fallenb`, tronçon de 4 m),
posés là où la carte a des arbres :

- en travers des routes (goudron, gravier, terre), au moins 1,2 km entre deux coupures, sauf dans
  l'enceinte de Zelenogorsk ; les véhicules doivent faire un détour ;
- couchés au bord des routes, sans les couper.

Les troncs suivent la pente, et leur hauteur de pose est celle des mêmes arbres placés par Bohemia sur la
carte. Pas d'arbre sur les ponts, dans les bâtiments ni sur nos mappings. Chaque arbre porte
`customString` `travers` ou `bord`. État actuel : 1 040 arbres, dont 82 en travers d'une route.

**Objets par chemin de modèle invisibles.** L'Object Spawner accepte des chemins `.p3d` de plantes et de
rochers (`DZ\plants…`, `DZ\rocks…`), mais il les crée en objets locaux au serveur (`createLocal`), que les
joueurs ne voient pas : la première version des arbres tombés (épicéas, pins, bouleaux, qui n'existent
qu'en modèle) était invisible en jeu. Il faut une classe d'objet (`StaticObj_*`, `Land_*`…). Les chemins
`.p3d` encore présents dans nos mappings (fougères, lierre, rochers dans `zeleno_enceinte.json` et
`PZero_SpawnTest_LordBionik.json`) sont donc probablement invisibles aussi.

### Traces de brûlé (ambiance `canicule`)

`custom/canicule_brulis.json`, généré par `python3 tools/canicule/generate.py`, est chargé seulement en
canicule (`meteo/canicule/mappings.txt`) : groupes de traces de brûlé de Nasdara (une grande, quelques
petites) en terrain dégagé autour des localités, posées comme les plaques de neige. Le lierre sec n'existe
qu'en modèle (invisible, voir plus haut). État actuel : 718 traces.

Les éclairages de Sakhal et de Nasdara (`lightingConfig` 2 et 3) viennent des DLC, mais leurs données sont
installées chez tous les joueurs (comme les plaques de neige de Sakhal, visibles sans le DLC).

Ce que Chernarus permet (vérifié dans les scripts du jeu, `ChernarusPlus.c`) :

- **La météo reste pilotée par le script de Chernarus.** `cfgweather.xml` ne fait que borner les valeurs
  (`limits`). Le script réimpose aussi le seuil de pluie (couverture 0.6), celui des éclairs (0.9) et une
  vitesse de vent maximale de 20 m/s (`SetWindMaximumSpeed`).
- **Le vent change vite, et ce n'est pas réglable.** À chaque changement de nuages (toutes les 10 à 15 min),
  le script tire un vent de 4 à 17 m/s, atteint en 60 à 90 s, puis le baisse d'un quart en 1 à 2 min.
  Les `timelimits` et `changelimits` de `cfgweather.xml` ne servent que si le script laisse le jeu choisir,
  ce qu'il ne fait jamais pour le vent. Pour adoucir, on resserre les `limits` : en `hiver`, 6 à 12 m/s.
  Le minimum est appliqué à coup sûr. Le maximum sous 20 est encore à confirmer en jeu.
- **Pas de chute de neige.** Le script remet la neige à 0 à chaque changement de météo. Il faudrait un
  `init.c`, non disponible sur console. La neige au sol passe par des mappings (voir plus haut).
- **Pas de tempête de sable.** Elle est gérée par le script de Nasdara, qui ne tourne pas sur Chernarus.
- **Le gel fonctionne.** Il ne dépend que de la température : avec l'ambiance `hiver`, l'eau et la
  nourriture gèlent comme sur Sakhal, et les joueurs ont froid.

Les ambiances `hiver`, `canicule` et `tempete` ont `reset="1"` : la météo sauvegardée est ignorée et
l'ambiance s'applique dès le redémarrage.

## Fêtes

Les décors de fête sont des mappings activés à la demande, indépendamment de l'ambiance météo :

| Fête | Mapping | Contenu |
| --- | --- | --- |
| `noel` | `custom/zeleno_christmas.json` | Enclos de Noël au centre de Zelenogorsk : sapins, traîneau, Père Noël, cadeaux, rennes, neige |
| `halloween` | `custom/zeleno_halloween.json` | Même enclos en version Halloween (cimetière, chaudron sur le feu, champ de citrouilles, chèvre spooky) et petits décors dans toute la ville safe : citrouilles et citrouilles sculptées lumineuses |
| `aucune` | — | Aucun mapping de fête |

Les deux fêtes utilisent le même enclos : une seule est active à la fois. Pour changer, en local :

```sh
tools/fete.sh halloween   # ou noel, aucune
```

Chaque dossier `fetes/<fete>/` contient :

| Fichier | Rôle |
| --- | --- |
| `mappings.txt` | Mappings de la fête, ajoutés à `objectSpawnersArr` de `cfggameplay.json` (un chemin `./custom/….json` par ligne) |
| `events.xml`, `types.xml` (facultatifs) | Blocs `<event>` / `<type>` complets qui remplacent ceux de `db/events.xml` / `db/types.xml` pendant la fête |
| `events.origine.xml`, `types.origine.xml` | Les mêmes blocs hors fête, remis quand la fête est désactivée |
| `effectareas.json` (facultatif) | Zones ajoutées à la fin de `Areas` dans `cfgEffectArea.json` |

Le script retire d'abord tout ce qui appartient à une fête (mappings, blocs, zones), puis ajoute ce qui
appartient à la fête choisie. Le reste des fichiers ne bouge pas, y compris les mappings de l'ambiance
météo. Si un bloc géré par une fête a été modifié à la main dans `db/`, le script s'arrête sans rien
écrire : reporter la modification dans `fetes/*/`. Il reste à envoyer sur le FTP `cfggameplay.json`,
`db/events.xml`, `db/types.xml`, `cfgEffectArea.json` (et le mapping de la fête s'il n'y est pas
déjà) puis à redémarrer.

### Événements d'Halloween

Le mode `halloween` active aussi les éléments d'Halloween prévus par le jeu (désactivés sinon). Les
modifications sont marquées `Halloween (tools/fete.sh)` dans `db/` :

| Élément | Détail |
| --- | --- |
| Feux d'Halloween (`StaticBonfire`) | 20 feux de camp allumés en permanence, parmi 62 positions de `cfgeventspawns.xml`. Autour de chacun : 4 à 8 objets de loot d'Halloween ou de pompiers, et 6 à 10 zombies pompiers (`InfectedFirefighter`) dans un rayon de 55 m (3 à 5 statiques + 3 à 5 dynamiques, `<zone>` de `StaticBonfire` dans `cfgeventspawns.xml`) |
| Zombies spooky (`InfectedSpooky`) | Zombies en tenue sombre (fermières en noir, bricoleurs en beige) dans les 6 zones `InfectedSpooky` de `env/zombie_territories.xml` (rayon 120 m) |
| Zones hantées (`SpookyArea`) | Sur ces 6 zones : brume, teinte de l'écran, chuchotements, bruits de pas et feuillages, coups de vent. Aucun dégât. La version 2023 du jeu (`SpookyArea23`, qui refroidit le joueur) n'a plus de classe de config et ne peut pas être utilisée |
| Loot d'Halloween | Chapeau de sorcière (10/5), capuches de sorcière noire, marron et rouge (6/3 chacune), chaudron, balai en bouleau, nez crochu (8/4 chacun) : autour des feux uniquement (`deloot`). Masque « mort » (6/3) : magasins et immeubles (`SeasonalEvent`). Citrouille sculptée (10/5) : fermes |

Zone safe : aucun de ces éléments ne touche Zelenogorsk. La position de feu de la ville est commentée
(`SafeZone Zelenogorsk`), le feu le plus proche est à 593 m de la zone safe et la zone spooky la plus
proche à 3,5 km. Le loot des feux (catégories `SeasonalEvent` et `Firefighter`) ne contient aucun objet
du loot restreint, dont le `nominal` est à 0, et les zombies de ces événements ont le même équipement
que les autres. Proches de mappings : un feu, une zone spooky et ses zombies au château du diable
(`devils_castle_secte.json`), un feu à 160 m du black market de Vybor et un à 288 m du shop admin.

## Outils

| Script | Rôle |
| --- | --- |
| `tools/meteo.sh <ambiance>` | Active une ambiance météo (voir Météo) |
| `tools/fete.sh <fete>` | Active une fête (mappings, événements, loot, zones) : `noel`, `halloween` ou `aucune` (voir Fêtes) |
| `tools/neige/generate.py` | Neige au sol de l'ambiance `hiver` → `custom/neige_*.json` |
| `tools/tempete/generate.py` | Arbres tombés de l'ambiance `tempete` → `custom/tempete_arbres.json` |
| `tools/canicule/generate.py` | Traces de brûlé de l'ambiance `canicule` → `custom/canicule_brulis.json` |
| `tools/neige/gamedata.py` | Bibliothèque commune : lecture des pbo, `config.bin`, modèles et terrain du jeu |

Prérequis : `bash` et Python 3 (bibliothèque standard uniquement, rien à installer). Les générateurs ont
besoin de DayZ installé sur le PC via Steam : par défaut
`~/snap/steam/common/.local/share/Steam/steamapps/common/DayZ`, sinon indiquer le dossier dans la variable
`DAYZ_DIR`. Les données extraites du jeu sont mises en cache dans `tools/neige/cache/` (non versionné,
à ne pas publier) ; supprimer ce dossier après une mise à jour du jeu.

## Déploiement (FTP)

1. Arrêter le serveur depuis l'interface Nitrado (sinon il peut réécrire des fichiers à l'arrêt).
2. Envoyer les fichiers modifiés avec FileZilla en mode binaire, en respectant l'arborescence
   et la casse des noms.
3. Vérifier que l'utilisation de `cfggameplay.json` est activée dans les réglages Nitrado.
4. Démarrer le serveur, puis contrôler `restart.log` et le dernier `.RPT` de `dayzxb/config/`
   (erreurs de parsing XML/JSON, `No custom folder found`…).

Les JSON et XML doivent être en UTF-8 sans BOM.
