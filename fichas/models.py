from django.db import models
from decimal import Decimal

class FichaPan(models.Model):
    seccion = models.CharField(
        max_length=50,
        default="Panadería",
    
    )
    imagen = models.ImageField(
        upload_to="panes/",
        null=True,
        blank=True
    )

    titulo = models.CharField(
        max_length=150,
        verbose_name="Nombre ficha / producto",
        help_text="Ej: FICHA TÉCNICA TREKKING BREAD JUMBO UN"
    )

    codigo = models.CharField(
        max_length=30,
        verbose_name="Código documento",
        help_text="Ej: 3514-D-PAN-058"
    )

    version = models.CharField(
        max_length=10,
        verbose_name="Versión",
        default="000"
    )

    fecha_revision = models.DateField(
        verbose_name="Fecha de revisión"
    )

    pagina = models.CharField(
        max_length=20,
        verbose_name="Página",
        blank=True
    )

    # RENDIMIENTO
    kg_producidos_receta = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        verbose_name="Kg producidos en base a receta"
    )

    kg_rendimiento_final = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        verbose_name="Kg rendimiento final"
    )

    unidades_rendimiento_final = models.PositiveIntegerField(
        verbose_name="Unidades rendimiento final"
    )

    # DESCRIPCIÓN DETALLADA DEL PROCESO (recuadro grande de la derecha)
    descripcion_proceso = models.TextField(
        verbose_name="Descripción detallada del proceso"
    )

    # DATOS DE PROCESO / ALMACENAMIENTO (simplificado para MVP)
    temperatura_horneado_c = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Temperatura de horneo (°C)"
    )

    tiempo_horneado_min = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Tiempo de horneo (min)"
    )

    temperatura_almacenamiento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Temperatura de almacenamiento",
        help_text="Ej: Temperatura ambiente, Cámara de frío, etc."
    )

    vida_util_camara_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Vida útil en cámara (días)"
    )

    vida_util_sala_ventas_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Vida útil en sala de ventas (días)"
    )

    notas = models.TextField(
        blank=True,
        verbose_name="Notas adicionales / advertencias"
    )

    # Para la calculadora (harina base)
    harina_base_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Harina base (kg) para cálculo",
        help_text="Harina usada en la receta base (ej: 16.00 kg)"
    )

    def __str__(self):
        return f"{self.titulo} ({self.codigo})"

    # Métodos de cálculo para escalado

    def factor_por_harina(self, harina_deseada_kg) -> Decimal:
        """
        Ej: harina_base_kg = 16, quiero 8 -> factor = 0.5
        """
        harina_deseada = Decimal(harina_deseada_kg)

        if not self.harina_base_kg or self.harina_base_kg == Decimal("0"):
            # por seguridad, si no hay harina base, devolvemos factor 1
            return Decimal("1.000")

        factor = harina_deseada / Decimal(self.harina_base_kg)
        # Redondeamos a 1 decimal, estándar industrial
        return factor.quantize(Decimal("0.1"))

    def rendimiento_escalado_unidades(self, factor: Decimal) -> int:
        return int(self.unidades_rendimiento_final * factor)


class MateriaPrima(models.Model):
    ficha = models.ForeignKey(
        FichaPan,
        related_name="materias_primas",
        on_delete=models.CASCADE
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name="Materia prima"
    )

    unidad = models.CharField(
        max_length=20,
        verbose_name="Unidad",
        help_text="Ej: Kg, Lt, g"
    )

    cantidad_receta = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        verbose_name="Cantidad receta"
    )

    cantidad_batida = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        verbose_name="Cantidad batida",
        null=True,
        blank=True
    )

    es_harina_base = models.BooleanField(
        default=False,
        verbose_name="¿Es la harina base?"
    )

    def __str__(self):
        return f"{self.nombre} ({self.ficha.titulo})"

    def cantidad_escalada(self, factor: Decimal):
        resultado = Decimal(self.cantidad_receta) * Decimal(factor)
        
        return resultado.quantize(Decimal("0.001"))



class Envase(models.Model):
    ficha = models.ForeignKey(
        FichaPan,
        related_name="envases",
        on_delete=models.CASCADE
    )

    descripcion = models.CharField(
        max_length=150,
        verbose_name="Descripción",
        help_text="Ej: ETIQUETA DIGI 12.3 x 5.7 cm"
    )

    unidad = models.CharField(
        max_length=20,
        verbose_name="Unidad",
        help_text="Ej: un, rollo, saco"
    )

    cantidad_por_produccion = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        verbose_name="Cantidad por producción"
    )

    peso_envase_kg = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        verbose_name="Peso envase (kg)",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.descripcion


class FormatoVenta(models.Model):
    ficha = models.ForeignKey(
        FichaPan,
        related_name="formatos_venta",
        on_delete=models.CASCADE
    )

    cod_sap = models.CharField(
        max_length=20,
        verbose_name="Código SAP"
    )

    descripcion = models.CharField(
        max_length=150,
        verbose_name="Descripción"
    )

    peso_producto_kg = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        verbose_name="Peso producto (kg)"
    )

    cod_barra = models.CharField(
        max_length=50,
        verbose_name="Código de barras",
        blank=True
    )

    cod_balanza = models.CharField(
        max_length=50,
        verbose_name="Código balanza",
        blank=True
    )

    def __str__(self):
        return f"{self.descripcion} ({self.cod_sap})"

class PasoHorneado(models.Model):
    ficha = models.ForeignKey(
        FichaPan,
        related_name="pasos_horneado",
        on_delete=models.CASCADE
    )

    orden = models.PositiveIntegerField(
        verbose_name="Orden del paso",
        help_text="Ej: 1, 2, 3..."
    )

    tiempo_min = models.PositiveIntegerField(
        verbose_name="Tiempo en minutos"
    )

    descripcion = models.CharField(
        max_length=200,
        verbose_name="Descripción del paso",
        help_text="Ej: 30 min con tiraje abierto"
    )

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return f"Paso {self.orden}: {self.descripcion}"
    
    
class Horneado(models.Model):
    ficha = models.OneToOneField(
        FichaPan,
        related_name="horneado",
        on_delete=models.CASCADE
    )

    temperatura_inicial_c = models.PositiveIntegerField(
        verbose_name="Temperatura inicial (°C)",
        help_text="Ej: 250"
    )

    vapor_segundos = models.PositiveIntegerField(
        verbose_name="Vapor (segundos)",
        null=True, blank=True,
        help_text="Ej: 2 segundos"
    )

    temperatura_final_c = models.PositiveIntegerField(
        verbose_name="Temperatura final (°C)",
        help_text="Ej: 180"
    )

    tiempo_total_min = models.PositiveIntegerField(
        verbose_name="Tiempo total (min)",
        help_text="Ej: 30"
    )

    tiro = models.CharField(
        max_length=50,
        verbose_name="Tiro (abierto/cerrado)",
        blank=True,
        help_text="Ej: tiro cerrado"
    )

    observaciones = models.TextField(
        blank=True,
        verbose_name="Notas adicionales de horneado"
    )

    def __str__(self):
        return f"Horneado — {self.ficha.titulo}"

