"""
Tests unitaires pour les relations du graphe de connaissances
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from knowledge_graph.relations import Relation, RelationType


class TestRelation:
    """Tests pour la classe Relation"""
    
    def test_relation_creation(self):
        """Test création d'une relation simple"""
        relation = Relation(
            source_id="COMPANY_1",
            source_type="COMPANY",
            target_id="EVENT_1",
            target_type="EVENT",
            relation_type=RelationType.INVOLVED_IN,
            confidence=0.85,
            source="text_matching"
        )
        
        assert relation.source_id == "COMPANY_1"
        assert relation.target_id == "EVENT_1"
        assert relation.relation_type == RelationType.INVOLVED_IN
        assert relation.confidence == 0.85
    
    def test_relation_to_dict(self):
        """Test conversion d'une relation en dictionnaire"""
        relation = Relation(
            source_id="COMPANY_1",
            source_type="COMPANY",
            target_id="RISK_1",
            target_type="RISK",
            relation_type=RelationType.EXPOSED_TO,
            confidence=0.9,
            source="analysis"
        )
        
        relation_dict = relation.to_dict()
        
        assert relation_dict["source_id"] == "COMPANY_1"
        assert relation_dict["target_id"] == "RISK_1"
        assert relation_dict["relation_type"] == "exposée_à"
        assert relation_dict["confidence"] == 0.9


class TestRelationType:
    """Tests pour RelationType enum"""
    
    def test_relation_types_exist(self):
        """Test présence de tous les types de relations"""
        assert RelationType.INVOLVED_IN.value == "impliquée_dans"
        assert RelationType.CAUSED_BY.value == "causée_par"
        assert RelationType.EXPOSED_TO.value == "exposée_à"
        assert RelationType.PROPAGATES_TO.value == "se_propage_à"
    
    def test_relation_type_values(self):
        """Test valeurs des types de relations"""
        relation_types = [rt.value for rt in RelationType]
        
        assert "impliquée_dans" in relation_types
        assert "causée_par" in relation_types
        assert "exposée_à" in relation_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
