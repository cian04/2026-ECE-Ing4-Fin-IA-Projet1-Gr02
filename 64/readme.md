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
hcjr/
├── README.md
├── src/
├── notebooks/
├── data/
└── docs/
```

## Installation
Prerequis : Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation
Exemples a venir. L'objectif e st de fournir :
- un script pour lancer une optimisation sur un scenario
- un notebook de demonstration
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
