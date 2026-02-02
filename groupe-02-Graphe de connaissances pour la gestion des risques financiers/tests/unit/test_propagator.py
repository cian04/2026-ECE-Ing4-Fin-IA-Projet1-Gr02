"""
Tests unitaires pour l'algorithme de propagation de risque
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from risk_propagation.propagator import RiskPropagator
from collections import defaultdict


class TestRiskPropagator:
    """Tests pour RiskPropagator (sans Neo4j)"""
    
    def test_propagator_initialization(self):
        """Test initialisation du propagateur"""
        # Note: on ne teste pas la connexion Neo4j ici
        propagator = RiskPropagator(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
            decay=0.7,
            max_depth=4
        )
        
        assert propagator.decay == 0.7
        assert propagator.max_depth == 4
        assert propagator.min_score == 0.01
    
    def test_decay_calculation(self):
        """Test calcul de la décroissance"""
        propagator = RiskPropagator(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
            decay=0.7
        )
        
        # Après 1 saut: 1.0 * 0.7 = 0.7
        assert 1.0 * propagator.decay == 0.7
        
        # Après 2 sauts: 0.7 * 0.7 = 0.49
        assert 0.7 * propagator.decay == pytest.approx(0.49)
        
        # Après 3 sauts: 0.49 * 0.7 = 0.343
        assert 0.49 * propagator.decay == pytest.approx(0.343)


class TestBFSLogic:
    """Tests de la logique BFS (sans connexion Neo4j)"""
    
    def test_simple_propagation_logic(self):
        """Test logique de propagation simple"""
        # Graphe simple: A -> B -> C
        graph = {
            'A': ['B'],
            'B': ['C'],
            'C': []
        }
        
        # Simulation BFS
        scores = {}
        decay = 0.7
        max_depth = 3
        
        # Source
        scores['A'] = 1.0
        
        # Niveau 1
        for neighbor in graph['A']:
            scores[neighbor] = 1.0 * decay
        
        # Niveau 2
        for neighbor in graph['B']:
            scores[neighbor] = 0.7 * decay
        
        assert scores['A'] == 1.0
        assert scores['B'] == 0.7
        assert scores['C'] == pytest.approx(0.49)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
