web: gunicorn --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-4} --preload --timeout 120 --graceful-timeout 30 --keep-alive 5 simulateur.wsgi:application
