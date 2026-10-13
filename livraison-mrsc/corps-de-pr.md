Moteur embarqué mis à jour vers 22957da, correctif du site rebasé

La copie embarquée du moteur datait du 8 octobre (99491d8). Depuis, l'amont a
gagné la fluidité (compression, cache du catalogue), la lecture en clair, le
lexique, le calcul des nuances institutionnelles, l'analyse de la Constitution,
les dynamiques croisées, le contrepouvoir et le registre des objections — et la
passe « visuel » entière : plancher de lisibilité, quatre paliers d'écran,
tableaux en cartes sur téléphone, une seule barre collante, surfaces natives
sombres.

Le correctif du site refusait de s'appliquer : l'amont avait bougé sous lui.
`outils/patchs/simulateur-securite-mrsc.patch` est donc **rebasé** — réunion à
trois branches, puis dix conflits résolus un par un dans `interface.py`. La
règle suivie : l'amont gagne pour la typographie et ses nouvelles fonctions, le
site garde ses durcissements. Les 26 identifiants et littéraux de protection du
correctif sont présents, et les six nouveaux points d'entrée du moteur sont
exposés.

Ce que le rebasage conserve, nommément : plafonds de corps et de cible HTTP
(413 et 414), plafonds de réponse (source, cotation), nombre de champs de
requête, délais et caches du navigateur, `X-Content-Type-Options: nosniff`, la
vérification des teintes avant injection dans une règle, l'échappement des
textes, l'exclusion des cibles locales, et les enveloppes défilantes des
tableaux d'audit.

Deux ajustements d'intégration :

- **Six routes exposées** (`constitution`, `contrepouvoirs`, `dynamiques`,
  `instances`, `nuances`, `objections`) : le moteur les sert, l'API du site les
  ignorait — `verifier-integration.py` le signalait comme une divergence.
- **Balise d'analytique Vercel retirée** de la copie embarquée : la page du site
  est autonome, cette ressource ne s'y trouve pas (elle fait échouer le contrôle
  des liens locaux).

Portes vertes : `verifier-securite`, `verifier-maj-amont`, `verifier-integration`,
`verifier-site-statique`, `verifier-rd-continue`, `construire-apprentissages`,
`construire-simulateur` et `generer-fonctions-api`. `verifier-source-distante`
ne peut pas joindre le réseau depuis l'atelier : elle le dit et laisse la copie
embarquée faire le calcul.
