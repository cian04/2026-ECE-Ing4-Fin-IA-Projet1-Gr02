# Graphe de Connaissances pour la Gestion des Risques Financiers

Projet de master en Intelligence Artificielle Exploratoire et Symbolique - ECE 2026 - Groupe 2

## 📋 Description du Projet

Ce projet implémente un **graphe de connaissances financier** permettant de modéliser les relations complexes entre entités (entreprises, personnes, événements) pour identifier et propager les risques financiers. 

L'approche adoptée est **neuro-symbolique**, combinant :
- 🧠 **Raisonnement sur graphes** : propagation de risques à travers les relations
- 🤖 **Apprentissage automatique** : prédiction de liens et identification de risques émergents

## 🎯 Objectifs

1. **Construire** un graphe de connaissances à partir de données financières publiques
2. **Modéliser** les relations entité-événement-risque en architecture multi-couches
3. **Implémenter** des algorithmes de propagation de risque sur le graphe
4. **Utiliser** des réseaux de neurones sur graphes (GNN) pour la prédiction
5. **Visualiser** et analyser les connexions entre risques identifiés

## 📚 Contexte Théorique

### Références Clés

1. **FEEKG** - Risk identification through knowledge Association
   - _Expert Systems with Applications_ (2024)
   - Focus: Financial Event Evolution Knowledge Graphs

2. **Supply Chain Risk** - Knowledge graph reasoning for supply chain risk management
   - _Taylor & Francis_ (2022)
   - Applications: Risk propagation in complex networks

3. **FinReflectKG** - Agentic Construction and Evaluation of Financial Knowledge Graphs
   - arXiv (2024)
   - Approche LLM + IA Neuro-Symbolique

4. **SEMANTiCS 2024** - Knowledge Graphs in the Age of LLMs and Neuro-Symbolic AI
   - _IOS Press_

## 🛠️ Architecture Prévue

### Stack Technologique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Base de Données Graphe** | Neo4j / Amazon Neptune | Stockage des entités et relations |
| **Apprentissage sur Graphes** | PyKEEN / DGL-KE | Embeddings et prédiction de liens |
| **Extraction d'Entités** | spaCy / Stanza | NER financière automatisée |
| **Visualisation** | Dash / Streamlit / Cytoscape.js | Interface interactive |
| **Langage** | Python 3.9+ | Développement principal |

### Structure du Projet

```
knowledgeGraph/
├── README.md                    # Ce fichier
├── src/
│   ├── knowledge_graph/        # Core KG module
│   │   ├── __init__.py
│   │   ├── entities.py         # Définition des entités
│   │   ├── relations.py        # Types de relations
│   │   └── graph_builder.py    # Construction du graphe
│   ├── risk_propagation/       # Algorithmes de propagation
│   │   ├── __init__.py
│   │   ├── propagator.py       # Moteur de propagation
│   │   └── algorithms.py       # Différents algorithmes
│   ├── ml_models/              # Modèles ML/GNN
│   │   ├── __init__.py
│   │   └── link_predictor.py   # Prédiction de liens
│   └── visualization/          # Interfaces visuelles
│       ├── __init__.py
│       └── dashboard.py        # Dashboard Streamlit/Dash
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_graph_construction.ipynb
│   └── 03_risk_analysis.ipynb
├── data/
│   ├── raw/                    # Données brutes
│   └── processed/              # Données prétraitées
├── docs/
│   ├── architecture.md         # Documentation architecture
│   ├── api_reference.md        # Référence API
│   └── examples.md             # Exemples d'utilisation
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── config.yaml
```

## 🚀 Installation & Configuration

### Prérequis

- Python 3.9+
- pip ou conda
- Git

### Étapes d'Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/your-username/2026-ECE-Ing4-Fin-IA-Projet1-Gr02.git
cd knowledgeGraph

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Initialiser la base de données graphe (si applicable)
python -m src.setup.init_database
```

## 📊 Données et Sources

**À définir** : Sources de données financières
- APIs publiques (Yahoo Finance, Alpha Vantage, etc.)
- Données de presse financière
- Reportages ESG et risques corporatifs
- Données de crédits et défauts

## 🧪 Tests

```bash
# Exécuter tous les tests
pytest

# Tests unitaires uniquement
pytest tests/unit/

# Tests avec couverture
pytest --cov=src tests/
```

## 📈 Résultats Attendus

1. **Graphe de connaissances fonctionnel** avec au minimum 100+ entités et 500+ relations
2. **Algorithmes de propagation de risque** testés et validés
3. **Modèles GNN** avec métriques de performance (précision, rappel, F1)
4. **Dashboard interactif** permettant l'exploration du graphe
5. **Rapports d'analyse** des risques identifiés

## 👥 Équipe

- Groupe 2 - Sujet 46
- Membres: (À remplir)

## 📅 Échéances

- **20 janvier 2026** : Présentation des sujets
- **31 janvier 2026** : Pull Request à soumettre
- **02 février 2026** : Présentation finale + slides

## 📝 Licence

Ce projet est fourni dans le cadre du cursus ECE.

---

**Dernière mise à jour** : 19 janvier 2026
