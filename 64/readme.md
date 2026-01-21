# Robo-advisor : optimisation de portefeuille goal-based

(ECE – Ing4 Finance).

## Membres du groupe
- Jules
- Raphaël
- Hugo
- Cian

## Objectif du projet
Ce projet vise à concevoir un robo-advisor orienté objectifs (goal-based investing). L'objectif est d'allouer un portefeuille sous contraintes (budget, risque, liquidité, diversification) et de maximiser la probabilité d'atteindre un objectif financier donné. L'approche combine l'IA symbolique (modélisation par contraintes) et l'IA exploratoire (simulations Monte Carlo).

## Approche générale
- Définition de l'univers d'actifs et des hypothèses financières.
- Modélisation des contraintes (budget, diversification, liquidité, risque).
- Génération de portefeuilles candidats via optimisation.
- Évaluation des portefeuilles par simulations Monte Carlo.
- Sélection du portefeuille optimal en fonction du taux de réussite.
- Interface utilisateur interactive pour paramétrer les objectifs et visualiser les résultats.

## Répartition des rôles
La répartition est transversale : chaque membre intervient sur plusieurs étapes du pipeline, avec un rôle principal identifié.

- Jules (lead interface) : interface Streamlit, visualisation, documentation utilisateur, et contribution aux tests de bout en bout. Fichiers principaux : `src/app_streamlit.py`, `docs/user_guide.md`, `docs/experiments.md`.
- Raphaël (lead modélisation) : modélisation financière (rendements, volatilités, corrélations), hypothèses macro (inflation, taux, horizon), scénarios utilisateurs, et appui à la calibration des simulations. Fichiers principaux : `docs/model_assumptions.md`, `docs/experiments.md`.
- Hugo (lead optimisation) : optimisation sous contraintes avec OR-Tools, formulation du modèle, et intégration des contraintes dans le pipeline de simulation. Fichiers principaux : `src/optimizer.py`, `src/constraints.py`, `docs/optimization_model.md`.
- Cian (lead simulation) : simulation Monte Carlo et évaluation goal-based, intégration avec l'optimiseur, et synthèse des résultats. Fichiers principaux : `src/simulator.py`, `docs/experiments.md`, `docs/optimization_model.md`.

## Structure du projet
```
64/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py      # Récupération et traitement des données
│   ├── portfolio_optimizer.py # Algorithmes d'optimisation
│   ├── monte_carlo.py       # Simulations probabilistes
│   ├── main.py             # Script principal
│   └── app.py              # Interface Streamlit
├── notebooks/
│   └── demo.ipynb          # Notebook de démonstration
├── data/                   # Données (si nécessaire)
└── docs/
    └── technical_doc.md    # Documentation technique
```

## Installation
Prérequis : Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

### Script en ligne de commande
```bash
python src/main.py
```

### Interface Web
```bash
streamlit run src/app.py
```

### Notebook
Ouvrez `notebooks/demo.ipynb` dans Jupyter pour une démonstration interactive.

## Fonctionnalités Implémentées

### ✅ Récupération de Données
- Intégration avec Yahoo Finance via `yfinance`
- Calcul automatique des rendements et statistiques

### ✅ Optimisation de Portefeuille
- Maximisation du ratio de Sharpe avec `cvxpy`
- Support des contraintes personnalisées
- Allocation goal-based pour objectifs multiples

### ✅ Simulations Monte Carlo
- Génération de trajectoires probabilistes
- Calcul des probabilités de succès
- Évaluation de la robustesse des allocations

### ✅ Visualisation
- Interface Streamlit interactive
- Graphiques Plotly pour les allocations et probabilités
- Analyse des données historiques

## Résultats d'Exemple

Sur un budget de 100k€ avec 3 objectifs :
- Objectif 1: 50k€ en 5 ans → 53.7% de succès
- Objectif 2: 100k€ en 10 ans → 56.4% de succès
- Objectif 3: 200k€ en 15 ans → 58.5% de succès

## Améliorations Futures
- Intégration de plus d'actifs et classes d'actifs
- Modélisation des coûts de transaction
- Optimisation multi-objectif avec contraintes métier avancées
- Machine Learning pour prédiction des rendements
- une interface simple pour comparer plusieurs objectifs

## Tests
Les tests unitaires seront ajoutes avec `pytest`.

```bash
streamlit run src/app_streamlit.py
```

## Résultats attendus
- Allocation de portefeuille adaptée aux objectifs.
- Probabilité d'atteinte de l'objectif financier.
- Distribution des résultats issue des simulations Monte Carlo.
- Comparaison de profils utilisateurs et de scénarios.
