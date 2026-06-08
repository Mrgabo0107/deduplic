import subprocess
import sys
import json
from pathlib import Path

TMP_REPORT_PATH = Path(__file__).parent / ".deduplic_tmp_report.json"

def launch_gui(report: list):
    """Saves the report to a hidden JSON and starts the Streamlit server."""
    current_file = Path(__file__).resolve()

    with open(TMP_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("Starting Streamlit server... Press Ctrl+C to stop it.", flush=True)

    try:
        subprocess.run(["streamlit", "run", str(current_file)], check=True)
    except KeyboardInterrupt:
        if TMP_REPORT_PATH.exists():
            TMP_REPORT_PATH.unlink()
        print("\nStreamlit server stopped successfully.")
        sys.exit(0)


if __name__ == "__main__":
    import streamlit as st

    # Academic clean setup (Leaves background handling to Streamlit native engine)
    st.set_page_config(
        page_title="Europarser - Deduplication Module",
        layout="wide"
    )

    translations = {
        "en": {
            "title": "≠ DEDUPLIC",
            "subtitle": "Analyse de corpus textuels et identification des structures redondantes.",
            "no_conflict": "No duplication conflicts detected in the corpus.",
            "conflict_count": "Detected clusters with duplication conflicts:",
            "cluster": "Conflict Cluster",
            "nodes": "Implicated records (Indices)",
            "leader": "Suggested Reference Record",
            "evidence_btn": "Review similarity metrics for Cluster",
            "shared_keys": "shares key(s)",
            "linear_sim": "linear similarity coefficient"
        },
        "fr": {
            "title": "≠ DEDUPLIC",
            "subtitle": "Analyse de corpus textuels et identification des structures redondantes.",
            "no_conflict": "Aucun conflit de duplication détecté dans le corpus.",
            "conflict_count": "Clusters détectés avec des conflits de duplication :",
            "cluster": "Cluster de Conflit",
            "nodes": "Enregistrements impliqués (Indices)",
            "leader": "Enregistrement de Référence Suggéré",
            "evidence_btn": "Examiner les métriques de similarité pour le Cluster",
            "shared_keys": "partage la ou les clé(s)",
            "linear_sim": "coefficient de similarité linéaire"
        }
    }

    # Initialize language session state
    if "lang" not in st.session_state:
        st.session_state.lang = "fr"

    # --- TOP HEADER NAVIGATION BAR ---
    # We split the top bar: 85% for title, 15% for the discrete language selector
    col_title, col_lang = st.columns([0.85, 0.15])
    
    with col_title:
        st.title(translations[st.session_state.lang]["title"])
        st.caption("Module de Déduplication et Analyse de Clusters — CERES (Sorbonne Université / Huma-Num)")
        
    with col_lang:
        # Subtle dropdown at the top right corner
        selected_lang = st.selectbox(
            "Language", 
            ["fr", "en"], 
            index=0 if st.session_state.lang == "fr" else 1,
            label_visibility="collapsed" # Hides the label to look like a navbar utility
        )
        if selected_lang != st.session_state.lang:
            st.session_state.lang = selected_lang
            st.rerun()

    st.divider()

    # Data layer validation
    if not TMP_REPORT_PATH.exists():
        st.error("Temporary data layer missing.")
    else:
        with open(TMP_REPORT_PATH, "r", encoding="utf-8") as f:
            reports = json.load(f)

        t = translations[st.session_state.lang]

        if not reports:
            st.info(t["no_conflict"])
        else:
            st.subheader(f"{t['conflict_count']} {len(reports)}")
            st.write("") # Spatial branding spacer

            # Render elements using strictly native components to respect user dark/light theme
            for comp in reports:
                comp_id = comp["component_id"]
                
                # Native Header for the Cluster
                st.markdown(f"### {t['cluster']} #{comp_id}")
                st.markdown(f"**{t['nodes']}:** `{comp['nodes']}`")
                st.markdown(f"**{t['leader']}:** :blue-background[Node {comp['leader']}]")
                
                # Safe native expander (Guaranteed arrow alignment and contrast)
                with st.expander(f"{t['evidence_btn']} #{comp_id}"):
                    for edge in comp["edges_trazability"]:
                        node_a, node_b = edge["pair"]
                        st.markdown(f"**Pair ({node_a} — {node_b})** {t['shared_keys']}:")
                        
                        for key, score in edge["details"].items():
                            percentage = score * 100
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; • *{key}*: `{percentage:.2f}%` ({t['linear_sim']})")
                
                st.divider()