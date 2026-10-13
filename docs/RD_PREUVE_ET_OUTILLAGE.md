# R&D — L'outillage et la preuve : quand l'instrument de mesure ment

Ce document raconte la passe de R&D du 13 octobre 2026 sur **ce qui prouve** :
les outils qui appliquent les réglages du dépôt, les documents qui les décrivent,
et le geste qui doit garantir qu'un contrôle refuse bien ce qu'il prétend
refuser. La conclusion tient en une phrase : *le code n'était pas faux, c'est la
mesure qui l'était* — et deux des valeurs publiées étaient fausses depuis des
semaines sans que rien ne le signale.

---

## 1. Le piège trouvé par un sabotage qui refusait de mourir

Le protocole de ce dépôt est simple : chaque contrôle neuf est **saboté**, et le
sabotage doit être attrapé. En éprouvant le bloc « About » (§ 3), un sabotage a
continué d'agir **après avoir été restauré**. Le fichier sur le disque était
revenu à la bonne version ; Python servait encore le bytecode du sabotage.

La cause est précise :

- `importlib.util.spec_from_file_location` — le chargeur utilisé pour les scripts
  dont le nom n'est pas un nom de module (`verifier-compteurs.py`,
  `api/[...path].py`) — passe par `SourceFileLoader` ;
- ce chargeur écrit un `.pyc` dans `__pycache__/` à côté de la source, et le
  croit encore valable tant que **la taille** et **l'horodatage en secondes** de
  la source n'ont pas bougé ;
- remplacer `None` par `True` ne change pas la taille ; écrire et restaurer dans
  la même seconde ne change pas la seconde. Le cache est donc déclaré valide, et
  Python rejoue l'ancien code — en silence.

Conséquence pour ce dépôt : **les sabotages ne prouvaient plus ce qu'ils
prétendaient**. Un contrôle saboté pouvait « passer », ou être « attrapé » alors
que le sabotage avait déjà été retiré. Six endroits du dépôt chargeaient ainsi
leurs scripts, dont quatre tests et un outil.

## 2. Un chargeur qui relit, sans cache

`outils/chargement_module.py` remplace ce charger de source : il lit le fichier
et le compile explicitement (`compile(texte, chemin, "exec")`), puis exécute le
code dans un module neuf. Rien n'est déposé à côté du script, rien n'est relu
d'un fichier intermédiaire. Coût : quelques millisecondes par test.

Trois garanties que le chargeur tient, et qui sont contrôlées :

| Garantie | Pourquoi elle compte |
|---|---|
| **La source est relue à chaque chargement** | c'est la condition pour qu'un sabotage restauré soit vraiment retiré, et pour qu'un `.pyc` oublié ne décide pas de ce que la suite mesure |
| **`__file__` est renseigné** | `verifier-compteurs.py` et la veille en ligne calculent leur racine depuis `__file__` ; `__file__` absent, la racine serait fausse et les contrôles porteraient sur le mauvais dépôt |
| **Le module est enregistré sous son nom**, et retiré en cas d'échec | les `@dataclass` à annotations différées ont besoin de retrouver le module dans `sys.modules` ; un échec ne doit pas laisser un module à moitié importé |

`tests/test_chargement_module.py` (12 contrôles) **reproduit le piège dans un
sous-processus** : deux écritures de même longueur, horodatage remis à un instant
fixé (l'an 2001, pour que le test ne dépende pas de l'heure qu'il est), cache
écrit, cache déclaré valide, ancienne valeur servie. Puis il montre que le
chargeur du dépôt rend la nouvelle. Un contrôle refuse par ailleurs le retour du
chargeur à cache dans `tests/`, `outils/`, `api/` et `simulateur/`.

*Le piège est reproduit, pas raconté : si Python cessait un jour de se comporter
ainsi, le test le dirait au lieu de laisser une justification périmée.*

## 3. Le bloc « About » : mesurer au lieu d'affirmer

`outils/details_depot.py` produit le bloc à coller dans *Edit repository
details* (description, site web, sujets, aperçu social) et tente de l'appliquer
par l'API. Il portait une **affirmation figée** : « le lien actuel est mort, on
recommande de vider le champ » — écrite un jour où c'était vrai, devenue fausse
sans que rien ne le signale. Le champ avait donc été vidé, et le dépôt ne
renvoyait plus vers une application pourtant en ligne.

Ce qui a changé :

- **l'adresse vient de la page elle-même** (`surface_publique.URL_CANONIQUE_PAR_DEFAUT`) :
  l'adresse déclarée dans GitHub et celle que la page annonce aux moteurs ne
  peuvent plus vieillir séparément. Un contrôle refuse l'adresse écrite en dur ;
- **la question est posée** : `adresse_repond()` interroge l'adresse. Trois
  réponses, pas deux — *elle répond*, *elle ne répond pas*, *je n'ai pas pu
  vérifier* (réseau injoignable). Cette troisième réponse est écrite telle quelle
  dans le bloc : se taire serait le pire, le champ resterait vide sans raison ;
- **« déjà à jour » parle aussi du site web** : un dépôt dont le champ est vide
  n'est pas à jour, même si la description et les sujets le sont ;
- **le bloc rappelle ce que les robots lisent** (`robots.txt`, `sitemap.xml`,
  `llms.txt`, `llms-full.txt`) et par quoi on le vérifie.

`tests/test_details_depot.py` (17 contrôles pour cette partie) donne à la sonde
un ouvreur simulé : un 200, un 404 levé par `urlopen`, une panne réseau, une
adresse vide. Six sabotages posés et attrapés — dont celui qui, avant le § 1,
mentait sur son propre résultat.

## 4. Le document tenu par sa source

`docs/REPOSITORY_DETAILS.md` est la référence des champs non versionnés du
dépôt. Ses valeurs étaient recopiées à la main, et **trois avaient dérivé** :

| Valeur | Ce que le document annonçait | La réalité |
|---|---|---|
| Compte de la description | 270 caractères | **271** |
| Empreinte de l'aperçu social | `90ef4a12…` | `2ecba5b1…` — une **autre image** |
| Taille de l'aperçu social | 52 Kio | 51 Kio (52 171 octets) |

Une empreinte fausse fait téléverser autre chose que ce que le document décrit :
c'est exactement ce qu'un document de référence ne doit pas faire. Il y avait
aussi un paragraphe entier recopié deux fois.

Le document est donc **engendré entre marques** — `<!-- engendre:nom -->` …
`<!-- /engendre:nom -->` — pour quatre régions : description (avec son compte),
sujets (avec leur compte), site web (l'adresse, la copie de secours, ce que les
robots lisent) et aperçu social (taille, empreintes hexadécimale et base64,
chiffres clés lus dans le catalogue). La prose reste éditable à la main.

```bash
python3 outils/details_depot.py --doc           # réécrit les quatre régions
python3 outils/details_depot.py --verifier-doc  # refuse une valeur périmée
```

Neuf contrôles tiennent l'ensemble : régions à jour, empreintes recalculées
depuis le fichier versionné, comptes de la description et des sujets, adresse
publiée, **aucune valeur engendrée recopiée deux fois**, valeur périmée refusée,
marques disparues signalées, réécriture qui répare **sans toucher à la prose**,
document absent signalé. Un dixième contrôle balaie tous les documents qui
annoncent « N / 350 caractères » et exige le même nombre — celui du catalogue.
Sept sabotages posés et attrapés.

*La réécriture a d'ailleurs révélé un défaut : `reecrire_document` plantait sur
un chemin hors du dépôt (`relative_to` lève). Un test qui travaille sur une copie
sabotée l'a montré tout de suite ; le défaut est corrigé, pas contourné.*

## 5. La page de réglages effaçait le lien

`outils/reglages_depot.html` applique ces réglages par l'API, avec un jeton
jetable fourni par la personne qui l'ouvre. Elle n'avait **aucun contrôle**, et
portait trois défauts qui se cumulaient :

1. **son champ « Adresse du site » partait vide**, sous un libellé qui
   conseillait de le laisser vide — cliquer sur *Appliquer au dépôt* effaçait
   donc le lien vers l'application ;
2. **le dépôt visé était tronqué** : `…/D-mocratie-et-politique-du-peuple` au lieu
   de `…-pour-le-peuple-par-le-peuple`. La page appelait un dépôt qui n'existe
   pas : elle n'a jamais pu appliquer quoi que ce soit ;
3. **le lien de repli vers la documentation était tronqué de la même façon**, dans
   la page *et* dans `outils/details_depot.py` : un lien mort, au titre de repli.
   Il est désormais bâti sur le nom du dépôt, pas recopié.

Six contrôles tiennent la page : description du formulaire, liste des sujets,
dépôt visé, adresse pré-remplie, lien de documentation complet, absence de toute
taille d'image recopiée (une taille vieillit : le renvoi au fichier suffit). Un
septième vérifie que le JavaScript de la page se compile (`node --check`) — la
page n'est utile que si elle s'exécute.

## 6. La licence : lue, jamais recopiée

**Le défaut, publié.** `simulateur/surface_publique.py` portait `LICENCE = "MIT"`
sous un commentaire qui parlait encore de MIT. Le dépôt, lui, est sous
**GPL-3.0** — son fichier `LICENSE`, le classificateur de `pyproject.toml`,
`package.json` et la section « Licence » du `README.md` le disent tous, et l'API
GitHub l'annonce (`gpl-3.0`). Trois fichiers **servis en ligne** annonçaient donc
« licence MIT » <!-- citation historique : licence corrigée --> à des moteurs de recherche et à des lecteurs
automatiques :

| Fichier | Ce qu'il annonçait | Où |
|---|---|---|
| `robots.txt` | « la licence MIT l'autorise déjà » <!-- citation historique : licence corrigée --> | servi aux robots |
| `llms.txt` | « licence MIT, historique complet, tests » <!-- citation historique : licence corrigée --> | lu par les agents |
| `llms-full.txt` | « Code source (licence MIT) » <!-- citation historique : licence corrigée --> | lu par les agents |

Une licence fausse n'est pas une coquille : c'est une **affirmation juridique**,
et elle portait sur ce qui est publié. Le même « MIT » traînait dans le
`README.md`, `docs/RD_INDEXATION.md`, `docs/RD_IMPORT_UCDP.md`,
`tests/fixtures/README.md` et `docs/RD_VALIDATION_TEMPORELLE.md` — et dans les
**données** de fixtures (74 enregistrements `"licence": "MIT"` <!-- citation historique : licence corrigée --> et un
contrat), qui se déclaraient sous une licence que le dépôt n'a pas.

**Le marqueur des citations.** Les documents qui **racontent** l'erreur — le
`CHANGELOG`, cette page — portent en fin de ligne
`<!-- citation historique : licence corrigée -->` : un commentaire invisible à la
lecture, que le balayage des tests voit. Sans lui, dire ce qui a été corrigé
serait impossible ; avec lui, l'exemption est un geste conscient. Trois garde-fous
l'encadrent : son nombre est borné (`PLAFOND_CITATIONS`), le plafond doit rester
petit, et **un marqueur posé sur une ligne qui ne cite rien est refusé** — sans
quoi marquer large reviendrait à éteindre le contrôle sans le dire.

**La correction, et sa règle.** Le nom n'est plus écrit : il est **lu**.
`licence_du_depot()` reconnaît ce que dit le fichier `LICENSE` parmi les
licences courantes (AGPL, LGPL et GPL se testent dans cet ordre : elles portent
toutes les mots « GENERAL PUBLIC LICENSE »), et rend `""` — un simple renvoi au
fichier — quand il ne reconnaît rien. *Deviner serait refaire l'erreur qu'on
répare.* Un texte publié écrit désormais « licence GPL-3.0 » par
`mention_licence()`, depuis cette source unique.

**Le contrôle, et ce qu'il a fallu lui ajouter.** `tests/test_licence_du_depot.py`
(23 contrôles) vérifie trois choses : la reconnaissance du fichier (avec un cas
négatif — une mention **partielle** ne suffit pas à nommer une licence), l'accord
de toutes les déclarations (`LICENSE`, `pyproject.toml`, `package.json`,
`README.md`, textes publiés, fichiers statiques de la racine), et un **balayage**
qui refuse toute ligne attribuant au projet un autre nom de licence.

La première version du balayage avait trois trous — trois sabotages posés sur
cinq ont survécu :

1. **une signature élargie** (« GENERAL PUBLIC LICENSE » sans « GNU ») restait
   invisible : les variantes se testant dans l'ordre, l'AGPL passait avant. D'où
   le cas négatif ;
2. **réduire la liste des extensions surveillées** ne faisait rien échouer : le
   balayage est devenu une fonction qu'on éprouve sur un **faux dépôt** où
   chaque extension surveillée porte une mention fautive ;
3. **sauter tous les fichiers** rendait le contrôle central vert — il n'avait
   plus rien à examiner. D'où un contrôle qui exige que le balayage voie des
   fichiers nommés (`README.md`, `simulateur/surface_publique.py`, `robots.txt`,
   `index.html`…) et plus de cent en tout.

**Quinze sabotages après correction, quinze attrapés** — dont deux qui ont
montré que le mécanisme de citation lui-même pouvait être contourné (marqueur
retiré d'une ligne qui cite ; plafond relevé à dix mille). Une **seule**
exemption, écrite, et un contrôle qui vérifie qu'elle reste la seule : ce fichier
de test **construit** des textes de licence pour éprouver la reconnaissance, donc
il cite les noms qu'il pourchasse.

**Ce que ce contrôle ne fait pas.** Il ne juge pas le choix de licence : il
vérifie que toutes les déclarations **disent la même chose que le fichier**. Un
changement de licence se fait donc en remplaçant `LICENSE` — le reste suit, et
si un texte recopié résiste, la suite échoue en le nommant.

## 7. Ce qui reste, et ce que ces contrôles ne font pas

- **Le bloc « About » n'est toujours pas appliqué dans GitHub.** Le jeton
  disponible ici est un jeton d'intégration sans droit d'administration :
  l'API refuse (`403 Resource not accessible by integration`), et l'outil le dit
  au lieu de faire semblant. Reste à faire par un humain : coller le bloc
  affiché dans *Settings → General → Edit repository details*.
- **L'aperçu social reste manuel** : GitHub ne l'accepte pas par API.
- **Depuis cette machine, l'adresse publiée n'a pas pu être sondée** (pas d'accès
  réseau sortant ici) : le script a donc écrit « l'adresse n'a pas pu être
  vérifiée » — la réponse honnête, et le contrôle qui garantit la justesse des
  empreintes porte sur le **fichier versionné**, pas sur ce que sert l'hébergeur.
  Ce qui est servi en ligne est mesuré par ailleurs, par
  `outils/verifier-surface-en-ligne.py` (voir `RD_INDEXATION.md`).
- **Les contrôles ne disent pas que le texte publié est bon** : ils disent qu'il
  correspond aux sources du dépôt et qu'aucune valeur recopiée n'a dérivé. Un
  désaccord entre les deux hébergeurs reste du ressort de la veille en ligne.
