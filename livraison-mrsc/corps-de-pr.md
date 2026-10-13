Moteur embarqué mis à jour vers le moteur du 13 octobre (`e1dc6a6`)

La copie embarquée du moteur datait du 8 octobre (99491d8). Depuis, l'amont a
gagné la fluidité (compression, cache du catalogue), la lecture en clair, le
lexique, le calcul des nuances institutionnelles, l'analyse de la Constitution,
les dynamiques croisées, le contrepouvoir et le registre des objections — et la
passe « visuel » entière : plancher de lisibilité, quatre paliers d'écran,
tableaux en cartes sur téléphone, une seule barre collante, surfaces natives
sombres.

Deux correctifs sont arrivés depuis, et la copie les emporte :

- **le nom d'une région défilante suit la taille de l'écran** : sous 640 px, un
  tableau devient une pile de cartes et sa région annonçait encore « faites
  défiler horizontalement », en gardant un arrêt clavier qui ne menait nulle
  part ;
- **la licence du dépôt est lue dans son fichier `LICENSE`**, plus recopiée :
  trois fichiers servis aux robots annonçaient une autre licence que la sienne.

Le correctif du site refusait de s'appliquer au moment du rebasage : l'amont
avait bougé sous lui, et `outils/mettre-a-jour-simulateur.py` a donc eu raison de
s'arrêter sans rien remplacer. `outils/patchs/simulateur-securite-mrsc.patch` est **rebasé** sur le
moteur du jour — réunion à trois branches
(`git merge-file` : moteur neuf, moteur d'origine du correctif, copie du site),
**sans conflit cette fois** : la base choisie était celle du correctif, pas une
copie antérieure du moteur. La règle suivie : l'amont gagne pour la typographie
et ses nouvelles fonctions, le site garde ses durcissements.

Le rebasage est vérifié dans les deux sens : `git apply --check` sur le moteur
du jour, puis `git apply --reverse --check` sur le résultat — et les cinq
fichiers obtenus sont identiques **à l'octet** à la copie publiée ici.

Ce que le rebasage conserve, nommément : plafonds de corps et de cible HTTP
(413 et 414), plafonds de réponse (source, cotation), nombre de champs de
requête, délais et caches du navigateur, `X-Content-Type-Options: nosniff`, la
vérification des teintes avant injection dans une règle, l'échappement des
textes, l'exclusion des cibles locales, et les enveloppes défilantes des
tableaux d'audit — seize protections nommées une par une dans la vérification de
publication, qui refuse de pousser si l'une disparaît.

Trois ajustements d'intégration :

- **Six routes exposées** (`constitution`, `contrepouvoirs`, `dynamiques`,
  `instances`, `nuances`, `objections`) : le moteur les sert, l'API du site les
  ignorait — `verifier-integration.py` le signalait comme une divergence.
- **Balise d'analytique Vercel retirée** de la copie embarquée : la page du site
  est autonome, cette ressource ne s'y trouve pas (elle fait échouer le contrôle
  des liens locaux).
- **L'adresse canonique du site, déclarée par le site.** Le moteur décrit sa
  page depuis une source unique (`simulateur/surface_publique.py` : description,
  canonique, aperçu de partage, données structurées, icônes). La copie embarquée
  ne recopie donc plus ces balises à la main : elle **surcharge** l'adresse,
  `SIMULATEUR_URL_CANONIQUE=https://thejmimiia-code.github.io/MRSC/simulateur/`,
  posée dans le bloc d'adaptation du correctif. Sans cela, la copie se
  déclarerait canonique ailleurs et les moteurs consolideraient le sous-dossier
  vers l'adresse de Vercel — c'est exactement ce que `verifier-site-statique.py`
  refusait (« canonique attendue … reçue […] »), et c'est ce contrôle qui a
  révélé le besoin.

La page reconstruite ne contient plus de marqueur de conflit — 374 967
caractères — et ses **scripts JavaScript** passent `node --check` ; ses données
structurées sont un JSON valide (`Organization`, `WebSite`, `WebApplication`),
et le contrôle de publication les distingue désormais du JavaScript : les
confondre faisait échouer `node --check` sur du JSON valide. La CI du site est rejouée avant la poussée :
`py_compile`, `construire-apprentissages --verifier`,
`construire-simulateur --verifier`, puis `verifier-rd-continue`,
`verifier-site-statique`, `verifier-securite` et `verifier-integration`.
`verifier-maj-amont` doit dire « à jour » : la copie prend le sommet de `main`.
`verifier-source-distante` interroge le réseau ; injoignable, elle le dit et
laisse la copie embarquée faire le calcul.
