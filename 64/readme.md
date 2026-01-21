# Robo-advisor goal-based

Projet du groupe (Jules, Hugo, Raphael, Cian) pour le sujet 64 : "Robo-advisor : optimisation de portefeuille goal-based".

## Contexte
Les robo-advisors doivent piloter plusieurs objectifs financiers en parallele (retraite, immobilier, etudes) avec des horizons et des profils de risque differents. Le but est de proposer une allocation d'actifs qui respecte des contraintes metier tout en maximisant la probabilite d'atteindre chaque objectif.

## Objectifs du projet
- Modeliser les objectifs comme contraintes (montant cible, horizon, probabilite de succes)
- Optimiser l'allocation d'actifs sous contraintes de risque et de budget
- Estimer les probabilites de succes via simulations Monte Carlo
- Visualiser des scenarios et recommandations compréhensibles par un utilisateur

## Approche proposee
1. Formulation des objectifs et contraintes (CSP / optimisation convexe)
2. Estimation des rendements et volatilites a partir de donnees historiques
3. Simulations Monte Carlo pour evaluer la robustesse des allocations
4. Interface simple pour explorer les scenarios

## Technologies ciblees
- Python
- `cvxpy` pour l'optimisation convexe
- `OR-Tools` pour les contraintes metier
- `yfinance` pour les donnees de marche
- `pandas`, `numpy` pour la manipulation de donnees
- `plotly` ou `streamlit` pour la visualisation

## Organisation du depot
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
Prerequis : Python 3.10+

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
pytest
```

## Resultats attendus
- Allocation d'actifs par objectif
- Probabilite de succes par objectif
- Visualisations (frontiere risque/rendement, distribution des outcomes)

## Roadmap
- [ ] Definition des objectifs et des contraintes
- [ ] Collecte et nettoyage des donnees
- [ ] Prototype d'optimisation
- [ ] Simulations Monte Carlo
- [ ] Interface et visualisations

## References
- Robo-Advisors Beyond Automation: Principles and Roadmap for AI-Driven Financial Planning (2025)
- InvestSuite : Goal-Based Personalized Investing
- Build a Robo-Advisor with Python (From Scratch)
