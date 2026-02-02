"""
Module Strategy Genes.
Ce module définit la stratégie de trading utilisée par Backtrader et contrôlée
par l'algorithme génétique. Il inclut la logique des indicateurs techniques,
les règles d'entrée/sortie et le décodage des chromosomes.
"""
import backtrader as bt
import datetime
from typing import Dict

class GeneticStrategy(bt.Strategy):
    """
    Stratégie de trading dont les paramètres sont optimisés génétiquement.
    
    Cette stratégie combine le suivi de tendance (moyennes mobiles) et 
    le retour à la moyenne (RSI) pour identifier des opportunités d'achat.
    Elle utilise des ordres "Bracket" pour sécuriser automatiquement les gains et les pertes.
    """
    
    params = (
        ('SMA_F', 20),      # Période SMA Rapide (Fast)
        ('SMA_S', 100),     # Période SMA Lente (Slow)
        ('RSI_P', 14),      # Période de calcul du RSI
        ('RSI_UP', 70),     # Seuil de sur-achat (Overbought)
        ('RSI_LO', 30),     # Seuil de sur-vente (Oversold)
        ('SL', 0.05),       # Stop Loss en pourcentage (ex: 0.05 = 5%)
        ('TP', 0.10),       # Take Profit en pourcentage
        ('trading_start_date', None), # Date de début effectif du trading (pour gérer le warm-up)
    )
    
    def __init__(self):
        """
        Initialisation des indicateurs techniques et validation des paramètres.
        
        Les indicateurs sont instanciés ici pour être calculés automatiquement
        par le moteur Backtrader à chaque étape de la simulation.
        """
        # Vérification logique : la moyenne rapide doit être plus courte que la lente
        # Sinon, le croisement n'a pas de sens dans cette stratégie.
        self.valid_params = self.params.SMA_F < self.params.SMA_S
        
        # Définition des indicateurs (Moyennes Mobiles Simples et RSI)
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.data.close, period=int(self.params.SMA_F)
        )
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.data.close, period=int(self.params.SMA_S)
        )
        self.rsi = bt.indicators.RSI(
            self.data.close, period=int(self.params.RSI_P)
        )
        
        self.order = None
        
    def notify_order(self, order):
        """
        Gère les notifications de changement d'état des ordres envoyées par le broker.

        Args:
            order: L'objet commande mis à jour.
        """
        # Ignore les ordres non finalisés (simplement soumis ou acceptés)
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        # Réinitialise le suivi de l'ordre s'il est terminé (exécuté) ou annulé
        if order.status in [order.Completed]:
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None
    
    def next(self):
        """
        Logique de décision exécutée à chaque nouvelle bougie (barre).
        
        C'est le cœur de la stratégie où sont définies les règles d'entrée et de sortie.
        """
        
        # --- Gestion du Warm-up (Préchauffage) ---
        # Si une date de démarrage est définie (notamment pour le Walk-Forward Analysis),
        # on attend qu'elle soit atteinte avant de passer le moindre ordre.
        # Cela permet aux indicateurs (ex: SMA 200) de se stabiliser.
        if self.params.trading_start_date:
            current_date = self.data.datetime.date(0)
            if current_date < self.params.trading_start_date:
                return

        # 1. Sécurité : Si les paramètres sont invalides ou si un ordre est déjà en attente, on ne fait rien.
        if not self.valid_params or self.order:
            return
        
        # 2. Logique d'Entrée (ACHAT)
        # On n'entre que si on n'a pas déjà de position ouverte.
        if not self.position:
            # Stratégie : "Buy the Dip" (Acheter le creux) en tendance haussière.
            # Condition A : Tendance de fond haussière (Moyenne Rapide > Moyenne Lente)
            # Condition B : L'actif est temporairement sous-évalué (RSI < Seuil bas)
            if (self.sma_fast[0] > self.sma_slow[0] and 
                self.rsi[0] < self.params.RSI_LO):
                
                # Calcul des prix cibles pour le Stop Loss et le Take Profit
                price = self.data.close[0]
                stop_price = price * (1.0 - self.params.SL)
                limit_price = price * (1.0 + self.params.TP)
                
                # Envoi d'un ordre "Bracket" (Groupe d'ordres liés) :
                # 1. Un ordre d'achat au marché immédiat
                # 2. Un ordre de vente Stop Loss (protection)
                # 3. Un ordre de vente Take Profit (prise de gain)
                # Si l'un des ordres de sortie est touché, l'autre est annulé (OCO).
                self.order = self.buy_bracket(
                    limitprice=limit_price, 
                    stopprice=stop_price,
                    exectype=bt.Order.Market
                )
        
        # 3. Logique de Sortie Technique (VENTE FORCEE)
        # Note : Le Bracket gère déjà la sortie financière (SL/TP).
        # Ici, on ajoute une sécurité pour sortir si la configuration technique se dégrade.
        else:
            # On force la clôture de la position si :
            # - Le RSI devient trop élevé (Sur-achat extrême, risque de correction)
            # - OU La tendance s'inverse (Croisement baissier des moyennes mobiles)
            if (self.rsi[0] > self.params.RSI_UP or 
                self.sma_fast[0] < self.sma_slow[0]):
                self.close()

def decode_chromosome(chromosome: list) -> Dict[str, float]:
    """
    Traduit un chromosome (liste brute de gènes) en un dictionnaire de paramètres nommés.
    
    Cette fonction fait le lien entre l'algorithme génétique (qui manipule des listes)
    et la stratégie Backtrader (qui attend des arguments nommés).

    Args:
        chromosome (list): Liste des valeurs issues de l'algorithme génétique.
                           Ordre attendu : [SMA_F, SMA_S, RSI_P, RSI_UP, RSI_LO, SL, TP]

    Returns:
        Dict[str, float]: Dictionnaire des paramètres formaté pour GeneticStrategy.
    """
    return {
        'SMA_F': int(chromosome[0]),
        'SMA_S': int(chromosome[1]),
        'RSI_P': int(chromosome[2]),
        'RSI_UP': int(chromosome[3]),
        'RSI_LO': int(chromosome[4]),
        'SL': float(chromosome[5]),
        'TP': float(chromosome[6]),
    }