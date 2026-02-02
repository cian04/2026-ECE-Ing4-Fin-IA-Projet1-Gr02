from pathlib import Path
import json
from neo4j import GraphDatabase

# =====================================================
# CHEMINS
# =====================================================
BASE_DIR = Path(__file__).resolve().parents[2]   # knowledgeGraph/
DATA_PATH = BASE_DIR / "data" / "processed" / "knowledge_graph.json"

# =====================================================
# CONNEXION NEO4J
# =====================================================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Neogeo124"  # ⚠️ mets TON mot de passe

# =====================================================
# MAIN
# =====================================================
def main():

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {DATA_PATH}")

    # Charger le graphe JSON généré par le monofichier
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes = graph["nodes"]
    edges = graph["edges"]

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    with driver.session() as session:

        # 🔥 Nettoyage base
        session.run("MATCH (n) DETACH DELETE n")

        # =====================================================
        # CRÉATION DES NOEUDS
        # =====================================================
        for node in nodes:
            session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.label = $label,
                    e.type = $type
                """,
                id=node["id"],
                label=node["label"],
                type=node["type"]
            )

        # =====================================================
        # CRÉATION DES RELATIONS (types réels)
        # =====================================================
        for edge in edges:
            relation_type = edge["type"]

            session.run(
                f"""
                MATCH (s:Entity {{id: $source}})
                MATCH (t:Entity {{id: $target}})
                MERGE (s)-[r:{relation_type}]->(t)
                SET r.confidence = $confidence
                """,
                source=edge["source"],
                target=edge["target"],
                confidence=edge["confidence"]
            )

    driver.close()
    print("✅ Export complet vers Neo4j terminé avec succès.")


if __name__ == "__main__":
    main()
