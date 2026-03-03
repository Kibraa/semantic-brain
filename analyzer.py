import json
import sys
from pathlib import Path
from typing import List, Optional

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class AnalyseDocument(BaseModel):
    resume: str = Field(
        description="Résumé concis du document en 3 à 5 phrases qui capture l'essentiel."
    )
    mots_cles: List[str] = Field(
        description="Liste de 5 à 10 mots-clés représentatifs : concepts, entités, thèmes."
    )
    actions: List[str] = Field(
        description="Actions concrètes commençant par un verbe à l'infinitif. "
                    "Si aucune action : ['Aucune action identifiée']."
    )
    sentiment: str = Field(
        description="Ton général : exactement 'positif', 'neutre' ou 'négatif'."
    )
    niveau_complexite: str = Field(
        description="Complexité : exactement 'simple', 'intermédiaire' ou 'avancé'."
    )


SYSTEM_PROMPT = """Tu es un expert en analyse documentaire et en extraction d'informations structurées.
Tu lis tout type de texte (article, rapport, email, compte-rendu, note technique…)
et tu en extrais les informations clés sous une forme concise et actionnable.

## Règles pour chaque champ :

### RÉSUMÉ
- 3 à 5 phrases maximum, en langage clair et direct
- Commence par identifier le TYPE de document (ex: "Ce rapport présente…", "Cet email demande…")
- Sois factuel et objectif — pas d'interprétation au-delà du texte

### MOTS-CLÉS
- Entre 5 et 10 termes, triés par ordre d'importance décroissante
- Préfère les concepts spécifiques au domaine plutôt que les mots génériques
- Inclus les entités nommées importantes (personnes, organisations, lieux, dates clés)

### ACTIONS
- Identifie ce que le lecteur DOIT ou DEVRAIT faire concrètement
- Chaque action commence par un verbe à l'infinitif (Contacter, Vérifier, Planifier, Lire…)
- Sois spécifique : évite les formulations vagues comme "S'informer davantage"
- Si le document est purement informatif sans appel à l'action, retourne exactement :
  ["Aucune action identifiée"]

### SENTIMENT
- Valeur stricte : "positif", "neutre" ou "négatif"
- Évalue le ton émotionnel global du texte

### NIVEAU DE COMPLEXITÉ
- Valeur stricte : "simple", "intermédiaire" ou "avancé"
- Base-toi sur le vocabulaire technique, la densité des concepts et le public cible implicite
"""

MAX_CHARS = 180_000


def lire_fichier_texte(chemin: str) -> str:
    chemin_path = Path(chemin)
    if not chemin_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")
    return chemin_path.read_text(encoding="utf-8")


def lire_fichier_pdf(chemin: str) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Installez pdfplumber : pip3 install pdfplumber")

    pages = []
    with pdfplumber.open(chemin) as pdf:
        for page in pdf.pages:
            texte = page.extract_text()
            if texte and texte.strip():
                pages.append(texte)

    if not pages:
        raise ValueError("Impossible d'extraire du texte de ce PDF.")

    return "\n\n".join(pages)


def analyser_texte(
    texte: str,
    client: Optional[anthropic.Anthropic] = None,
) -> AnalyseDocument:
    if client is None:
        client = anthropic.Anthropic()

    tronque = False
    if len(texte) > MAX_CHARS:
        texte = texte[:MAX_CHARS]
        tronque = True

    response = client.messages.parse(
        model="claude-haiku-4-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyse le document suivant et extrais les informations structurées.\n\n"
                    "--- DÉBUT DU DOCUMENT ---\n\n"
                    f"{texte}\n\n"
                    "--- FIN DU DOCUMENT ---"
                    + ("\n\n[Note : le document a été tronqué.]" if tronque else "")
                ),
            }
        ],
        output_format=AnalyseDocument,
    )

    return response.parsed_output


def analyser_fichier(
    chemin: str,
    client: Optional[anthropic.Anthropic] = None,
) -> AnalyseDocument:
    extension = Path(chemin).suffix.lower()

    if extension == ".pdf":
        texte = lire_fichier_pdf(chemin)
    elif extension in (".txt", ".md"):
        texte = lire_fichier_texte(chemin)
    else:
        raise ValueError(f"Format non supporté : '{extension}'. Acceptés : .txt, .md, .pdf")

    return analyser_texte(texte, client)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python analyzer.py <fichier>")
        sys.exit(1)

    try:
        resultat = analyser_fichier(sys.argv[1])
        print(json.dumps(resultat.model_dump(), ensure_ascii=False, indent=2))
    except anthropic.AuthenticationError:
        print("Clé API invalide. Vérifiez ANTHROPIC_API_KEY dans votre .env", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)
