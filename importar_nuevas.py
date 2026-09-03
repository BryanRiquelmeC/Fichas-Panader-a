import os
import json
import django

from django.db import transaction

# --------------------------------------------------
# CONFIGURACIÓN DE DJANGO
# --------------------------------------------------

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panaderia.settings")
django.setup()

from fichas.models import (
    FichaPan,
    MateriaPrima,
    Envase,
    FormatoVenta,
    PasoHorneado,
    Horneado,
)


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

ARCHIVO = "nuevas_fichas.json"


# --------------------------------------------------
# CARGAR JSON
# --------------------------------------------------

print("\n========================================")
print(" IMPORTADOR DE NUEVAS FICHAS")
print("========================================\n")

print(f"Leyendo archivo: {ARCHIVO}")

with open(ARCHIVO, "r", encoding="utf-8") as archivo:
    datos = json.load(archivo)

print(f"Objetos encontrados en JSON: {len(datos)}")


# --------------------------------------------------
# SEPARAR FICHAS PRINCIPALES
# --------------------------------------------------

fichas_json = [
    objeto
    for objeto in datos
    if objeto["model"] == "fichas.fichapan"
]

print(f"Fichas principales encontradas: {len(fichas_json)}")


# --------------------------------------------------
# MOSTRAR FICHAS QUE SE VAN A IMPORTAR
# --------------------------------------------------

print("\nFichas que serán importadas:\n")

for objeto in fichas_json:
    fields = objeto["fields"]

    print(
        f"PK local: {objeto['pk']} | "
        f"Código: {fields['codigo']} | "
        f"Título: {fields['titulo']}"
    )


# --------------------------------------------------
# COMPROBAR CÓDIGOS DUPLICADOS
# --------------------------------------------------

codigos = [
    objeto["fields"]["codigo"]
    for objeto in fichas_json
]

duplicados = [
    codigo
    for codigo in codigos
    if FichaPan.objects.filter(codigo=codigo).exists()
]


if duplicados:

    print("\n========================================")
    print(" ERROR: CÓDIGOS YA EXISTENTES")
    print("========================================\n")

    for codigo in duplicados:
        print(f"Ya existe: {codigo}")

    print(
        "\nNo se importará ninguna ficha para evitar "
        "duplicados o modificaciones accidentales."
    )

    raise SystemExit(1)


# --------------------------------------------------
# MAPEO DE MODELOS
# --------------------------------------------------

modelos = {
    "fichas.materiaprima": MateriaPrima,
    "fichas.envase": Envase,
    "fichas.formatoventa": FormatoVenta,
    "fichas.pasohorneado": PasoHorneado,
    "fichas.horneado": Horneado,
}


# --------------------------------------------------
# IMPORTACIÓN
# --------------------------------------------------

print("\n========================================")
print(" INICIANDO IMPORTACIÓN")
print("========================================\n")


with transaction.atomic():

    # ----------------------------------------------
    # 1. CREAR FICHAS PRINCIPALES
    # ----------------------------------------------

    mapa_fichas = {}

    for objeto in fichas_json:

        fields = objeto["fields"].copy()

        # NO usamos el PK del JSON.
        # PostgreSQL generará uno nuevo.
        ficha = FichaPan.objects.create(**fields)

        mapa_fichas[objeto["pk"]] = ficha

        print(
            f"✓ Ficha creada: "
            f"{ficha.codigo} "
            f"(ID nuevo: {ficha.pk})"
        )


    # ----------------------------------------------
    # 2. CREAR REGISTROS RELACIONADOS
    # ----------------------------------------------

    contadores = {
        "fichas.materiaprima": 0,
        "fichas.envase": 0,
        "fichas.formatoventa": 0,
        "fichas.pasohorneado": 0,
        "fichas.horneado": 0,
    }


    for objeto in datos:

        modelo_nombre = objeto["model"]

        # Saltamos FichaPan porque ya fueron creadas
        if modelo_nombre == "fichas.fichapan":
            continue


        if modelo_nombre not in modelos:
            raise ValueError(
                f"Modelo no reconocido en JSON: {modelo_nombre}"
            )


        Model = modelos[modelo_nombre]

        fields = objeto["fields"].copy()


        # ------------------------------------------
        # RELACIÓN CON FICHAPAN
        # ------------------------------------------

        pk_ficha_local = fields.pop("ficha", None)


        if pk_ficha_local is None:

            raise ValueError(
                f"El objeto {objeto['pk']} "
                f"no tiene relación 'ficha'."
            )


        if pk_ficha_local not in mapa_fichas:

            raise ValueError(
                f"No se encontró la ficha local "
                f"{pk_ficha_local}."
            )


        # Reemplazamos el ID local por
        # la instancia nueva de FichaPan.
        fields["ficha"] = mapa_fichas[pk_ficha_local]


        # ------------------------------------------
        # CREAR REGISTRO
        # ------------------------------------------

        Model.objects.create(**fields)

        contadores[modelo_nombre] += 1


# --------------------------------------------------
# RESUMEN
# --------------------------------------------------

print("\n========================================")
print(" IMPORTACIÓN COMPLETADA")
print("========================================\n")

print(f"Fichas principales: {len(fichas_json)}")

print(
    f"Materias primas: "
    f"{contadores['fichas.materiaprima']}"
)

print(
    f"Envases: "
    f"{contadores['fichas.envase']}"
)

print(
    f"Formatos de venta: "
    f"{contadores['fichas.formatoventa']}"
)

print(
    f"Pasos de horneado: "
    f"{contadores['fichas.pasohorneado']}"
)

print(
    f"Registros de horneado: "
    f"{contadores['fichas.horneado']}"
)

print("\n✓ Todos los registros fueron importados correctamente.")