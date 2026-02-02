"""
Risk Propagation Algorithm via BFS with Exponential Decay

Propagates risk through a knowledge graph:
- Starts from RISK-type nodes (sources)
- Flows to neighbors with decay factor (risk diminishes with distance)
- Uses BFS for breadth-first exploration
- Saves results to Neo4j and CSV

Key Concepts:
  - decay: How much risk is lost per hop (0.7 = 30% loss per step)
  - max_depth: How far to propagate (default 4 hops)
  - min_score: Ignore if risk below threshold (avoid noise)
  
Example:
  propagator = RiskPropagator(driver, decay=0.7, max_depth=4)
  scores = propagator.propagate_from_risk_nodes()
  propagator.save_to_neo4j(scores)
"""

from collections import deque, defaultdict
from neo4j import GraphDatabase
import pandas as pd
from typing import Dict, List


class RiskPropagator:
    """
    Propagate risk through a Neo4j knowledge graph using BFS with decay.
    """
    
    def __init__(self, uri: str, user: str, password: str, 
                 decay: float = 0.7, max_depth: int = 4, min_score: float = 0.01):
        """
        Initialize propagator connected to Neo4j.
        
        Args:
            uri: Neo4j Bolt URI (e.g., 'bolt://localhost:7687')
            user: Neo4j username
            password: Neo4j password
            decay: Decay factor per hop (0 < decay <= 1)
            max_depth: Maximum propagation distance
            min_score: Ignore scores below this threshold
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.decay = decay
        self.max_depth = max_depth
        self.min_score = min_score
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """Close the driver connection."""
        self.driver.close()
    
    def _fetch_adjacency_from_neo4j(self):
        """
        Load entire graph adjacency list from Neo4j.
        
        Returns:
            Dict {node_id: [neighbor_ids]} (undirected)
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Entity)-[r]-(b:Entity)
                RETURN a.id AS src, b.id AS dst
            """)
            
            graph = defaultdict(set)
            for record in result:
                src, dst = record['src'], record['dst']
                graph[src].add(dst)
                graph[dst].add(src)  # Undirected (risk flows both ways)
            
            # Convert sets to lists for compatibility
            return {k: list(v) for k, v in graph.items()}
    
    def _fetch_risk_nodes(self):
        """
        Fetch all RISK-type entities from Neo4j.
        
        Returns:
            List of entity IDs with type='RISK'
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Entity {type:'RISK'})
                RETURN r.id AS id
            """)
            return [record['id'] for record in result]
    
    def _fetch_all_nodes(self):
        """
        Fetch all entities from Neo4j.
        
        Returns:
            List of dicts {id, label, type}
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.id AS id, e.label AS label, e.type AS type
            """)
            return [dict(record) for record in result]
    
    def propagate_from_risk_nodes(self, start_score: float = 1.0) -> Dict[str, float]:
        """
        Propagate risk from all RISK-type nodes across the graph.
        
        Args:
            start_score: Initial risk score for RISK nodes (default 1.0 = 100%)
        
        Returns:
            Dict {entity_id: final_risk_score}
        """
        print("\n📊 PROPAGATION DE RISQUE")
        print("=" * 60)
        
        # Fetch graph and sources
        print("[1/3] Chargement du graphe depuis Neo4j...")
        graph = self._fetch_adjacency_from_neo4j()
        print(f"  ✓ {len(graph)} nœuds dans le graphe")
        
        print("[2/3] Identification des sources (nœuds RISK)...")
        risk_nodes = self._fetch_risk_nodes()
        if not risk_nodes:
            print("  ⚠️  Aucun nœud RISK trouvé. Aborting.")
            return {}
        print(f"  ✓ {len(risk_nodes)} sources: {risk_nodes}")
        
        # BFS propagation
        print(f"[3/3] Propagation (decay={self.decay}, max_depth={self.max_depth})...")
        scores = {}
        queue = deque()
        
        # Initialize with RISK nodes
        for node_id in risk_nodes:
            scores[node_id] = start_score
            queue.append((node_id, start_score, 0))
        
        # BFS loop
        steps = 0
        while queue:
            node, score, depth = queue.popleft()
            steps += 1
            
            # Stop if max depth reached
            if depth >= self.max_depth:
                continue
            
            # Calculate next score
            next_score = score * self.decay
            if next_score < self.min_score:
                continue
            
            # Propagate to neighbors
            for neighbor in graph.get(node, []):
                if neighbor not in scores or next_score > scores[neighbor]:
                    scores[neighbor] = next_score
                    queue.append((neighbor, next_score, depth + 1))
        
        print(f"  ✓ {len(scores)} nœuds affectés, {steps} étapes")
        
        # Stats
        if scores:
            min_score = min(scores.values())
            max_score = max(scores.values())
            print(f"\n  Statistiques:")
            print(f"    - Score min/max: {min_score:.4f} / {max_score:.4f}")
            
            top_10 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"    - Top 10 risques:")
            nodes_info = {n['id']: n for n in self._fetch_all_nodes()}
            for i, (nid, score) in enumerate(top_10, 1):
                label = nodes_info.get(nid, {}).get('label', nid)
                print(f"        {i:2d}. {label:30s} [{score:.4f}]")
        
        return scores
    
    def save_to_neo4j(self, scores: Dict[str, float]):
        """
        Write risk scores back to Neo4j as entity.risk_score property.
        
        Args:
            scores: Dict {entity_id: score}
        """
        print("\n💾 SAUVEGARDE DANS NEO4J")
        print("=" * 60)
        
        with self.driver.session() as session:
            # First, reset all scores (optional)
            session.run("MATCH (e:Entity) SET e.risk_score = null")
            
            # Batch write scores
            batch_size = 100
            for i in range(0, len(scores), batch_size):
                batch = dict(list(scores.items())[i:i+batch_size])
                session.run("""
                    UNWIND $data AS item
                    MATCH (e:Entity {id: item.id})
                    SET e.risk_score = item.score
                """, data=[{'id': nid, 'score': float(score)} for nid, score in batch.items()])
                print(f"  ✓ {min(i+batch_size, len(scores))}/{len(scores)} scores écrits")
        
        print(f"✅ {len(scores)} scores écrits dans Neo4j")
    
    def export_to_csv(self, scores: Dict[str, float], output_path: str):
        """
        Export risk scores to CSV.
        
        Args:
            scores: Dict {entity_id: score}
            output_path: File path for CSV output
        """
        print("\n📄 EXPORT EN CSV")
        print("=" * 60)
        
        # Fetch node metadata
        nodes_info = self._fetch_all_nodes()
        node_map = {n['id']: n for n in nodes_info}
        
        # Build DataFrame
        data = []
        for entity_id, score in scores.items():
            node = node_map.get(entity_id, {})
            data.append({
                'entity_id': entity_id,
                'entity_label': node.get('label', ''),
                'entity_type': node.get('type', ''),
                'risk_score': float(score)
            })
        
        df = pd.DataFrame(data).sort_values('risk_score', ascending=False)
        
        # Save
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"  ✓ {len(df)} lignes écrites")
        print(f"  ✓ Fichier: {output_path}")
