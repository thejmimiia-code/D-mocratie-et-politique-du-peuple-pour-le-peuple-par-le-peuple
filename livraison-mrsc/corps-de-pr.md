Moteur embarqué mis à jour vers le moteur du 13 octobre, correctif du site rebasé

La copie embarquée du moteur datait du 8 octobre (99491d8). Depuis, l'amont a
gagné la fluidité (compression, cache du catalogue), la lecture en clair, le
lexique, le calcul des nuances institutionnelles, l'analyse de la Constitution,
les dynamiques croisées, le contrepouvoir et le registre des objections — et la
passe « visuel » entière : plancher de lisibilité, quatre paliers d'écran,
tableaux en cartes sur téléphone, une seule barre collante, surfaces natives
sombres.

Le correctif du site refusait de s'appliquer : l'amont avait bougé sous lui, et
`outils/mettre-a-jour-simulateur.py` a donc eu raison de s'arrêter sans rien
remplacer. `outils/patchs/simulateur-securite-mrsc.patch` est **rebasé** —
réunion à trois branches, puis dix conflits résolus un par un dans
`interface.py`. La règle suivie : l'amont gagne pour la typographie et ses
nouvelles fonctions, le site garde ses durcissements.

Ce que le rebasage conserve, nommément : plafonds de corps et de cible HTTP
(413 et 414), plafonds de réponse (source, cotation), nombre de champs de
requête, délais et caches du navigateur, `X-Content-Type-Options: nosniff`, la
vérification des teintes avant injection dans une règle, l'échappement des
textes, l'exclusion des cibles locales, et les enveloppes défilantes des
tableaux d'audit — seize protections nommées une par une dans la vérification de
publication, qui refuse de pousser si l'une disparaît.

Deux ajustements d'intégration :

- **Six routes exposées** (`constitution`, `contrepouvoirs`, `dynamiques`,
  `instances`, `nuances`, `objections`) : le moteur les sert, l'API du site les
  ignorait — `verifier-integration.py` le signalait comme une divergence.
- **Balise d'analytique Vercel retirée** de la copie embarquée : la page du site
  est autonome, cette ressource ne s'y trouve pas (elle fait échouer le contrôle
  des liens locaux).

La page reconstruite ne contient plus de marqueur de conflit et ses trois
scripts en ligne passent `node --check` — c'est là qu'une fusion de HTML en
conflit se casse en silence, `py_compile` ne voyant pas les marqueurs qui vivent
dans des chaînes Python. La CI du site est rejouée avant la poussée :
`py_compile`, `construire-apprentissages --verifier`,
`construire-simulateur --verifier`, puis `verifier-rd-continue`,
`verifier-site-statique`, `verifier-securite` et `verifier-integration`.
`verifier-maj-amont` doit dire « à jour » : la copie prend le sommet de `main`.
`verifier-source-distante` interroge le réseau ; injoignable, elle le dit et
laisse la copie embarquée faire le calcul.
