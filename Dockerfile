# Image de production du simulateur.
#
# Le simulateur lui-même n'a aucune dépendance applicative (bibliothèque
# standard seule). gunicorn est ajouté uniquement pour servir l'application
# WSGI derrière un hébergeur ; en local, `python3 -m simulateur.dashboard`
# suffit et n'installe rien.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Utilisateur non-root : le conteneur n'a besoin d'aucun privilège.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

# Les dépendances d'hébergement d'abord : la couche est mise en cache tant que
# requirements.txt ne change pas, donc le code peut être recopié à chaque build
# sans réinstaller quoi que ce soit.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# /app doit rester accessible en écriture : les routes d'export écrivent un
# fichier temporaire dans le répertoire courant avant de l'envoyer, puis
# l'effacent (voir `DashboardHandler._send_fichier`).
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; \
urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/api/lexique').read()"

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", \
     "--timeout", "120", "simulateur.wsgi:application"]
