import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import streamlit as st

from src.cpsat_solver import solve_with_cpsat
from src.minizinc_refine import refine_with_minizinc
from src.validate import compute_metrics, validate_schedule
from src.travel_metrics import compute_travel_metrics


Schedule = Dict[int, List[Tuple[str, str]]]



def charger_instance_depuis_fichier(chemin: str) -> dict:
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def calendrier_en_lignes_par_jour(calendrier: Schedule) -> List[dict]:
    lignes = []
    for d in sorted(calendrier.keys()):
        matchs = calendrier[d]
        txt = "  |  ".join([f"{dom} vs {ext}" for (dom, ext) in matchs])
        lignes.append({"Journée": d + 1, "Matchs": txt})
    return lignes


def bloc_indicateurs(titre: str, metriques: dict, trajets: Optional[dict]) -> None:
    st.subheader(titre)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Breaks (répétitions H/H ou A/A)", metriques["total_breaks"])
    c2.metric("Série max à l'extérieur", max(metriques["max_away_streak"].values()) if metriques.get("max_away_streak") else 0)
    c3.metric("Déséquilibre max |Domicile-Extérieur|", max(abs(v) for v in metriques["balance"].values()) if metriques.get("balance") else 0)

    if trajets:
        c4.metric("Distance totale", trajets["total_distance"])
    else:
        c4.metric("Distance totale", "—")

    with st.expander("Détails par équipe", expanded=False):
        st.write("Breaks par équipe :", metriques["breaks_per_team"])
        st.write("Série max à l'extérieur :", metriques["max_away_streak"])
        st.write("Équilibre (Domicile - Extérieur) :", metriques["balance"])
        if trajets:
            st.write("Distance par équipe :", trajets["distance_per_team"])
            st.write("Violations 2 déplacements consécutifs trop loin :", trajets["consec_away_violations_count"])
            if trajets["consec_away_violations_count"] > 0:
                st.write(trajets["consec_away_violations"])


def afficher_table_calendrier(calendrier: Schedule) -> None:
    st.markdown("### Calendrier par journée")
    st.dataframe(calendrier_en_lignes_par_jour(calendrier), use_container_width=True)



st.set_page_config(page_title="Calendrier sportif — CP-SAT + MiniZinc", layout="wide")

st.title("Générateur de calendrier sportif")
st.caption("Génération par CP-SAT, puis amélioration par MiniZinc (contraintes dures + optimisation).")

with st.sidebar:
    st.header("Paramètres")

   
    exemples = []
    dossier_data = Path("data")
    if dossier_data.exists():
        exemples = [str(p) for p in sorted(dossier_data.glob("*.json"))]

    source = st.radio("Source de l'instance", ["Exemples du projet", "Importer un JSON"], index=0)

    instance = None

    if source == "Exemples du projet":
        if not exemples:
            st.warning("Aucun fichier JSON trouvé dans le dossier data/.")
        else:
            choix = st.selectbox("Choisir une instance", exemples, index=0)
            instance = charger_instance_depuis_fichier(choix)
    else:
        fichier = st.file_uploader("Importer un fichier JSON", type=["json"])
        if fichier is not None:
            instance = json.loads(fichier.read().decode("utf-8"))

    st.divider()

    limite_temps = st.slider("Limite de temps CP-SAT (secondes)", 1, 60, 10)
    activer_minizinc = st.checkbox("Activer l'affinage MiniZinc", value=True)

    if instance is not None:
        st.divider()
        st.subheader("Contraintes (modification rapide)")

        
        instance["max_away_streak"] = int(instance.get("max_away_streak", 2))
        instance["max_home_streak"] = int(instance.get("max_home_streak", 2))
        instance["max_consec_away_travel"] = int(instance.get("max_consec_away_travel", 600))

        instance["max_away_streak"] = int(st.number_input("Série max à l'extérieur", 0, 10, int(instance["max_away_streak"])))
        instance["max_home_streak"] = int(st.number_input("Série max à domicile", 0, 10, int(instance["max_home_streak"])))
        instance["max_consec_away_travel"] = int(st.number_input("Distance max entre 2 déplacements consécutifs", 0, 5000, int(instance["max_consec_away_travel"])))

    st.divider()
    bouton_lancer = st.button(" Lancer", type="primary", use_container_width=True)

if instance is None:
    st.info("Choisis une instance (ou importe un JSON), puis clique sur « Lancer ».")
    st.stop()

equipes = instance["teams"]

if bouton_lancer:
    
    with st.spinner("Génération du calendrier (BASE) avec CP-SAT..."):
        calendrier_base = solve_with_cpsat(instance, time_limit_s=limite_temps)

    
    try:
        validate_schedule(
            teams=equipes,
            schedule=calendrier_base,
            unavailable_home=instance.get("unavailable_home", {}),
        )
        base_valide = True
    except Exception as e:
        base_valide = False
        st.error(f"Calendrier BASE invalide : {e}")

    metriques_base = compute_metrics(equipes, calendrier_base)

    trajets_base = None
    if "distances" in instance:
        trajets_base = compute_travel_metrics(
            teams=equipes,
            schedule=calendrier_base,
            distances=instance["distances"],
            max_consec_away_travel=int(instance.get("max_consec_away_travel", 10**9)),
        )

   
    calendrier_affine = None
    metriques_affine = None
    trajets_affine = None

    if activer_minizinc:
        with st.spinner("Affinage du calendrier avec MiniZinc (breaks + contraintes + distance)..."):
            try:
                calendrier_affine = refine_with_minizinc(calendrier_base, equipes, instance)

                validate_schedule(
                    teams=equipes,
                    schedule=calendrier_affine,
                    unavailable_home=instance.get("unavailable_home", {}),
                )

                metriques_affine = compute_metrics(equipes, calendrier_affine)

                if "distances" in instance:
                    trajets_affine = compute_travel_metrics(
                        teams=equipes,
                        schedule=calendrier_affine,
                        distances=instance["distances"],
                        max_consec_away_travel=int(instance.get("max_consec_away_travel", 10**9)),
                    )
            except Exception as e:
                st.error(f"Affinage MiniZinc impossible : {e}")

    st.divider()

    
    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        bloc_indicateurs("BASE (CP-SAT)", metriques_base, trajets_base)
        afficher_table_calendrier(calendrier_base)

    with col_droite:
        if calendrier_affine and metriques_affine:
            bloc_indicateurs("AFFINÉ (MiniZinc)", metriques_affine, trajets_affine)
            afficher_table_calendrier(calendrier_affine)
        else:
            st.info("Aucun calendrier affiné disponible (MiniZinc désactivé ou échec).")

    st.divider()
    st.subheader(" Résumé des améliorations")

    
    if metriques_affine:
        st.write(f"- Breaks : **{metriques_base['total_breaks']} → {metriques_affine['total_breaks']}**")
    else:
        st.write(f"- Breaks : **{metriques_base['total_breaks']}** (pas d'affinage)")

    
    if trajets_base and trajets_affine:
        st.write(f"- Distance totale : **{trajets_base['total_distance']} → {trajets_affine['total_distance']}**")
        st.write(f"- Violations (2 déplacements consécutifs trop loin) : **{trajets_affine['consec_away_violations_count']}**")

   
