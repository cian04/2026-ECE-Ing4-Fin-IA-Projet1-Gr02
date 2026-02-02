#!/usr/bin/env python3
"""
Script principal pour l'optimisation de portefeuille goal-based.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from data_fetcher import get_historical_data, calculate_returns, calculate_stats
from portfolio_optimizer import goal_based_optimization
from monte_carlo import simulate_goal_success, save_monte_carlo_paths_plot
import numpy as np

def main():
    # Exemple de tickers (indices ou ETFs)
    tickers = ['SPY', 'EXSA.DE', 'SLV']  # S&P 500 ETF, STOXX Europe 600, Physical Silver ETF

    # Récupérer les données
    print("Récupération des données historiques...")
    data = get_historical_data(tickers)
    returns = calculate_returns(data)
    stats = calculate_stats(returns)

    if returns.empty:
        print("Erreur: aucune donnée historique disponible. Vérifiez les symboles.")
        sys.exit(1)

    expected_returns = np.array(list(stats['expected_return'].values()))
    volatilities = np.array(list(stats['volatility'].values()))

    # Matrice de covariance
    cov_matrix = returns.cov().values * 252  # Annualisée

    if not np.isfinite(expected_returns).all():
        print("Erreur: rendements attendus invalides (NaN/inf).")
        sys.exit(1)

    # Définir les objectifs
    goals = [
        {
            'target_amount': 50000,
            'horizon_years': 5,
            'risk_tolerance': 0.2
        },
        {
            'target_amount': 100000,
            'horizon_years': 10,
            'risk_tolerance': 0.1
        },
        {
            'target_amount': 200000,
            'horizon_years': 20,
            'risk_tolerance': 0.05
        }
    ]

    total_budget = 2000

    # Optimisation
    print("Optimisation des allocations...")
    try:
        allocations = goal_based_optimization(goals, expected_returns, cov_matrix, total_budget)
    except ValueError as exc:
        print(f"Erreur d'optimisation: {exc}")
        sys.exit(1)

    # Simulations Monte Carlo
    print("Simulations Monte Carlo...")
    goal_budgets = {goal_name: alloc['budget'] for goal_name, alloc in allocations.items()}
    goal_weights = {goal_name: alloc['allocation']['weights'] for goal_name, alloc in allocations.items()}
    success_probs = simulate_goal_success(
        goals,
        expected_returns,
        cov_matrix,
        total_budget,
        goal_budgets=goal_budgets,
        goal_weights=goal_weights
    )

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    num_simulations_plot = 1000
    for goal_name, alloc in allocations.items():
        goal_idx = int(goal_name.split('_')[1]) - 1
        goal = goals[goal_idx]
        filename = f"monte_carlo_paths_{goal_name}.png"
        plot_path = save_monte_carlo_paths_plot(
            expected_returns,
            cov_matrix,
            alloc['budget'],
            goal['horizon_years'],
            data_dir,
            filename,
            num_simulations=num_simulations_plot,
            weights=alloc['allocation']['weights']
        )
        if plot_path:
            print(f"Graphique Monte Carlo sauvegarde: {plot_path}")

    # Afficher les résultats
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
