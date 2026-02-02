"""
Pipeline complet - VERSION MONOFILE (sans imports complexes)
Toutes les classes dans un seul fichier pour éviter les problèmes d'import
"""

import sys
import os
import pandas as pd
import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path

# ============================================================================
# CLASSE 1 : Entités
# ============================================================================

class EntityType(Enum):
    """Types d'entités supportées dans le graphe."""
    COMPANY = "company"
    PERSON = "person"
    EVENT = "event"
    RISK = "risk"
    ASSET = "asset"
    TRANSACTION = "transaction"


@dataclass
class Entity:
    """Classe représentant une entité dans le graphe de connaissances."""
    id: str
    type: EntityType
    text: str
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "text": self.text,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


# ============================================================================
# CLASSE 2 : Relations
# ============================================================================

class RelationType(Enum):
    """Types de relations supportées dans le graphe."""
    INVOLVED_IN = "impliquée_dans"
    CAUSED_BY = "causée_par"
    TRIGGERED_BY = "déclenchée_par"
    EXPOSED_TO = "exposée_à"
    PROPAGATES_TO = "se_propage_à"
    ASSOCIATED_WITH = "associée_avec"
    OWNS = "possède"
    AFFILIATED_WITH = "affiliée_à"
    PRECEDES = "précède"
    FOLLOWS = "suit"
    INCREASES_RISK = "augmente_risque"
    MITIGATES_RISK = "atténue_risque"


@dataclass
class Relation:
    """Classe représentant une relation entre deux entités."""
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relation_type: RelationType
    confidence: float
    source: str
    timestamp: str = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "relation_type": self.relation_type.value,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


# ============================================================================
# CLASSE 3 : Constructeur du Graphe
# ============================================================================

class KnowledgeGraphBuilder:
    """Construit et gère le graphe de connaissances financier."""
    
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
    
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
    
    def add_relation(self, relation: Relation) -> None:
        """Ajoute une relation au graphe."""
        self.relations.append(relation)
    
    def build_graph_dict(self) -> Dict:
        """Construit une représentation dictionnaire du graphe."""
        nodes = [
            {
                "id": e.id,
                "label": e.text,
                "type": e.type.name,
                "metadata": e.metadata
            }
            for e in self.entities.values()
        ]
        
        edges = [
            {
                "source": r.source_id,
                "target": r.target_id,
                "type": r.relation_type.value,
                "confidence": r.confidence,
                "source_type": r.source_type,
                "target_type": r.target_type,
            }
            for r in self.relations
        ]
        
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
    
    def save_relations_csv(self, filename: str = "relations.csv") -> Path:
        """Sauvegarde les relations au format CSV."""
        relations_data = [
            {
                "source_id": r.source_id,
                "source_type": r.source_type,
                "relation_type": r.relation_type.value,
                "target_id": r.target_id,
                "target_type": r.target_type,
                "confidence": r.confidence,
                "source": r.source,
            }
            for r in self.relations
        ]
        
        df = pd.DataFrame(relations_data)
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"✓ Relations sauvegardées : {output_path}")
        return output_path
    
    def save_entities_csv(self, filename: str = "entities.csv") -> Path:
        """Sauvegarde les entités au format CSV."""
        entities_data = [
            {
                "entity_id": e.id,
                "entity_type": e.type.name,
                "entity_text": e.text,
                "created_at": e.created_at
            }
            for e in self.entities.values()
        ]
        
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


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 PIPELINE COMPLET DE GRAPHE DE CONNAISSANCES FINANCIER")
    print("="*70)
    
    # ÉTAPES 1-2 : DONNÉES D'EXEMPLE
    print("\n📊 ÉTAPE 1-2 : PRÉPARATION DES DONNÉES")
    print("-"*70)
    
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    articles_data = {
        "Entreprise": ["BNP Paribas", "Société Générale", "Crédit Agricole", "AXA", "TotalEnergies",
                       "BNP Paribas", "Société Générale", "Orange", "Airbus", "LVMH"],
        "Ticker": ["BNP.PA", "GLE.PA", "ACA.PA", "CS.PA", "TTE.PA",
                   "BNP.PA", "GLE.PA", "ORA.PA", "AIR.PA", "MC.PA"],
        "Date": [datetime(2026, 1, 15+i).date() for i in range(10)],
        "Article": [
            "BNP Paribas dénonce une cyberattaque majeure affectant ses systèmes",
            "Société Générale subit une perte de 50 millions dans une fraude interne",
            "Crédit Agricole : nouveau scandale de conformité détecté",
            "AXA annonce une hausse de ses réserves suite à une catastrophe naturelle",
            "TotalEnergies face à de nouvelles sanctions environnementales",
            "BNP Paribas lance une enquête après la fuite de données client",
            "Société Générale déclare un risque opérationnel majeur",
            "Orange : rupture de service dans le réseau fibre optique",
            "Airbus confronté à une disruption majeure de sa chaîne d'approvisionnement",
            "LVMH : associée à BNP Paribas dans le scandale de cyberattaque",
        ],
        "Variation (%)": [-3.2, -2.1, -1.5, -0.8, -2.5, -1.9, -1.3, -0.5, -2.8, -0.3],
        "Impact": ["Baisse (événement à risque)"] * 10,
        "Source": ["News Financial", "Bloomberg", "Reuters", "Reuters", "AFP", "News Financial", "Bloomberg", "Reuters", "AFP", "Reuters"]
    }
    
    linked_df = pd.DataFrame(articles_data)
    linked_df.to_csv("data/raw/article_price_links.csv", index=False)
    print(f"✓ {len(linked_df)} articles créés")
    
    # ÉTAPE 3 : NETTOYAGE
    print("\n🧹 ÉTAPE 3 : NETTOYAGE")
    print("-"*70)
    
    cleaned_df = linked_df.drop_duplicates(subset=["Entreprise", "Date", "Article"])
    cleaned_df["Date"] = pd.to_datetime(cleaned_df["Date"])
    cleaned_df = cleaned_df.dropna(subset=["Entreprise", "Article"])
    cleaned_df["Article"] = cleaned_df["Article"].str.strip()
    cleaned_df.to_csv("data/processed/cleaned_financial_data.csv", index=False)
    print(f"✓ {len(cleaned_df)} lignes après nettoyage")
    
    # ÉTAPE 4 : EXTRACTION D'ENTITÉS
    print("\n🔍 ÉTAPE 4 : EXTRACTION D'ENTITÉS")
    print("-"*70)
    
    entities_list = []
    entity_id_counter = 0
    
    for company in cleaned_df["Entreprise"].unique():
        entity_id_counter += 1
        entities_list.append({
            "entity_id": f"COMPANY_{entity_id_counter}",
            "entity_type": "COMPANY",
            "entity_text": company,
            "source": "data_source"
        })
        print(f"   ✓ {company}")
    
    for idx, article in enumerate(cleaned_df["Article"].unique(), 1):
        entity_id_counter += 1
        entities_list.append({
            "entity_id": f"EVENT_{entity_id_counter}",
            "entity_type": "EVENT",
            "entity_text": article[:100],
            "source": "news_article"
        })
    
    risk_keywords = {
        "RISK_OPERATIONAL": ["cyberattaque", "hack", "panne", "disruption"],
        "RISK_REPUTATION": ["scandale", "fraude", "affaire"],
        "RISK_LEGAL": ["sanction", "amende", "compliance"],
    }
    
    created_risks = set()
    for risk_type, keywords in risk_keywords.items():
        for keyword in keywords:
            if any(keyword in article.lower() for article in cleaned_df["Article"]) and risk_type not in created_risks:
                entities_list.append({
                    "entity_id": risk_type,
                    "entity_type": "RISK",
                    "entity_text": f"Risque : {keyword}",
                    "source": "keyword_detection"
                })
                print(f"   ✓ {risk_type}")
                created_risks.add(risk_type)
    
    entities_df = pd.DataFrame(entities_list)
    entities_df.to_csv("data/processed/extracted_entities.csv", index=False)
    print(f"✓ {len(entities_df)} entités extraites")
    
    # ÉTAPES 5-6 : RELATIONS ET GRAPHE
    print("\n🔗 ÉTAPES 5-6 : RELATIONS ET GRAPHE")
    print("-"*70)
    
    builder = KnowledgeGraphBuilder(output_dir="data/processed")
    
    # Ajouter les entités
    for _, entity_row in entities_df.iterrows():
        entity_type = EntityType[entity_row["entity_type"]]
        builder.add_entity(
            entity_id=entity_row["entity_id"],
            entity_type=entity_type,
            text=entity_row["entity_text"],
            metadata={"source": entity_row["source"]}
        )
    
    print(f"✓ {len(builder.entities)} entités ajoutées au graphe")
    
    # Créer les relations
    companies_entities = entities_df[entities_df["entity_type"] == "COMPANY"]
    events_entities = entities_df[entities_df["entity_type"] == "EVENT"]
    risk_entities = entities_df[entities_df["entity_type"] == "RISK"]
    
    relations_count = 0
    
    # Relation 1 : Entreprise → impliquée dans → Événement
    for _, company in companies_entities.iterrows():
        for _, event in events_entities.iterrows():
            if company["entity_text"].lower() in event["entity_text"].lower():
                builder.add_relation(Relation(
                    source_id=company["entity_id"],
                    source_type="COMPANY",
                    target_id=event["entity_id"],
                    target_type="EVENT",
                    relation_type=RelationType.INVOLVED_IN,
                    confidence=0.85,
                    source="text_matching"
                ))
                relations_count += 1
    
    # Relation 2 : Événement → cause → Risque
    for _, event in events_entities.iterrows():
        for _, risk in risk_entities.iterrows():
            risk_keyword = risk["entity_text"].lower().split(": ")[-1]
            if risk_keyword in event["entity_text"].lower():
                builder.add_relation(Relation(
                    source_id=event["entity_id"],
                    source_type="EVENT",
                    target_id=risk["entity_id"],
                    target_type="RISK",
                    relation_type=RelationType.CAUSED_BY,
                    confidence=0.80,
                    source="keyword_analysis"
                ))
                relations_count += 1
    
    # Relation 3 : Risque → se propage à → Entreprise
    for _, risk in risk_entities.iterrows():
        for _, company in companies_entities.iterrows():
            builder.add_relation(Relation(
                source_id=risk["entity_id"],
                source_type="RISK",
                target_id=company["entity_id"],
                target_type="COMPANY",
                relation_type=RelationType.PROPAGATES_TO,
                confidence=0.70,
                source="propagation_model"
            ))
            relations_count += 1
    
    print(f"✓ {relations_count} relations créées")
    
    # SAUVEGARDE
    print("\n💾 SAUVEGARDE DU GRAPHE")
    print("-"*70)
    
    builder.save_graph_json("knowledge_graph.json")
    builder.save_relations_csv("relations.csv")
    builder.save_entities_csv("entities.csv")
    
    # STATISTIQUES
    builder.print_statistics()
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLET TERMINÉ AVEC SUCCÈS !")
    print("="*70)
    print("\n📁 Fichiers générés :")
    print("   • data/processed/cleaned_financial_data.csv")
    print("   • data/processed/extracted_entities.csv")
    print("   • data/processed/knowledge_graph.json")
    print("   • data/processed/relations.csv")
    print("   • data/processed/entities.csv")
