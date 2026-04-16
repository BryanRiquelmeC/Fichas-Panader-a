import os
import io
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panaderia.settings')
django.setup()

from django.core.management import call_command

with io.open('datos.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', 'accounts', 'fichas',
                 '--natural-foreign', '--natural-primary',
                 '--indent', '2', stdout=f)

print("✅ Exportado correctamente en datos.json")