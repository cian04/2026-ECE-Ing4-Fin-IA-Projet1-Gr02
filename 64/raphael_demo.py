"""raphael_demo.py

Script de démonstration destiné aux relecteurs du projet (Raphaël et équipe).

But : fournir une preuve visuelle et reproductible que la partie "optimisation +
Monte Carlo" fonctionne sans dépendre de sources externes. Le script :
 - construit des rendements synthétiques et une matrice de covariance
 - appelle l'optimiseur goal-based pour obtenir des poids par objectif
 - exécute des simulations Monte Carlo en appliquant ces poids
 - génère un dashboard HTML (tableau, allocations, histogrammes) et un CSV

Utilisation : exécuter dans l'environnement `project_env` (voir 64/README.md).
"""

from src.portfolio_optimizer import goal_based_optimization
from src.monte_carlo import simulate_goal_success, monte_carlo_simulation, calculate_success_probability
import numpy as np

def run_demo():
    # Tickeurs fictifs (4 actifs)
    tickers = ['A', 'B', 'C', 'D']

    # Rendements attendus annuels (synthetiques)
    expected_returns = np.array([0.07, 0.03, 0.02, 0.09])

    # Matrice de covariance simple (variances + petites corrélations)
    vols = np.array([0.15, 0.08, 0.12, 0.20])
    corr = np.array([
        [1.0, 0.2, 0.1, 0.3],
        [0.2, 1.0, 0.05, 0.1],
        [0.1, 0.05, 1.0, 0.15],
        [0.3, 0.1, 0.15, 1.0]
    ])
    cov_matrix = np.outer(vols, vols) * corr

    # Objectifs identiques à ceux du main
    goals = [
        {'target_amount': 50000, 'horizon_years': 5, 'risk_tolerance': 0.2},
        {'target_amount': 100000, 'horizon_years': 10, 'risk_tolerance': 0.1},
        {'target_amount': 200000, 'horizon_years': 20, 'risk_tolerance': 0.05}
    ]

    total_budget = 100000

    print("Running Raphaël demo: optimization + Monte Carlo (synthetic data)")

    allocations = goal_based_optimization(goals, expected_returns, cov_matrix, total_budget)

    # Simulations : utiliser les poids retournés par l'optimiseur pour chaque objectif
    success_probs = {}
    final_values_dict = {}
    for i, goal_key in enumerate(sorted(allocations.keys())):
        alloc = allocations[goal_key]
        weights = alloc['allocation']['weights']
        budget = alloc['budget']
        horizon = goals[i]['horizon_years']

        # num_simulations réglé à 2000 pour un bon compromis vitesse/qualité dans la démo
        final_vals = monte_carlo_simulation(expected_returns, cov_matrix, budget, horizon, num_simulations=2000, weights=weights)
        final_values_dict[goal_key] = final_vals
        prob = calculate_success_probability(final_vals, alloc['target'])
        success_probs[goal_key] = prob

    print("\n--- Allocation results ---")
    for goal_name, alloc in allocations.items():
        print(f"\n{goal_name}:")
        print(f"  Budget allocated: {alloc['budget']:.2f}")
        print(f"  Target: {alloc['target']:.2f}")
        print(f"  Expected return: {alloc['allocation']['expected_return']:.2%}")
        print(f"  Volatility: {alloc['allocation']['volatility']:.2%}")
        print("  Weights:")
        for i, t in enumerate(tickers):
            print(f"    {t}: {alloc['allocation']['weights'][i]:.2%}")

    print("\n--- Monte Carlo success probabilities ---")
    for g, p in success_probs.items():
        print(f"  {g}: {p:.2%}")

    # Visualisation interactive — dashboard Plotly (tableau récapitulatif, allocations, histogrammes)
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        goals_sorted = sorted(allocations.keys())
        n_goals = len(goals_sorted)

        # 1) Table récapitulative
        header = ['Goal', 'Budget', 'Target', 'Expected Return', 'Volatility', 'Success Prob']
        rows = []
        for g in goals_sorted:
            a = allocations[g]
            rows.append([
                g,
                f"{a['budget']:.2f}€",
                f"{a['target']:.2f}€",
                f"{a['allocation']['expected_return']:.2%}",
                f"{a['allocation']['volatility']:.2%}",
                f"{success_probs[g]:.2%}"
            ])

        table_fig = go.Figure(data=[go.Table(
            header=dict(values=header, fill_color='darkslateblue', font=dict(color='white', size=12)),
            cells=dict(values=list(zip(*rows)), fill_color='lightgrey', align='left')
        )])

        # 2) Graphique d'allocations (barres groupées par actif)
        assets = ['A', 'B', 'C', 'D']
        alloc_fig = go.Figure()
        for i, asset in enumerate(assets):
            alloc_fig.add_trace(go.Bar(name=asset, x=goals_sorted, y=[allocations[g]['allocation']['weights'][i] for g in goals_sorted]))
        alloc_fig.update_layout(barmode='stack', title='Allocations par actif (weights)')

        # 3) Histogrammes des valeurs finales (un subplot par objectif)
        hist_fig = make_subplots(rows=n_goals, cols=1, shared_xaxes=False, subplot_titles=[f"{g} — target {allocations[g]['target']:.0f}€" for g in goals_sorted])
        for idx, g in enumerate(goals_sorted, start=1):
            vals = final_values_dict[g]
            target = allocations[g]['target']
            counts, bins = np.histogram(vals, bins=50)
            hist_fig.add_trace(go.Bar(x=(bins[:-1]+bins[1:]) / 2, y=counts, marker_color='steelblue', name=f"{g} distribution"), row=idx, col=1)
            hist_fig.add_trace(go.Scatter(x=[target, target], y=[0, max(counts)*1.05], mode='lines', name='Target', line=dict(color='red', dash='dash')), row=idx, col=1)
        hist_fig.update_layout(height=300 * n_goals, title_text='Monte Carlo: distributions finales par objectif')

        # Export CSV des valeurs finales pour inspection
        import csv
        csv_path = 'raphael_demo_final_values.csv'
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = ['simulation_index'] + [f"{g}_final" for g in goals_sorted]
            writer.writerow(header_row)
            max_len = max(len(v) for v in final_values_dict.values())
            for i in range(max_len):
                row = [i]
                for g in goals_sorted:
                    vals = final_values_dict[g]
                    row.append(vals[i] if i < len(vals) else '')
                writer.writerow(row)

        # Construire une page HTML composite
        out_path = 'raphael_demo_results.html'
        html_parts = []
        html_parts.append('<html><head><meta charset="utf-8"><title>Raphaël — Demo Results</title></head><body>')
        html_parts.append('<h1 style="font-family:Arial,Helvetica,sans-serif;color:darkslateblue">Raphaël — Demo: Optimization & Monte Carlo Results</h1>')
        html_parts.append('<p style="font-family:Arial">Résumé des objectifs, allocations optimales et probabilités de succès calculées par simulation Monte Carlo.</p>')

        html_parts.append('<h2>Summary</h2>')
        html_parts.append(table_fig.to_html(full_html=False, include_plotlyjs='cdn'))
        html_parts.append('<h2>Allocations (weights)</h2>')
        html_parts.append(alloc_fig.to_html(full_html=False, include_plotlyjs=False))
        html_parts.append('<h2>Monte Carlo Distributions</h2>')
        html_parts.append(hist_fig.to_html(full_html=False, include_plotlyjs=False))

        html_parts.append(f'<p>CSV des valeurs finales: <a href="{csv_path}">{csv_path}</a></p>')
        html_parts.append('</body></html>')

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))

        print(f"\nDashboard enregistré: {out_path} (ouvrir dans un navigateur)")
        print(f"CSV des valeurs finales: {csv_path}")
    except Exception as e:
        print(f"Impossible de générer la visualisation interactive: {e}")

if __name__ == '__main__':
    run_demo()
