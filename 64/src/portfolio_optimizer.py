import cvxpy as cp
import numpy as np
import pandas as pd


def optimize_portfolio(expected_returns, cov_matrix, risk_tolerance=0.1, constraints=None):
    """
    Résout un problème d'optimisation quadratique simple pour déterminer
    les poids d'un portefeuille qui maximisent le trade-off rendement/risque.

    Formulation : Maximize (mu^T w - lambda * w^T Sigma w)

    Arguments :
    - expected_returns: np.array shape (n,) des rendements annuels attendus
    - cov_matrix: np.array shape (n,n) matrice de covariance annualisée
    - risk_tolerance: float, coefficient lambda (plus grand => plus d'aversion au risque)
    - constraints: dict optionnel contenant 'min_weights' et/ou 'max_weights'

    Retourne un dict contenant les poids optimaux et quelques métriques.
    """
    n = len(expected_returns)
    w = cp.Variable(n)

    # Objectif : maximiser rendement attendu moins pénalité variance
    objective = cp.Maximize(expected_returns @ w - risk_tolerance * cp.quad_form(w, cov_matrix))

    # Contraintes de base : sommes des poids = 1 et pas de positions short
    constraints_list = [
        cp.sum(w) == 1,
        w >= 0
    ]

    # Contraintes optionnelles (min/max par actif)
    if constraints:
        if 'min_weights' in constraints:
            for i, min_w in enumerate(constraints['min_weights']):
                constraints_list.append(w[i] >= min_w)
        if 'max_weights' in constraints:
            for i, max_w in enumerate(constraints['max_weights']):
                constraints_list.append(w[i] <= max_w)

    prob = cp.Problem(objective, constraints_list)
    prob.solve()

    if prob.status != cp.OPTIMAL:
        # Si l'optimiseur échoue, on lève une erreur explicite
        raise ValueError("Problème d'optimisation non résoluble")

    weights = w.value
    portfolio_return = expected_returns @ weights
    portfolio_volatility = np.sqrt(weights @ cov_matrix @ weights)

    return {
        'weights': weights,
        'expected_return': portfolio_return,
        'volatility': portfolio_volatility,
        'sharpe_ratio': portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
    }

def goal_based_optimization(goals, expected_returns, cov_matrix, total_budget=100000):
    """
    Optimisation goal-based pour plusieurs objectifs financiers.

    Parameters:
    - goals: list of dict, chaque dict contient 'target_amount', 'horizon_years', 'risk_tolerance'
    - expected_returns: np.array
    - cov_matrix: np.array
    - total_budget: float, budget total

    Returns:
    - dict: allocations par objectif
    """
    # Allouer le budget proportionnellement aux montants cibles fournis
    total_target = sum([goal['target_amount'] for goal in goals])
    allocations = {}
    for i, goal in enumerate(goals):
        # Budget proportionnel au montant cible
        budget_per_goal = total_budget * (goal['target_amount'] / total_target)

        # Ajuster la tolérance au risque basée sur l'horizon (ex : diversification temporelle)
        adjusted_risk = goal['risk_tolerance'] / np.sqrt(goal['horizon_years'])

        # Contraintes simples pour forcer une diversification minimale et éviter une concentration extrême
        constraints = {
            'min_weights': [0.05] * len(expected_returns),  # Min 5% par actif
            'max_weights': [0.6] * len(expected_returns)    # Max 60% par actif
        }

        result = optimize_portfolio(expected_returns, cov_matrix, risk_tolerance=adjusted_risk, constraints=constraints)
        allocations[f"goal_{i+1}"] = {
            'allocation': result,
            'budget': budget_per_goal,
            'target': goal['target_amount']
        }

    return allocations