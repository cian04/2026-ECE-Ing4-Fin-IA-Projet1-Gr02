# Graphe de Connaissances pour la Gestion des Risques Financiers

Projet de master en Intelligence Artificielle Exploratoire et Symbolique - ECE 2026 - Groupe 2

## 📋 Description du Projet

Ce projet implémente un graphe de connaissances financier permettant de modéliser les relations complexes entre entités (entreprises, personnes, événements) pour identifier et propager les risques financiers. 
Par relations complexes entre entités ici: Cela désigne des liens multiples et en chaîne entre entreprises, personnes et événements, où un risque chez l’un peut affecter les autres.

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

## 🛠️ Architecture (réelle)

### Stack Technologique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Base de Données Graphe** | Neo4j | Stockage des entités et relations |
| **Pipeline data** | Python + pandas | Nettoyage, extraction et export CSV/JSON |
| **Récupération données** | yfinance, GNews | Prix boursiers et actualités |
| **Propagation du risque** | BFS (Python) | Diffusion du risque avec décroissance |
| **Visualisation** | Streamlit + PyVis | Dashboard + graphe interactif |
| **ML (optionnel)** | PyKEEN + torch | Prédiction de liens (si utilisé) |

### Structure du Projet

```
knowledgeGraph/
├── readme.md
├── notebooks/
│   ├── pipeline_complete.py
│   └── 04_graph_visualization.ipynb
├── src/
│   ├── knowledge_graph/        # construction et export Neo4j
│   │   ├── graph_builder.py
│   │   └── export_to_neo4j.py
│   ├── risk_propagation/       # propagation du risque
│   │   ├── propagator.py
│   │   └── run_propagation.py
│   ├── ml_models/              # optionnel
│   │   └── link_predictor.py
│   └── visualization/
│       └── dashboard.py
├── data/
│   ├── raw/
│   └── processed/
└── docs/
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

# 3. Installer les dépendances (exemples)
pip install pandas yfinance gnews neo4j streamlit pyvis
```

## ▶️ Exécution par étapes

```bash
# Étapes 1-6 : pipeline complet
python notebooks/pipeline_complete.py

# Étape 7 : import Neo4j
python src/knowledge_graph/export_to_neo4j.py

# Étape 8 : propagation du risque (mot de passe via variable ou option)
$env:NEO4J_PASSWORD = "<TON_MDP>"
python src/risk_propagation/run_propagation.py

# Dashboard
streamlit run src/visualization/dashboard.py
```

## 📊 Données et Sources

- **Prix boursiers** : Yahoo Finance via `yfinance`
- **Actualités** : GNews via `gnews`

## 🧪 Tests

Le projet dispose d'une suite de tests complète avec **21 tests** couvrant toutes les fonctionnalités principales.

### Installation de pytest

```bash
pip install pytest
```

### Exécution des tests

```bash
# Exécuter tous les tests
python -m pytest

# Tests avec affichage détaillé
python -m pytest -v

# Tests d'un module spécifique
python -m pytest tests/unit/test_entities.py

# Tests avec couverture de code
pip install pytest-cov
python -m pytest --cov=src tests/
```

### Structure des tests

```
tests/
├── conftest.py                    # Configuration pytest
├── unit/                          # Tests unitaires
│   ├── test_entities.py          # Entity, EntityType, EntityFactory (9 tests)
│   ├── test_relations.py         # Relation, RelationType (4 tests)
│   ├── test_graph_builder.py    # KnowledgeGraphBuilder (4 tests)
│   └── test_propagator.py       # RiskPropagator (3 tests)
└── integration/                   # Tests d'intégration
    └── test_pipeline.py          # Pipeline complet (2 tests)
```

### Résultats des tests

```
========================= 21 passed in 1.43s ==========================
✅ 21 tests passent
❌ 0 test échoue
```

**Couverture** :
- ✅ Création et sérialisation des entités
- ✅ Création et validation des relations
- ✅ Construction du graphe et export JSON
- ✅ Algorithme de propagation de risque (logique BFS)
- ✅ Pipeline d'intégration complet

## 📈 Résultats Attendus

1. **Graphe de connaissances fonctionnel** avec au minimum 100+ entités et 500+ relations
2. **Algorithmes de propagation de risque** testés et validés
3. **Modèles GNN** avec métriques de performance (précision, rappel, F1)
4. **Dashboard interactif** permettant l'exploration du graphe
5. **Rapports d'analyse** des risques identifiés

## 👥 Équipe

- Groupe 2 - Sujet 46
- Membre: MBWEBI FANDJA Donald Brownnell 

## 📅 Échéances

- **20 janvier 2026** : Présentation des sujets
- **31 janvier 2026** : Pull Request à soumettre
- **02 février 2026** : Présentation finale + slides

## 📝 Licence

Ce projet est fourni dans le cadre du cursus ECE.

---

**Dernière mise à jour** : 02 février 2026
