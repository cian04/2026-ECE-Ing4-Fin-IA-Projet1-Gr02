import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import des modules locaux
from data_fetcher import get_historical_data, calculate_returns, calculate_stats
from portfolio_optimizer import goal_based_optimization
from monte_carlo import simulate_goal_success

st.set_page_config(page_title="Robo-Advisor Goal-Based", page_icon="📈", layout="wide")

st.title("🤖 Robo-Advisor Goal-Based")
st.markdown("Optimisation de portefeuille pour objectifs financiers multiples")

# Sidebar pour les paramètres
st.sidebar.header("Paramètres d'Investissement")

# Sélection des actifs
tickers = st.sidebar.multiselect(
    "Sélectionnez les actifs",
    ['SPY', 'BND', 'GLD', 'QQQ', 'VTI', 'VEA', 'VWO'],
    default=['SPY', 'BND', 'GLD', 'QQQ']
)

# Budget total
total_budget = st.sidebar.number_input(
    "Budget total (€)",
    min_value=10000,
    max_value=1000000,
    value=100000,
    step=10000
)

# Objectifs
st.sidebar.header("Objectifs Financiers")

num_goals = st.sidebar.slider("Nombre d'objectifs", 1, 5, 3)

goals = []
for i in range(num_goals):
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        target = st.number_input(f"Objectif {i+1} (€)", min_value=10000, value=50000*(i+1), key=f"target_{i}")
    with col2:
        horizon = st.slider(f"Horizon {i+1} (années)", 1, 30, 5*(i+1), key=f"horizon_{i}")
    with col3:
        risk = st.slider(f"Risque {i+1}", 0.01, 0.5, 0.2, key=f"risk_{i}")
    goals.append({
        'target_amount': target,
        'horizon_years': horizon,
        'risk_tolerance': risk
    })

# Bouton de calcul
if st.sidebar.button("Calculer l'optimisation", type="primary"):
    with st.spinner("Récupération des données..."):
        # Récupération des données
        data = get_historical_data(tickers)
        returns = calculate_returns(data)
        stats = calculate_stats(returns)

    # Préparation des données pour l'optimisation
    expected_returns = np.array([stats['expected_return'][t] for t in tickers])
    cov_matrix = returns.cov().values * 252

    # Optimisation
    with st.spinner("Optimisation en cours..."):
        allocations = goal_based_optimization(goals, expected_returns, cov_matrix, total_budget)

    # Simulations Monte Carlo
    with st.spinner("Simulations Monte Carlo..."):
        success_probs = simulate_goal_success(goals, expected_returns, cov_matrix, total_budget)

    # Affichage des résultats
    st.header("📊 Résultats de l'Optimisation")

    # Métriques générales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Budget Total", f"{total_budget:,.0f}€")
    with col2:
        total_success = np.mean(list(success_probs.values()))
        st.metric("Probabilité de Succès Moyenne", f"{total_success:.1%}")
    with col3:
        st.metric("Nombre d'Objectifs", len(goals))

    # Résultats par objectif
    for goal_name, alloc in allocations.items():
        goal_idx = int(goal_name.split('_')[1]) - 1
        goal = goals[goal_idx]

        with st.expander(f"🎯 Objectif {goal_idx+1}: {goal['target_amount']:,.0f}€ en {goal['horizon_years']} ans", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Budget Alloué", f"{alloc['budget']:,.0f}€")
            with col2:
                st.metric("Probabilité de Succès", f"{success_probs[goal_name]:.1%}")
            with col3:
                st.metric("Rendement Attendu", f"{alloc['allocation']['expected_return']:.1%}")
            with col4:
                st.metric("Volatilité", f"{alloc['allocation']['volatility']:.1%}")

            # Graphique d'allocation
            weights = alloc['allocation']['weights']
            fig = px.pie(
                values=weights,
                names=tickers,
                title=f"Allocation pour Objectif {goal_idx+1}"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Graphique des probabilités de succès
    st.header("📈 Probabilités de Succès")
    success_data = pd.DataFrame({
        'Objectif': [f"Objectif {i+1}" for i in range(len(goals))],
        'Probabilité': [success_probs[f"goal_{i+1}"] for i in range(len(goals))],
        'Horizon': [goal['horizon_years'] for goal in goals]
    })

    fig = px.bar(
        success_data,
        x='Objectif',
        y='Probabilité',
        color='Horizon',
        title="Probabilités de Succès par Objectif"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Données historiques
    st.header("📊 Données Historiques")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Rendements Annuels")
        returns_df = pd.DataFrame({
            'Actif': tickers,
            'Rendement (%)': [stats['expected_return'][t] * 100 for t in tickers],
            'Volatilité (%)': [stats['volatility'][t] * 100 for t in tickers]
        })
        st.dataframe(returns_df.style.format({'Rendement (%)': '{:.1f}', 'Volatilité (%)': '{:.1f}'}))

    with col2:
        st.subheader("Évolution des Prix")
        # Normaliser les prix pour la comparaison
        normalized_prices = data.copy()
        for ticker in tickers:
            if not data[ticker].empty:
                normalized_prices[ticker] = (data[ticker] / data[ticker].iloc[0]) * 100

        fig = px.line(
            normalized_prices,
            title="Évolution Normalisée des Prix (Base 100)",
            labels={'value': 'Prix Normalisé', 'variable': 'Actif'}
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Configurez vos paramètres dans la barre latérale et cliquez sur 'Calculer l'optimisation'")

st.markdown("---")
st.markdown("**Note**: Cette application est à des fins éducatives uniquement. Les résultats passés ne garantissent pas les performances futures.")