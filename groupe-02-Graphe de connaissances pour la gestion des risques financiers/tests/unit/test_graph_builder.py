"""
Tests unitaires pour le constructeur de graphe
"""

import pytest
from pathlib import Path
import sys
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from knowledge_graph.graph_builder import KnowledgeGraphBuilder
from knowledge_graph.entities import EntityType
from knowledge_graph.relations import RelationType


class TestKnowledgeGraphBuilder:
    """Tests pour KnowledgeGraphBuilder"""
    
    def test_builder_initialization(self):
        """Test initialisation du builder"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = KnowledgeGraphBuilder(output_dir=tmpdir)
            assert len(builder.entities) == 0
            assert len(builder.relations) == 0
    
    def test_add_entity(self):
        """Test ajout d'une entité"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = KnowledgeGraphBuilder(output_dir=tmpdir)
            
            entity = builder.add_entity(
                entity_id="TEST_1",
                entity_type=EntityType.COMPANY,
                text="Test Company"
            )
            
            assert entity.id == "TEST_1"
            assert len(builder.entities) == 1
            assert "TEST_1" in builder.entities
    
    def test_build_graph_dict(self):
        """Test construction du dictionnaire graphe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = KnowledgeGraphBuilder(output_dir=tmpdir)
            
            # Ajouter des entités
            builder.add_entity("C1", EntityType.COMPANY, "Company 1")
            builder.add_entity("E1", EntityType.EVENT, "Event 1")
            
            graph_dict = builder.build_graph_dict()
            
            assert "nodes" in graph_dict
            assert "edges" in graph_dict
            assert len(graph_dict["nodes"]) == 2
    
    def test_save_to_json(self):
        """Test sauvegarde en JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = KnowledgeGraphBuilder(output_dir=tmpdir)
            
            # Ajouter données
            builder.add_entity("C1", EntityType.COMPANY, "Company 1")
            builder.add_entity("R1", EntityType.RISK, "Risk 1")
            
            # Sauvegarder
            output_file = Path(tmpdir) / "test_graph.json"
            builder.save_to_json(str(output_file))
            
            # Vérifier
            assert output_file.exists()
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert "nodes" in data
                assert len(data["nodes"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
