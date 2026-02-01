# 📊 Optimisation de Portefeuille sous Contraintes Pratiques (MILP & CSP)

Arthur Louis / Manon Giraudeau / Noam Gisclon

---

## Vue d'ensemble

Ce projet implémente un **optimiseur de portefeuille professionnel** utilisant une formulation **MILP (Mixed Integer Linear Programming)** avec gestion du **CVaR (Conditional Value at Risk)** et des **contraintes réelles** (cardinalité, coûts de transaction, secteurs, turnover).

L'interface permet à un professionnel de prendre des décisions d'optimisation de portefeuille de manière interactive et data-driven, sans accès Internet requis (option desktop locale).

---

## Contraintes prises en compte

Les contraintes pratiques suivantes sont modélisées :

- **Contrainte de cardinalité** : nombre maximal d’actifs dans le portefeuille
- **Contraintes de diversification sectorielle**
- **Coûts de transaction et rééquilibrage du portefeuille**
- **Portefeuilles long-only**
- **Contrainte de budget**

Le risque est modélisé à l’aide de :
- l’optimisation moyenne–variance (Markowitz, baseline)
- extensions vers des mesures de risque de type **CVaR / drawdown**

---

## Technologies utilisées

- Python  
- Gurobi (optimisation MILP / MIQP)  
- OR-Tools (formulation CSP)  
- cvxpy (optimisation convexe)  
- pandas, numpy  
- yfinance (données financières)  
- matplotlib / plotly (visualisation)  
- pytest (tests automatisés)  

---

## 🔍 Comment avons-nous réfléchi pour construire ce projet

### **Étape 1 : Diagnostic initial**
- **Problème trouvé** : Le script `main.py` nécessitait `--tickers` obligatoire mais ne compilait pas sans dépendances.
- **Décision** : Configurer un environnement virtuel Python `.venv`, installer tous les paquets (`pandas`, `yfinance`, `ortools`, `numpy`, `scipy`).
- **Résultat** : `main.py` exécutable avec arguments CLI.

### **Étape 2 : Rendre le projet "plug & play"**
- **Problème** : Les utilisateurs devaient toujours fournir `--tickers` manuellement; risque d'erreurs d'import silencieuses.
- **Décision** : 
  - Ajouter des **valeurs par défaut** (`AAPL,MSFT,AMZN`).
  - Implémenter un **auto-installeur de dépendances** au démarrage de `main.py` et `gui_streamlit.py`.
- **Résultat** : Lancer le script sans argument ne plante plus; packages installés automatiquement.

### **Étape 3 : Interface graphique web (Streamlit)**
- **Problème** : Les utilisateurs veulent une UI visuelle, pas CLI.
- **Décision** : Créer `gui_streamlit.py` avec Streamlit (web UI simple, pas de serveur complexe).
- **Défis rencontrés** :
  - yfinance retournait des données vides (problème de plage de dates futures).
  - Solution : Ajouter des **dates par défaut** (2 ans en arrière jusqu'à aujourd'hui).
  - Erreur `IndexError` quand données vides → Ajouter validation claire en `data_utils.py`.

### **Étape 4 : Interface desktop (option offline)**
- **Problème** : Streamlit nécessite serveur web; certains préfèrent une fenêtre native.
- **Décision** : Créer `gui_desktop.py` avec **Tkinter** (natif, pas de dépendances externes majeures).
- **Fonctionnalité** : Charger un CSV de prix **local** (pas Internet), lancer l'optimiseur, afficher résultats.

### **Étape 5 : Améliorer UX & richesse des actions**
- **Problème** : UI basique; pas de presets, pas d'export, pas de guidance.
- **Décision** : Créer `gui_streamlit_v2.py` avec :
  - **7 presets de tickers** (Tech, Finance, Healthcare, Energy, Dividendes, S&P500, ETFs mondiaux).
  - **Boutons d'actions** : Reset, Template CSV, Help, Export JSON.
  - **Fiche technique intégrée** expliquant chaque paramètre.
  - **Layout professionnel** avec emojis, colonnes, métriques.
- **Résultat** : Interface prête pour clients / présentations.

### **Étape 6 : Gestion d'erreurs robuste**
- **Problèmes rencontrés** :
  - Port 8501 occupé → Tuer processus anciens.
  - Dates nulles → Préfiller sensiblement.
  - Données manquantes → Messages clairs au lieu de stacktrace.
- **Décision** : Ajouter try/except partout, afficher erreurs user-friendly en UI.

---

## 📦 Architecture du projet

```
Gr02-Louis_Giraudeau_Gisclon-Sujet40
│
├── README.md                   # Ce fichier
├── src/
│ ├── requirements.md # Bibliothèques utilisées
│ ├── main.py # Script principal d’exécution
│ ├── optimizer.py # Cœur : formulation MILP + solveur OR-Tools
│ ├── data_utils.py # Téléchargement données, chargement CSV, utilitaires
│ ├── gui_desktop.py # UI desktop Tkinter (local, pas Internet)
│ └── gui_steamlt_v2.py # UI web Streamlit v2 (riche, presets, exports)
├── docs/ # Documentation technique et théorique
├── slides/ # Support de présentation
│

```

### **Modules clés**

| Fichier | Rôle | Décision |
|---------|------|----------|
| `optimizer.py` | Formulation MILP + CVaR + solveur | Utilise OR-Tools pour flexibilité (SCIP/CBC) |
| `data_utils.py` | yfinance + CSV + utilities | yfinance pour flexibilité; CSV pour offline |
| `main.py` | CLI simple | Argparse standard; easy to script |
| `gui_streamlit_v2.py` | **Interface principale** | Streamlit = déploiement facile, UI réactive |
| `gui_desktop.py` | Alternative desktop | Tkinter = zéro dépendance externe, fenêtre native |

---

## 🚀 Comment utiliser

### **Option 1 : Interface web (recommandée)**

#### 1. Activer l'environnement
```powershell
cd "C:\Users\arthu\Desktop\Projet IA 40\2026-ECE-Ing4-Fin-IA-Projet1-Gr02"
.\.venv\Scripts\Activate.ps1
```

#### 2. Lancer Streamlit
```powershell
streamlit run "C:\Users\arthu\Documents\ING4\ING4-S2\Projet IA 40\gui_streamlit_v2.py" --server.port 8501
```

#### 3. Navigateur s'ouvre automatiquement
- Ouvrez http://localhost:8501
- **Sélectionnez un preset** (Tech 10, Finance 10, etc.) ou entrez tickers manuels
- Les dates se pré-remplissent automatiquement (2 ans en arrière)
- Cliquez **▶️ Run optimization**
- Visualisez portefeuille + exportez (CSV/JSON)

### **Option 2 : Interface desktop (offline)**

```powershell
cd "C:\Users\arthu\Desktop\Projet IA 40\2026-ECE-Ing4-Fin-IA-Projet1-Gr02"
.\.venv\Scripts\Activate.ps1
python "C:\Users\arthu\Documents\ING4\ING4-S2\Projet IA 40\gui_desktop.py"
```

- Une fenêtre Tkinter s'ouvre
- Charger un CSV de prix local (colonnes = tickers, index = date)
- Configurer paramètres
- Cliquer **Run Optimization (local only)**
- Exporter poids en CSV

### **Option 3 : CLI (scripter)**

```powershell
python main.py --tickers "AAPL,MSFT,AMZN" --start "2024-01-01" --end "2026-01-31" --solver CBC --n_max 5 --w_max 0.4
```

---

## 🔧 Paramètres clés (explications simples)

| Paramètre | Effet |
|-----------|-------|
| **Tickers** | Univers d'actifs; change complètement les choix possibles |
| **Start / End** | Fenêtre historique; plus longue = CVaR plus stable |
| **CVaR beta** | Confiance (0.95 = 95%); plus haut = focus sur pertes extrêmes |
| **Lambda (risk)** | Aversion au risque; plus grand = portefeuille plus conservateur |
| **Max assets** | Nombre max d'actifs sélectionnés; restreint diversification |
| **Max weight** | Limite de concentration par actif; trop serré = infaisable |
| **Turnover** | Limite rebalancement; serré = moins de trading |
| **Transaction cost** | Pénalise le trading; favorise stabilité |
| **Solver / Time** | Algorithme + durée; affectent qualité de la solution |

---

## 🛠️ Problèmes rencontrés & solutions

### ❌ **Erreur : "the following arguments are required: --tickers"**
**Cause** : `--tickers` était obligatoire au départ.  
**Solution** : Rendu optionnel avec défaut `AAPL,MSFT,AMZN`.

### ❌ **Erreur : "ModuleNotFoundError: No module named 'yfinance'"**
**Cause** : Dépendances manquantes.  
**Solution** : Ajouter auto-installeur au début de `main.py` et `gui_streamlit.py`.

### ❌ **Erreur : "No price data available" / "IndexError: single positional indexer is out-of-bounds"**
**Cause** : Dates nulles ou futures; yfinance retourne DataFrame vide.  
**Solution** : Préfiller dates sensiblement (2 ans en arrière) + valider DataFrame non vide.

### ❌ **Port 8501 occupé / Streamlit ne démarre pas**
**Cause** : Instance précédente pas fermée proprement.  
**Solution** : Tuer processus Python/Streamlit anciens; utiliser `--server.port 8502` si 8501 reste occupé.

### ❌ **INFEASIBLE : "No solution"**
**Cause** : Contraintes trop serrées (w_max trop petit, n_max trop petit, turnover trop serré).  
**Solution** : Relacher paramètres (augmenter w_max, n_max, réduire lambda_cvar).

---

## 📊 Flux de décision (optimisation)

```
1. Utilisateur remplit paramètres (tickers, dates, beta, lambda, etc.)
   ↓
2. Télécharger historique prix (yfinance) ou charger CSV local
   ↓
3. Calculer retours (pct_change) & mu (moyen annualisé)
   ↓
4. Formuler MILP:
   - Variables: w (poids), x (sélection binaire), b/s (rebalance), xi (CVaR)
   - Objectif: max E[R] - lambda*CVaR - coûts_transaction
   - Contraintes: somme(w)=1, somme(x)<=n_max, w<=w_max*x, turnover, secteurs, etc.
   ↓
5. Appeler solveur (OR-Tools SCIP/CBC)
   ↓
6. Extraire solution (poids, statut, métriques CVaR/objectif)
   ↓
7. Afficher résultats + proposer exports (CSV/JSON)
```

---

## 🎓 Concepts financiers simplifiés

### **CVaR (Conditional Value at Risk)**
- Mesure des **pertes moyennes au-delà d'un seuil** (ex: 95%).
- Plus informatif que la volatilité simple; capture "pire cas".

### **MILP (Mixed Integer Linear Programming)**
- Problème d'optimisation avec variables continues (poids) ET binaires (sélection).
- Permet contraintes réalistes: cardinalité, coûts fixes, secteurs.

### **Turnover**
- Somme des changements |w_nouveau - w_ancien|; mesure coûts de trading.
- Limite turnoever = limite rebalancing.

### **Coûts de transaction**
- `tc_rate`: coût proportionnel au turnover (ex: 10 bps = 0.001).
- `tc_fixed`: coût fixe par actif tradé (ex: frais de courtage).

---

## 📋 Checklist projet

- ✅ Environnement virtuel configuré
- ✅ Dépendances installées (pandas, yfinance, ortools, streamlit)
- ✅ `main.py` (CLI) fonctionnel
- ✅ `optimizer.py` (MILP core) validé
- ✅ `data_utils.py` (données) robuste
- ✅ `gui_streamlit_v2.py` (UI web) en production
- ✅ `gui_desktop.py` (UI desktop) alternative offline
- ✅ Gestion d'erreurs complète
- ✅ Presets de tickers + exports (CSV/JSON)
- ✅ README documentation

---

## 🎯 Prochaines améliorations possibles

1. **Backtesting** : Tester portefeuille sur période passée, comparer vs benchmark.
2. **Optimisation multi-période** : Rééquilibrage dans le temps (rolling window).
3. **Analyse de sensibilité** : Graphiques montrant effet de lambda, beta sur poids.
4. **API REST** : Déployer optimiseur sur cloud (Flask/FastAPI).
5. **Support shorting** : Autoriser positions courtes (actuellement long-only).
6. **Contraintes additionnelles** : ESG scores, volatilité max, etc.

---

## 📞 Support

- **Erreur Streamlit** : Vérifier port 8501, relancer serveur.
- **Données manquantes** : Vérifier tickers vs yfinance (certains tickers rares non dispo).
- **Infaisable** : Relacher w_max, augmenter n_max, réduire lambda_cvar.
- **Performance lente** : Augmenter time_limit ou utiliser solveur CBC (plus rapide).

---

## 📜 Fichiers importants

| Fichier | Description |
|---------|-------------|
| `requirements.txt` | Dépendances Python |
| `.venv/Scripts/Activate.ps1` | Activer l'env virtuel (PowerShell) |
| `gui_streamlit_v2.py` | **Interface principale à utiliser** |
| `optimizer.py` | Logique d'optimisation (ne pas toucher sauf amélioration) |
| `data_utils.py` | Utilitaires données (robuste, erreurs gérées) |

---
