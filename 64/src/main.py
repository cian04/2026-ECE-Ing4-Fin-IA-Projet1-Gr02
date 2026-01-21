#!/usr/bin/env python3
"""
Script principal pour l'optimisation de portefeuille goal-based.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from data_fetcher import get_historical_data, calculate_returns, calculate_stats
from portfolio_optimizer import goal_based_optimization
from monte_carlo import simulate_goal_success
import numpy as np

# Script principal
# Ce fichier montre un exemple d'exécution bout-en-bout :
# 1. récupération des données (via yfinance)
# 2. calcul des rendements et statistiques
# 3. optimisation goal-based pour plusieurs objectifs
# 4. simulations Monte Carlo pour estimer la probabilité d'atteindre chaque objectif

def main():
    # Exemple de tickers (indices ou ETFs)
    tickers = ['SPY', 'BND', 'GLD', 'QQQ']  # SP500, Bonds, Gold, Nasdaq

    # Récupérer les données
    print("Récupération des données historiques...")
    data = get_historical_data(tickers)
    returns = calculate_returns(data)
    stats = calculate_stats(returns)

    # Construire les vecteurs attendus par l'optimiseur
    expected_returns = np.array(list(stats['expected_return'].values()))
    volatilities = np.array(list(stats['volatility'].values()))

    # Matrice de covariance annualisée (à partir des rendements quotidiens)
    cov_matrix = returns.cov().values * 252

    # Définir les objectifs (exemple)
    goals = [
        {'target_amount': 50000, 'horizon_years': 5, 'risk_tolerance': 0.2},
        {'target_amount': 100000, 'horizon_years': 10, 'risk_tolerance': 0.1},
        {'target_amount': 200000, 'horizon_years': 20, 'risk_tolerance': 0.05}
    ]

    total_budget = 100000

    # Optimisation
    print("Optimisation des allocations...")
    allocations = goal_based_optimization(goals, expected_returns, cov_matrix, total_budget)

    # Simulations Monte Carlo pour estimer la probabilité d'atteindre chaque objectif
    print("Simulations Monte Carlo...")
    success_probs = simulate_goal_success(goals, expected_returns, cov_matrix, total_budget)

    # Afficher les résultats de manière lisible
    print("\n=== RÉSULTATS ===")
    for goal_name, alloc in allocations.items():
        print(f"\n{goal_name.upper()}:")
        print(f"  Budget alloué: {alloc['budget']:.2f}€")
        print(f"  Objectif: {alloc['target']:.2f}€")
        prob = success_probs[goal_name]
        print(f"  Probabilité de succès: {prob:.2%}")
        print(f"  Rendement attendu: {alloc['allocation']['expected_return']:.2%}")
        print(f"  Volatilité: {alloc['allocation']['volatility']:.2%}")
        print("  Allocation:")
        for i, ticker in enumerate(tickers):
            weight = alloc['allocation']['weights'][i]
            print(f"    {ticker}: {weight:.2%}")

if __name__ == "__main__":
    main()