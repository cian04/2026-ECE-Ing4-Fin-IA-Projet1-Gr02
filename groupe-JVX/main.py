"""
Module Main (Point d'Entrée).
Ce script est le point d'entrée principal de l'application de trading algorithmique.

Il orchestre l'exécution du système selon différents modes définis par l'utilisateur :
1. Test : Vérification simple de la connexion aux données.
2. Simple : Lancement d'une optimisation génétique unique sur une période donnée.
3. WFA : Exécution complète de l'analyse Walk-Forward pour valider la robustesse.
4. All : Exécution séquentielle de tous les modes.

Usage :
    python main.py --mode [test|simple|wfa|all]
"""
import argparse
import sys
from src.config import Config
from src.data_manager import DataManager
from src.ga_core import GAEcosystem
from src.walk_forward import WalkForwardAnalyzer
from src.strategy_genes import decode_chromosome

def setup_argparse():
    """
    Configure et analyse les arguments passés en ligne de commande.

    Returns:
        argparse.Namespace: Objet contenant les arguments analysés (ex: args.mode).
    """
    parser = argparse.ArgumentParser(description='GA Trading System')

    # Argument 'mode' : détermine quelle partie du programme exécuter.
    # Par défaut, le mode 'simple' est sélectionné.
    parser.add_argument('--mode', type=str, choices=['test', 'simple', 'wfa', 'all'], 
                        default='simple', help='Execution mode')
    
    return parser.parse_args()

def test_data_download():
    """
    Mode 'Test' : Vérifie uniquement la connexion aux données de marché.
    
    Ce mode est utile pour s'assurer que l'API Yahoo Finance répond correctement
    et que les données sont bien mises en cache avant de lancer des calculs lourds.
    """
    print("\n" + "="*70)
    print("TEST DE TÉLÉCHARGEMENT DES DONNÉES")
    print("="*70)
    dm = DataManager()
    data = dm.get_full_data()
    
    if not data.empty:
        print("\nDonnées téléchargées avec succès !")
        print(f"Ticker      : {Config.TICKER}")
        print(f"Plage       : {data.index[0]} à {data.index[-1]}")
        print(f"Total Barres: {len(data)}")
        print("\n5 premières lignes :")
        print(data.head())
        print("\n5 dernières lignes :")
        print(data.tail())
    else:
        print("Erreur : Aucune donnée trouvée.")

def run_simple_ga(dm):
    """
    Mode 'Simple' : Lance une optimisation génétique classique.
    
    Cette fonction divise les données en un jeu d'entraînement et un jeu de test fixe (Hold-out),
    entraîne l'IA sur la première partie et valide les résultats sur la seconde.
    C'est une démonstration rapide de la capacité de l'IA à apprendre.

    Args:
        dm (DataManager): Le gestionnaire de données initialisé.
    """
    print("\n" + "="*70)
    print("LANCEMENT DE L'ALGORITHME GÉNÉTIQUE (MODE SIMPLE)")
    print("="*70)
    
    # 1. Préparation des données (Split Train/Test classique)
    full_data = dm.get_full_data()
    split_idx = int(len(full_data) * Config.TRAIN_RATIO)
    train_data = full_data.iloc[:split_idx]
    test_data = full_data.iloc[split_idx:]
    
    print(f"\nDonnées Train : {len(train_data)} barres ({train_data.index[0].date()} au {train_data.index[-1].date()})")
    print(f"Données Test  : {len(test_data)} barres ({test_data.index[0].date()} au {test_data.index[-1].date()})")
    
    # 2. Lancement de l'Optimisation (Entraînement)
    print("\nOptimisation en cours sur les données d'entraînement...")
    print(f"Paramètres GA : Population={Config.GA_POPULATION}, Générations={Config.GA_GENERATIONS}")
    
    # Utilisation de l'écosystème génétique
    ga = GAEcosystem(train_data)
    pop, log = ga.run_evolution(verbose=True)
    
    print("\nÉvolution terminée !")
    
    # 3. Récupération du meilleur résultat
    # On sélectionne l'individu avec le meilleur Profit (fitness.values[0])
    best_ind = max(pop, key=lambda ind: ind.fitness.values[0])
    best_params = decode_chromosome(best_ind)
    
    print("\n" + "="*70)
    print("MEILLEURS PARAMÈTRES TROUVÉS (SUR TRAIN)")
    print("="*70)
    for k, v in best_params.items():
        print(f"{k}: {v}")
    print(f"Fitness In-Sample : {best_ind.fitness.values}")
    
    # 4. Validation (Test Out-Of-Sample)
    # On applique les paramètres trouvés sur les données "inconnues" (Test)
    from src.backtest_runner import run_simple_backtest
    
    print("\n" + "="*70)
    print("RÉSULTATS DU TEST OUT-OF-SAMPLE")
    print("="*70)
    run_simple_backtest(best_params, test_data, verbose=True)

def run_walk_forward(dm):
    """
    Mode 'WFA' : Lance l'analyse de robustesse complète (Walk-Forward Analysis).
    
    Ce mode est le plus rigoureux : il simule un trading réaliste avec ré-optimisation
    périodique de la stratégie sur des fenêtres glissantes.

    Args:
        dm (DataManager): Le gestionnaire de données initialisé.
    """
    # Utilisation de l'analyseur WFA dédié
    wfa = WalkForwardAnalyzer(dm)
    wfa.run_analysis()

def main():
    """
    Fonction principale.
    Charge la configuration, initialise les composants et dirige l'exécution vers
    la fonction correspondant au mode choisi.
    """
    args = setup_argparse()
    
    print("\n" + "="*70)
    print("SYSTÈME DE TRADING PAR ALGORITHME GÉNÉTIQUE - GROUPE JVX")
    print("="*70)
    print(f"Actif Cible : {Config.TICKER}")
    print(f"Mode Choisi : {args.mode}")
    print("="*70)
    
    dm = DataManager()
    
    try:
        # Aiguillage selon le mode
        if args.mode == 'test':
            test_data_download()
        elif args.mode == 'simple':
            run_simple_ga(dm)
        elif args.mode == 'wfa':
            run_walk_forward(dm)
        elif args.mode == 'all':
            # Exécute toute la pipeline pour une vérification complète
            test_data_download()
            run_simple_ga(dm)
            run_walk_forward(dm)
            
        print("\n" + "="*70)
        print("FIN DE L'EXÉCUTION DU PROGRAMME")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\nArrêt manuel par l'utilisateur.")
    except Exception as e:
        print(f"\nERREUR CRITIQUE : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Protection essentielle pour Windows :
    # La librairie 'multiprocessing' (utilisée par DEAP) nécessite cette garde
    # pour éviter de lancer des processus récursifs infinis.
    import multiprocessing
    multiprocessing.freeze_support()
    main()