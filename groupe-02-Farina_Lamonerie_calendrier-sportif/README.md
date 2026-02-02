# Génération de calendrier sportif — CP-SAT & MiniZinc

Projet d’optimisation de calendrier de championnat (type round-robin) réalisé dans le cadre du module IA / Programmation par contraintes.

L’objectif est de générer un calendrier de rencontres en respectant plusieurs contraintes sportives réalistes, puis de l’améliorer grâce à des techniques d’optimisation.



## Objectifs du projet

Nous cherchons à :

- Faire rencontrer chaque équipe exactement une fois (tournoi toutes rondes)
- Respecter des contraintes logistiques et d’équité
- Minimiser les « breaks » (deux matchs consécutifs à domicile ou à l’extérieur)
- Limiter les déplacements consécutifs trop longs
- Équilibrer les matchs domicile / extérieur



## Technologies utilisées

- OR-Tools CP-SAT (Python) : génération du calendrier de base
- MiniZinc : amélioration du calendrier (optimisation sous contraintes complexes)
- Streamlit : interface graphique interactive
- Python : orchestration et calcul des métriques



## Structure du projet

groupe-02-calendrier-sportif/

app.py                 Interface graphique Streamlit  
main.py                Version ligne de commande  

src/  
- cpsat_solver.py      Génération calendrier base (CP-SAT)  
- minizinc_refine.py  Lien Python ↔ MiniZinc  
- validate.py         Vérification et métriques  
- travel_metrics.py   Calcul des distances et déplacements  

mzn/  
- refine.mzn          Modèle MiniZinc principal  
- README.md           Explication du modèle MiniZinc  

data/  
- example_6teams.json  
- example_8cities.json  

requirements.txt  



## Installation

Créer un environnement virtuel :

python -m venv .venv

Activer :

Windows :  
.venv\Scripts\activate

Installer les dépendances :

pip install -r requirements.txt

Installer MiniZinc si nécessaire :  
https://www.minizinc.org/software.html



## Lancer en ligne de commande

python main.py --instance data/example_8cities.json

Options :

--time-limit : limite de temps CP-SAT  
--no-minizinc : désactiver MiniZinc  



## Lancer l’interface graphique

streamlit run app.py

Fonctionnalités :

- Choix de l’instance
- Modification des contraintes
- Comparaison BASE / AFFINÉ
- Visualisation claire des résultats



## Contraintes gérées

Contraintes dures :

- Indisponibilités de stades
- Maximum de matchs consécutifs à l’extérieur
- Maximum de matchs consécutifs à domicile
- Équilibre domicile / extérieur
- Limitation de la distance entre déplacements consécutifs

Optimisation :

- Minimisation des breaks
- Minimisation de la distance totale parcourue



## Résultats observés

En général :

- Forte réduction des breaks (ex : 16 → 4)
- Meilleure équité entre équipes
- Diminution des déplacements inutiles



## Conclusion

Ce projet illustre :

- L’utilisation combinée de CP-SAT et MiniZinc
- La modélisation de contraintes sportives réalistes
- L’optimisation multi-critères
- Une interface pédagogique pour analyser les résultats



## Auteurs

Groupe 02 Léo FARINA - Arthur LAMONERIE — Calendrier sportif  
ECE Ing4 — Projet IA / Programmation par contraintes
