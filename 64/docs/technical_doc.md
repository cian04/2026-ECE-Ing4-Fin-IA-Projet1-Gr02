# Documentation Technique - Robo-Advisor Goal-Based

## Architecture

Le projet est organisé en modules Python dans le dossier `src/` :

- `data_fetcher.py` : Récupération et traitement des données financières
- `portfolio_optimizer.py` : Algorithmes d'optimisation de portefeuille
- `monte_carlo.py` : Simulations probabilistes
- `main.py` : Script principal d'exécution

## Algorithmes

### Optimisation de Portefeuille
Utilise l'optimisation convexe (cvxpy) pour maximiser le ratio de Sharpe sous contraintes :
- Somme des poids = 1
- Poids ≥ 0 (pas de vente à découvert)
- Contraintes personnalisables (min/max par actif)

### Simulations Monte Carlo
- Génération de rendements quotidiens corrélés via décomposition de Cholesky
- Projection des trajectoires sur l'horizon d'investissement
- Calcul des probabilités de succès pour atteindre les objectifs

## Données
- Sources : Yahoo Finance (yfinance)
- Actifs : SPY (S&P 500), BND (obligations), GLD (or), QQQ (Nasdaq)
- Période : 5 ans par défaut

## Métriques
- Rendement annuel attendu
- Volatilité annualisée
- Ratio de Sharpe
- Probabilité de succès des objectifs

## Améliorations Possibles
- Intégration de plus d'actifs
- Modélisation des coûts de transaction
- Optimisation multi-objectif avec contraintes métier
- Interface utilisateur avec Streamlit