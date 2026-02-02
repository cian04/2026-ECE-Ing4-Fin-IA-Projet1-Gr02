"""
Neo4j Cypher Queries for Risk Visualization in Browser

Copie-colle les requêtes ci-dessous dans Neo4j Browser (http://localhost:7474)
pour visualiser le graphe de risque avec couleurs et tailles.
"""

# ===================================================================
# REQUÊTE 1: Visualiser le graphe complet (fonctionnel)
# ===================================================================
QUERY_1 = """
MATCH (e:Entity)-[r]-(o:Entity)
RETURN e AS node1, r AS relationship, o AS node2
LIMIT 100
"""

# ✅ FONCTIONNE: Affiche le graphe avec tous les nœuds colorés par type
# Dans Neo4j Browser, clique sur "Graph" pour voir la visualisation
# Les nœuds s'affichent colorés par type (RISK, COMPANY, EVENT, etc.)


# ===================================================================
# REQUÊTE 2: Top 10 risques avec voisins (TABLEAU - plus lisible)
# ===================================================================
QUERY_2 = """
MATCH (e:Entity) WHERE e.risk_score IS NOT NULL
RETURN e.label AS Entité, e.type AS Type, ROUND(e.risk_score, 4) AS Score_Risque
ORDER BY e.risk_score DESC
LIMIT 10
"""

# ✅ FONCTIONNE: Affiche un TABLEAU avec top 10 risques
# Clique sur "Table" pour voir les résultats lisibles


# ===================================================================
# REQUÊTE 3: Vue tableau - Top risques
# ===================================================================
QUERY_3 = """
MATCH (e:Entity) WHERE e.risk_score IS NOT NULL
RETURN 
    e.label AS Entité,
    e.type AS Type,
    ROUND(e.risk_score, 4) AS Score_Risque,
    CASE 
        WHEN e.risk_score >= 0.9 THEN 'CRITIQUE'
        WHEN e.risk_score >= 0.7 THEN 'ÉLEVÉ'
        WHEN e.risk_score >= 0.5 THEN 'MOYEN'
        WHEN e.risk_score >= 0.3 THEN 'BAS'
        ELSE 'MINIMAL'
    END AS Niveau
ORDER BY e.risk_score DESC
LIMIT 20
"""

# Affiche un tableau avec top risques et leur niveau de sévérité


# ===================================================================
# REQUÊTE 4: Statistiques par type
# ===================================================================
QUERY_4 = """
MATCH (e:Entity)
WHERE e.risk_score IS NOT NULL
RETURN 
    e.type AS Type,
    COUNT(*) AS Nombre,
    ROUND(MIN(e.risk_score), 4) AS Score_Min,
    ROUND(MAX(e.risk_score), 4) AS Score_Max,
    ROUND(AVG(e.risk_score), 4) AS Score_Moyen
ORDER BY Score_Moyen DESC
"""

# Vue tableau: résumé des risques par type d'entité


# ===================================================================
# REQUÊTE 5: Chemins de propagation (de RISK aux autres)
# ===================================================================
QUERY_5 = """
MATCH (risk:Entity {type:'RISK'})
MATCH path = (risk)-[*1..3]-(other:Entity)
WHERE other.type <> 'RISK'
RETURN path
ORDER BY length(path)
LIMIT 50
"""

# Affiche comment le risque s'est propagé depuis les nœuds RISK


# ===================================================================
# REQUÊTE 6: Distribution des scores (histogramme-like)
# ===================================================================
QUERY_6 = """
MATCH (e:Entity) WHERE e.risk_score IS NOT NULL
WITH 
    CASE 
        WHEN e.risk_score >= 0.9 THEN '0.9-1.0 (CRITIQUE)'
        WHEN e.risk_score >= 0.7 THEN '0.7-0.9 (ÉLEVÉ)'
        WHEN e.risk_score >= 0.5 THEN '0.5-0.7 (MOYEN)'
        WHEN e.risk_score >= 0.3 THEN '0.3-0.5 (BAS)'
        ELSE '0-0.3 (MINIMAL)'
    END AS Niveau
RETURN Niveau, COUNT(*) AS Nombre
ORDER BY Nombre DESC
"""

# Affiche la distribution des niveaux de risque


# ===================================================================
# REQUÊTE 7: Nœuds les plus connectés ET risqués
# ===================================================================
QUERY_7 = """
MATCH (e:Entity)-[r]-(other:Entity)
WHERE e.risk_score IS NOT NULL
WITH e, COUNT(r) AS degree, e.risk_score AS risk
ORDER BY degree DESC, risk DESC
LIMIT 15
MATCH (e)-[r]-(neighbor:Entity)
RETURN e, r, neighbor
"""

# Affiche les nœuds avec le plus de connexions + haut risque


# ===================================================================
# REQUÊTE 8: Clusters de risque (entities connectées par risque)
# ===================================================================
QUERY_8 = """
MATCH (e:Entity) WHERE e.risk_score >= 0.7
MATCH (e)-[r]-(neighbor:Entity) WHERE neighbor.risk_score >= 0.7
RETURN e, r, neighbor
"""

# Affiche les clusters de nœuds très risqués


print("""
📊 VISUALISATION DANS NEO4J BROWSER
====================================

1️⃣  GRAPHE COMPLET (Visualisation interactive):
   Copie cette requête dans http://localhost:7474
""")

print(QUERY_1)

print("""
2️⃣  TOP 10 RISQUES AVEC VOISINS:
""")
print(QUERY_2)

print("""
3️⃣  TABLEAU TOP RISQUES:
""")
print(QUERY_3)

print("""
4️⃣  STATISTIQUES PAR TYPE:
""")
print(QUERY_4)

print("""
5️⃣  CHEMINS DE PROPAGATION:
""")
print(QUERY_5)

print("""
6️⃣  DISTRIBUTION DES SCORES:
""")
print(QUERY_6)

print("""
7️⃣  NŒUDS LES PLUS CONNECTÉS + RISQUÉS:
""")
print(QUERY_7)

print("""
8️⃣  CLUSTERS TRÈS RISQUÉS:
""")
print(QUERY_8)

print("""
📝 INSTRUCTIONS:
================

1. Ouvre Neo4j Browser: http://localhost:7474
2. Authentifie-toi (neo4j / MavieVanelle123!)
3. Copie une requête ci-dessus dans l'éditeur
4. Appuie sur Play (▶️) ou Ctrl+Enter

CONSEILS:
- QUERY_1 donne la vue la plus complète (graphe interactif)
- QUERY_2 montre le focus sur top risques
- QUERY_3-6 donnent des vues tabulaires (statistiques)
- QUERY_7-8 montrent les clusters et connexions

Les nœuds s'affichent:
✓ Couleur: par type (RISK/COMPANY/EVENT/etc)
✓ Taille: pas native, mais tu vois les labels
✓ Position: layout algorithmique (spring)
""")
