"""
Test d'intégration du pipeline complet
"""

import pytest
from pathlib import Path
import sys
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from knowledge_graph.graph_builder import KnowledgeGraphBuilder
from knowledge_graph.entities import EntityType
from knowledge_graph.relations import Relation, RelationType


class TestPipelineIntegration:
    """Tests d'intégration du pipeline complet"""
    
    def test_full_pipeline_execution(self):
        """Test exécution complète du pipeline"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Créer le builder
            builder = KnowledgeGraphBuilder(output_dir=tmpdir)
            
            # 2. Ajouter des entités
            builder.add_entity("COMPANY_1", EntityType.COMPANY, "BNP Paribas")
            builder.add_entity("COMPANY_2", EntityType.COMPANY, "LVMH")
            builder.add_entity("EVENT_1", EntityType.EVENT, "Cyberattaque")
            builder.add_entity("RISK_OP", EntityType.RISK, "Risque opérationnel")
            
            # 3. Ajouter des relations
            relation1 = Relation(
                source_id="COMPANY_1",
                source_type="COMPANY",
                target_id="EVENT_1",
                target_type="EVENT",
                relation_type=RelationType.INVOLVED_IN,
                confidence=0.85,
                source="test"
            )
            builder.add_relation(relation1)
            
            relation2 = Relation(
                source_id="EVENT_1",
                source_type="EVENT",
                target_id="RISK_OP",
                target_type="RISK",
                relation_type=RelationType.CAUSED_BY,
                confidence=0.9,
                source="test"
            )
            builder.add_relation(relation2)
            
            # 4. Construire le graphe
            graph_dict = builder.build_graph_dict()
            
            # 5. Vérifications
            assert len(graph_dict["nodes"]) == 4
            assert len(graph_dict["edges"]) == 2
            
            # Vérifier les nœuds
            node_ids = [node["id"] for node in graph_dict["nodes"]]
            assert "COMPANY_1" in node_ids
            assert "EVENT_1" in node_ids
            assert "RISK_OP" in node_ids
            
            # Vérifier les relations
            edge_sources = [edge["source"] for edge in graph_dict["edges"]]
            assert "COMPANY_1" in edge_sources
            assert "EVENT_1" in edge_sources
    
    def test_json_export_import(self):
        """Test export et import JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = KnowledgeGraphBuilder(output_dir=tmpdir)
            
            # Ajouter données
            builder.add_entity("C1", EntityType.COMPANY, "Company 1")
            builder.add_entity("R1", EntityType.RISK, "Risk 1")
            
            # Export JSON
            json_path = Path(tmpdir) / "graph.json"
            builder.save_to_json(str(json_path))
            
            # Import et vérification
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert "nodes" in data
            assert "edges" in data
            assert len(data["nodes"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
