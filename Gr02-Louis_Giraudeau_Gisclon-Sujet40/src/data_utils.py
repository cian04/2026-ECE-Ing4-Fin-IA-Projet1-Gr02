from __future__ import annotations

import pandas as pd
import numpy as np
import yfinance as yf
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class MarketData:
    tickers: List[str]
    returns: pd.DataFrame  # rows=time, cols=tickers
    mu: pd.Series          # expected return per ticker
    last_prices: pd.Series # last close per ticker


def download_market_data(
    tickers: List[str],
    start: str = "2020-01-01",
    end: Optional[str] = None,
    interval: str = "1d",
    price_field: str = "Adj Close",
) -> MarketData:
    """
    Download price history with yfinance, compute simple returns.
    Returns are used as scenarios for CVaR.
    """
    if not tickers:
        raise ValueError("tickers is empty")

    df = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=False,
        progress=False,
        group_by="column",
        threads=True,
    )

    # yfinance can return multi-index columns when multiple tickers
    if isinstance(df.columns, pd.MultiIndex):
        if price_field not in df.columns.get_level_values(0):
            # Fallback: try Close
            if "Close" in df.columns.get_level_values(0):
                price_field_use = "Close"
            else:
                raise ValueError(f"Could not find {price_field} or Close in downloaded data.")
        else:
            price_field_use = price_field

        prices = df[price_field_use].copy()
    else:
        # single ticker returns a flat DF
        if price_field in df.columns:
            prices = df[[price_field]].copy()
            prices.columns = tickers
        elif "Close" in df.columns:
            prices = df[["Close"]].copy()
            prices.columns = tickers
        else:
            raise ValueError(f"Could not find {price_field} or Close in downloaded data.")

    prices = prices.dropna(how="all")
    prices = prices.ffill().dropna()

    if prices.empty:
        raise ValueError(
            f"No price data available for tickers={tickers} in the date range {start} to {end}."
            " Check tickers, date range, or network access."
        )

    rets = prices.pct_change().dropna()
    # expected returns = mean of daily returns (can scale later)
    mu = rets.mean(axis=0)
    last_prices = prices.iloc[-1]

    # Ensure order
    rets = rets[tickers]
    mu = mu[tickers]
    last_prices = last_prices[tickers]

    return MarketData(tickers=tickers, returns=rets, mu=mu, last_prices=last_prices)


def load_sectors_csv(path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    CSV columns: ticker, sector, region
    Returns: (sector_map, region_map)
    """
    df = pd.read_csv(path)
    needed = {"ticker", "sector", "region"}
    if not needed.issubset(set(df.columns)):
        raise ValueError(f"{path} must contain columns: {sorted(list(needed))}")

    sector_map = {r["ticker"]: r["sector"] for _, r in df.iterrows()}
    region_map = {r["ticker"]: r["region"] for _, r in df.iterrows()}
    return sector_map, region_map


def load_current_weights_csv(path: str) -> Dict[str, float]:
    """
    CSV columns: ticker, weight
    Weights should sum ~ 1 (or less; remainder is cash implicitly).
    """
    df = pd.read_csv(path)
    needed = {"ticker", "weight"}
    if not needed.issubset(set(df.columns)):
        raise ValueError(f"{path} must contain columns: {sorted(list(needed))}")
    w0 = {r["ticker"]: float(r["weight"]) for _, r in df.iterrows()}
    return w0


def make_bounds_by_group(
    tickers: List[str],
    group_map: Dict[str, str],
    default_group: str = "UNKNOWN",
) -> Dict[str, List[str]]:
    """
    Returns dict group -> list of tickers in that group.
    """
    groups: Dict[str, List[str]] = {}
    for t in tickers:
        g = group_map.get(t, default_group)
        groups.setdefault(g, []).append(t)
    return groups


def annualize_mean_return(mu_daily: pd.Series, periods_per_year: int = 252) -> pd.Series:
    return mu_daily * periods_per_year
