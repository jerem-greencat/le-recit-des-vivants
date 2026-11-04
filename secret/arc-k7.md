# Arc K-7 — document de l'équipe (secret)

Ce dossier `secret/` est exclu de git (`.gitignore`) : le dépôt GitHub est public. Ne rien y mettre
qui doive être partagé par git, et ne jamais en recopier le contenu dans `LORE.md` ou le `README.md`
avant que les joueurs l'aient découvert en jeu.

## Principe

Le manifeste ne mène pas au labo : chaque étape mène à la suivante. Une étape n'existe sur la carte
qu'une fois mappée : on ne déploie la suivante que quand la précédente est résolue (délai minimum au
choix de l'équipe). Chaque indice écrit ou sonore passe par le Discord, donné seulement à celui qui le
trouve : l'information est fragmentée entre les joueurs.

**Aucun joueur ni aucune faction n'est dans le secret**, y compris le black market de Vybor (faction de
joueurs qui découvre le lore comme les autres). Les indices sont placés par l'équipe seule, et jamais
dans la base d'une faction (elle les trouverait avant tout le monde).

## Les actes

| Acte | Contenu | État |
| --- | --- | --- |
| 1. Le crash | Le manifeste révèle K-7, les doses VZ-2 et le vol de la cargaison. Il ne donne pas l'emplacement de K-7. Piste : les pilleurs et le dossier | **En place** (à vérifier en jeu) |
| 2. Les pilleurs | Le camp dans la queue de l'avion est celui des pilleurs, partis depuis. Restes de la cargaison semés ailleurs, mappés au moment voulu (conteneur VZ-2 vide au bord d'une route, caisse au tabor de Novaya, à la casse…) | À détailler |
| 3. Le dossier | Le dossier scellé a été découpé par les pilleurs, qui voulaient le vendre à un acheteur inconnu. Les pages sont cachées par l'équipe sur leur route (anciennes caches, lieu de rendez-vous de la vente qui a mal tourné…), jamais confiées à des joueurs. Chaque page n'est donnée qu'à celui qui la trouve ; ensuite les joueurs les échangent, vendent ou volent comme ils veulent | À détailler |
| 4. La fausse piste | Le dossier réuni désigne la « station relais K-7 » à l'Altar (x 8170, z 9050 : antennes, tour TV, 3 puits d'aération). Poste technique abandonné, pas le labo. Dernier journal radio (audio Discord) : évacuation du personnel, énigme vers le vrai emplacement | À détailler |
| 5. K-7 | Entrée trouvée, porte fermée. Ouverture : mallette scientifique et ses clés, code tiré du dossier, ou événement de l'équipe. L'intérieur et les révélations restent pour plus tard (qui faisait voler les avions, efficacité des doses, lien avec la voix du Dernier Appel ?) | Emplacement à choisir, loin des lieux évidents |

Lieux écartés pour le labo (trop faciles), utilisables comme étapes ou fausses pistes : l'Altar, les mines
et puits d'aération au nord de l'aérodrome NW (x 4650, z 10950), les mines à l'ouest de Zelenogorsk
(x 1270, z 6290).

## Acte 1 — le crash du vol 404 Sierra

Décidé : le modèle de l'avion ne change pas, pas de boîte noire. Le joueur envoie une capture de sa
trouvaille sur le Discord ; le texte du manifeste n'est envoyé qu'à lui. Le jeu ne permet pas de nommer
la feuille « Manifeste » (nom fixé par la config du jeu) : c'est la mise en scène et le message radio du
survivant qui la désignent.

Épave près de Vyshnoye (x 6735, z 6650). **Secret** : l'équipe veut que les joueurs mettent du temps à
trouver l'avion ; aucun texte public ne doit donner le lieu.

Scène (`custom/vyshnoye_plane_base.json`, 21 objets avec le `customString` `manifeste`) : cargaison
éventrée et vide à l'est de l'aile ; traînée de 3 bandages ; squelette du pilote au pied d'un épicéa
(x 6757.9, z 6623.2), le manifeste (`Paper`) sur la poitrine, un stylo près de la main.

Noms gardés : Site A-1 (origine), Site K-7 (destination), Andreï (copilote), VZ-2 (le second vaccin).

À trancher : le moment du crash (camp aménagé dans la queue, donc ancien ? ou monté vite par les
pilleurs ?), le texte du message radio du survivant (à publier avant la découverte).

### Message radio du survivant (audio Discord, à publier avant la découverte)

Durée visée : environ 1 min. Survivant anonyme, de passage, voix basse et fatiguée, il chuchote par
moments. Il ne doit pas guider jusqu'au corps : seulement dire qu'il existe, plus bas, et qu'il tient
des papiers.

---

[Friture radio, la fréquence s'accroche mal. Vent dans le micro.]

Survivant (voix basse, essoufflée, comme après une longue marche) :

« … si quelqu'un écoute encore cette fréquence… c'est à propos de l'avion. Celui du Mayday. »

[Pause. Bruit de pas dans les feuilles, il s'arrête.]

« Je l'ai trouvé. Loin dans les collines, en pleine forêt… On le voit pas depuis la route, je suis tombé
dessus par hasard. La carlingue est cassée en deux, il y a une aile plantée dans la terre… On voit
encore les trous de l'impact. »

« Mais j'étais pas le premier. Les caisses sont ouvertes. Toutes. Vidées. Même les glacières. Quelqu'un
a fait du feu dans la queue de l'avion, y a des lits, des affaires… Comme si des gens avaient vécu
là-dedans. »

[Il baisse la voix, presque un chuchotement.]

« Et le pilote… Il est pas dans l'avion. Il s'est traîné dehors. Plus bas, sous les sapins. Y a des
bandages par terre tout le long… Il a essayé de tenir. »

[Silence. Il déglutit.]

« Il serre encore des papiers contre lui. Des papiers de bord, je crois. J'ai pas osé y toucher. J'ai…
j'ai pas pu. »

[Un bruit au loin, un râle de Z. Il retient son souffle.]

« … Faut que j'y aille. Si vous passez par là, faites attention. Ceux qui ont vidé l'avion… ils savaient
ce qu'ils cherchaient. Ou pas. Je sais pas ce qui est le pire. »

« Paix à lui. »

[Coupure. Friture 2 secondes.]

---

Ce que le message donne : aucun lieu (« loin dans les collines, en pleine forêt, pas visible depuis la
route » : les joueurs doivent chercher l'épave, voulu par l'équipe), la cargaison pillée, le camp dans la
queue (acte 2), et surtout le pilote, plus bas, avec ses papiers. Il ne dit pas « manifeste » : c'est au
joueur de le découvrir. « Ils savaient ce qu'ils cherchaient. Ou pas » laisse ouverte la question des
pilleurs (dans le manifeste, le pilote pense qu'ils ne savent pas).

### Texte du manifeste (à envoyer au joueur qui le trouve)

---

**MANIFESTE DE FRET — VOL 404 S (SIERRA)**
Transport sous contrat — **PRIORITÉ ABSOLUE** — Ne pas ouvrir sans autorisation

| | |
| --- | --- |
| Appareil | Cargo bimoteur, immatriculation : *rayée* |
| Origine | Site **A-1** |
| Destination | Site **K-7** — Chernarus, secteur *[taché de sang]* |
| Destinataire | Dr. *[illisible]* — remise en main propre |

| Lot | Désignation | Qté | Mentions |
| --- | --- | --- | --- |
| 01 | Conteneurs isothermes « VZ-2 » | 6 | Chaîne du froid −70 °C — **ne jamais rompre** |
| 02 | Échantillons biologiques | 4 | Classe 6.2 — risque infectieux |
| 03 | Mallettes de décontamination | 4 | |
| 04 | Matériel de laboratoire | 12 | Fragile |
| 05 | Dossier scellé | 1 | **Confidentiel** — à détruire en cas de perte de l'appareil |

*Notes au stylo, d'une écriture de plus en plus tremblante :*

> Personne au point de livraison depuis 3 jours. Plus de réponse de K-7.
>
> Moteur gauche. On ne rentrera pas.
>
> Andreï est mort à l'impact. Moi la jambe. Je ne sens plus le froid.
>
> Des hommes sont venus cette nuit. Ils ont tout pris. Les caisses, le dossier. Ils ne savent pas ce que
> c'est. Ils ont fait du feu dans la carlingue. Ils parlaient de vendre.
>
> Si quelqu'un lit ça : VZ-2 ne doit pas se perdre. Ce n'est pas ce que vous croyez. Ce n'est pas le
> premier.
>
> K-7 ne répond plus. Le dossier. Tout est dans le dossier.
>
> Dites-leur que j'ai essayé.

---

Ce que les notes donnent aux joueurs : K-7 existe mais n'est pas localisé ; la cargaison (dont des doses
du second vaccin) et le dossier ont été volés ; les pilleurs ont campé dans la carlingue (acte 2) et
voulaient revendre (acte 3 : à un acheteur inconnu, pas au black market).
