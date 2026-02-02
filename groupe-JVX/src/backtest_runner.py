"""
Module Backtest Runner.
Ce module utilise le moteur Backtrader pour exécuter des simulations de trading
basées sur les paramètres optimisés par l'algorithme génétique.
"""
import backtrader as bt
import pandas as pd
import datetime
import traceback
from typing import Tuple, Dict
from src.strategy_genes import GeneticStrategy
from src.config import Config

#
#
#
class PandasData(bt.feeds.PandasData):
    """
    Configuration personnalisée du flux de données pour Backtrader.
    Définit comment mapper les colonnes d'un DataFrame Pandas aux champs 
    attendus par le moteur de backtest.
    """
    params = (
        ('datetime', None),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', None),
    )


def run_backtest(params: Dict[str, float], data_feed: pd.DataFrame) -> Tuple[float, float]:
    """
    Exécute un backtest simplifié pour l'évaluation de l'algorithme génétique.

    Args:
        params (Dict[str, float]): Dictionnaire des paramètres de la stratégie (SMA, RSI, SL, TP).
        data_feed (pd.DataFrame): Données historiques du marché.

    Returns:
        Tuple[float, float]: Un couple (profit_pourcentage, drawdown_maximal).
        En cas d'échec ou d'absence de trade, retourne (-100.0, 100.0).
    """
    try:
        if data_feed.empty or len(data_feed) < 100:
            return (-100.0, 100.0)
        
        cerebro = bt.Cerebro()
        cerebro.addstrategy(GeneticStrategy, **params)
        data = PandasData(dataname=data_feed)
        cerebro.adddata(data)
        cerebro.broker.setcash(Config.INITIAL_CASH)
        cerebro.broker.setcommission(commission=Config.get_commission())
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        results = cerebro.run()
        strat = results[0]
        
        trade_analysis = strat.analyzers.trades.get_analysis()
        total_trades = trade_analysis.get('total', {}).get('closed', 0)
        
        if total_trades == 0:
            return (-100.0, 100.0)
        
        initial_value = cerebro.broker.get_cash() 
        final_value = cerebro.broker.getvalue()
        
        profit_pct = ((final_value - Config.INITIAL_CASH) / Config.INITIAL_CASH) * 100.0
        
        dd_analysis = strat.analyzers.drawdown.get_analysis()
        max_drawdown_pct = dd_analysis.get('max', {}).get('drawdown', 0.0)
        
        if pd.isna(profit_pct) or pd.isna(max_drawdown_pct):
            return (-100.0, 100.0)
        
        return (profit_pct, max_drawdown_pct)
        
    except Exception:
        return (float('-inf'), float('+inf'))


def run_simple_backtest(params: Dict[str, float], 
                       data_feed: pd.DataFrame,
                       initial_cash: float = Config.INITIAL_CASH,
                       verbose: bool = True,
                       trading_start_date: datetime.date = None) -> Dict: # [CORRECTION] Nouvel argument
    """
    Exécute un backtest détaillé pour l'analyse finale ou l'affichage sur le dashboard.

    Fournit des statistiques complètes incluant le ratio de Sharpe et le taux de victoire.

    Args:
        params (Dict[str, float]): Paramètres optimisés de la stratégie.
        data_feed (pd.DataFrame): Données historiques (incluant éventuellement une période de warm-up).
        initial_cash (float): Capital de départ. Par défaut celui de Config.
        verbose (bool): Si True, affiche les résultats dans la console.
        trading_start_date (datetime.date, optional): Date à laquelle les ordres commencent 
            réellement à être passés (après la période de warm-up).

    Returns:
        Dict: Dictionnaire contenant les métriques de performance (profit, trades, win_rate, etc.).
    """
    try:
        # Sécurité : Vérifier si on a assez de données pour les indicateurs
        max_period_needed = params.get('SMA_S', 200)
        # Note : Avec le warm-up, data_feed est plus grand, donc ce check passe plus facilement
        if len(data_feed) < max_period_needed:
            if verbose: print(f"Warning: Not enough data ({len(data_feed)}) for SMA_S ({max_period_needed}). Skipping.")
            raise ValueError("Not enough data for indicators")

        cerebro = bt.Cerebro()
        
        strategy_params = params.copy()
        if trading_start_date:
            strategy_params['trading_start_date'] = trading_start_date
            
        cerebro.addstrategy(GeneticStrategy, **strategy_params)
        
        data = PandasData(dataname=data_feed)
        cerebro.adddata(data)
        
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=Config.get_commission())
        
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        
        initial_value = cerebro.broker.getvalue()
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        strat = results[0]
        
        trade_analysis = strat.analyzers.trades.get_analysis()
        dd_analysis = strat.analyzers.drawdown.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        
        total_trades = trade_analysis.get('total', {}).get('closed', 0)
        won_trades = trade_analysis.get('won', {}).get('total', 0)
        lost_trades = trade_analysis.get('lost', {}).get('total', 0)
        max_drawdown = dd_analysis.get('max', {}).get('drawdown', 0.0)
        sharpe_ratio = sharpe.get('sharperatio', 0.0)

        results_dict = {
            'initial_value': initial_value,
            'final_value': final_value,
            'profit': final_value - initial_value,
            'profit_pct': ((final_value - initial_value) / initial_value) * 100,
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades,
            'win_rate': (won_trades / total_trades * 100) if total_trades > 0 else 0,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio if sharpe_ratio is not None else 0,
        }
        
        if verbose:
            print(f"  > Result: Profit {results_dict['profit_pct']:.2f}% | Trades: {total_trades}")
        
        return results_dict
        
    except Exception as e:
        print(f"\n!!! ERREUR BACKTEST : {e}")
        return {
            'error': str(e),
            'profit_pct': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0,
            'won_trades': 0,
            'lost_trades': 0,
            'win_rate': 0.0,
            'initial_value': initial_cash,
            'final_value': initial_cash
        }