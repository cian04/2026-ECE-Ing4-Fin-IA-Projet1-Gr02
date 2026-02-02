"""
Module de configuration centrale.
Ce fichier regroupe tous les paramètres globaux du système : 
données de marché, backtesting, algorithme génétique et chemins de fichiers.
"""
from typing import Dict

class Config:
    """
    Classe statique contenant la configuration du système de trading.
    Toutes les variables sont accessibles sans instanciation.
    """
    # === Market Data ===
    # Symbole de l'actif à trader (ex: ETH-USD, BTC-USD, SPY)
    TICKER: str = "ETH-USD"
    # Intervalle de temps des bougies (1d = 1 jour)
    INTERVAL: str = "1d"
    # Date de début pour la récupération historique (large pour permettre le warm-up)
    START_DATE: str = "2018-01-01" # On prend plus d'historique pour être large
    # Date de fin pour la récupération historique
    END_DATE: str = "2026-01-01"
    
    # === Data Split ===
    # Pourcentage des données utilisé pour l'entraînement/optimisation
    TRAIN_RATIO: float = 0.70
    # Pourcentage des données réservé pour le test final (Out-Of-Sample)
    TEST_RATIO: float = 0.30
    
    # === Backtesting ===
    # Capital de départ en dollars
    INITIAL_CASH: float = 10_000.0
    # Commission par trade pour les crypto-monnaies (0.1%)
    COMMISSION_CRYPTO: float = 0.001 
    # Commission par trade pour les actions (0.01%)
    COMMISSION_STOCK: float = 0.0001
    
    @classmethod
    def get_commission(cls) -> float:
        """
        Détermine automatiquement le taux de commission en fonction du ticker.

        Returns:
            float: Le taux de commission (crypto ou action).
        """
        if "BTC" in cls.TICKER or "ETH" in cls.TICKER:
            return cls.COMMISSION_CRYPTO
        return cls.COMMISSION_STOCK
    
    # === Algorithme Génétique (DEAP) ===
    # Nombre d'individus dans chaque génération
    GA_POPULATION: int = 30 
    # Nombre de cycles d'évolution (générations)
    GA_GENERATIONS: int = 5 
    # Probabilité de croisement entre deux individus (Crossover)
    GA_CXPB: float = 0.7
    # Probabilité de mutation d'un gène
    GA_MUTPB: float = 0.2
    
    # === Walk-Forward Analysis (WFA) ===
    # Nombre de mois pour la fenêtre d'entraînement
    WFA_TRAIN_MONTHS: int = 24  
    # Nombre de mois pour la fenêtre de test
    WFA_TEST_MONTHS: int = 6    
    # Pas de glissement de la fenêtre à chaque itération
    WFA_STEP_MONTHS: int = 3
    
    # === Bornes des Gènes (Gene Bounds) ===
    # Définit les intervalles de recherche pour l'optimisation génétique.
    GENE_BOUNDS: Dict[str, tuple] = {
        'SMA_F': (5, 20),       # Très rapide (5 à 20 jours)
        'SMA_S': (25, 60),      # Rapide (max 60 jours pour éviter le warm-up trop long)
        'RSI_P': (5, 14),       # RSI standard ou rapide
        'RSI_UP': (70, 95),     
        'RSI_LO': (30, 65),     # IMPORTANT: On achète même si le RSI est à 65 (presque neutre)
        'SL': (0.02, 0.15),     
        'TP': (0.05, 0.50),     # On vise des gros gains
    }
    
    # === Paths ===
    # Répertoire de stockage des données CSV (cache)
    DATA_DIR: str = "data"
    # Répertoire de stockage des fichiers de logs
    LOGS_DIR: str = "logs"