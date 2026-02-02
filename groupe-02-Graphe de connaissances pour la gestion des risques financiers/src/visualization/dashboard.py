import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import pandas as pd

# =====================
# CONFIG NEO4J
# =====================
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "Neogeo124"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.set_page_config(page_title="Risk Graph Dashboard", layout="wide")
st.title("📊 Dashboard – Graphe & Niveaux de Risque")

# =====================
# SIDEBAR – FILTRES
# =====================
st.sidebar.header("🎛️ Filtres")

min_score = st.sidebar.slider(
    "Score de risque minimum",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.05
)

selected_types = st.sidebar.multiselect(
    "Types d'entités",
    ["RISK", "COMPANY", "EVENT"],
    default=["RISK", "COMPANY", "EVENT"]
)

# =====================
# 1. TABLEAU DES RISQUES
# =====================
st.header("📈 Scores de risque")

with driver.session() as session:
    result = session.run("""
        MATCH (e:Entity)
        WHERE e.risk_score IS NOT NULL
          AND e.risk_score >= $min_score
          AND e.type IN $types
        RETURN e.id AS id, e.label AS label, e.type AS type, e.risk_score AS risk
        ORDER BY risk DESC
    """, min_score=min_score, types=selected_types)

    df = pd.DataFrame([r.data() for r in result])

st.dataframe(df, use_container_width=True)

# =====================
# 2. GRAPHE VISUEL
# =====================
st.header("🕸️ Graphe filtré")

net = Network(
    height="650px",
    width="100%",
    bgcolor="#111111",
    font_color="white",
    directed=True
)

net.barnes_hut()

with driver.session() as session:
    result = session.run("""
        MATCH (a:Entity)-[r]->(b:Entity)
        WHERE a.risk_score IS NOT NULL
          AND a.risk_score >= $min_score
          AND a.type IN $types
          AND b.type IN $types
        RETURN a, r, b
    """, min_score=min_score, types=selected_types)

    for record in result:
        a = record["a"]
        b = record["b"]
        r = record["r"]

        def node_color(node):
            if node["type"] == "RISK":
                return "#ff4d4d"   # rouge
            if node["type"] == "COMPANY":
                return "#ffa500"   # orange
            return "#4da6ff"       # bleu

        net.add_node(
            a["id"],
            label=f"{a['label']}\n({a.get('risk_score', 0):.2f})",
            color=node_color(a),
            size=20 + 20 * a.get("risk_score", 0)
        )

        net.add_node(
            b["id"],
            label=b["label"],
            color=node_color(b),
            size=18
        )

        net.add_edge(
            a["id"],
            b["id"],
            label=r.type,
            color="#aaaaaa"
        )

# =====================
# AFFICHAGE DU GRAPHE
# =====================
net.save_graph("graph.html")

st.components.v1.html(
    open("graph.html", "r", encoding="utf-8").read(),
    height=650
)

driver.close()
