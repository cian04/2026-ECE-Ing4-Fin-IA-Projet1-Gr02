import numpy as np
import pandas as pd

def monte_carlo_simulation(expected_returns, cov_matrix, initial_investment, horizon_years, num_simulations=10000):
    """
    Simule les trajectoires de portefeuille via Monte Carlo.

    Parameters:
    - expected_returns: np.array, rendements attendus annuels
    - cov_matrix: np.array, matrice de covariance
    - initial_investment: float, investissement initial
    - horizon_years: int, horizon en années
    - num_simulations: int, nombre de simulations

    Returns:
    - np.array: matrice des valeurs finales (num_simulations,)
    """
    n_assets = len(expected_returns)
    num_days = horizon_years * 252  # Approximation

    # Cholesky decomposition pour générer des rendements corrélés
    L = np.linalg.cholesky(cov_matrix)

    final_values = []

    for _ in range(num_simulations):
        # Générer des rendements quotidiens aléatoires
        random_shocks = np.random.normal(0, 1, (num_days, n_assets))
        daily_returns = np.exp(np.dot(random_shocks, L.T) + (expected_returns / 252 - 0.5 * np.diag(cov_matrix) / 252))

        # Calculer la valeur du portefeuille
        portfolio_value = initial_investment
        for ret in daily_returns:
            portfolio_value *= np.prod(ret)  # Supposant allocation égale pour simplification

        final_values.append(portfolio_value)

    return np.array(final_values)

def calculate_success_probability(final_values, target_amount):
    """
    Calcule la probabilité de succès (atteindre le montant cible).

    Parameters:
    - final_values: np.array, valeurs finales simulées
    - target_amount: float, montant cible

    Returns:
    - float: probabilité de succès
    """
    successes = np.sum(final_values >= target_amount)
    return successes / len(final_values)

def simulate_goal_success(goals, expected_returns, cov_matrix, total_budget):
    """
    Simule la probabilité de succès pour chaque objectif.

    Parameters:
    - goals: list of dict
    - expected_returns: np.array
    - cov_matrix: np.array
    - total_budget: float

    Returns:
    - dict: probabilités de succès par objectif
    """
    num_goals = len(goals)
    budget_per_goal = total_budget / num_goals

    success_probs = {}
    for i, goal in enumerate(goals):
        final_values = monte_carlo_simulation(
            expected_returns,
            cov_matrix,
            budget_per_goal,
            goal['horizon_years']
        )
        prob = calculate_success_probability(final_values, goal['target_amount'])
        success_probs[f"goal_{i+1}"] = prob

    return success_probs