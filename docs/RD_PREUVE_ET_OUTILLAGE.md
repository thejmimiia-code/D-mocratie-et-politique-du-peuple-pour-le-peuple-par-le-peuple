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

## 6. Ce qui reste, et ce que ces contrôles ne font pas

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
