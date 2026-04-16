from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import FichaPanListSerializer, FichaPanDetailSerializer
from decimal import Decimal
from .models import FichaPan



# ============================================
# LISTA DE FICHAS (BUSCADOR PROFESIONAL)
# ============================================

def lista_fichas(request):
    # 1. Obtener el texto del buscador
    q = request.GET.get("q", "").strip()

    # 2. Base query ordenada alfabéticamente
    fichas = FichaPan.objects.all().order_by("titulo")

    # 3. Si hay búsqueda, filtrar por nombre o código
    if q:
        fichas = fichas.filter(
            Q(titulo__icontains=q) |
            Q(codigo__icontains=q)
        )

    context = {
        "fichas": fichas,
        "q": q,              # mantengo el valor del buscador
        "total": fichas.count(),  # cantidad de resultados
    }

    return render(request, "fichas/lista.html", context)


# ============================================
# DETALLE FICHA + CALCULADORA (NO MODIFICAR)
# ============================================

def detalle_ficha(request, id):
    ficha = get_object_or_404(FichaPan, id=id)

    # obtener harina deseada desde el GET (si no viene, usamos la base)
    harina_deseada = request.GET.get("harina", ficha.harina_base_kg)
    harina_deseada = Decimal(harina_deseada)

    factor = ficha.factor_por_harina(harina_deseada)
    rendimiento = ficha.rendimiento_escalado_unidades(factor)

    materias = []
    for mp in ficha.materias_primas.all():
        materias.append({
            "nombre": mp.nombre,
            "unidad": mp.unidad,
            "base": mp.cantidad_receta,
            "ajustada": mp.cantidad_escalada(factor),
        })

    return render(request, "fichas/detalle.html", {
        "ficha": ficha,
        "harina_deseada": harina_deseada,
        "factor": factor,
        "rendimiento_escalado": rendimiento,
        "materias": materias,
        "pasos": ficha.pasos_horneado.all(),
        "envases": ficha.envases.all(),
        "formatos": ficha.formatos_venta.all(),
    })

def autocomplete_fichas(request):
    q = request.GET.get("q", "").strip()

    resultados = []

    if q:
        palabras = q.split()
        fichas = FichaPan.objects.all()

        for palabra in palabras:
            fichas = fichas.filter(
                Q(titulo__icontains=palabra) |
                Q(codigo__icontains=palabra)
            )

        for ficha in fichas[:10]:  # máximo 10 sugerencias
            resultados.append({
                "id": ficha.id,
                "titulo": ficha.titulo,
                "codigo": ficha.codigo
            })

    return JsonResponse(resultados, safe=False)


# CREANDO ENDPOINTS AJAX EVITAR SCROLL

def calcular_ajax(request, id):
    ficha = get_object_or_404(FichaPan, id=id)

    harina = Decimal(request.GET.get("harina", ficha.harina_base_kg))
    factor = ficha.factor_por_harina(harina)
    rendimiento = ficha.rendimiento_escalado_unidades(factor)

    materias = []
    for mp in ficha.materias_primas.all():
        materias.append({
            "nombre": mp.nombre,
            "unidad": mp.unidad,
            "base": float(mp.cantidad_receta),
            "ajustada": float(mp.cantidad_escalada(factor)),
        })

    return JsonResponse({
        "factor": float(factor),
        "rendimiento": rendimiento,
        "materias": materias
    })




@api_view(["GET"])
def api_fichas_list(request):
    fichas = FichaPan.objects.all().order_by("titulo")
    data = FichaPanListSerializer(fichas, many=True, context={"request": request}).data
    return Response(data)

@api_view(["GET"])
def api_ficha_detalle(request, id):
    ficha = FichaPan.objects.get(id=id)
    data = FichaPanDetailSerializer(ficha, context={"request": request}).data
    return Response(data)

@login_required
def menu_principal(request):
    return render(request, 'accounts/menu_principal.html')
