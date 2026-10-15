# R&D « être trouvé » : ce que la page dit d'elle-même aux robots

**Demande.** « Il faut permettre l'indexation par des robots qui font les
classements des moteurs de recherche, et autres solutions qui lisent les
contenus. »

**Ce qui existait avant cette passe.** Rien. Ni description, ni adresse
canonique, ni `robots.txt`, ni `sitemap.xml`, ni aperçu de partage : la page
n'avait qu'un `<title>`. Elle était donc indexable *par accident*, et elle
l'était mal — deux hébergeurs servaient la même page, aucune ne disait laquelle
fait foi, et un partage sur un réseau social affichait une vignette vide.

**Ce qui existe après.** Une source unique, cinq fichiers publiés, un en-tête
complet, des images, et une suite de contrôles qui refusent la divergence.

---

## 1. Le problème : ce que la page ne disait pas

| Ce qu'un robot cherche | Ce qu'il trouvait | Conséquence |
| --- | --- | --- |
| Ce qu'est la page | un `<title>` | une description inventée par la machine, souvent fausse |
| Quelle adresse fait foi | rien | deux copies (Vercel, Render) se concurrencent |
| Où est le plan | `sitemap.xml` absent | découverte au petit bonheur |
| Ce qui est ouvert | `robots.txt` absent | un robot prudent passe, un autre calcule tout |
| Une vignette de partage | rien | lien nu dans les messageries |
| Une icône | rien | onglet anonyme |
| Un résumé lisible sans JavaScript | rien | un lecteur automatique ne voyait qu'un squelette vide |

Le dernier point est le plus coûteux : la page **calcule** tout en JavaScript.
Un robot qui ne l'exécute pas ne voit qu'une coquille. Il faut donc lui donner
le contenu en texte — c'est à quoi sert `llms.txt`, et surtout `llms-full.txt`.

---

## 2. Une seule source : `simulateur/surface_publique.py`

Recopier ces éléments à quatre endroits est la façon la plus sûre de les voir
diverger, et personne ne s'en aperçoit avant de se demander pourquoi la page ne
sort pas. Le module devient donc **la** source :

| Ce qu'il produit | Qui le sert |
| --- | --- |
| `robots.txt` | fichier à la racine (Vercel) **et** route du serveur Python (Render) |
| `sitemap.xml` | idem |
| `llms.txt` | idem |
| `llms-full.txt` | idem |
| l'en-tête de la page (description, canonique, icônes, données structurées, aperçu de partage) | injecté dans `HTML_PAGE` au chargement de `simulateur/interface.py` |

`outils/generer-surface-publique.py` écrit les quatre fichiers à la racine et
sait les **vérifier** (`--verifier`) : la CI refuse une divergence entre le
module et les fichiers publiés. Le serveur Python, lui, sert le même texte sans
passer par le disque — les deux hébergeurs disent donc mot pour mot la même
chose.

Le module n'importe que la bibliothèque standard et ne fait **aucun appel
réseau** : un robot qui demande `/llms.txt` l'obtient même si la collecte de
données est hors ligne, et même sur un hébergeur qui n'a rien installé de plus
que le strict nécessaire.

---

## 3. `robots.txt` : ouvert, sauf ce qui n'est pas une page

```text
User-agent: *
Content-Signal: search=yes, ai-input=yes, ai-train=yes
Allow: /
Disallow: /api/
Sitemap: https://d-mocratie-…vercel.app/sitemap.xml
```

**Un seul groupe `User-agent: *`.** Ajouter un groupe par robot (GPTBot,
ClaudeBot, PerplexityBot, Google-Extended…) serait plus bavard et plus risqué :
un groupe nommé **remplace** le groupe générique pour ce robot, donc chaque
groupe devrait répéter l'exclusion de `/api/`. Un seul groupe ne peut pas
diverger de lui-même — et il vaut mieux autoriser largement un outil citoyen à
code ouvert, financé par personne, que de tenir une liste à jour.

**`Content-Signal`** (contentsignals.org) est écrit explicitement : c'est la
convention émergente lue par les robots qui la connaissent. Recherche, lecture
pour réponse assistée et entraînement sont autorisés — le dépôt est ouvert
(GPL-3.0) et ses textes sont faits pour être lus. L'écrire ne coûte rien et
évite un doute. Le nom de cette licence n'est pas recopié : il est **lu** dans
le fichier `LICENSE` (`simulateur/surface_publique.py`), parce qu'il avait été
recopié faux — voir `RD_PREUVE_ET_OUTILLAGE.md`, § 6.

**`/api/` est fermé, et c'est le seul.** Ce sont des points de calcul, pas des
pages : indexer `/api/simuler` ne remplit les résultats que de pages vides, et
chaque visite déclenche une simulation complète. Fermer `/` aurait été absurde.

---

## 4. `sitemap.xml` : une adresse, et pas de faux indices

Une seule URL — la canonique. Les vues (scénario choisi, scène ouverte, onglet)
sont des **états internes**, pas des adresses : elles ne sont pas listées.

Pas de `lastmod`, pas de `priority`, pas de `changefreq` au-delà de
`weekly` : une date de modification qui n'est pas la vraie est pire que pas de
date. Les moteurs cessent de s'y fier, y compris quand elle redevient juste.

---

## 5. L'en-tête de la page

- **`rel="canonical"`** — une seule adresse fait foi. La page est servie par
  Vercel, par Render et par le site M.R.S.C. Trois copies identiques sans
  canonique, ce sont trois pages concurrentes ; avec, c'est une page et deux
  copies.
- **`description`** — 150 caractères utiles, **sans aucun nombre**. La page a
  déjà affiché « 93 leviers » et « 38 indicateurs publics » après qu'ils étaient
  faux ; une description qui vieillit ne se voit jamais. Un test refuse tout
  chiffre dans les métadonnées.
- **`robots`** — `index, follow, max-snippet:-1, max-image-preview:large,
  max-video-preview:-1` : les extraits longs et les grandes images sont
  autorisés. Rien n'est demandé qu'on ne veuille donner.
- **Open Graph + Twitter Card** — titre, accroche, image absolue (1200 × 630)
  avec ses dimensions, son type et son texte de remplacement. Une vignette
  annoncée en 1200 × 630 qui ne l'est pas s'affiche rognée, ou pas du tout.
- **Icônes en `data:`** — la page reste **un fichier unique** : elle doit
  s'ouvrir hors ligne, et le site M.R.S.C la recopie dans un sous-dossier, où un
  chemin absolu pointerait à côté. Une icône en `data:` règle les deux cas. Le
  contrôle ne se contente pas de la forme : il **décode** chaque `data:` et
  compare les octets à ceux du fichier versionné.
- **`favicon.ico` reste publié à la racine** : c'est ce que cherchent les robots
  qui ne lisent pas la page (Google, notamment).

### Données structurées (JSON-LD)

Trois nœuds reliés — `Organization` (le M.R.S.C), `WebSite` et `WebApplication`
(l'outil) — et **rien d'autre**. Pas de note agrégée, pas d'avis, pas de
« foire aux questions » balisée : les moteurs sanctionnent les balisages qui
promettent un résultat enrichi sans contenu réel derrière, et une page qui
triche n'est plus classée du tout. Un test refuse explicitement
`aggregateRating`, `review`, `ratingValue` et `faqPage`.

Le JSON-LD vit **dans** la page : un test vérifie qu'il ne peut pas en sortir
(pas de `</script`, pas d'U+2028 brut) et qu'aucun nombre étranger au catalogue
n'y est annoncé.

---

## 6. `llms.txt` et `llms-full.txt` : le contenu pour qui ne joue pas la page

Le format [llms.txt](https://llmstxt.org) tient en trois règles : un titre, une
citation qui résume, puis des sections de liens. `llms.txt` est donc **court**
(3,4 Ko) — il dit où est le contenu et ce qu'il contient.

`llms-full.txt` (45 Ko) est le contenu lui-même : les 156 leviers avec leur
clé, leur unité, leurs bornes et leur description, les 20 domaines, les 11
scénarios types, les 5 classes, et ce que l'outil ne fait pas. Il est **engendré
depuis le catalogue** au moment où il est écrit : les nombres annoncés sont ceux
de l'outil publié, pas une photographie. Un contrôle compare les comptes au
catalogue et vérifie que chaque levier, domaine, scénario et classe y figure.

C'est la réponse à « que contient cet outil ? » pour un agent qui ne peut pas
exécuter la page — et le fichier est lu à la source, pas deviné.

---

## 7. Ce qui n'a **pas** été fait, et pourquoi

- **`lastmod` dans le sitemap** : la date viendrait d'un `git log` au moment de
  la construction, et personne ne la maintiendrait. Une date fausse coûte plus
  qu'elle ne rapporte.
- **Un flux RSS/Atom** : il n'y a pas de contenu daté — les données publiques
  changent, mais elles n'ont pas d'article à annoncer.
- **`humans.txt`, `security.txt`, `ai.txt`, `ads.txt`** : rien à dire de plus,
  ou hors sujet. Inventer un fichier de plus n'aide personne.
- **Un manifeste d'application (`manifest.webmanifest`)** : écrit, essayé, puis
  **retiré** — il exige un `<link>` vers un fichier, donc une ressource à
  charger, ce que la page s'interdit (voir § 8). Une page qui s'installe comme
  une application n'était pas le besoin ; être trouvée l'était.
- **Un service Render statique supplémentaire** : il publierait une quatrième
  copie de la même page pour trois fichiers. Le service Python les sert déjà
  (§ 2), c'est suffisant.
- **Un `hreflang`** : une seule langue.
- **Ping automatique des moteurs** : les API de Google et de Bing exigent un
  compte et un jeton ; un ping non authentifié est ignoré, et le faire depuis la
  CI serait du bruit. La soumission se fait à la main, une fois — voir § 10.

---

## 8. La contrainte assumée : la page reste un fichier unique

Le dépôt tient une règle : la page ne charge **rien** de l'extérieur (aucun
CDN, aucune police, aucun `<script src>`). Elle doit vivre hors ligne et rester
auditable par des non-informaticiens.

Cette passe ajoute exactement deux `<link>`, et aucun ne charge de fichier :
`rel="canonical"` (une adresse, pas une ressource) et les icônes en `data:`.
Le test d'origine a donc été **précisé** plutôt que contourné : il refuse
toujours tout `<link>` de chargement (`stylesheet`, `preload`, `preconnect`,
`modulepreload`), tout `@import`, toute `url(http…)` et tout `<script src>`, et
exige désormais que chaque `<link>` restant soit une métadonnée ou un `data:`.

L'aperçu de partage, lui, est **absolu** : c'est une adresse annoncée aux
robots, pas un fichier chargé par la page. C'est la seule URL absolue de tout le
montage, et elle est motivée.

---

## 9. Les garde-fous

`tests/test_indexation.py` — 35 contrôles, cinq familles :

1. **L'en-tête** — langue, titre, description (présente, bornée, sans chiffre),
   directives d'indexation, canonique unique, aperçu de partage complet et
   cohérent avec la taille réelle de l'image, icônes décodées et comparées aux
   fichiers, aucune ressource distante, données structurées valides et honnêtes,
   JSON-LD incapable de sortir de la page.
2. **Les fichiers publiés** — identiques au module, sans gabarit non rempli,
   `robots.txt` ouvert sauf `/api/`, `sitemap.xml` à une seule adresse et sans
   faux indices, `llms.txt` lisible, `llms-full.txt` complet (comparé au
   catalogue), liens du dépôt existants, images à la taille annoncée, icônes
   valides, module sans dépendance.
3. **Les routes du serveur** — les cinq chemins répondent 200 avec le bon type
   et le bon corps, les images aussi, `HEAD` ne renvoie pas de corps, un chemin
   hors liste blanche est refusé, l'API n'a pas régressé.
4. **La cohérence avec le site M.R.S.C** — rien de ce qui se charge ne pointe
   vers un autre hôte (la copie vit dans un sous-dossier), les chemins restent
   relatifs, le module ne charge rien au-delà de la bibliothèque standard.
5. **L'adresse canonique surchargeable** — le défaut est bien celui publié, une
   valeur sans barre finale est complétée, un miroir déclaré (`http://…`) est
   accepté, et une adresse douteuse (schéma inconnu, paramètre, fragment,
   espace, guillemet) **arrête la construction** au lieu de passer inaperçue
   jusque dans les résultats de recherche. Robots, plan et `llms.txt` suivent la
   surcharge — c'est vérifié, pas supposé.

**Sabotages posés et attrapés** pendant cette passe :

| Sabotage | Attrapé par |
| --- | --- |
| Un nombre dans la description (`156 leviers — …`) | `test_les_metadonnees_ne_promettent_aucun_nombre` |
| L'en-tête injecté *dans* un commentaire | `test_le_jeton_de_l_entete_est_remplace_partout` (le défaut est arrivé pour de vrai : le jeton figurait aussi dans le commentaire, et `str.replace` remplace toutes les occurrences) |
| Une icône en `data:` tronquée | `test_les_icones_voyagent_dans_la_page` (décodage + comparaison binaire) |
| `Sitemap:` retiré de `robots.txt` | `outils/generer-surface-publique.py --verifier` (refus, puis réécriture) |
| Une adresse du plan modifiée d'un caractère | le même vérificateur, sur `sitemap.xml` |
| Le paramètre d'URL accepté dans l'adresse canonique | `test_une_adresse_dangereuse_est_refusee_bruyamment` (une valeur refusée n'arrête plus la construction) |

---

## 10. Ce qui reste à faire, et par qui

Ces gestes demandent un compte : ils ne peuvent pas être automatisés ici.

1. **Google Search Console** — ajouter la propriété
   `https://d-mocratie-et-politique-du-peuple-p.vercel.app/`, vérifier par
   fichier HTML (déposer le fichier fourni à la racine du dépôt : Vercel le
   servira) puis soumettre `sitemap.xml`.
2. **Bing Webmaster Tools** — même propriété, puis « Importer depuis Google
   Search Console » : une seule saisie pour les deux moteurs.
3. **Le site M.R.S.C** — son `sitemap.xml` existe depuis longtemps ; il n'a pas
   de `robots.txt`. C'est une lacune du dépôt du site, pas de celui-ci : à
   traiter côté `thejmimiia-code/MRSC` (même modèle, plus simple : un
   `User-agent: *`, un `Allow: /`, un `Disallow: /api/`, un `Sitemap:`).
4. **Vérifier après publication** — les chemins `/robots.txt`, `/sitemap.xml`,
   `/llms.txt`, `/llms-full.txt`, `/og-image.png` doivent répondre 200 sur les
   deux hébergeurs, et un aperçu de partage doit afficher la vignette.

---

## 11. Les images, en un mot

`outils/apercu_social.py` produit désormais trois images, toutes **versionnées**
(les hébergeurs servent des fichiers, ils ne les fabriquent pas) :

| Fichier | Taille | Usage |
| --- | --- | --- |
| `docs/apercu_social.png` | 1280 × 640 | aperçu social du dépôt GitHub (à téléverser dans les réglages — GitHub ne l'accepte que par l'interface web) |
| `og-image.png` | 1200 × 630 | vignette annoncée par `<meta property="og:image">` |
| `apple-touch-icon.png` | 180 × 180 | icône du raccourci sur téléphone (insérée en `data:`) |
| `favicon.svg` | vectoriel | icône d'onglet, écrite en clair (insérée en `data:`) |
| `favicon.ico` | 16, 32, 48 | repli publié à la racine |

Le dessin reprend la palette de la page. Les quatre chiffres qu'il affiche
(leviers, domaines, indicateurs publics, classes) sont **lus dans le
catalogue** au moment où l'image est faite : une vignette qui annonce un nombre
faux est une promesse non tenue. Le verdict du ruban (« VIGILANCE · 7
alertes ») est, lui, une illustration de l'interface — il ne prétend à aucun
résultat de calcul.

---

## 12. Trois hébergeurs, une seule adresse qui fait foi

La même page est servie par trois endroits : Vercel (la référence), Render (la
version qui calcule, lue par l'API) et le site M.R.S.C (une copie dans un
sous-dossier). Trois adresses, trois pages identiques : sans canonique, les
moteurs voient trois concurrentes et choisissent à la place de l'auteur.

Le défaut est donc **un seul** : `URL_CANONIQUE_PAR_DEFAUT` désigne Vercel, et
les robots, le plan et `llms.txt` annoncent la même adresse. Une copie qui se
déclare ailleurs n'est pas pénalisée — elle est simplement *consolidée* vers
l'originale, ce qui est le comportement voulu pour un miroir de service.

Un miroir qui voudrait être indexé **lui-même** (un domaine propre, une
préproduction ouverte aux robots) n'a pas à dupliquer ce module : il définit
`SIMULATEUR_URL_CANONIQUE` avant de construire sa page.

```bash
SIMULATEUR_URL_CANONIQUE=https://exemple.fr/outil \
  python3 outils/generer-surface-publique.py        # plan et robots suivent
```

La valeur est vérifiée avant usage : schéma `http`/`https` obligatoire, hôte
présent, ni paramètre, ni fragment, ni espace, ni `"`, `'`, `<`, `>` ; la barre
finale est ajoutée si elle manque. Une valeur refusée **arrête la construction
avec un message** au lieu de produire une page silencieusement mal déclarée :
une adresse canonique fausse ne se voit pas à l'écran, elle se voit des semaines
plus tard dans les résultats de recherche, quand tout est déjà indexé.

**Décision pour Render** : le service ne s'auto-canonise pas. Il publie la même
page que Vercel à une adresse technique ; la faire concourir avec la référence
diviserait les signaux pour aucun gain. La variable est là le jour où l'usage
change.

---

## 13. Ce qui est publié est vérifié publié

Rien, dans un dépôt, ne dit ce que les hébergeurs servent réellement : un fichier
peut être présent et jamais déployé, une route ajoutée au moteur et absente des
fonctions serverless, une réécriture d'hébergeur peut avaler un chemin. La suite
de tests s'arrête au bord du réseau — et c'est heureux, un test qui interroge
Internet devient rouge pour des raisons qui ne regardent pas le dépôt.

`outils/verifier-surface-en-ligne.py` comble ce trou, et le comble **au
caractère** : le texte servi doit être égal à celui que `surface_publique.py`
engendre ici, l'image servie égale au fichier versionné. Comparer à une
photographie ne dirait rien des jours suivants — le module et les fichiers
publiés ne peuvent pas diverger sans que la veille le voie.

Les 68 épreuves, sur les deux adresses :

| Famille | Ce qui est exigé |
| --- | --- |
| La page | 200 en `text/html`, canonique, description, aperçu absolu, directives, données structurées |
| Les textes | `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt` **égaux** au texte engendré |
| Les images | type annoncé, et octets identiques au fichier versionné |
| Les routes GET | seize routes, 200 en JSON exploitable |
| Les routes GET paramétrées | `run?scenario=mandature`, `bulle?levier=…` |
| Les routes POST | `simuler`, `donnees`, `conseil`, `nuances` — la page les appelle en direct |
| Les refus | route inconnue, proxy sans cible, POST sur une route qui n'existe pas |

**Le piège de la copie de secours.** Elle s'endort quand personne ne l'appelle,
puis répond **200 avec une page qui raconte qu'elle démarre**. Prendre cette page
pour une réponse serait le pire des silences : la veille dirait que tout va bien
au moment précis où rien ne répond. Elle insiste donc — mais **seulement sur la
page**, car c'est elle qui réveille, et en le disant.

**Trois distinctions apprises le 14 octobre 2026**, quand la copie de secours est
tombée en **502** (« Bad Gateway » : la passerelle répond, personne derrière) :

| Ce qui arrive | Ce que c'est | Ce que fait la veille |
|---|---|---|
| La page dit « Application loading » | un **réveil** | elle attend, et recommence |
| La passerelle répond 502, 503, 504 | une **panne** | elle le dit et passe — insister ne réveille rien |
| Aucune réponse du tout (TLS coupé, délai dépassé) | un hôte **muet** | elle le dit **une fois**, puis arrête là cet hôte |

La ligne « aucune réponse de l'hôte » n'est pas un détail : avant, une panne
réseau **tuait le rapport** (`Réseau injoignable…`), c'est-à-dire que la veille
devenait muette au moment où elle servait le plus. Et l'insistance appliquée à
toutes les adresses faisait durer une veille sur un hôte suspendu **trois quarts
d'heure** au lieu de deux minutes.

**Le verdict se publie.** Le rapport est un commentaire **tenu à jour** sur une
page du dépôt (« Veille en ligne », créée au premier passage, marqueur
`<!-- veille-en-ligne -->`, mise à jour par `gh api -X PATCH`) — lisible sans rien
installer, contrairement au résumé d'un run, qui vit à l'intérieur d'un workflow
et disparaît avec lui. L'étape s'exécute **même quand la veille échoue**
(`if: always()`) : sinon la panne la plus intéressante serait celle qu'on ne
publie pas.

**Deux poids, deux mesures.** L'adresse canonique est celle qu'on partage : son
échec **fait rougir** la veille. La copie de secours peut être endormie, suspendue
ou absente sans que le dépôt soit en faute : son échec est **publié, pas
sanctionné**. Une veille rouge chaque semaine pour un service d'appoint cesse
d'être lue, et une veille qu'on ne lit plus ne sert à rien.

**Ce que la veille ne peut pas faire**, et qui reste manuel : elle constate
qu'une adresse répond, pas qu'un moteur l'a indexée. Les gestes de Search
Console et de Bing Webmaster Tools (§ 10) restent des gestes humains.

**Ce qu'elle ne peut pas réparer non plus** : le service de la copie de secours.
Elle le constate et le publie. Le réveil, lui, se fait par un **crochet de
déploiement** (`deploy-secours.yml`, secret `RENDER_DEPLOY_HOOK`) ou depuis le
tableau de bord de l'hébergeur — le mode d'emploi est dans
[`HEBERGEMENT.md`](HEBERGEMENT.md#quand-la-copie-de-secours-ne-répond-pas-502).

**Empêcher la panne, maintenant qu'on sait la voir.** La veille constate ; elle
ne peut pas empêcher la copie de secours de s'endormir — c'est le comportement
du palier gratuit, et c'est ce sommeil qui montre un 502 au visiteur. Un second
rendez-vous, `.github/workflows/garde-veille.yml`, frappe donc à la porte
**toutes les dix minutes** pendant les heures de consultation, avec un seul
appel (la sonde de l'hébergeur). Il ne commente **que lorsqu'un état change** —
la panne, puis le retour —, sa page est distincte, et sa fenêtre est calculée
pour rester sous le quota d'heures du palier gratuit : voir
[`HEBERGEMENT.md`](HEBERGEMENT.md#le-garde-veille--empêcher-le-service-de-sendormir).

Le workflow `.github/workflows/veille-en-ligne.yml` l'exécute **après chaque
fusion sur `main`** — le seul instant où la question a une réponse neuve, parce
qu'un déploiement vient d'avoir lieu —, avant une fusion qui touche la veille
elle-même, à la demande, et une fois par semaine si le calendrier veut bien
livrer (mesuré le 15 octobre 2026 : il ne livre rien dans ce dépôt). Jamais à
chaque poussée ordinaire : une panne d'hébergeur ne doit pas faire rougir la
contribution de quelqu'un d'autre.

**Et la veille sait attendre un déploiement.** Juste après une fusion, la page
servie est encore celle d'avant pendant une à deux minutes : « pas encore » n'est
pas « faux ». La page — et elle seule, parce qu'un déploiement la remplace en
dernier et qu'elle réveille un service endormi — est réessayée jusqu'à être
**complète** ; les autres adresses gardent leur verdict au premier essai, sans
quoi une veille sur un hôte suspendu durerait quarante minutes.

**Un 502 isolé, lui, se reprend.** Exception mesurée le 15 octobre 2026 : une
seule des soixante-huit adresses de la copie de secours est tombée en 502, à la
seconde où Render redéployait, pendant que les soixante-sept autres répondaient
200. Une adresse se reprend donc **une fois** quand l'hôte a répondu ailleurs
dans le même passage — un hôte qui répond est debout —, et jamais quand l'hôte
n'a rien répondu du tout : ce n'est alors pas un à-coup, c'est une panne, et
insister ferait durer la veille pour rien. Le verdict ne dit plus « le service
n'est pas derrière » sur un hôte qui vient de répondre : il dit ce qu'il a vu.
La veille tourne aussi à la main, sur n'importe quel poste :

```bash
python3 outils/verifier-surface-en-ligne.py                # les deux hôtes
python3 outils/verifier-surface-en-ligne.py --hote secours # la copie de secours seule
```
