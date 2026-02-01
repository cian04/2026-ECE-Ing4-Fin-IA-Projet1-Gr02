# Système de Trading Algorithmique par Algorithmes Génétiques (GA)

**Projet ECE Paris - Ing4 Fin-IA - Groupe 02**

Ce projet implémente un système d'optimisation de stratégies de trading utilisant des **Algorithmes Génétiques (GA)** et une validation robuste par **Walk-Forward Analysis (WFA)**. L'objectif est de résoudre le problème de l'optimisation combinatoire des paramètres de trading tout en minimisant le risque de surapprentissage (overfitting).

---

## 👥 Équipe JVX
* **Jean-François**
* **Valentin**
* **Xavier**

---

## 📝 Contexte du Projet

Dans le cadre du module "Finance & IA", ce projet répond à la problématique : **"Stratégies de trading par algorithmes génétiques"**.

L'optimisation de stratégies de trading nécessite d'explorer un espace immense de paramètres (indicateurs, seuils, stop-loss). Les méthodes traditionnelles (Brute Force) sont coûteuses et sujettes au curve-fitting. Notre solution utilise l'évolution darwinienne pour sélectionner les meilleures configurations et valide leur robustesse sur des données inconnues via une fenêtre glissante.

### Approche Scientifique
* **Encodage** : Stratégie encodée sous forme de chromosome (SMA, RSI, SL, TP).
* **Moteur Évolutif** : Utilisation de `DEAP` pour la sélection (NSGA-II), le croisement et la mutation.
* **Fonction Fitness** : Multi-objectifs (Maximisation du Profit, Minimisation du Drawdown).
* **Validation** : Walk-Forward Analysis (Train sur 12 mois -> Test sur 3 mois -> Glissement).

---

## 🚀 Fonctionnalités Clés

* **Moteur de Backtesting** : Basé sur `Backtrader`, rapide et événementiel.
* **Algorithme Génétique** : Optimisation des paramètres (Périodes SMA, Seuils RSI, Stop Loss, Take Profit).
* **Walk-Forward Analysis (WFA)** : Simulation réaliste de ré-optimisation périodique pour tester la robustesse.
* **Dashboard Interactif** : Interface `Streamlit` pour visualiser les résultats et les courbes de performance.
* **Architecture Modulaire** : Séparation claire entre les données, le cœur GA, la stratégie et l'exécution.

---

## 🛠️ Architecture Technique

Le projet est structuré autour de plusieurs modules interconnectés :

```mermaid
graph TD
    A[Data Source (Yahoo/CSV)] --> B(DataManager)
    B --> C{Mode d'Exécution}
    C -- Simple --> D[GA Ecosystem (DEAP)]
    C -- WFA --> E[Walk-Forward Analyzer]
    D --> F[Backtrader Engine]
    E --> F
    F --> G[Résultats & Métriques]
    G --> H[Dashboard Streamlit]

  ```  
## Structure des Fichiers

* `main.py` : Point d'entrée principal en ligne de commande (CLI).
* `dashboard.py` : Interface utilisateur web.
* `src/` :
    * `strategy_genes.py` : Définition de la stratégie (SMA cross + RSI) et du génome.
    * `ga_core.py` : Cœur de l'algorithme génétique (Population, Mutation, Évaluation).
    * `backtest_runner.py` : Wrapper pour exécuter Backtrader et extraire les stats.
    * `walk_forward.py` : Logique de la fenêtre glissante (Training/Testing sets).
    * `config.py` : Paramètres globaux (Population, Dates, Commissions).
    * `data_manager.py` : Gestion du téléchargement et formatage des données.

## 💻 Installation

### Prérequis
* **OS** : Windows 10/11 (Recommandé), Linux, macOS.
* **Python** : Version 3.10 ou 3.11 (Éviter 3.12+ pour compatibilité backtrader/deap).

### 1. Cloner et préparer l'environnement

```bash
# Création de l'environnement virtuel
python -m venv .venv

# Activation (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activation (Linux/Mac)
source .venv/bin/activate
``` 

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
``` 

| Bibliothèque | Rôle du module |
| :--- | :--- |
| **backtrader** | Moteur de trading pour l'exécution des simulations et le backtesting |
| **deap** | Framework de calcul évolutionnaire pour l'optimisation génétique |
| **yfinance** | Interface de récupération des données de marché historiques |
| **streamlit** | Outil de génération et de déploiement du dashboard interactif |
| **pandas, numpy, matplotlib** | Bibliothèques essentielles pour la manipulation de données, les calculs et la visualisation |

### 3.🎮 Utilisation

Le projet peut être utilisé via le Terminal (CLI) pour les calculs ou via le Dashboard pour la visualisation.A. Interface Graphique (Dashboard)

Pour analyser les résultats et lancer des optimisations visuelles :

```bash
streamlit run groupe-JVX/dashboard.py
```

Accessible ensuite via votre navigateur à l'adresse : http://localhost:8501B. Ligne de Commande (CLI)

Le script main.py offre plusieurs modes d'exécution 

1. Mode Test (Vérification des données)Vérifie la connexion à Yahoo Finance et le téléchargement des CSV.

```bash
python  main.py --mode test --ticker BTC-USD
```

2. Mode Simple (Optimisation GA unique)Lance une optimisation génétique sur l'ensemble de la période d'entraînement définie.

```bash
python main.py --mode simple
```

3. Mode Walk-Forward (Recommandé)Lance l'analyse complète avec fenêtres glissantes (Train/Test) pour valider la robustesse.

```bash
python main.py --mode wfa
```

4. Options Avancées Vous pouvez surcharger les paramètres par défaut :

```bash
python main.py --mode wfa --ticker SPY --generations 20 --population 100
```

| Argument | Description | Défaut |
| :--- | :--- | :--- |
| **--mode** | Choix du mode d'exécution (test, simple, wfa, all) | simple |
| **--ticker** | Symbole de l'actif (ex: BTC-USD, AAPL) | BTC-USD |
| **--generations** | Nombre de cycles d'évolution (générations) | 10 |
| **--population** | Taille de la population d'individus | 50 |


### 4. ⚙️ Configuration

Le fichier src/config.py centralise tous les hyperparamètres.

Vous pouvez y ajuster :
```bash
 --- Données ---
TICKER = "BTC-USD"
START_DATE = "2020-01-01"
INTERVAL = "1d"
```


# --- Algorithme Génétique ---
```bash
GA_POPULATION = 50       # Taille de la population
GA_GENERATIONS = 10      # Nombre d'itérations
GA_CXPB = 0.7            # Probabilité de croisement (Crossover)
GA_MUTPB = 0.2           # Probabilité de mutation
```

# --- Walk-Forward Analysis ---
```bash
WFA_TRAIN_MONTHS = 12    # Taille fenêtre d'entraînement
WFA_TEST_MONTHS = 3      # Taille fenêtre de test (Out-of-sample)
WFA_STEP_MONTHS = 3      # Décalage de la fenêtre
```

# 🧬 Détails de la Stratégie (Gènes)

L'algorithme génétique optimise un chromosome composé de 7 gènes pour piloter une stratégie de "Trend Following" sur repli (Dip buying) :

| Paramètre | Rôle technique |
| :--- | :--- |
| **SMA_F** | Moyenne Mobile Courte pour la réactivité du prix |
| **SMA_S** | Moyenne Mobile Longue pour définir la tendance de fond |
| **RSI_P** | Période de calcul de l'indice de force relative |
| **RSI_UP** | Seuil de surachat déclenchant la vente |
| **RSI_LO** | Seuil de survente identifiant le point d'achat |
| **SL** | Pourcentage de Stop Loss (perte maximale tolérée) |
| **TP** | Pourcentage de Take Profit (objectif de gain cible) |

**Logique d'Exécution**
* **Achat** | Tendance haussière (**SMA_F > SMA_S**) ET Repli temporaire (**RSI < RSI_LO**)
* **Vente** | Sortie par objectifs (**SL / TP**) OU Signal d'excès (**RSI > RSI_UP**) OU Inversion de tendance (**SMA_F < SMA_S**)

# 📚 Références & Bibliographie : 

Ce projet s'appuie sur les recherches académiques récentes : Robust Metaheuristic Optimization for Algorithmic Trading (MDPI, 2024).
