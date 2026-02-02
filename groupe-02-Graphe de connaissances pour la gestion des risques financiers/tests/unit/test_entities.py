"""
Tests unitaires pour les entités du graphe de connaissances
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from knowledge_graph.entities import Entity, EntityType, EntityFactory


class TestEntity:
    """Tests pour la classe Entity"""
    
    def test_entity_creation(self):
        """Test création d'une entité simple"""
        entity = Entity(
            id="TEST_1",
            type=EntityType.COMPANY,
            text="Test Company"
        )
        assert entity.id == "TEST_1"
        assert entity.type == EntityType.COMPANY
        assert entity.text == "Test Company"
    
    def test_entity_to_dict(self):
        """Test conversion d'une entité en dictionnaire"""
        entity = Entity(
            id="TEST_2",
            type=EntityType.EVENT,
            text="Test Event",
            metadata={"source": "test"}
        )
        entity_dict = entity.to_dict()
        
        assert entity_dict["id"] == "TEST_2"
        assert entity_dict["type"] == "event"
        assert entity_dict["text"] == "Test Event"
        assert entity_dict["metadata"]["source"] == "test"
    
    def test_entity_equality(self):
        """Test égalité entre entités"""
        entity1 = Entity("E1", EntityType.COMPANY, "Company A")
        entity2 = Entity("E1", EntityType.COMPANY, "Company A")
        entity3 = Entity("E2", EntityType.COMPANY, "Company B")
        
        assert entity1 == entity2
        assert entity1 != entity3
    
    def test_entity_hash(self):
        """Test hash d'entité (pour utilisation en dict/set)"""
        entity1 = Entity("E1", EntityType.COMPANY, "Company A")
        entity2 = Entity("E1", EntityType.COMPANY, "Company A")
        
        assert hash(entity1) == hash(entity2)
        
        # Test utilisation dans un set
        entities = {entity1, entity2}
        assert len(entities) == 1  # Même ID = même entité


class TestEntityFactory:
    """Tests pour EntityFactory"""
    
    def test_create_company(self):
        """Test création d'une entreprise"""
        factory = EntityFactory()
        company = factory.create_company(company_id="TEST_BNP", name="BNP Paribas")
        
        assert company.type == EntityType.COMPANY
        assert company.text == "BNP Paribas"
        assert company.id == "TEST_BNP"
    
    def test_create_event(self):
        """Test création d'un événement"""
        factory = EntityFactory()
        event = factory.create_event(event_id="TEST_CYBER", description="Cyberattaque majeure")
        
        assert event.type == EntityType.EVENT
        assert event.text == "Cyberattaque majeure"
        assert event.id == "TEST_CYBER"
    
    def test_create_risk(self):
        """Test création d'un risque"""
        factory = EntityFactory()
        risk = factory.create_risk("RISK_OPERATIONAL", "Risque opérationnel")
        
        assert risk.type == EntityType.RISK
        assert risk.text == "Risque opérationnel"
        assert risk.id == "RISK_OPERATIONAL"


class TestEntityType:
    """Tests pour EntityType enum"""
    
    def test_entity_types_exist(self):
        """Test présence de tous les types d'entités"""
        assert EntityType.COMPANY.value == "company"
        assert EntityType.EVENT.value == "event"
        assert EntityType.RISK.value == "risk"
        assert EntityType.PERSON.value == "person"
        assert EntityType.ASSET.value == "asset"
        assert EntityType.TRANSACTION.value == "transaction"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
