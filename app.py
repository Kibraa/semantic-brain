import io
import json

import anthropic
import streamlit as st
from dotenv import load_dotenv

from analyzer import analyser_texte

load_dotenv()

st.set_page_config(
    page_title="Semantic Brain",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
    .keyword-badge {
        display: inline-block;
        background: #1e3a5f;
        color: #e8f0fe;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 3px 4px;
        font-size: 0.85em;
        font-weight: 500;
    }
    .action-card {
        background: #f0f4ff;
        border-left: 4px solid #1e3a5f;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.95em;
    }
</style>
""", unsafe_allow_html=True)

st.title("Semantic Brain")
st.markdown("**Analyse intelligente de documents par Claude AI** — résumé, mots-clés, actions.")
st.divider()

with st.sidebar:
    st.header("Configuration")

    api_key_input = st.text_input(
        "Clé API Anthropic (optionnel)",
        type="password",
        placeholder="sk-ant-...",
        help="Laissez vide si ANTHROPIC_API_KEY est défini dans votre fichier .env.",
    )

    st.divider()
    st.markdown("**Modèle :** Claude Haiku 4.5")
    st.markdown("**Sortie :** JSON structuré (Pydantic)")
    st.markdown("**Limite :** ~180 000 caractères")
    st.divider()
    st.markdown("**Ce qui est extrait :**")
    st.markdown("- Résumé (3-5 phrases)")
    st.markdown("- Mots-clés (5-10 termes)")
    st.markdown("- Actions à entreprendre")
    st.markdown("- Sentiment & Complexité")

tab_texte, tab_fichier = st.tabs(["Coller un texte", "Importer un fichier"])

texte_a_analyser: str | None = None

with tab_texte:
    texte_saisi = st.text_area(
        "Votre texte",
        height=280,
        placeholder=(
            "Collez ici un article, un rapport, un email, des notes de réunion…\n"
            "Semantic Brain en extraira l'essentiel en quelques secondes."
        ),
        label_visibility="collapsed",
    )
    if texte_saisi.strip():
        texte_a_analyser = texte_saisi
        st.caption(f"{len(texte_saisi):,} caractères saisis.")

with tab_fichier:
    fichier = st.file_uploader(
        "Choisissez un fichier",
        type=["txt", "md", "pdf"],
        help="Formats supportés : .txt, .md, .pdf",
    )
    if fichier is not None:
        try:
            if fichier.type == "application/pdf":
                import pdfplumber
                with pdfplumber.open(io.BytesIO(fichier.read())) as pdf:
                    pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                texte_a_analyser = "\n\n".join(pages)
            else:
                texte_a_analyser = fichier.read().decode("utf-8")

            st.success(f"Fichier chargé : **{fichier.name}** — {len(texte_a_analyser):,} caractères")
        except Exception as e:
            st.error(f"Impossible de lire le fichier : {e}")

st.divider()

col_btn, col_hint = st.columns([1, 4])

with col_btn:
    lancer_analyse = st.button(
        "Analyser",
        type="primary",
        disabled=(texte_a_analyser is None),
        use_container_width=True,
    )

with col_hint:
    if texte_a_analyser is None:
        st.info("Collez un texte ou importez un fichier pour activer l'analyse.")
    else:
        st.success(f"Texte prêt — {len(texte_a_analyser):,} caractères.")

if lancer_analyse and texte_a_analyser:
    try:
        if api_key_input.strip():
            client = anthropic.Anthropic(api_key=api_key_input.strip())
        else:
            client = anthropic.Anthropic()
    except Exception as e:
        st.error(f"Impossible d'initialiser le client Anthropic : {e}")
        st.stop()

    with st.spinner("Claude analyse votre document…"):
        try:
            resultat = analyser_texte(texte_a_analyser, client)
        except anthropic.AuthenticationError:
            st.error("Clé API invalide. Vérifiez votre clé dans la sidebar ou le fichier .env.")
            st.stop()
        except anthropic.RateLimitError:
            st.error("Limite de requêtes atteinte. Patientez quelques secondes et réessayez.")
            st.stop()
        except Exception as e:
            st.error(f"Erreur lors de l'analyse : {e}")
            st.stop()

    st.success("Analyse terminée !")
    st.divider()

    SENTIMENT_ICONE = {"positif": "✅", "neutre": "⚖️", "négatif": "⚠️"}
    COMPLEXITE_ICONE = {"simple": "🟢", "intermédiaire": "🟡", "avancé": "🔴"}

    col1, col2, col3 = st.columns(3)
    with col1:
        icone_s = SENTIMENT_ICONE.get(resultat.sentiment.lower(), "❓")
        st.metric("Sentiment", f"{icone_s} {resultat.sentiment.capitalize()}")
    with col2:
        icone_c = COMPLEXITE_ICONE.get(resultat.niveau_complexite.lower(), "❓")
        st.metric("Complexité", f"{icone_c} {resultat.niveau_complexite.capitalize()}")
    with col3:
        st.metric("Mots-clés identifiés", len(resultat.mots_cles))

    st.divider()

    st.subheader("Résumé")
    st.write(resultat.resume)

    st.subheader("Mots-clés")
    badges = " ".join(
        f'<span class="keyword-badge">{kw}</span>'
        for kw in resultat.mots_cles
    )
    st.markdown(badges, unsafe_allow_html=True)

    st.subheader("Actions à entreprendre")
    if resultat.actions and resultat.actions[0].lower() != "aucune action identifiée":
        for action in resultat.actions:
            st.markdown(f'<div class="action-card">▶ {action}</div>', unsafe_allow_html=True)
    else:
        st.info("Aucune action spécifique identifiée — ce document est purement informatif.")

    st.divider()
    with st.expander("Voir le JSON brut retourné par l'API"):
        st.json(resultat.model_dump())

    st.download_button(
        label="Télécharger le résultat (JSON)",
        data=json.dumps(resultat.model_dump(), ensure_ascii=False, indent=2),
        file_name="semantic_brain_resultat.json",
        mime="application/json",
    )
