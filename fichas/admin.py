from django.contrib import admin
from .models import FichaPan, MateriaPrima, Envase, FormatoVenta, PasoHorneado, Horneado


class MateriaPrimaInline(admin.TabularInline):
    model = MateriaPrima
    extra = 1  # cuántas filas vacías muestra por defecto


class EnvaseInline(admin.TabularInline):
    model = Envase
    extra = 1


class FormatoVentaInline(admin.TabularInline):
    model = FormatoVenta
    extra = 1

class PasoHorneadoInline(admin.TabularInline):
    model = PasoHorneado
    extra = 1

class HorneadoInline(admin.StackedInline):
    model = Horneado
    extra = 0


@admin.register(FichaPan)
class FichaPanAdmin(admin.ModelAdmin):
    list_display = ("titulo", "codigo", "version", "fecha_revision")
    search_fields = ("titulo", "codigo")
    inlines = [MateriaPrimaInline, EnvaseInline, FormatoVentaInline, PasoHorneadoInline, HorneadoInline,]

