# Politique de sécurité

## Signaler une vulnérabilité

Si vous découvrez une vulnérabilité de sécurité dans ce projet, veuillez la
signaler de manière **responsable**.

### Comment signaler

**Ne publiez PAS d'issue publique pour les vulnérabilités de sécurité.**

Envoyez un e-mail décrivant :
1. La nature de la vulnérabilité
2. Les étapes pour la reproduire
3. L'impact potentiel
4. Une proposition de correction (si possible)

### Délai de réponse

- **Accusé de réception** : sous 48 heures
- **Évaluation initiale** : sous 7 jours
- **Correctif publié** : sous 30 jours (selon la gravité)

## Périmètre de sécurité

Ce projet est un **simulateur académique et d'aide à la décision**. Il ne
gère pas de données personnelles, ne stocke pas d'informations sensibles
et n'interagit avec aucun système bancaire ou fiscal réel.

Cependant, les vulnérabilités suivantes sont prises au sérieux :

### Vulnérabilités couvertes

- **Injection de code** dans les entrées CLI ou API REST
- **Manipulation des données** de simulation (résultats faussés)
- **Fuite d'informations** via le serveur web (endpoints non protégés)
- **Déni de service** via des requêtes malveillantes
- **Erreurs de calcul** dans le moteur de simulation SFC

### Hors périmètre

- Les données sources publiques (INSEE, DGFIP, etc.) ne sont pas de notre
  responsabilité ; elles sont intégrées telles quelles avec leur source
- Le serveur web est conçu pour un usage local/développement ; il n'est
  pas prévu pour un déploiement en production sans reverse proxy

## Bonnes pratiques

- Ne jamais exposer le serveur web directement sur Internet sans proxy
- Vérifier l'intégrité des données sources avant chaque simulation
- Les résultats de simulation ne doivent jamais être présentés comme des
  prédictions certaines mais comme des projections conditionnelles

## Historique des vulnérabilités

Aucune vulnérabilité connue à ce jour.