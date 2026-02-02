import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def _normalize_weights(weights, n_assets):
    if weights is None:
        return np.full(n_assets, 1.0 / n_assets, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if weights.shape[0] != n_assets:
        raise ValueError("La taille des poids ne correspond pas au nombre d'actifs.")
    total = weights.sum()
    if total == 0:
        raise ValueError("La somme des poids doit etre non nulle.")
    return weights / total

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

    weights = _normalize_weights(weights, n_assets)

    mean_daily = expected_returns / 252
    cov_daily = cov_matrix / 252

    daily_returns = np.random.multivariate_normal(
        mean_daily,
        cov_daily,
        size=(num_simulations, num_days)
    )

    portfolio_daily_returns = daily_returns @ weights
    portfolio_values = initial_investment * np.cumprod(1 + portfolio_daily_returns, axis=1)
    return portfolio_values[:, -1]

def monte_carlo_simulation_paths(expected_returns, cov_matrix, initial_investment, horizon_years, num_simulations=1000, weights=None):
    """
    Simule des trajectoires complètes de portefeuille via Monte Carlo.

    Returns:
    - np.array: matrice (num_days, num_simulations) des valeurs simulées
    """
    n_assets = len(expected_returns)
    num_days = horizon_years * 252  # Approximation

    weights = _normalize_weights(weights, n_assets)

    mean_daily = expected_returns / 252
    cov_daily = cov_matrix / 252

    daily_returns = np.random.multivariate_normal(
        mean_daily,
        cov_daily,
        size=(num_simulations, num_days)
    )

    portfolio_daily_returns = daily_returns @ weights
    paths = initial_investment * np.cumprod(1 + portfolio_daily_returns, axis=1)
    return paths.T

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

def simulate_goal_success(goals, expected_returns, cov_matrix, total_budget, num_simulations=10000, goal_budgets=None, goal_weights=None, return_details=False):
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
    default_budget = total_budget / num_goals if num_goals else 0

    success_probs = {}
    details = {}
    for i, goal in enumerate(goals):
        goal_key = f"goal_{i+1}"
        budget_per_goal = default_budget
        if goal_budgets and goal_key in goal_budgets:
            budget_per_goal = goal_budgets[goal_key]

        weights = None
        if goal_weights and goal_key in goal_weights:
            weights = goal_weights[goal_key]

        final_values = monte_carlo_simulation(
            expected_returns,
            cov_matrix,
            budget_per_goal,
            goal['horizon_years'],
            num_simulations=num_simulations,
            weights=weights
        )
        prob = calculate_success_probability(final_values, goal['target_amount'])
        success_probs[goal_key] = prob

        if return_details:
            successes = int(np.sum(final_values >= goal['target_amount']))
            details[goal_key] = {
                'num_simulations': num_simulations,
                'horizon_years': goal['horizon_years'],
                'num_days': goal['horizon_years'] * 252,
                'initial_investment': budget_per_goal,
                'target_amount': goal['target_amount'],
                'successes': successes,
                'final_values': final_values,
                'summary': {
                    'min': float(np.min(final_values)),
                    'p10': float(np.percentile(final_values, 10)),
                    'median': float(np.median(final_values)),
                    'mean': float(np.mean(final_values)),
                    'p90': float(np.percentile(final_values, 90)),
                    'max': float(np.max(final_values)),
                    'std': float(np.std(final_values))
                }
            }

    if return_details:
        return success_probs, details
    return success_probs

def save_monte_carlo_plot(details, output_dir, filename="monte_carlo_simulations.html"):
    """
    Genere un graphique des distributions finales et le sauvegarde en HTML.

    Parameters:
    - details: dict, details par objectif (inclut final_values)
    - output_dir: str, dossier de sortie
    - filename: str, nom du fichier HTML

    Returns:
    - str: chemin du fichier genere, ou None si details est vide
    """
    if not details:
        return None

    os.makedirs(output_dir, exist_ok=True)
    goal_items = list(details.items())
    rows = len(goal_items)

    subplot_titles = []
    for goal_key, info in goal_items:
        success_prob = info['successes'] / info['num_simulations'] if info['num_simulations'] else 0
        subplot_titles.append(
            f"{goal_key} | horizon {info['horizon_years']} ans | cible {info['target_amount']:.0f}€ | succes {success_prob:.1%}"
        )

    fig = make_subplots(rows=rows, cols=1, subplot_titles=subplot_titles)

    for idx, (goal_key, info) in enumerate(goal_items, start=1):
        final_values = info['final_values']
        fig.add_trace(
            go.Histogram(
                x=final_values,
                nbinsx=50,
                marker_color="#4C78A8",
                showlegend=False
            ),
            row=idx,
            col=1
        )
        fig.add_vline(
            x=info['target_amount'],
            line_dash="dash",
            line_color="#E45756",
            row=idx,
            col=1
        )
        fig.update_yaxes(title_text="Frequence", row=idx, col=1)

    fig.update_xaxes(title_text="Valeur finale (€)", row=rows, col=1)
    fig.update_layout(
        title="Monte Carlo - Distribution des valeurs finales",
        template="plotly_white",
        height=280 * rows + 120
    )

    output_path = os.path.join(output_dir, filename)
    fig.write_html(output_path, include_plotlyjs=True, full_html=True)
    return output_path

def save_monte_carlo_paths_plot(expected_returns, cov_matrix, initial_investment, horizon_years, output_dir, filename, num_simulations=1000, weights=None):
    """
    Genere un graphique de trajectoires Monte Carlo et sauvegarde en PNG.

    Returns:
    - str: chemin du fichier genere
    """
    os.makedirs(output_dir, exist_ok=True)

    sim_results = monte_carlo_simulation_paths(
        expected_returns,
        cov_matrix,
        initial_investment,
        horizon_years,
        num_simulations=num_simulations,
        weights=weights
    )

    time_horizon = sim_results.shape[0]
    median = np.percentile(sim_results, 50, axis=1)
    p5 = np.percentile(sim_results, 5, axis=1)
    p95 = np.percentile(sim_results, 95, axis=1)

    fig = plt.figure(figsize=(12, 6))
    plt.plot(sim_results, color='royalblue', alpha=0.03)
    plt.plot(median, color='black', linewidth=2, label='Médiane')
    plt.fill_between(
        range(time_horizon),
        p5,
        p95,
        color='gray',
        alpha=0.2,
        label='Intervalle de confiance 90%'
    )
    plt.title(f"Monte Carlo : Projection du Portefeuille sur {horizon_years} ans")
    plt.xlabel("Jours")
    plt.ylabel("Valeur du portefeuille (€)")
    plt.legend()

    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path
