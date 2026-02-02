"""
Module de définition des types de relations dans le graphe de connaissances financier.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict


class RelationType(Enum):
    """Types de relations supportées dans le graphe."""
    
    # Relations entité-événement
    INVOLVED_IN = "impliquée_dans"  # Entreprise -> impliquée dans -> Événement
    CAUSED_BY = "causée_par"         # Risque -> causée par -> Événement
    CAUSES = "cause"                  # Événement -> cause -> Risque
    TRIGGERED_BY = "déclenchée_par"  # Événement -> déclenchée par -> Événement
    
    # Relations entité-risque
    EXPOSED_TO = "exposée_à"         # Entreprise -> exposée à -> Risque
    PROPAGATES_TO = "se_propage_à"   # Risque -> se propage à -> Entreprise
    
    # Relations entité-entité
    ASSOCIATED_WITH = "associée_avec" # Entreprise -> associée avec -> Entreprise
    OWNS = "possède"                  # Entreprise -> possède -> Entreprise
    AFFILIATED_WITH = "affiliée_à"    # Personne -> affiliée à -> Entreprise
    
    # Relations temporelles
    PRECEDES = "précède"              # Événement -> précède -> Événement
    FOLLOWS = "suit"                  # Événement -> suit -> Événement
    
    # Relations de causalité
    INCREASES_RISK = "augmente_risque" # Événement -> augmente risque -> Risque
    MITIGATES_RISK = "atténue_risque"  # Événement -> atténue risque -> Risque


@dataclass
class Relation:
    """Classe représentant une relation entre deux entités."""
    
    source_id: str
    source_type: str  # "COMPANY", "PERSON", "EVENT", "RISK"
    target_id: str
    target_type: str
    relation_type: RelationType
    confidence: float  # Score de confiance entre 0 et 1
    source: str  # Source de la relation (ex: "news_article", "extraction")
    timestamp: str = None  # Date de découverte/publication
    metadata: Dict = None  # Données additionnelles
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convertit la relation en dictionnaire."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "relation_type": self.relation_type.value,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class RelationExtractor:
    """Extrait les relations entre entités selon des règles simples."""
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict:
        """Initialise les règles de relation."""
        return {
            # Règles événement -> risque
            "bankruptcy": {
                "keywords": ["faillite", "insolvabilité", "liquidation"],
                "relations": [
                    (RelationType.CAUSED_BY, "RISK_CREDIT"),
                    (RelationType.CAUSES, "RISK_SYSTEMIC")
                ]
            },
            "fraud": {
                "keywords": ["fraude", "escroquerie", "manipulation"],
                "relations": [
                    (RelationType.CAUSED_BY, "RISK_LEGAL"),
                    (RelationType.CAUSES, "RISK_REPUTATION")
                ]
            },
            "cyber_incident": {
                "keywords": ["cyberattaque", "hack", "données volées", "ransomware"],
                "relations": [
                    (RelationType.CAUSED_BY, "RISK_OPERATIONAL"),
                    (RelationType.CAUSES, "RISK_REPUTATION")
                ]
            },
            "regulatory_fine": {
                "keywords": ["amende", "sanction", "régulation", "compliance"],
                "relations": [
                    (RelationType.CAUSED_BY, "RISK_LEGAL"),
                    (RelationType.INCREASES_RISK, "RISK_FINANCIAL")
                ]
            },
            "supply_chain_disruption": {
                "keywords": ["chaîne d'approvisionnement", "disruption", "rupture"],
                "relations": [
                    (RelationType.PROPAGATES_TO, "RISK_OPERATIONAL"),
                    (RelationType.TRIGGERED_BY, "RISK_SYSTEMIC")
                ]
            }
        }
    
    def extract_relations(self, entities: List[Dict], texts: List[str]) -> List[Relation]:
        """
        Extrait les relations entre entités à partir de textes.
        
        Args:
            entities: Liste des entités (avec id, type, texte)
            texts: Liste des textes sources
        
        Returns:
            Liste des relations découvertes
        """
        relations = []
        
        # Exemple de relations simples basées sur le type d'entité
        entity_map = {e["id"]: e for e in entities}
        
        for text in texts:
            text_lower = text.lower()
            
            # Pour chaque règle, chercher les mots-clés dans le texte
            for event_type, rule_config in self.rules.items():
                if any(kw in text_lower for kw in rule_config["keywords"]):
                    # Créer des relations pour chaque entité EVENT/COMPANY trouvée
                    for entity in entities:
                        if entity["type"] in ["EVENT", "COMPANY"]:
                            # Relation : Événement -> cause -> Risque
                            for rel_type, risk_type in rule_config["relations"]:
                                rel = Relation(
                                    source_id=entity["id"],
                                    source_type=entity["type"],
                                    target_id=f"RISK_{risk_type}_{entity['id']}",
                                    target_type="RISK",
                                    relation_type=rel_type,
                                    confidence=0.8,
                                    source="text_analysis",
                                    metadata={"event_type": event_type}
                                )
                                relations.append(rel)
        
        # Ajouter relations simples : Entreprise -> impliquée dans -> Événement
        companies = [e for e in entities if e["type"] == "COMPANY"]
        events = [e for e in entities if e["type"] == "EVENT"]
        
        for company in companies:
            for event in events:
                # Heuristique : si l'événement contient le nom de l'entreprise
                if company["text"].lower() in event["text"].lower():
                    rel = Relation(
                        source_id=company["id"],
                        source_type="COMPANY",
                        target_id=event["id"],
                        target_type="EVENT",
                        relation_type=RelationType.INVOLVED_IN,
                        confidence=0.85,
                        source="entity_matching"
                    )
                    relations.append(rel)
        
        return relations


def get_relation_description(rel_type: RelationType) -> str:
    """Retourne une description lisible d'un type de relation."""
    descriptions = {
        RelationType.INVOLVED_IN: "est impliquée dans",
        RelationType.CAUSED_BY: "est causée par",
        RelationType.EXPOSED_TO: "est exposée à",
        RelationType.PROPAGATES_TO: "se propage à",
        RelationType.ASSOCIATED_WITH: "est associée avec",
        RelationType.INCREASES_RISK: "augmente le risque de",
    }
    return descriptions.get(rel_type, str(rel_type))
