set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py loaddata datos.json
python manage.py createsuperuser --noinput --username bryan --email $DJANGO_SUPERUSER_EMAIL || true