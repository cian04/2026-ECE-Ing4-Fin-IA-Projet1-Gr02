"""
Module de définition des entités dans le graphe de connaissances financier.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


class EntityType(Enum):
    """Types d'entités supportées dans le graphe."""
    
    COMPANY = "company"           # Entreprises, banques, fonds
    PERSON = "person"             # Individus (CEO, traders, fraudeurs)
    EVENT = "event"               # Événements (faillites, cyberattaques, mergers)
    RISK = "risk"                 # Risques (opérationnel, crédit, systémique)
    ASSET = "asset"               # Actifs financiers (actions, obligations, crypto)
    TRANSACTION = "transaction"   # Transactions, flux financiers


@dataclass
class Entity:
    """Classe représentant une entité dans le graphe de connaissances."""
    
    id: str                        # Identifiant unique
    type: EntityType               # Type d'entité
    text: str                      # Représentation textuelle
    metadata: Dict = field(default_factory=dict)  # Métadonnées additionnelles
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __hash__(self):
        """Permet l'utilisation de l'entité comme clé de dictionnaire."""
        return hash(self.id)
    
    def __eq__(self, other):
        """Comparaison d'entités par ID."""
        if isinstance(other, Entity):
            return self.id == other.id
        return False
    
    def to_dict(self) -> Dict:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "type": self.type.value,
            "text": self.text,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    def get_attribute(self, key: str, default=None):
        """Récupère une valeur de métadonnée."""
        return self.metadata.get(key, default)
    
    def set_attribute(self, key: str, value):
        """Définit une valeur de métadonnée."""
        self.metadata[key] = value


class EntityFactory:
    """Factory pour créer des entités avec des paramètres prédéfinis."""
    
    @staticmethod
    def create_company(company_id: str, name: str, sector: str = None, 
                      country: str = None) -> Entity:
        """Crée une entité entreprise."""
        metadata = {}
        if sector:
            metadata["sector"] = sector
        if country:
            metadata["country"] = country
        
        return Entity(
            id=company_id,
            type=EntityType.COMPANY,
            text=name,
            metadata=metadata
        )
    
    @staticmethod
    def create_event(event_id: str, description: str, date: str = None, 
                    severity: str = None) -> Entity:
        """Crée une entité événement."""
        metadata = {}
        if date:
            metadata["date"] = date
        if severity:
            metadata["severity"] = severity
        
        return Entity(
            id=event_id,
            type=EntityType.EVENT,
            text=description,
            metadata=metadata
        )
    
    @staticmethod
    def create_risk(risk_id: str, description: str, category: str = None) -> Entity:
        """Crée une entité risque."""
        metadata = {}
        if category:
            metadata["category"] = category
        
        return Entity(
            id=risk_id,
            type=EntityType.RISK,
            text=description,
            metadata=metadata
        )
    
    @staticmethod
    def create_person(person_id: str, name: str, role: str = None, 
                     affiliation: str = None) -> Entity:
        """Crée une entité personne."""
        metadata = {}
        if role:
            metadata["role"] = role
        if affiliation:
            metadata["affiliation"] = affiliation
        
        return Entity(
            id=person_id,
            type=EntityType.PERSON,
            text=name,
            metadata=metadata
        )
