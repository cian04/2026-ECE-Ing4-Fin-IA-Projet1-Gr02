"""
Module Data Manager.
Ce module est responsable du téléchargement, de la mise en cache et du nettoyage
des données de marché provenant de Yahoo Finance.
"""
import os
from pathlib import Path
import pandas as pd
import yfinance as yf
from src.config import Config

class DataManager:
    """
    Gère le cycle de vie des données de marché (téléchargement, stockage local et prétraitement).
    
    Cette classe permet d'éviter les téléchargements redondants en utilisant un système
    de cache local au format CSV.
    """
    
    def __init__(self, ticker: str = Config.TICKER, interval: str = Config.INTERVAL):
        """
        Initialise le gestionnaire de données.

        Args:
            ticker (str): Le symbole boursier à récupérer (ex: 'ETH-USD').
            interval (str): L'intervalle de temps entre chaque bougie (ex: '1d').
        """
        self.ticker = ticker
        self.interval = interval
        self.data_dir = Path(Config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_file = self.data_dir / f"{ticker}_{interval}.csv"
        
    def download_data(self, start_date: str, end_date: str, force_download: bool = False) -> pd.DataFrame:
        """
        Télécharge les données de marché ou les charge depuis le cache si disponible.

        Args:
            start_date (str): Date de début du téléchargement.
            end_date (str): Date de fin du téléchargement.
            force_download (bool): Si True, ignore le cache et télécharge à nouveau.

        Returns:
            pd.DataFrame: Un DataFrame nettoyé contenant les données OHLCV.
        """
        if self.cache_file.exists() and not force_download:
            print(f"Loading cached data from {self.cache_file}")
            try:
                df = pd.read_csv(self.cache_file, index_col=0, parse_dates=True)
                return self._sanitize_data(df)
            except Exception:
                print("Cache corrupted, re-downloading...")
        
        print(f"Downloading {self.ticker} data from {start_date} to {end_date}...")
        try:
            # Récupération via l'API yfinance
            df = yf.download(
                self.ticker, start=start_date, end=end_date, 
                interval=self.interval, progress=False, multi_level_index=False
            )
            
            # Gestion des cas où aucune donnée n'est renvoyée
            if df.empty:
                # Tentative fallback (parfois nécessaire pour les cryptos)
                df = yf.download(
                    self.ticker, period="5y", interval=self.interval, 
                    progress=False, multi_level_index=False
                )

            if df.empty:
                raise ValueError(f"No data for {self.ticker}")
            
            # Sauvegarde dans le répertoire de données local
            df.to_csv(self.cache_file)
            return self._sanitize_data(df)
            
        except Exception as e:
            print(f"Error downloading data: {e}")
            # Retourner un DataFrame vide sécurisé pour éviter le crash total
            return pd.DataFrame()
    
    def _sanitize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie et standardise le DataFrame pour assurer la compatibilité avec Backtrader.

        Effectue la suppression des valeurs manquantes, la conversion des dates et
        la vérification des colonnes requises.

        Args:
            df (pd.DataFrame): Le DataFrame brut.

        Returns:
            pd.DataFrame: Le DataFrame nettoyé et trié.
        """
        # Nettoyage des index colonnes MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        df = df.sort_index()
        
        # S'assure que la colonne 'Close' est présente pour les calculs
        if 'Adj Close' in df.columns and 'Close' not in df.columns:
            df['Close'] = df['Adj Close']
            
        # Correction automatique de la casse des colonnes si nécessaire
        required = ['Open', 'High', 'Low', 'Close']
        for col in required:
            if col not in df.columns:
                 # Tentative de réparation (cas fréquents avec CSV malformés)
                 df = df.rename(columns=str.capitalize)
        
        return df
    
    def get_full_data(self) -> pd.DataFrame:
        """
        Récupère l'intégralité des données configurées dans Config.

        Returns:
            pd.DataFrame: Données historiques complètes.
        """
        return self.download_data(Config.START_DATE, Config.END_DATE)
        
    def get_data_slice(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Extrait une tranche temporelle spécifique des données complètes.

        Args:
            start_date (str): Date de début de la tranche.
            end_date (str): Date de fin de la tranche.

        Returns:
            pd.DataFrame: Sous-ensemble des données.
        """
        full_data = self.get_full_data()
        if full_data.empty:
            return full_data
        mask = (full_data.index >= start_date) & (full_data.index <= end_date)
        return full_data[mask].copy()