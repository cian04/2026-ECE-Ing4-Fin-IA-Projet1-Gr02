# Documentation technique — Coloration de graphe / carte (CSP)

## 1) Problème
L’objectif est d’attribuer une couleur à chaque nœud d’un graphe (ex : régions d’une carte) de manière à respecter la contrainte suivante : deux nœuds reliés par une arête (donc adjacents) ne doivent jamais avoir la même couleur.

On étudie deux variantes :
- **K-coloration (faisabilité)** : “est-ce qu’il existe une coloration avec K couleurs ?”, cela nous sera utile pour montrer que la coloration n'est pas possible si K est trop petit.
- **Minimisation** : “quel est le plus petit K pour lequel une coloration existe ?”

Ce problème est connu pour être NP-difficile en général, ce qui motive l’utilisation d’outils de programmation par contraintes.


## 2) Modélisation en CSP
J’ai modélisé la coloration comme un **problème de satisfaction de contraintes (CSP)**.

### Variables
Pour chaque nœud `v` du graphe, je crée une variable de décision :
- `c[v]` = couleur du nœud `v`

### Contraintes
Pour chaque arête `(u, v)` du graphe :
- `c[u] != c[v]`

Une variable par nœud, et une contrainte de différence par arête.

Comme les couleurs sont interchangeables (permuter les couleurs donne une solution équivalente), j’ajoute parfois une contrainte simple pour réduire les symétries :
- fixer la couleur d’un nœud (ex : le premier) à 0

En pratique, ça peut aider le solveur à éviter d’explorer des solutions doublons.


## 3) Bibliothèque OR-Tools
J’ai utilisé **Google OR-Tools**, qui est une bibliothèque de résolution combinatoire (CSP/CP, optimisation, etc.).  
Dans OR-Tools, j’utilise le solveur **CP-SAT**.

### CP-SAT
CP-SAT est un solveur qui combine :
- une modélisation type **CP** (variables, domaines, contraintes),
- et une résolution basée sur du **SAT** (satisfaction de formules booléennes) + des techniques de propagation et de recherche.


### Pertinence du choix de ces outils
- Le graphe a beaucoup de contraintes locales (arêtes), et CP-SAT gère bien ce type de structure.
- Je peux rapidement tester la faisabilité pour différents K (utile pour la minimisation).
- OR-Tools donne un cadre très propre : `CpModel` + `CpSolver`.


## 4) Algorithme : K-coloration
Pour tester une K-coloration, je fais :
1. Construire le graphe `G` (depuis un dataset ou un générateur).
2. Créer un modèle CP-SAT :
   - variables `c[v]` pour chaque nœud,
   - contraintes `c[u] != c[v]` pour chaque arête.
3. Lancer le solveur CP-SAT avec une limite de temps.
4. Lire le résultat :
   - si le solveur trouve une affectation → **faisable**
   - sinon (infeasible ou timeout) → **pas de solution dans ce cadre** (aucun graphe coloré ne sera affiché)

Dans le code, je fais aussi attention aux labels de nœuds : je peux relabel le graphe en interne pour faciliter la résolution, puis je remappe la solution vers les labels d’origine.


## 5) Minimisation de K
Pour trouver le plus petit nombre de couleurs, je teste `K = 1, 2, 3, ...` jusqu’à trouver le premier K faisable.

Cette méthode n’est pas la plus “théorique”, mais elle est suffisante pour des graphes de taille moyenne (comme les datasets que j'ai utilisés).


## 6) Validation de la solution
Après résolution, je vérifie systématiquement que la coloration est correcte :
- pour chaque arête `(u, v)` :
  - vérifier `color[u] != color[v]`

Cette étape sert à s’assurer que la solution affichée est bien cohérente avec le graphe chargé.

---

## 7) Visualisation (NetworkX + Matplotlib)
Pour prouver visuellement que ça fonctionne, je trace :
- les nœuds avec une couleur correspondant à `c[v]`
- les arêtes
- les labels (numéros) des nœuds

Dans le cas où le graphe contient plusieurs composantes (ex : nœuds isolés), je garde un rendu lisible en plaçant la composante principale et en mettant les composantes isolées dans un “encart”.

On remarque sur les dataset de liste d'adjascences des états des Etats-Unis ainsi que les département de France que leur graphe correspondant prend vaguement la forme du pays du aux contraintes d'adjascence. Cela prouve que les datasets et la modélisation du graphe sont corrects

## 8) Reproductibilité (commandes)
Depuis `groupe2-lamy-coloration-graphe/` :

Sous Windows PowerShell :
- activer l’import depuis `src/`
  powershell
  $env:PYTHONPATH="src"

- Minimiser K sur un dataset :
  powershell
  python -m graph_coloring.cli --instance file --path data/us_states_adjacency.txt --minimize --plot

- Tester un K spécifique :
  powershell
  python -m graph_coloring.cli --instance file --path data/us_states_adjacency.txt --k 3 --plot
