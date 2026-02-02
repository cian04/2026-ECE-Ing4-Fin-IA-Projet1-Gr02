"""
Neo4j loader for the Financial Knowledge Graph

Reads `data/processed/knowledge_graph.json` and writes nodes and edges to Neo4j.

Usage (example):

# set env vars (Windows PowerShell)
$env:NEO4J_URI = 'bolt://localhost:7687'
$env:NEO4J_USER = 'neo4j'
$env:NEO4J_PASSWORD = 'password'

python -m knowledge_graph.neo4j_loader --file ../../data/processed/knowledge_graph.json --batch 200

Notes:
- Uses official `neo4j` Python driver (install: `pip install neo4j`).
- Creates constraints (uniqueness) on node `id` property.
"""

import os
import json
import argparse
from pathlib import Path
try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None  # allow dry-run/validation without neo4j installed
from typing import Dict, Any, List


def validate_graph_json(graph_json_path: Path) -> Dict[str, int]:
    """Load and validate the graph JSON file. Returns counts summary."""
    with open(graph_json_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    nodes = graph.get('nodes')
    edges = graph.get('edges')

    if nodes is None or edges is None:
        raise ValueError('Invalid graph JSON: missing "nodes" or "edges" keys')

    # Basic structural checks
    sample_node = nodes[0] if nodes else None
    sample_edge = edges[0] if edges else None

    print(f"✓ JSON loaded: {len(nodes)} nodes, {len(edges)} edges")
    if sample_node:
        print(f"  • Exemple nœud: id={sample_node.get('id')}, label={sample_node.get('label')}, type={sample_node.get('type')}")
    if sample_edge:
        print(f"  • Exemple arête: source={sample_edge.get('source')}, target={sample_edge.get('target')}, type={sample_edge.get('type')}, confidence={sample_edge.get('confidence')}")

    return {'nodes': len(nodes), 'edges': len(edges)}


def _create_constraints(tx):
    # Create uniqueness constraint on :Entity(id)
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")


def _create_node_tx(tx, node: Dict[str, Any]):
    # parameterized merge to avoid duplicates
    cypher = (
        "MERGE (n:Entity {id: $id})\n"
        "SET n.label = $label, n.type = $type, n.metadata = $metadata"
    )
    tx.run(cypher, id=node.get("id"), label=node.get("label"), type=node.get("type"), metadata=node.get("metadata", {}))


def _create_relation_tx(tx, rel: Dict[str, Any]):
    cypher = (
        "MATCH (a:Entity {id: $source}) MATCH (b:Entity {id: $target})\n"
        "MERGE (a)-[r:RELATION {type: $type, confidence: $confidence}]-(b)\n"
        "SET r.source = $src, r.target_type = $target_type, r.source_type = $source_type, r.metadata = $metadata"
    )
    tx.run(
        cypher,
        source=rel.get("source"),
        target=rel.get("target"),
        type=rel.get("type"),
        confidence=float(rel.get("confidence", 0.0)),
        src=rel.get("source_type"),
        target_type=rel.get("target_type"),
        source_type=rel.get("source_type"),
        metadata=rel.get("metadata", {}),
    )


def load_graph_to_neo4j(uri: str, user: str, password: str, graph_json_path: Path, batch_size: int = 200):
    try:
        if GraphDatabase is None:
            raise RuntimeError("Neo4j Python driver not installed. Install with `pip install neo4j` to run an actual upload.")
        driver = GraphDatabase.driver(uri, auth=(user, password))
    except Exception as e:
        print(f"ERROR: could not create Neo4j driver: {e}")
        raise

    print(f"Connecting to Neo4j at {uri} as {user}")

    try:
        with driver.session() as session:
            # Create constraints
            session.write_transaction(_create_constraints)
            print("✓ Uniqueness constraint ensured on :Entity(id)")

            # Load JSON
            with open(graph_json_path, 'r', encoding='utf-8') as f:
                graph = json.load(f)

            nodes = graph.get('nodes', [])
            edges = graph.get('edges', [])

            print(f"Found {len(nodes)} nodes and {len(edges)} edges in JSON")

            # Insert nodes in batches
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i+batch_size]
                def create_nodes(tx):
                    for n in batch:
                        _create_node_tx(tx, n)
                session.write_transaction(create_nodes)
                print(f"  - Inserted nodes {i+1}..{i+len(batch)}")

            # Insert relations in batches
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i+batch_size]
                def create_rels(tx):
                    for e in batch:
                        rel = {
                            'source': e.get('source'),
                            'target': e.get('target'),
                            'type': e.get('type'),
                            'confidence': e.get('confidence', 0.0),
                            'source_type': e.get('source_type'),
                            'target_type': e.get('target_type'),
                            'metadata': e.get('metadata', {})
                        }
                        _create_relation_tx(tx, rel)
                session.write_transaction(create_rels)
                print(f"  - Inserted relations {i+1}..{i+len(batch)}")

    except Exception as exc:
        print(f"ERROR during upload: {exc}")
        raise
    finally:
        driver.close()

    print("✓ Upload complete")


def main():
    parser = argparse.ArgumentParser(description='Load knowledge_graph.json into Neo4j')
    parser.add_argument('--file', '-f', type=str, default='data/processed/knowledge_graph.json', help='Path to knowledge_graph.json')
    parser.add_argument('--batch', '-b', type=int, default=200, help='Batch size for writes')
    parser.add_argument('--dry-run', action='store_true', help='Validate JSON and print summary without connecting to Neo4j')
    parser.add_argument('--uri', type=str, default=os.getenv('NEO4J_URI'), help='Neo4j URI (bolt://host:7687)')
    parser.add_argument('--user', type=str, default=os.getenv('NEO4J_USER'), help='Neo4j user')
    parser.add_argument('--password', type=str, default=os.getenv('NEO4J_PASSWORD'), help='Neo4j password')

    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return

    # If requested, only validate the JSON and exit (no DB connection)
    if args.dry_run:
        try:
            validate_graph_json(path)
            print("Dry-run validation successful. No DB operations performed.")
        except Exception as e:
            print(f"ERROR during dry-run validation: {e}")
        return

    if not args.uri or not args.user or not args.password:
        print("ERROR: please set NEO4J_URI, NEO4J_USER and NEO4J_PASSWORD environment variables or pass --uri,--user,--password")
        return

    load_graph_to_neo4j(args.uri, args.user, args.password, path, args.batch)


if __name__ == '__main__':
    main()
