import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panaderia.settings')
django.setup()

import cloudinary.uploader
from fichas.models import FichaPan
import cloudinary
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or 'dug5o1ps7',
    api_key    = os.environ.get('CLOUDINARY_API_KEY') or '291852661743715',
    api_secret = os.environ.get('CLOUDINARY_API_SECRET') or 'IrJ0vmsfd_3AMwBlkhtbiOUhDkc'
)

fichas_con_imagen = FichaPan.objects.exclude(imagen='').exclude(imagen=None)
total = fichas_con_imagen.count()
print(f"Fichas con imagen: {total}")

for i, ficha in enumerate(fichas_con_imagen, 1):
    ruta_local = os.path.join('media', str(ficha.imagen))
    
    if not os.path.exists(ruta_local):
        print(f"[{i}/{total}] ⚠️  Archivo no encontrado: {ruta_local}")
        continue

    try:
        resultado = cloudinary.uploader.upload(
            ruta_local,
            folder="panes",
            public_id=os.path.splitext(os.path.basename(str(ficha.imagen)))[0],
            overwrite=True
        )
        # Guardar la nueva URL de Cloudinary en la base de datos
        ficha.imagen = resultado['public_id'] + '.' + resultado['format']
        ficha.save()
        print(f"[{i}/{total}] ✅ {ficha.titulo}")
    except Exception as e:
        print(f"[{i}/{total}] ❌ Error en {ficha.titulo}: {e}")

print("\n🎉 Migración completada.")