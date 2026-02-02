"""
Module de construction du graphe de connaissances financier.
Transforme les entités et relations en graphe structuré.
"""

import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import asdict
from pathlib import Path

from .entities import Entity, EntityType
from .relations import Relation, RelationType, RelationExtractor


class KnowledgeGraphBuilder:
    """Construit et gère le graphe de connaissances financier."""
    
    def __init__(self, output_dir: str = "data/processed"):
        """
        Initialise le constructeur de graphe.
        
        Args:
            output_dir: Répertoire de sortie pour les fichiers du graphe
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.relation_extractor = RelationExtractor()
    
    def add_entity(self, entity_id: str, entity_type: EntityType, 
                   text: str, metadata: Dict = None) -> Entity:
        """Ajoute une entité au graphe."""
        entity = Entity(
            id=entity_id,
            type=entity_type,
            text=text,
            metadata=metadata or {}
        )
        self.entities[entity_id] = entity
        return entity
    
    def add_entities_from_dataframe(self, df: pd.DataFrame) -> None:
        """
        Charge les entités à partir d'un DataFrame.
        
        Attendu : colonnes ["entity_id", "entity_type", "entity_text"]
        """
        for _, row in df.iterrows():
            entity_type = EntityType[row["entity_type"].upper()]
            self.add_entity(
                entity_id=row["entity_id"],
                entity_type=entity_type,
                text=row["entity_text"],
                metadata={"source": row.get("source", "unknown")}
            )
    
    def add_relation(self, relation: Relation) -> None:
        """Ajoute une relation au graphe."""
        self.relations.append(relation)
    
    def extract_relations_from_texts(self, texts: List[str]) -> None:
        """Extrait automatiquement les relations à partir de textes."""
        entities_list = [
            {
                "id": e.id,
                "type": e.type.name,
                "text": e.text
            }
            for e in self.entities.values()
        ]
        
        extracted = self.relation_extractor.extract_relations(entities_list, texts)
        self.relations.extend(extracted)
    
    def build_graph_dict(self) -> Dict:
        """
        Construit une représentation dictionnaire du graphe.
        
        Returns:
            Dict avec "nodes" et "edges"
        """
        nodes = []
        for entity in self.entities.values():
            nodes.append({
                "id": entity.id,
                "label": entity.text,
                "type": entity.type.name,
                "metadata": entity.metadata
            })
        
        edges = []
        for rel in self.relations:
            edges.append({
                "source": rel.source_id,
                "target": rel.target_id,
                "type": rel.relation_type.value,
                "confidence": rel.confidence,
                "source_type": rel.source_type,
                "target_type": rel.target_type,
                "metadata": rel.metadata
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "num_entities": len(nodes),
                "num_relations": len(edges)
            }
        }
    
    def save_graph_json(self, filename: str = "knowledge_graph.json") -> Path:
        """Sauvegarde le graphe au format JSON."""
        graph_dict = self.build_graph_dict()
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Graphe sauvegardé : {output_path}")
        return output_path
    
    def save_to_json(self, filepath: str) -> Path:
        """Alias pour save_graph_json (pour compatibilité avec les tests)."""
        return self.save_graph_json(filepath)
    
    def save_relations_csv(self, filename: str = "relations.csv") -> Path:
        """Sauvegarde les relations au format CSV."""
        relations_data = []
        for rel in self.relations:
            relations_data.append({
                "source_id": rel.source_id,
                "source_type": rel.source_type,
                "relation_type": rel.relation_type.value,
                "target_id": rel.target_id,
                "target_type": rel.target_type,
                "confidence": rel.confidence,
                "source": rel.source,
                "timestamp": rel.timestamp
            })
        
        df = pd.DataFrame(relations_data)
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"✓ Relations sauvegardées : {output_path}")
        return output_path
    
    def save_entities_csv(self, filename: str = "entities.csv") -> Path:
        """Sauvegarde les entités au format CSV."""
        entities_data = []
        for entity in self.entities.values():
            entities_data.append({
                "entity_id": entity.id,
                "entity_type": entity.type.name,
                "entity_text": entity.text,
                "created_at": entity.created_at
            })
        
        df = pd.DataFrame(entities_data)
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"✓ Entités sauvegardées : {output_path}")
        return output_path
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur le graphe."""
        entity_counts = {}
        for entity in self.entities.values():
            entity_type = entity.type.name
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        relation_counts = {}
        for rel in self.relations:
            rel_type = rel.relation_type.value
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
        
        return {
            "total_entities": len(self.entities),
            "entities_by_type": entity_counts,
            "total_relations": len(self.relations),
            "relations_by_type": relation_counts,
            "average_confidence": sum(r.confidence for r in self.relations) / len(self.relations) if self.relations else 0
        }
    
    def print_statistics(self) -> None:
        """Affiche les statistiques du graphe."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("📊 STATISTIQUES DU GRAPHE DE CONNAISSANCES")
        print("="*60)
        print(f"\n🔵 Entités totales : {stats['total_entities']}")
        for entity_type, count in stats['entities_by_type'].items():
            print(f"   - {entity_type}: {count}")
        
        print(f"\n🔗 Relations totales : {stats['total_relations']}")
        for rel_type, count in stats['relations_by_type'].items():
            print(f"   - {rel_type}: {count}")
        
        print(f"\n📈 Confiance moyenne : {stats['average_confidence']:.2f}")
        print("="*60 + "\n")


def create_sample_graph() -> KnowledgeGraphBuilder:
    """
    Crée un exemple de graphe pour démonstration.
    """
    builder = KnowledgeGraphBuilder()
    
    # Ajouter des entités d'exemple
    builder.add_entity(
        "APPLE_INC",
        EntityType.COMPANY,
        "Apple Inc.",
        {"sector": "Technology", "country": "USA"}
    )
    
    builder.add_entity(
        "SECURITY_BREACH_2024",
        EntityType.EVENT,
        "Cyberattaque Apple 2024",
        {"date": "2024-03-15", "severity": "high"}
    )
    
    builder.add_entity(
        "DATA_THEFT",
        EntityType.RISK,
        "Vol de données client",
        {"category": "operational"}
    )
    
    builder.add_entity(
        "REPUTATION_DAMAGE",
        EntityType.RISK,
        "Dommage à la réputation",
        {"category": "reputational"}
    )
    
    # Ajouter des relations
    from .relations import RelationType
    
    builder.add_relation(Relation(
        source_id="APPLE_INC",
        source_type="COMPANY",
        target_id="SECURITY_BREACH_2024",
        target_type="EVENT",
        relation_type=RelationType.INVOLVED_IN,
        confidence=0.9,
        source="news"
    ))
    
    builder.add_relation(Relation(
        source_id="SECURITY_BREACH_2024",
        source_type="EVENT",
        target_id="DATA_THEFT",
        target_type="RISK",
        relation_type=RelationType.CAUSED_BY,
        confidence=0.95,
        source="analysis"
    ))
    
    builder.add_relation(Relation(
        source_id="DATA_THEFT",
        source_type="RISK",
        target_id="REPUTATION_DAMAGE",
        target_type="RISK",
        relation_type=RelationType.PROPAGATES_TO,
        confidence=0.85,
        source="analysis"
    ))
    
    return builder
