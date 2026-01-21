import numpy as np
import pandas as pd


"""Monte Carlo utilities

Ce module contient des fonctions pour simuler la distribution finale
des valeurs de portefeuille en fonction des rendements attendus,
de la covariance et d'un vecteur de poids d'allocation.

Notes :
- Les simulations utilisent une approximation quotidienne (252 jours par an).
- `weights` est appliqué chaque jour comme pondération des multiplicateurs
    d'actifs pour obtenir la variation quotidienne du portefeuille.
"""


def monte_carlo_simulation(expected_returns, cov_matrix, initial_investment, horizon_years, num_simulations=10000, weights=None):
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

    # Si pas de poids fournis, utiliser allocation égale
    if weights is None:
        weights = np.ones(n_assets) / n_assets
    weights = np.array(weights)

    # Cholesky decomposition pour générer des rendements corrélés
    L = np.linalg.cholesky(cov_matrix)

    final_values = []

    for _ in range(num_simulations):
        # Générer des rendements quotidiens aléatoires (normaux)
        random_shocks = np.random.normal(0, 1, (num_days, n_assets))

        # Calcul des multiplicateurs journaliers par actif : exp(drift + choc)
        # drift approximé par expected_returns/252, la partie -0.5*var provient de la log-normalité
        asset_multipliers = np.exp(np.dot(random_shocks, L.T) + (expected_returns / 252 - 0.5 * np.diag(cov_matrix) / 252))

        # Calculer la valeur du portefeuille en appliquant les poids
        portfolio_value = initial_investment
        for day_mult in asset_multipliers:
            # On calcule la variation quotidienne du portefeuille comme la somme pondérée
            # des multiplicateurs d'actifs (pondération par `weights`).
            portfolio_mult = float(np.dot(weights, day_mult))
            portfolio_value *= portfolio_mult

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
    # Proportion de simulations atteignant ou dépassant l'objectif
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