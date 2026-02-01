"""
Module GA Core (Genetic Algorithm).
Ce module orchestre l'évolution génétique en utilisant la bibliothèque DEAP.
Il gère la création de la population, les mutations, les croisements et la sélection
des meilleures stratégies de trading basées sur deux objectifs : Profit et Drawdown.
"""
import random
import numpy as np
import warnings
from deap import base, creator, tools, algorithms
from src.strategy_genes import decode_chromosome
from src.backtest_runner import run_backtest
from src.config import Config

# Désactivation des avertissements liés aux calculs sur des valeurs infinies (cas de backtests échoués)
warnings.filterwarnings("ignore")

# --- Configuration des Types DEAP ---

# Création de l'objectif de fitness : 
# weights=(1.0, -1.0) signifie qu'on maximise le premier critère (Profit) 
# et qu'on minimise le second (Drawdown).
if not hasattr(creator, "FitnessMulti"):
    creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))

# Définition d'un individu comme une liste de gènes associée à sa fitness.
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMulti)

def eval_genome(individual, data):
    """
    Fonction d'évaluation d'un individu (génome).
    
    Cette fonction décode les gènes en paramètres réels, lance un backtest
    et retourne les scores de performance.

    Note : Placée au niveau supérieur du module pour permettre le multiprocessing 
    sous Windows (nécessaire pour la sérialisation 'pickle').

    Args:
        individual: L'individu (liste de gènes) à évaluer.
        data: Les données de marché pour le test.

    Returns:
        tuple: (profit_pct, max_drawdown_pct)
    """
    try:
        params = decode_chromosome(individual)
        # Run backtest
        profit, drawdown = run_backtest(params, data)
        return (profit, drawdown)
    except Exception:
        return (-100.0, 100.0)

# --- Fonctions de Statistiques ---
# Ces fonctions traitent les valeurs de fitness de la population pour le suivi.
def stats_mean(ind_fits):
    """Calcule la moyenne des profits valides dans la population."""
    valid_vals = [x for x in ind_fits if np.isfinite(x)]
    return np.mean(valid_vals) if valid_vals else 0.0

def stats_std(ind_fits):
    """Calcule l'écart-type des profits dans la population."""
    valid_vals = [x for x in ind_fits if np.isfinite(x)]
    return np.std(valid_vals) if valid_vals else 0.0

def stats_min(ind_fits):
    """Retourne le profit minimum trouvé."""
    valid_vals = [x for x in ind_fits if np.isfinite(x)]
    return np.min(valid_vals) if valid_vals else -100.0

def stats_max(ind_fits):
    """Retourne le profit maximum trouvé."""
    valid_vals = [x for x in ind_fits if np.isfinite(x)]
    return np.max(valid_vals) if valid_vals else -100.0


class GAEcosystem:
    """
    Gestionnaire de l'écosystème génétique.
    
    Configure les opérateurs (sélection, croisement, mutation) et 
    exécute la boucle d'évolution.
    """
    
    def __init__(self, data):
        """
        Initialise la boîte à outils (toolbox) de DEAP.

        Args:
            data: Les données d'entraînement pour l'évaluation.
        """
        self.data = data
        self.toolbox = base.Toolbox()
        self._setup_toolbox()
        
    def _setup_toolbox(self):
        """Enregistre les opérateurs génétiques et les générateurs de gènes."""
        bounds = Config.GENE_BOUNDS
        
        # Enregistrement des générateurs de gènes (Entiers et Flottants)
        self.toolbox.register("attr_sma_f", random.randint, *bounds['SMA_F'])
        self.toolbox.register("attr_sma_s", random.randint, *bounds['SMA_S'])
        self.toolbox.register("attr_rsi_p", random.randint, *bounds['RSI_P'])
        self.toolbox.register("attr_rsi_up", random.randint, *bounds['RSI_UP'])
        self.toolbox.register("attr_rsi_lo", random.randint, *bounds['RSI_LO'])
        self.toolbox.register("attr_sl", random.uniform, *bounds['SL'])
        self.toolbox.register("attr_tp", random.uniform, *bounds['TP'])
        
        # Structure d'un individu (cycle de 7 gènes)
        self.toolbox.register("individual", tools.initCycle, creator.Individual,
                            (self.toolbox.attr_sma_f, self.toolbox.attr_sma_s,
                             self.toolbox.attr_rsi_p, self.toolbox.attr_rsi_up,
                             self.toolbox.attr_rsi_lo, self.toolbox.attr_sl,
                             self.toolbox.attr_tp), n=1)

        # Générateur de population                     
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Opérateurs d'évolution
        self.toolbox.register("evaluate", eval_genome, data=self.data)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self._custom_mutation)
        self.toolbox.register("select", tools.selNSGA2)
        
    def _custom_mutation(self, individual, indpb=0.2):
        """
        Mutation personnalisée gérant le mélange de gènes entiers et flottants.

        Args:
            individual: L'individu à muter.
            indpb (float): Probabilité de mutation par gène.

        Returns:
            tuple: L'individu muté.
        """
        for i in range(len(individual)):
            if random.random() < indpb:
                if i < 5: # Gènes entiers (SMA, RSI)
                    individual[i] = int(individual[i] + random.randint(-5, 5))
                    if individual[i] < 5: individual[i] = 5
                else: # Gènes flottants (SL, TP)
                    individual[i] += random.gauss(0, 0.02)
                    if individual[i] < 0.01: individual[i] = 0.01
        return individual,

    def run_evolution(self, population_size=Config.GA_POPULATION, generations=Config.GA_GENERATIONS, verbose=True):
        """
        Lance la boucle d'évolution génétique.

        Args:
            population_size (int): Taille de la population.
            generations (int): Nombre de générations.
            verbose (bool): Affichage des logs d'évolution.

        Returns:
            tuple: (Dernière population, Logbook des statistiques)
        """
        
        pop = self.toolbox.population(n=population_size)
        
        # Configuration du suivi statistique (basé sur le Profit).
        stats = tools.Statistics(lambda ind: ind.fitness.values[0])
        
        stats.register("avg", stats_mean)
        stats.register("std", stats_std)
        stats.register("min", stats_min)
        stats.register("max", stats_max)
        
        # Exécution de l'algorithme évolutionnaire simple
        pop, logbook = algorithms.eaSimple(pop, self.toolbox, 
                                         cxpb=Config.GA_CXPB, 
                                         mutpb=Config.GA_MUTPB, 
                                         ngen=generations, 
                                         stats=stats, 
                                         verbose=verbose)
                                         
        return pop, logbook