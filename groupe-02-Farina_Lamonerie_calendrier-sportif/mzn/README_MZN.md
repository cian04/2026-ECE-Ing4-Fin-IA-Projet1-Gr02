# MiniZinc — Optimisation du calendrier

Ce dossier contient le modèle MiniZinc utilisé pour améliorer le calendrier généré par CP-SAT.

Fichier principal :

refine.mzn



## Objectif

MiniZinc sert à :

- Choisir l’orientation domicile / extérieur des matchs
- Respecter des contraintes sportives avancées
- Optimiser la qualité du calendrier



## Données en entrée

Le modèle reçoit :

- D : nombre de journées  
- T : nombre d’équipes  
- M : matchs par journée  

- match[d,m,1..2] : paires d’équipes par journée (sans orientation)

- unavailable_home[t,d] : 1 si l’équipe t ne peut pas jouer à domicile le jour d

- dist[i,j] : distance entre les villes des équipes



## Paramètres principaux

- MAX_AWAY : max matchs consécutifs à l’extérieur  
- MAX_HOME : max matchs consécutifs à domicile  
- MAX_CONSEC_AWAY_TRAVEL : distance max entre deux déplacements consécutifs  
- BIG : poids pour prioriser les breaks



## Variables importantes

- orient[d,m] : choix domicile / extérieur  
- is_home[t,d] : statut domicile d’une équipe  
- location[t,d] : ville où joue une équipe



## Contraintes appliquées

- Indisponibilités de stade respectées  
- Séries max domicile / extérieur limitées  
- Équilibre domicile / extérieur  
- Déplacements consécutifs pas trop longs  



## Optimisation

Fonction objectif :

objectif = total_breaks × BIG + total_distance  

→ priorité à la réduction des breaks  
→ puis réduction de la distance totale



## Résultat

MiniZinc renvoie un JSON :

{
  "total_breaks": ...,
  "total_distance": ...,
  "orient": [...]
}

Ce résultat est utilisé par Python pour reconstruire le calendrier final.



## Intérêt

- Gestion simple de contraintes complexes  
- Amélioration forte du calendrier  
- Complémentaire à CP-SAT
