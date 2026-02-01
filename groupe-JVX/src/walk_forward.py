"""
Module Walk-Forward Analysis (WFA).
Ce module orchestre la validation robuste de la stratégie.
Il simule le passage du temps en entraînant l'IA sur une période passée (In-Sample)
puis en la testant sur une période immédiatement suivante (Out-Of-Sample),
avant de décaler la fenêtre temporelle et de recommencer.
"""
import pandas as pd
from dateutil.relativedelta import relativedelta
from src.ga_core import GAEcosystem
from src.backtest_runner import run_simple_backtest
from src.strategy_genes import decode_chromosome
from src.config import Config

class WalkForwardAnalyzer:
    """
    Orchestrateur de l'analyse Walk-Forward.
    
    Responsable de :
    1. Découper les données historiques en fenêtres glissantes (Train + Test).
    2. Gérer le "Warm-up" (données tampons) pour que les indicateurs techniques 
       (ex: Moyenne Mobile 200) soient prêts dès le premier jour du test.
    3. Lancer l'optimisation génétique sur la partie Train.
    4. Valider la meilleure stratégie sur la partie Test.
    5. Agréger les résultats pour évaluer la robustesse globale.
    """
    
    def __init__(self, data_manager):
        """
        Initialise l'analyseur.

        Args:
            data_manager (DataManager): Instance du gestionnaire de données pour 
                                        récupérer les tranches historiques à la demande.
        """
        self.dm = data_manager
        
    def run_analysis(self):
        """
        Exécute la boucle principale de l'analyse Walk-Forward.

        Logique de la boucle :
        - Définir une fenêtre d'entraînement (ex: 24 mois).
        - Définir une fenêtre de test (ex: 6 mois) juste après.
        - Optimiser l'IA sur l'entraînement.
        - Tester sur la fenêtre de test (avec préchauffage des données).
        - Avancer (glisser) les fenêtres d'un pas défini (ex: 3 mois).

        Returns:
            List[Dict]: Une liste de résultats par fenêtre (profit, trades, etc.).
        """
        print("\n" + "="*70)
        print("DÉMARRAGE DE L'ANALYSE WALK-FORWARD (AVEC WARM-UP)")
        print("="*70)
        
        # Récupération de l'ensemble des données disponibles
        full_data = self.dm.get_full_data()
        if full_data.empty:
            print("Erreur : Aucune données disponible pour le WFA.")
            return []
            
        start_date = full_data.index[0]
        end_date = full_data.index[-1]
        
        # Date de début de la première fenêtre d'entraînement
        current_train_start = start_date
        
        wfa_results = []
        window_count = 1
        
        # Boucle Principale de Fenêtre Glissante
        while True:
            # 1. Calcul des bornes temporelles
            train_end = current_train_start + relativedelta(months=Config.WFA_TRAIN_MONTHS)
            test_start = train_end  # Le test commence immédiatement après l'entraînement
            test_end = test_start + relativedelta(months=Config.WFA_TEST_MONTHS)
            
            # Condition d'arrêt : Si la fin du test dépasse la dernière donnée disponible
            if test_end > end_date:
                break
                
            print(f"\n--- Fenêtre {window_count} ---")
            print(f"Entraînement : {current_train_start.date()} -> {train_end.date()}")
            print(f"Test         : {test_start.date()} -> {test_end.date()}")
            
            # --- Gestion Critique du Warm-up (Préchauffage) ---
            # Pour tester la stratégie à partir de 'test_start', il nous faut des données AVANT cette date.
            # Sinon, une Moyenne Mobile 200 jours ne donnerait aucune valeur avant le 201ème jour du test.
            
            # On détermine la période maximale nécessaire (ex: 60 jours ou 200 jours selon config)
            max_indicator_period = 60  # Valeur de sécurité (peut être dynamique selon GENE_BOUNDS)
            warmup_buffer_days = max_indicator_period + 10  # Marge de sécurité supplémentaire
            
            # On recule dans l'index pour trouver la date de début du préchauffage
            test_data_index = full_data.index.get_loc(test_start, method='nearest')
            warmup_start_index = max(0, test_data_index - warmup_buffer_days)
            warmup_start = full_data.index[warmup_start_index]
            
            print(f"Warm-up      : {warmup_start.date()} -> {test_start.date()} ({warmup_buffer_days} bougies)")
            
            # 2. Extraction des tranches de données
            train_data = self.dm.get_data_slice(
                str(current_train_start.date()), 
                str(train_end.date())
            )
            
            # La tranche de test INCLUT le warm-up (données passées) + la vraie période de test
            test_data_with_warmup = self.dm.get_data_slice(
                str(warmup_start.date()), 
                str(test_end.date())
            )
            
            # Vérifications de sécurité (quantité de données suffisante ?)
            if len(train_data) < 50:
                print("Fenêtre ignorée : Pas assez de données d'entraînement.")
                current_train_start += relativedelta(months=Config.WFA_STEP_MONTHS)
                window_count += 1
                continue
                
            if len(test_data_with_warmup) < warmup_buffer_days + 10:
                print("Fenêtre ignorée : Pas assez de données de test (warm-up inclus).")
                current_train_start += relativedelta(months=Config.WFA_STEP_MONTHS)
                window_count += 1
                continue

            # 3. Optimisation (Phase In-Sample)
            print("  > Optimisation en cours sur données passées...")
            # On lance un mini-AG sur la période d'entraînement
            ga = GAEcosystem(train_data)
            pop, log = ga.run_evolution(population_size=30, generations=5, verbose=False)
            
            # Sélection du meilleur individu (basé sur le fitness Profit)
            best_ind = max(pop, key=lambda ind: ind.fitness.values[0])
            best_params = decode_chromosome(best_ind)
            
            print(f"  > Meilleurs Params : SMA_F={best_params['SMA_F']}, SMA_S={best_params['SMA_S']}, RSI_LO={best_params['RSI_LO']}")
            
            # 4. Validation (Phase Out-Of-Sample)
            print("  > Test sur données inconnues (avec warm-up)...")
            
            # On lance le backtest sur les données de test (incluant le warm-up)
            # MAIS on spécifie 'trading_start_date' pour ne commencer à trader qu'au vrai début du test.
            result = run_simple_backtest(
                best_params, 
                test_data_with_warmup, 
                verbose=False,
                trading_start_date=test_start.date()  # Paramètre crucial pour ignorer les trades pendant le warm-up
            )
            
            # Enregistrement des résultats de cette fenêtre
            window_result = {
                'window': window_count,
                'train_period': f"{current_train_start.date()} à {train_end.date()}",
                'test_period': f"{test_start.date()} à {test_end.date()}",
                'profit_pct': result['profit_pct'],
                'drawdown': result['max_drawdown'],
                'trades': result['total_trades'],
                'win_rate': result.get('win_rate', 0)
            }
            wfa_results.append(window_result)
            
            print(f"  > Résultat : Profit {result['profit_pct']:.2f}% | Trades : {result['total_trades']} | WR : {result.get('win_rate', 0):.1f}%")
            
            # Glissement de la fenêtre (Slide)
            current_train_start += relativedelta(months=Config.WFA_STEP_MONTHS)
            window_count += 1
            
        self._print_summary(wfa_results)
        return wfa_results

    def _print_summary(self, results):
        """
        Affiche un rapport récapitulatif de l'analyse Walk-Forward dans la console.

        Args:
            results (List[Dict]): Liste des résultats agrégés.
        """
        if not results:
            print("Aucun résultat généré.")
            return

        print("\n" + "="*70)
        print("RÉSUMÉ FINAL WALK-FORWARD")
        print("="*70)
        
        total_profit = 0
        total_trades = 0
        wins = 0
        
        # En-têtes du tableau
        print(f"{'Fenêtre':<8} | {'Période de Test':<25} | {'Profit %':<10} | {'Trades':<8} | {'Win %':<8}")
        print("-" * 75)
        
        for r in results:
            print(f"{r['window']:<8} | {r['test_period']:<25} | {r['profit_pct']:>9.2f}% | {r['trades']:>8} | {r['win_rate']:>7.1f}%")
            total_profit += r['profit_pct']
            total_trades += r['trades']
            if r['profit_pct'] > 0: wins += 1
            
        print("-" * 75)
        
        # Calcul des moyennes globales
        avg_profit = total_profit / len(results) if results else 0
        win_rate = (wins / len(results)) * 100 if results else 0
        
        print(f"Profit Moyen par Fenêtre       : {avg_profit:.2f}%")
        print(f"Profit Cumulé Total (Somme)    : {total_profit:.2f}%")
        print(f"Taux de Fenêtres Gagnantes     : {win_rate:.2f}%")
        print(f"Total Trades (Toutes fenêtres) : {total_trades}")
        print("="*70)