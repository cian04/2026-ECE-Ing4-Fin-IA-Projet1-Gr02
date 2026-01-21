import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_historical_data(tickers, start_date=None, end_date=None, period="5y"):
    """
    Récupère les données historiques pour une liste de tickers.

    Parameters:
    - tickers: list of str, symboles des actifs
    - start_date: str, date de début (YYYY-MM-DD)
    - end_date: str, date de fin (YYYY-MM-DD)
    - period: str, période si start_date non spécifiée

    Returns:
    - dict: dictionnaire avec les données par ticker
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            data[ticker] = hist['Close']
        except Exception as e:
            print(f"Erreur pour {ticker}: {e}")
            data[ticker] = pd.Series(dtype=float)

    return data

def calculate_returns(data):
    """
    Calcule les rendements quotidiens à partir des prix.

    Parameters:
    - data: dict, données de prix par ticker

    Returns:
    - pd.DataFrame: rendements quotidiens
    """
    df = pd.DataFrame(data)
    returns = df.pct_change().dropna()
    return returns

def calculate_stats(returns):
    """
    Calcule les statistiques de rendement : moyenne et volatilité annualisée.

    Parameters:
    - returns: pd.DataFrame, rendements quotidiens

    Returns:
    - dict: moyennes et volatilités par ticker
    """
    annual_returns = returns.mean() * 252  # 252 jours de trading par an
    annual_volatility = returns.std() * np.sqrt(252)

    stats = {
        'expected_return': annual_returns.to_dict(),
        'volatility': annual_volatility.to_dict()
    }
    return stats