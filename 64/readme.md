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
├── src/
│   ├── app_streamlit.py
│   ├── optimizer.py
│   ├── constraints.py
│   ├── simulator.py
│   └── data/
├── docs/
│   ├── user_guide.md
│   ├── model_assumptions.md
│   ├── optimization_model.md
│   └── experiments.md
└── slides/
```

## Installation
Prérequis : Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation
Lancer l'application Streamlit :

```bash
streamlit run src/app_streamlit.py
```

## Résultats attendus
- Allocation de portefeuille adaptée aux objectifs.
- Probabilité d'atteinte de l'objectif financier.
- Distribution des résultats issue des simulations Monte Carlo.
- Comparaison de profils utilisateurs et de scénarios.
