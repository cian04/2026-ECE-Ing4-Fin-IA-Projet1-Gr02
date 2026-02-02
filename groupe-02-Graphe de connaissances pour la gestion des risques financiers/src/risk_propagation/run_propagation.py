#!/usr/bin/env python
"""
Execute Risk Propagation - Step 8

Connects to Neo4j, propagates risk from RISK nodes, saves scores.
"""

import os
import sys
import argparse
from pathlib import Path

# 🔧 Fix import path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.append(str(CURRENT_DIR))

from propagator import RiskPropagator


def main():
    parser = argparse.ArgumentParser(description="Run risk propagation on Neo4j graph")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument("--decay", type=float, default=0.7)
    parser.add_argument("--max-depth", type=int, default=4)

    args = parser.parse_args()

    if not args.password:
        print("❌ NEO4J_PASSWORD manquant")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ÉTAPE 8 — PROPAGATION DU RISQUE")
    print("=" * 60)

    propagator = RiskPropagator(
        uri=args.uri,
        user=args.user,
        password=args.password,
        decay=args.decay,
        max_depth=args.max_depth
    )

    try:
        # 🔁 Propagation
        scores = propagator.propagate_from_risk_nodes(start_score=1.0)

        if not scores:
            print("❌ Aucun score généré")
            return

        # 💾 Sauvegarde Neo4j
        propagator.save_to_neo4j(scores)

        # 💾 Sauvegarde CSV
        output_csv = Path("knowledgeGraph/data/processed/risk_scores.csv")
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        propagator.export_to_csv(scores, str(output_csv))

        print("\n✅ Propagation terminée")
        print(f"→ {len(scores)} nœuds scorés")
        print(f"→ CSV : {output_csv}")

    finally:
        propagator.close()


if __name__ == "__main__":
    main()
