# Guide d'Entretien — Semantic Brain

Questions fréquentes sur les LLMs, avec des réponses adaptées au niveau débutant.

---

## Question 1 : "C'est quoi un token ?"

**Réponse courte :**
Un token est l'unité de base que le modèle lit et produit.
Ce n'est ni un mot, ni un caractère : c'est une découpe statistique du texte.

**Réponse développée pour l'entretien :**
> "Un token, c'est un fragment de texte. En anglais, un mot court comme 'cat' = 1 token.
> Un mot long comme 'tokenization' peut être découpé en 2-3 tokens.
> En français, c'est légèrement plus gourmand car Claude est entraîné majoritairement en anglais.
> En pratique, 1 000 tokens ≈ 750 mots.
>
> Pourquoi c'est important ? Parce que les LLMs ont une limite de contexte mesurée en tokens.
> Claude Opus 4.6 accepte jusqu'à 200 000 tokens en entrée — ce qui représente
> environ un livre entier. Et la facturation se fait aussi par token :
> input tokens + output tokens = coût total de la requête."

**Exemple concret à donner :**
> "Dans ce projet, j'ai mis une limite de 180 000 caractères (~45 000 tokens) pour
> rester dans le contexte et maîtriser les coûts."

---

## Question 2 : "Comment tu gères si le texte est trop long pour l'IA ?"

**Réponse courte :**
Plusieurs stratégies existent selon le cas d'usage : tronquer, chunker, résumer en cascade.

**Réponse développée pour l'entretien :**
> "Il y a plusieurs approches, de la plus simple à la plus avancée :
>
> **1. Tronquer** (ce que je fais ici pour rester simple) :
> On coupe le texte à une limite sûre et on prévient l'utilisateur.
> C'est adapté quand les informations importantes sont au début du document.
>
> **2. Le Chunking** : découper le texte en morceaux qui se chevauchent légèrement
> (ex: par pages ou par blocs de 4 000 tokens), analyser chaque morceau séparément,
> puis fusionner les résultats. C'est plus précis mais nécessite plusieurs appels API.
>
> **3. La résumé en cascade (Map-Reduce)** : résumer chaque chunk d'abord,
> puis demander à Claude de synthétiser tous les résumés. C'est l'approche
> qu'utilisent des outils comme LangChain, mais on peut la coder soi-même avec
> quelques boucles Python et des appels directs à l'API.
>
> **4. Le RAG** (Retrieval-Augmented Generation) : stocker le texte dans une base
> vectorielle, ne récupérer que les passages pertinents selon la question posée.
> C'est la technique la plus scalable, mais aussi la plus complexe à mettre en place."

---

## Question 3 : "C'est quoi la différence entre un System Prompt et un User Message ?"

**Réponse courte :**
Le System Prompt définit le comportement global du modèle ;
le User Message contient la requête spécifique de l'utilisateur.

**Réponse développée pour l'entretien :**
> "L'API Claude distingue deux types de messages :
>
> **Le `system` prompt** : c'est le contexte permanent, chargé une fois.
> Il définit le rôle, le ton, les règles et les contraintes du modèle.
> Dans ce projet, mon System Prompt dit à Claude qu'il est un 'expert en analyse documentaire'
> et lui donne des règles précises pour chaque champ à extraire.
> Il est traité en priorité par le modèle et n'est pas visible de l'utilisateur final.
>
> **Le `user` message** : c'est la requête variable, différente à chaque appel.
> Ici, c'est simplement le texte du document à analyser.
>
> Cette séparation permet de ne pas répéter les instructions dans chaque requête.
> Sur des milliers d'appels, ça économise des tokens — et donc de l'argent —
> grâce au mécanisme de **Prompt Caching** : Anthropic peut mettre en cache
> un System Prompt stable et ne pas le refacturer à chaque requête."

**À mentionner si on creuse :**
> "Dans ce projet, j'ai volontairement mis toutes les règles dans le System Prompt
> plutôt que dans le User Message. C'est du Prompt Engineering : séparer ce qui
> est stable (les règles) de ce qui varie (les données)."

---

## Bonus — Si on te demande : "Pourquoi tu n'as pas utilisé LangChain ?"

> "LangChain est un excellent outil pour des pipelines complexes, mais il introduit
> une couche d'abstraction qui cache ce qui se passe réellement avec l'API.
> Pour ce projet de portfolio, j'ai voulu montrer que je comprends les fondamentaux :
> comment construire un bon prompt, comment structurer une réponse JSON,
> comment gérer les erreurs de l'API. Avec la bibliothèque `anthropic` directe,
> je sais exactement ce que j'envoie et ce que je reçois. C'est aussi beaucoup
> plus simple à debugger et à expliquer en entretien."
