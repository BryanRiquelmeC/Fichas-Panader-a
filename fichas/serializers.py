from rest_framework import serializers
from .models import FichaPan, FormatoVenta, PasoHorneado, Envase, MateriaPrima , Horneado

class MateriaPrimaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MateriaPrima
        fields = ['id', 'nombre', 'unidad', 'cantidad_receta']
    
class EnvaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envase
        fields= ['id', 'descripcion', 'unidad', 'cantidad_por_produccion', 'peso_envase_kg']

class FormatoVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatoVenta
        fields = ['id','cod_sap','descripcion','peso_producto_kg','cod_barra','cod_balanza']

class PasoHorneadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasoHorneado
        fields = ['id','orden','tiempo_min','descripcion']

class HorneadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horneado
        fields = ['id','temperatura_inicial_c', 'vapor_segundos', 'temperatura_final_c', 'tiempo_total_min', 'tiro', 'observaciones']

class FichaPanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FichaPan
        fields = ['id', 'titulo', 'codigo' , 'version', 'imagen']

class FichaPanDetailSerializer(serializers.ModelSerializer):
    materias_primas = MateriaPrimaSerializer(many=True, read_only=True)
    envases = EnvaseSerializer(many=True, read_only=True)
    formatos_venta = FormatoVentaSerializer(many=True, read_only=True)
    pasos_horneado = PasoHorneadoSerializer(many=True, read_only=True)
    horneado = HorneadoSerializer(read_only=True)

    class Meta:
        model = FichaPan
        fields = [
            "id", "seccion", "titulo", "codigo", "version", "fecha_revision", "pagina",
            "kg_producidos_receta", "kg_rendimiento_final", "unidades_rendimiento_final",
            "descripcion_proceso", "temperatura_almacenamiento", "vida_util_camara_dias",
            "vida_util_sala_ventas_dias", "notas", "harina_base_kg", "imagen",
            "materias_primas", "envases", "formatos_venta", "pasos_horneado", "horneado"
        ]