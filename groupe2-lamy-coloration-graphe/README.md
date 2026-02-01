# Coloration de graphe et de carte (CSP)

## Contexte
Projet IA (Groupe 2) : modéliser et résoudre le problème de **coloration de graphe / carte** comme un **CSP**
(variable = couleur d’un nœud, domaine = {0..K-1}, contraintes binaires : deux nœuds adjacents ne peuvent pas avoir la même couleur).

## Fonctionnalités
- **K-coloration (faisabilité)** : décider si un graphe est coloriable avec **K** couleurs.
- **Minimisation** : trouver le plus petit **K** par itération (1..Kmax).
- **Validation** : vérifie que la coloration respecte toutes les arêtes.
- **Visualisation** : affichage du graphe colorié avec NetworkX et MatPlotLib, y compris le cas de plusieurs composantes.

## Organisation du dépôt
Le travail est dans :
`groupe2-lamy-coloration-graphe/`

Structure :
groupe2-lamy-coloration-graphe/
  ─ data/              # datasets (liste d’adjacence)
  ─ src/graph_coloring # code python
  ─ tests/             # tests pytest
  ─ docs/              # documentation technique, sources
  ─ slides/            # slides de présentation

## Prérequis
- Python
- Windows / macOS / Linux
- Dépendances principales : OR-Tools, NetworkX, Matplotlib

## Installation
### Windows (PowerShell)
Depuis le dossier `groupe2-lamy-coloration-graphe/` :
powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

### macOS / Linux
bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

## Utilisation (CLI)
Important : pour lancer depuis Windows PowerShell, définir le PYTHONPATH afin d’importer le package depuis `src/` :
powershell
$env:PYTHONPATH="src"

### Charger un dataset depuis fichier (liste d’adjacence)
- Pour avoir le plus faible nombre de couleur :
powershell
python -m graph_coloring.cli --instance file --path data/us_states_adjacency.txt --minimize --plot
(3 datasets disponibles : us_states_adjacency.txt ; dep_france.txt ; regions_france.txt)

- Tester un K spécifique :
powershell
python -m graph_coloring.cli --instance file --path data/us_states_adjacency.txt --k 3
python -m graph_coloring.cli --instance file --path data/us_states_adjacency.txt --k 4 --plot

### Générateurs d’instances (debug / benchmarks)
- Cycle :
powershell
python -m graph_coloring.cli --instance cycle --n 20 --minimize

- Grille :
powershell
python -m graph_coloring.cli --instance grid --m 8 --n 8 --minimize

- Erdos-Rényi :
powershell
python -m graph_coloring.cli --instance er --n 50 --p 0.2 --seed 0 --minimize

## Format des datasets (liste d’adjacence)
Une ligne par nœud :
node voisin1 voisin2 ... voisinN

Exemple :
1 2 3
2 1
3 1

Note : une ligne avec seulement `node` signifie que le nœud est isolé.

## Sortie attendue
Le programme affiche notamment :
- Instance, nombre de nœuds / arêtes
- K trouvé (ou K testé)
- Faisabilité (K-feasible)
- Temps
- Validation de la coloration
- Extrait de l’affectation node -> color
- Affichage graphique si `--plot` est utilisé.

## Tests
Depuis `groupe2-lamy-coloration-graphe/` :
powershell
pytest -q

## Résultats (exemple)
- US states (50 nœuds, 107 arêtes) : minimum trouvé **K = 4** (CP-SAT OR-Tools), coloration valide.

## Équipe
Groupe 2 — Robin LAMY
