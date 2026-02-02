"""
Module Dashboard (Interface Graphique).
Ce module déploie une application web interactive avec Streamlit pour piloter
le système de trading complet.

Fonctionnalités principales :
1. Visualisation des données de marché (Bougies, Volumes).
2. Lancement et suivi en temps réel de l'optimisation génétique.
3. Exécution et analyse des résultats de la validation Walk-Forward (WFA).
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import Config
from src.data_manager import DataManager
from src.ga_core import GAEcosystem
from src.walk_forward import WalkForwardAnalyzer
from src.strategy_genes import decode_chromosome

# --- CONFIGURATION DE LA PAGE ---
# Définit le titre de l'onglet du navigateur et le mode "wide" pour utiliser tout l'écran.
st.set_page_config(
    page_title="JVX ENGINE",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CHARTE GRAPHIQUE EVOLIA (CSS STRICT) ---
# Injection de CSS personnalisé pour forcer un thème sombre "Cyberpunk/Finance"
# et standardiser les boutons, les entrées de texte et les polices.
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');

    /* GLOBAL THEME */
    .stApp {
        background-color: #000000;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #333;
    }

    /* TYPOGRAPHY */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
        color: #ffffff !important;
        text-transform: uppercase;
    }
    .metric-label {
        font-family: 'Roboto Mono', monospace;
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
    }
    .metric-value {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.8rem;
        color: #fff;
        font-weight: bold;
    }

    /* BUTTONS & INPUTS (SQUARE STYLE) */
    .stButton > button {
        background-color: #333333;
        color: #ffffff;
        border: 1px solid #555555;
        border-radius: 0px !important;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.85rem;
        transition: all 0.2s;
        width: 100%;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        background-color: #ffffff;
        color: #000000;
        border-color: #ffffff;
    }
    
    /* INPUT FIELDS */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background-color: #000000;
        color: #ffffff;
        border: 1px solid #333;
        border-radius: 0px !important;
        font-family: 'Roboto Mono', monospace;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #111111;
        border-radius: 0px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #000000;
        border-radius: 0px;
        color: #888;
        font-family: 'Roboto Mono', monospace;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #222 !important;
        color: #fff !important;
        border: 1px solid #555 !important;
    }
    
    /* REMOVE DEFAULT STREAMLIT DECORATION */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    
    /* CUSTOM BORDERS */
    .projetstyle-box {
        border: 1px solid #333;
        padding: 20px;
        background-color: #0a0a0a;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURATION SYSTÈME ---
# Panneau latéral pour le contrôle global des paramètres (Actif, Dates, Hyperparamètres GA)
st.sidebar.markdown("### SYSTEM CONFIGURATION")

st.sidebar.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='metric-label'>ASSET SELECTION</div>", unsafe_allow_html=True)
# Correction label_visibility: on donne un label "Ticker" mais on le cache
ticker = st.sidebar.text_input("Ticker", value=Config.TICKER, label_visibility="collapsed")

st.sidebar.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='metric-label'>TIMEFRAME SELECTION</div>", unsafe_allow_html=True)
start_date = st.sidebar.date_input("Start", pd.to_datetime(Config.START_DATE), label_visibility="collapsed")
end_date = st.sidebar.date_input("End", pd.to_datetime(Config.END_DATE), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("### GENETIC ENGINE")
pop_size = st.sidebar.number_input("POPULATION SIZE", value=Config.GA_POPULATION, step=10)
generations = st.sidebar.number_input("GENERATIONS", value=Config.GA_GENERATIONS, step=1)

st.sidebar.markdown("---")
st.sidebar.markdown("### WFA PARAMETERS")
wfa_train = st.sidebar.number_input("TRAIN WINDOW (MONTHS)", value=Config.WFA_TRAIN_MONTHS)
wfa_test = st.sidebar.number_input("TEST WINDOW (MONTHS)", value=Config.WFA_TEST_MONTHS)

st.sidebar.markdown("---")
st.sidebar.info("GENETIC TRADING STRATEGY")

# --- MAIN CONTENT ---

# Header Section
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("GENETIC TRADING STRATEGY")


# Main Tabs
tab1, tab2, tab3 = st.tabs(["MARKET_DATA", "OPTIMIZATION_CORE", "WFA_ROBUSTNESS"])

def get_candlestick_chart(df, title):
    """
    Génère un graphique en chandeliers japonais (Candlestick) avec Plotly.

    Args:
        df (pd.DataFrame): Données historiques (Open, High, Low, Close).
        title (str): Titre du graphique (Ticker).

    Returns:
        go.Figure: Objet Figure Plotly prêt à être affiché.
    """
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'])])
    fig.update_layout(
        title=None,
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#0a0a0a',
        font=dict(family="Roboto Mono", color="#aaa"),
        xaxis_rangeslider_visible=False
    )
    # Grille subtile pour l'analyse technique
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#222')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#222')
    return fig

# --- TAB 1: DONNÉES DE MARCHÉ (MARKET DATA) ---
with tab1:
    st.markdown("<div class='projetstyle-box'>", unsafe_allow_html=True)
    
    col_ctrl, col_info = st.columns([1, 4])
    with col_ctrl:
        # Bouton pour charger les données depuis Yahoo Finance
        if st.button("INITIALIZE DATA STREAM"):
            with st.spinner('ESTABLISHING CONNECTION...'):
                try:
                    dm = DataManager()
                    df = dm.get_full_data()
                    # Stockage des données en session pour persistance entre les rechargements
                    st.session_state['data'] = df
                    st.success("DATA SYNC COMPLETE")
                except Exception as e:
                    st.error(f"CONNECTION FAILED: {e}")
                    
    with col_info:
        # Affichage des métadonnées du dataset
        if 'data' in st.session_state:
            df = st.session_state['data']
            st.markdown(f"""
            <div style='display: flex; gap: 30px;'>
                <div><span class='metric-label'>RECORDS</span><br><span class='metric-value'>{len(df)}</span></div>
                <div><span class='metric-label'>START</span><br><span class='metric-value'>{df.index[0].strftime('%Y-%m-%d')}</span></div>
                <div><span class='metric-label'>END</span><br><span class='metric-value'>{df.index[-1].strftime('%Y-%m-%d')}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Affichage du graphique si les données sont chargées
    if 'data' in st.session_state:
        # Correction warning: utilisation de use_container_width=True (standard moderne)
        st.plotly_chart(get_candlestick_chart(st.session_state['data'], ticker), use_container_width=True)
        
        with st.expander("VIEW RAW DATA MATRIX"):
            # Correction warning: si votre version le demande spécifiquement
            try:
                st.dataframe(st.session_state['data'].style.highlight_max(axis=0), use_container_width=True)
            except:
                # Fallback pour compatibilité
                st.dataframe(st.session_state['data'].style.highlight_max(axis=0), width=1500)

# --- TAB 2: CŒUR D'OPTIMISATION (OPTIMIZATION CORE) ---
with tab2:
    col_opt_left, col_opt_right = st.columns([1, 2])
    
    # Panneau de Contrôle (Gauche)
    with col_opt_left:
        st.markdown("<div class='projetstyle-box'>", unsafe_allow_html=True)
        st.markdown("### EXECUTION CONTROL")
        st.markdown(f"""
        <div style='font-family: Roboto Mono; font-size: 0.9rem; color: #888; margin-bottom: 20px;'>
        TARGET: {ticker}<br>
        ALGORITHM: NSGA-II<br>
        POPULATION: {pop_size}<br>
        GENERATIONS: {generations}
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton de lancement de l'AG
        if st.button("INITIATE SEQUENCE"):
            dm = DataManager()
            full_data = dm.get_full_data()
            train_len = int(len(full_data) * 0.7)
            train_data = full_data.iloc[:train_len]
            
            # Hack config (pour session actuelle)
            Config.GA_POPULATION = pop_size
            Config.GA_GENERATIONS = generations
            
            status_container = st.empty()
            status_container.markdown("<div style='color: #FDD835; font-family: Roboto Mono;'>PROCESSING...</div>", unsafe_allow_html=True)
            
            try:
                ga = GAEcosystem(train_data)
                pop, log = ga.run_evolution(verbose=True)
                
                status_container.markdown("<div style='color: #4CAF50; font-family: Roboto Mono;'>SEQUENCE COMPLETED</div>", unsafe_allow_html=True)
                
                best_ind = max(pop, key=lambda ind: ind.fitness.values[0])
                st.session_state['best_params'] = decode_chromosome(best_ind)
                st.session_state['best_fitness'] = best_ind.fitness.values[0]
                st.session_state['ga_log'] = log # Sauvegarde pour les stats
                
            except Exception as e:
                status_container.error(f"RUNTIME ERROR: {e}")
                import traceback
                st.code(traceback.format_exc())
                
        st.markdown("</div>", unsafe_allow_html=True)

    # Panneau de Résultats (Droite)
    with col_opt_right:
        if 'best_params' in st.session_state:
            st.markdown("<div class='projetstyle-box'>", unsafe_allow_html=True)
            st.markdown("### OPTIMIZED GENOME")
            
            p = st.session_state['best_params']
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("SMA FAST", p.get('SMA_F', 'N/A'))
            c2.metric("SMA SLOW", p.get('SMA_S', 'N/A'))
            c3.metric("RSI PERIOD", p.get('RSI_P', 'N/A'))
            c4.metric("RISK%", f"{p.get('SL', 0)*100:.1f}")
            
            st.markdown("---")
            
            # --- Graphique de Convergence ---
            if 'ga_log' in st.session_state:
                log = st.session_state['ga_log']
                gen = log.select("gen")
                avg = log.select("avg")
                max_ = log.select("max")
                
                fig_ga = go.Figure()
                fig_ga.add_trace(go.Scatter(x=gen, y=max_, mode='lines', name='Max Profit', line=dict(color='#4CAF50', width=2)))
                fig_ga.add_trace(go.Scatter(x=gen, y=avg, mode='lines', name='Avg Profit', line=dict(color='#888', width=1, dash='dot')))
                
                fig_ga.update_layout(
                    title="GENETIC CONVERGENCE (FITNESS)",
                    template="plotly_dark",
                    height=300,
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font=dict(family="Roboto Mono", color="#aaa"),
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig_ga, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("AWAITING OPTIMIZATION SEQUENCE RESULTS...")

# --- TAB 3: ROBUSTESSE WFA (WALK-FORWARD ANALYSIS) ---
with tab3:
    st.markdown("<div class='projetstyle-box'>", unsafe_allow_html=True)
    st.markdown("### WALK-FORWARD VALIDATION PROTOCOL")
    st.markdown("""
    <p style='font-family: Roboto Mono; color: #888; font-size: 0.9rem;'>
    Protocol executes iterative optimization over sliding windows to validate strategy robustness against market regime changes.
    </p>
    """, unsafe_allow_html=True)
    
    if st.button("EXECUTE WFA PROTOCOL"):
        with st.spinner("EXECUTING ROLLING ANALYSIS... THIS MAY TAKE TIME."):
            try:
                dm = DataManager()
                
                # Mise à jour config temporaire
                Config.WFA_TRAIN_MONTHS = wfa_train
                Config.WFA_TEST_MONTHS = wfa_test
                
                wfa = WalkForwardAnalyzer(dm)
                results = wfa.run_analysis()
                
                st.session_state['wfa_results'] = results
                st.success("PROTOCOL COMPLETE")
                
            except Exception as e:
                st.error(f"WFA ERROR: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # --- Visualisation des Résultats WFA ---
    if 'wfa_results' in st.session_state and st.session_state['wfa_results']:
        results = st.session_state['wfa_results']
        df_wfa = pd.DataFrame(results)
        
        # Calcul des statistiques globales
        total_profit = df_wfa['profit_pct'].sum()
        avg_win = df_wfa['profit_pct'].mean()
        win_rate = (df_wfa[df_wfa['profit_pct'] > 0].shape[0] / df_wfa.shape[0]) * 100
        
        # Affichage des métriques clés
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("CUMULATIVE PROFIT", f"{total_profit:.2f}%")
        col_m2.metric("AVG WINDOW PROFIT", f"{avg_win:.2f}%")
        col_m3.metric("WIN RATE", f"{win_rate:.1f}%")
        
        st.markdown("---")
        
        # Création des graphiques WFA (Barres + Courbe Cumulative)
        fig_wfa = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                subplot_titles=("PROFIT PER WINDOW (%)", "CUMULATIVE PROFIT (%)"),
                                vertical_spacing=0.1)
        
        # Logique de couleur (Vert si gain, Rouge si perte)
        colors = ['#4CAF50' if v >= 0 else '#EF5350' for v in df_wfa['profit_pct']]
        
        # 1. Bar Chart (Profit par fenêtre)
        fig_wfa.add_trace(go.Bar(
            x=df_wfa['window'], 
            y=df_wfa['profit_pct'],
            marker_color=colors,
            name="Window Profit"
        ), row=1, col=1)
        
        # 2. Cumulative Line (Courbe de performance globale)
        df_wfa['cumulative'] = df_wfa['profit_pct'].cumsum()
        fig_wfa.add_trace(go.Scatter(
            x=df_wfa['window'], 
            y=df_wfa['cumulative'],
            mode='lines+markers',
            line=dict(color='#2196F3', width=3),
            marker=dict(size=8),
            name="Cumulative"
        ), row=2, col=1)
        
        fig_wfa.update_layout(
            template="plotly_dark",
            height=600,
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family="Roboto Mono", color="#aaa"),
            showlegend=False
        )
        st.plotly_chart(fig_wfa, use_container_width=True)
        
        with st.expander("DETAILED REPORT DATA"):
            st.dataframe(df_wfa, use_container_width=True)
            
    elif 'wfa_results' in st.session_state and not st.session_state['wfa_results']:
        st.warning("NO RESULTS GENERATED. CHECK DATA RANGE.")
        
    st.markdown("</div>", unsafe_allow_html=True)