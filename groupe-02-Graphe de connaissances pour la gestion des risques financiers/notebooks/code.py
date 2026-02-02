"""
Pipeline complet : Données → Nettoyage → Extraction d'entités → Construction du graphe
Étapes 1-6 du projet de graphe de connaissances financier
"""

import yfinance as yf
import os
import sys
import pandas as pd
from gnews import GNews
from datetime import datetime
import re
from pathlib import Path

# Ajouter le répertoire src au chemin pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge_graph.entities import Entity, EntityType, EntityFactory
from knowledge_graph.relations import Relation, RelationType, RelationExtractor
from knowledge_graph.graph_builder import KnowledgeGraphBuilder

# ============================================================================
# ÉTAPES 1-2 : RÉCUPÉRATION DES DONNÉES
# ============================================================================

print("\n" + "="*70)
print("📊 ÉTAPE 1-2 : RÉCUPÉRATION DES DONNÉES (Prix + Actualités)")
print("="*70)

# ---------- ENTREPRISES ----------
companies = {
    # Banques
    "BNP.PA": "BNP Paribas",
    "GLE.PA": "Société Générale",
    "ACA.PA": "Crédit Agricole",
    "MC.PA": "LVMH",

    # Assurance
    "CS.PA": "AXA",
    "ORA.PA": "Orange",

    # Gestion / investissement
    "RF.PA": "Eurazeo",
    "MF.PA": "Wendel",

    # Énergie / systémique
    "TTE.PA": "TotalEnergies",
    "ENGI.PA": "Engie",

    # Industrie / transport
    "AIR.PA": "Airbus",
    "AI.PA": "Air Liquide",

    # Luxe / conso
    "KER.PA": "Kering",
    "RMS.PA": "Hermès",

    # Infrastructure / BTP
    "VIE.PA": "Veolia",
    "EN.PA": "Bouygues"
}

tickers = list(companies.keys())

# ---------- DOSSIERS ----------
os.makedirs("knowledgeGraph/data/raw", exist_ok=True)
os.makedirs("knowledgeGraph/data/processed", exist_ok=True)

print("\n1️⃣  Récupération des prix...")
prices = yf.download(tickers, start="2020-01-01", end="2026-01-01", progress=False)
prices.to_csv("knowledgeGraph/data/raw/prices.csv")
print(f"   ✓ {len(prices)} jours de données de prix téléchargés")

close_prices = prices["Close"]

print("\n2️⃣  Récupération des actualités...")
google_news = GNews(language="fr", country="FR", max_results=10)
news_rows = []

for ticker, company in companies.items():
    try:
        articles = google_news.get_news(company)
        for a in articles:
            news_rows.append({
                "ticker": ticker,
                "company": company,
                "title": a.get("title"),
                "date": pd.to_datetime(a.get("published date")).date(),
                "source": a.get("publisher", {}).get("title")
            })
    except Exception as e:
        print(f"   ⚠ Erreur pour {company}: {e}")

news_df = pd.DataFrame(news_rows)
news_df.to_csv("knowledgeGraph/data/raw/news.csv", index=False)
print(f"   ✓ {len(news_df)} articles téléchargés")

# ---------- LIEN ARTICLE ↔ PRIX ----------
print("\n3️⃣  Liaison articles ↔ prix...")
linked_rows = []

for _, row in news_df.iterrows():
    ticker = row["ticker"]
    date = row["date"]

    if ticker not in close_prices.columns:
        continue

    try:
        price_t = close_prices.loc[str(date)][ticker]
        price_t_1 = close_prices.shift(1).loc[str(date)][ticker]
    except KeyError:
        continue

    if pd.isna(price_t) or pd.isna(price_t_1):
        continue

    variation = (price_t - price_t_1) / price_t_1
    variation_pct = round(variation * 100, 2)

    impact = "Hausse" if variation > 0 else "Baisse (événement à risque)"

    linked_rows.append({
        "Entreprise": row["company"],
        "Ticker": ticker,
        "Date": date,
        "Article": row["title"],
        "Variation (%)": variation_pct,
        "Impact": impact,
        "Source": row["source"]
    })

linked_df = pd.DataFrame(linked_rows)
linked_df.to_csv("knowledgeGraph/data/raw/article_price_links.csv", index=False)
print(f"   ✓ {len(linked_df)} liaisons article-prix identifiées")

# ============================================================================
# ÉTAPE 3 : NETTOYAGE ET PRÉPARATION
# ============================================================================

print("\n" + "="*70)
print("🧹 ÉTAPE 3 : NETTOYAGE ET PRÉPARATION DES DONNÉES")
print("="*70)

print("\n✓ Nettoyage en cours...")

# Supprimer les doublons
cleaned_df = linked_df.drop_duplicates(subset=["Entreprise", "Date", "Article"])

# Convertir les dates en datetime
cleaned_df["Date"] = pd.to_datetime(cleaned_df["Date"])

# Supprimer les lignes avec données manquantes
cleaned_df = cleaned_df.dropna(subset=["Entreprise", "Article"])

# Trim les textes
cleaned_df["Article"] = cleaned_df["Article"].str.strip()

# Sauvegarder les données nettoyées
cleaned_df.to_csv("knowledgeGraph/data/processed/cleaned_financial_data.csv", index=False)
print(f"   ✓ Données nettoyées : {len(linked_df)} → {len(cleaned_df)} lignes")
print(f"   ✓ Doublons supprimés : {len(linked_df) - len(cleaned_df)}")

# ============================================================================
# ÉTAPE 4 : EXTRACTION D'ENTITÉS
# ============================================================================

print("\n" + "="*70)
print("🔍 ÉTAPE 4 : EXTRACTION D'ENTITÉS")
print("="*70)

print("\n✓ Extraction des entités...")

entities_list = []
entity_id_counter = 0

# Extraire les entreprises
print("\n   📍 Entités COMPANY :")
for company in cleaned_df["Entreprise"].unique():
    entity_id_counter += 1
    entity_id = f"COMPANY_{entity_id_counter}"
    entities_list.append({
        "entity_id": entity_id,
        "entity_type": "COMPANY",
        "entity_text": company,
        "source": "data_source"
    })
    print(f"      - {company}")

# Extraire les événements (articles)
print("\n   📌 Entités EVENT :")
for idx, article in enumerate(cleaned_df["Article"].unique()[:10], 1):  # Limiter à 10
    entity_id_counter += 1
    entity_id = f"EVENT_{entity_id_counter}"
    entities_list.append({
        "entity_id": entity_id,
        "entity_type": "EVENT",
        "entity_text": article[:100],  # Limiter la longueur
        "source": "news_article"
    })
    print(f"      - {article[:80]}...")

# Créer des entités RISK basées sur les mots-clés
risk_keywords = {
    "RISK_OPERATIONAL": ["cyberattaque", "hack", "panne", "disruption", "outage"],
    "RISK_CREDIT": ["défaut", "faillite", "insolvabilité", "non-paiement"],
    "RISK_MARKET": ["baisse", "volatilité", "krach", "correction"],
    "RISK_REPUTATION": ["scandale", "fraude", "affaire", "controverse"],
}

print("\n   ⚠️  Entités RISK :")
for risk_type, keywords in risk_keywords.items():
    for keyword in keywords:
        matching_articles = cleaned_df[cleaned_df["Article"].str.lower().str.contains(keyword, na=False)]
        if len(matching_articles) > 0:
            entity_id_counter += 1
            entity_id = risk_type
            entities_list.append({
                "entity_id": entity_id,
                "entity_type": "RISK",
                "entity_text": f"Risque : {keyword}",
                "source": "keyword_detection"
            })
            print(f"      - {risk_type} (detected: {keyword})")

# Sauvegarder les entités
entities_df = pd.DataFrame(entities_list)
entities_df.to_csv("knowledgeGraph/data/processed/extracted_entities.csv", index=False)
print(f"\n✓ {len(entities_df)} entités extraites et sauvegardées")

# ============================================================================
# ÉTAPES 5-6 : DÉFINIR LES RELATIONS ET CONSTRUIRE LE GRAPHE
# ============================================================================

print("\n" + "="*70)
print("🔗 ÉTAPES 5-6 : RELATIONS ET CONSTRUCTION DU GRAPHE")
print("="*70)

print("\n✓ Construction du graphe de connaissances...")

# Créer le builder
builder = KnowledgeGraphBuilder(output_dir="knowledgeGraph/data/processed")

# Ajouter les entités au graphe
print("\n1️⃣  Ajout des entités...")
for _, entity_row in entities_df.iterrows():
    entity_type = EntityType[entity_row["entity_type"]]
    builder.add_entity(
        entity_id=entity_row["entity_id"],
        entity_type=entity_type,
        text=entity_row["entity_text"],
        metadata={"source": entity_row["source"]}
    )

print(f"   ✓ {len(builder.entities)} entités ajoutées")

# Créer les relations
print("\n2️⃣  Création des relations...")

relations_list = []

# Relation 1 : Entreprise → impliquée dans → Événement
companies_entities = entities_df[entities_df["entity_type"] == "COMPANY"]
events_entities = entities_df[entities_df["entity_type"] == "EVENT"]

for _, company in companies_entities.iterrows():
    for _, event in events_entities.iterrows():
        # Vérifier si l'entreprise est mentionnée dans l'événement
        if company["entity_text"].lower() in event["entity_text"].lower():
            rel = Relation(
                source_id=company["entity_id"],
                source_type="COMPANY",
                target_id=event["entity_id"],
                target_type="EVENT",
                relation_type=RelationType.INVOLVED_IN,
                confidence=0.85,
                source="text_matching"
            )
            relations_list.append(rel)

# Relation 2 : Événement → cause → Risque
risk_entities = entities_df[entities_df["entity_type"] == "RISK"]

for _, event in events_entities.iterrows():
    for _, risk in risk_entities.iterrows():
        # Chercher les mots-clés du risque dans l'événement
        risk_keywords_lower = risk["entity_text"].lower().split(": ")[-1]
        if risk_keywords_lower in event["entity_text"].lower():
            rel = Relation(
                source_id=event["entity_id"],
                source_type="EVENT",
                target_id=risk["entity_id"],
                target_type="RISK",
                relation_type=RelationType.CAUSED_BY,
                confidence=0.80,
                source="keyword_analysis"
            )
            relations_list.append(rel)

# Relation 3 : Risque → se propage à → Entreprise
for _, risk in risk_entities.iterrows():
    for _, company in companies_entities.iterrows():
        rel = Relation(
            source_id=risk["entity_id"],
            source_type="RISK",
            target_id=company["entity_id"],
            target_type="COMPANY",
            relation_type=RelationType.PROPAGATES_TO,
            confidence=0.70,
            source="propagation_model"
        )
        relations_list.append(rel)

# Ajouter les relations au builder
for rel in relations_list:
    builder.add_relation(rel)

print(f"   ✓ {len(relations_list)} relations créées")

# ============================================================================
# SAUVEGARDE ET STATISTIQUES
# ============================================================================

print("\n" + "="*70)
print("💾 SAUVEGARDE DU GRAPHE")
print("="*70)

builder.save_graph_json("knowledge_graph.json")
builder.save_relations_csv("relations.csv")
builder.save_entities_csv("entities.csv")

# Afficher les statistiques
builder.print_statistics()

print("\n" + "="*70)
print("✅ PIPELINE COMPLET TERMINÉ !")
print("="*70)
print("\n📁 Fichiers générés dans knowledgeGraph/data/processed/ :")
print("   • cleaned_financial_data.csv")
print("   • extracted_entities.csv")
print("   • knowledge_graph.json")
print("   • relations.csv")
print("   • entities.csv")
