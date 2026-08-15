# HUMANOR — PLAN DE ROLL-OUT v2.0
*Remplace les packs 1.0 et 1.1. Ce qui est construit, ce qui reste, et dans quel ordre.*

---

## 0. ÉTAT RÉEL AU 15/08/2026

**Acquis (fait aujourd'hui, vérifié)**
- Identité étanche : iCloud `humanor.ai@icloud.com` · IG `@humanor.ai` · GitHub `humanor-ai` · clé PGP `1CCE660983E9DA6D` · zéro fil vers flom95/urs
- `humanor.co` acheté, DNS Cloudflare, site v1 **en ligne**, commit Genesis signé
- Gate G1 (match verbatim) et commit-reveal cryptographique : codés, testés
- Avatar, 5 familles de fonds, studio de rendu Reels : codés, rendus, vérifiés à l'œil
- Séquence de labels : générateur + audit statistique (aucune stratégie > 57%)
- Backend V2 (Worker + D1) : écrit, prêt à déployer

**Pas encore vrai — et c'est important**
- Publication auto Instagram : **bloquée par Meta**, voir §4
- Musique : à choisir dans la bibliothèque IG (je ne peux ni produire ni licencier)
- Sources Gibran / Dickinson / Tagore : **doivent passer G1 sur ta machine** avant publication
- Aucun vote réel, aucun fool rate : ils naissent avec le premier post

---

## 1. LA PIEUVRE — ARCHITECTURE

Un cerveau, six tentacules indépendants. Chacun testable seul, aucun ne bloque les autres.

```
                        ┌──────────────┐
                        │  D1 (rounds, │
                        │    votes)    │
                        └──────┬───────┘
   ┌──────────┬──────────┬─────┴─────┬──────────┬──────────┐
   │          │          │           │          │          │
 CORPUS   GÉNÉRATEUR  SÉQUENCE    STUDIO    PUBLICATION  INTELLIGENCE
 G1 verba-  phrases   audit im-  reels,    IG (manuel   fool rate,
 tim vs     IA + G4   prévisi-   reveals,  → API)       repondération
 Gutenberg  collision bilité     OG                     du générateur
```

| Tentacule | Fichier | État |
|---|---|---|
| Corpus (G1) | `verifier/g1_verify.py` | ✅ testé |
| Générateur IA | modèle open-weight local | ⬜ à brancher |
| Séquence | `tools/sequence.py` | ✅ audité |
| Sceaux | `proof/seal.py` + `verify.sh` | ✅ testé |
| Studio | `design/studio.py`, `backgrounds.py` | ✅ rendus |
| Backend | `api/worker.js`, `schema.sql` | ✅ écrit, ⬜ à déployer |
| Site | `site/` | ✅ en ligne |
| Publication | Business Suite → API | ⬜ voir §4 |
| Intelligence | requêtes D1 + rapport hebdo | ⬜ après 30 manches |

---

## 2. LA SÉQUENCE — POURQUOI ELLE N'EST PAS ALTERNÉE

Ton point était juste, et la réponse n'est pas celle qu'on croit.

Les deux réflexes sont faux :
- **Alterner** (H A H A) : prévisible à 100% dès la deuxième manche.
- **Plafonner** (« jamais 3 identiques ») : **fuite d'information**. Après deux AI, le joueur sait. Une contrainte dure distribue des indices gratuits.

Donc : **tirage à pile ou face équitable**, le seul processus sans structure exploitable — puis **audit**. Une séquence n'est retenue que si elle passe équilibre, longueur de séries, autocorrélation aux rangs 1-2-3, biais conditionnel, et surtout : *aucune stratégie simple de joueur ne gagne*.

Résultat mesuré sur 200 séquences générées : **pire stratégie 57%**, série identique la plus longue **4**.

```
make sequence N=30
```

---

## 3. LE STUDIO — CE QUI SORT

**Reel** 1080×1920, 7 s, 24 fps, boucle sans couture (zoom cosinusoïdal : la dernière image rejoint la première). La phrase est affichée **100% de la durée** et ne bouge jamais ; seul le fond respire à 3%. Zone sûre respectée : rien d'important sous les 430 derniers pixels, mangés par l'interface IG.

**Carte de reveal** (story J+1, 17h55) : la phrase en retrait, le verdict en grand — `HUMAN` en serif, `AI` en mono, la même tension typographique que le site.

**Image OG** 1200×630 : ce que voit quelqu'un à qui on colle le lien. Sans elle, un partage sur X ou WhatsApp n'affiche rien — c'est le frein n°1 à la viralité.

**Fonds** : 5 familles génératives (dusk, paper, concrete, silver, fog), monochromes, luminance bornée 5–34/255 pour que le texte gagne toujours. Rotation `(no × 3) mod 5` : jamais deux fois de suite la même.

```
make studio            # posters + reveals + OG
make studio VIDEO=7    # encode 7 reels (lent)
```

---

## 4. INSTAGRAM — LA VÉRITÉ SUR L'AUTOMATISATION

**Ce que Meta exige pour publier par API** : compte Business/Creator lié à une Page Facebook, app Meta Developer, permission `instagram_content_publish`, et **App Review avec vérification d'entreprise**. Compte plusieurs semaines, et une entité juridique — ce qui entre en tension avec l'anonymat.

**Donc le plan en deux temps :**

**Phase A — semaines 1 à 4 : semi-auto.** Batch du dimanche, 2 h : générer les 7 Reels, sceller les 7 réponses, programmer les 7 posts dans **Meta Business Suite** (natif, gratuit, autorisé). Le reveal de 17h55 reste manuel : 3 minutes par jour, story + commentaire épinglé + `daily.sh reveal`.

**Phase B — dès que la review passe (si tu la lances).** Un cron remplace le batch. Le pipeline est déjà écrit pour ça : `studio.py` produit le fichier, il ne manque que l'appel de publication.

**Alternative honnête** : rester en Phase A indéfiniment. 2 h le dimanche + 3 min/jour, c'est tenable et ça évite d'exposer une entité juridique.

---

## 5. LE RITUEL QUOTIDIEN

| Heure | Geste | Commande |
|---|---|---|
| dimanche 2 h | batch : sceller, rendre, programmer J+1→J+7 | `make week` |
| 17h55 | reveal J-1 : story, commentaire épinglé, sel publié | `./api/daily.sh reveal 007 AI "Whitman, 1855"` |
| 18h00 | drop (programmé, rien à faire) | — |
| 18h05 | screenshot des meilleurs commentaires → story | — |

Le Worker **re-vérifie le sceau lui-même** avant de rendre une réponse publique : une faute de frappe dans le sel est refusée (HTTP 409), jamais publiée. La promesse ne peut pas être cassée par erreur humaine.

---

## 6. CALENDRIER DE LANCEMENT

| Jour | Ce qui se passe |
|---|---|
| **J-3** | G1 sur les 7 sources humaines · choix des 3 pistes musicales · déploiement du Worker + D1 · bascule du site sur l'API |
| **J-2** | Batch semaine 1 · programmation Business Suite · compte IG échauffé (bio, quelques follows) |
| **J-1** | Répétition à blanc : sceller, publier, révéler la manche 0 en privé · vérifier l'image OG sur X et WhatsApp |
| **J1** | Premier drop, 18h00 |
| **J2** | Premier reveal, 17h55 — le rituel commence vraiment |
| **J7** | Product Hunt : *« The daily game that seals its answers before you vote »* |
| **J14** | **Kill / scale.** Partages spontanés et croissance organique → phase B + clone FR. Rien → un pivot d'habillage, 7 jours, puis arrêt propre. |

---

## 7. RÉFÉRENCEMENT ET VIRALITÉ

**Ce qui manque encore au site** (une session de travail) :
- `sitemap.xml` + `robots.txt`
- Archive rendue côté serveur : chaque phrase révélée devient une page indexable — c'est le seul canal SEO durable du projet
- `og:image` pointant vers la carte générée par manche
- Données structurées (schema.org `Quotation`) sur les pages d'archive

**Le moteur viral réel n'est pas le SEO, c'est le fool rate.** « 68% des gens prennent du Gibran de 1923 pour de l'IA » est une phrase qui se partage seule, alimente les stories, les captions du lendemain, et le pitch presse. Elle n'existe qu'à partir du moment où les votes sont comptés — d'où le Worker.

---

## 8. MUSIQUE — MÉTHODE, PAS FICHIER

Je ne peux ni produire ni licencier de musique. La seule source sûre pour un compte qui pourrait un jour monétiser : **la bibliothèque audio d'Instagram**.

Critères : instrumental strict (une voix concurrence la lecture), tempo lent, pas de montée dramatique sur 7 secondes, texture ambient ou néoclassique. Teste 3 pistes la première semaine, garde celle qui performe, puis **fixe-la définitivement** : une identité sonore constante rend le compte reconnaissable son coupé.

---

## 9. LES TROIS DÉCISIONS QUI RESTENT

1. **Déployer le Worker maintenant ou après 15 jours de v1 ?** Ma reco : maintenant, parce que sans votes comptés tu n'as pas de fool rate, et sans fool rate tu n'as pas de contenu viral.
2. **Lancer l'App Review Meta ?** Elle demande une entité juridique. Si l'anonymat prime, reste en phase A.
3. **Auto-héberger les polices avant J1.** Google Fonts transmet les IP des visiteurs — contradiction directe avec le manifeste. 10 minutes de travail.
