"""
Motor de cálculo de valorización de obras de riego (CNR).

Migración a Python del núcleo de cálculo de las macros VBA del libro
"Anexo 9-5 Desarrollo informatico v4.xlsm" (extraídas en
cnr_extract_macro_code/codigo_macro_anexo_9-5.txt).

El paquete cubre exclusivamente la base de cálculo, sin la capa de
presentación Excel (plantillas, protección de hojas, imágenes, PDF):

- hidraulica:    altura normal (Manning) y altura crítica.
- parametros:    cuantía de acero, espesor de revestimiento y módulos estándar.
- cubicaciones:  cantidades de obra por tipología (hormigón, enfierradura,
                 moldaje, movimiento de tierras, excedentes, etc.).
- tablas:        selección de fila en tablas de dimensiones estándar
                 (reemplaza las búsquedas sobre hojas CajonM/Arco/Compuerta).

Solo usa la biblioteca estándar de Python.
"""

from .hidraulica import GRAVEDAD, altura_critica_rectangular, altura_normal_manning
from .parametros import (
    cuantia_acero,
    espesor_revestimiento,
    numero_cajones_paralelos,
    numero_modulos_largo,
)
from .cubicaciones import (
    CubicacionCajon,
    CubicacionCanoa,
    CubicacionCompuerta,
    CubicacionDesarenador,
    CubicacionDisipador,
    CubicacionPartidor,
    CubicacionPortal,
    CubicacionRejaSifon,
    CubicacionReparacionSifon,
    CubicacionRevestimientoCanal,
    CubicacionTunelShotcrete,
    cubicacion_cajon,
    cubicacion_canoa,
    cubicacion_compuerta,
    cubicacion_desarenador,
    cubicacion_disipador,
    cubicacion_partidor,
    cubicacion_portal,
    cubicacion_reja_sifon,
    cubicacion_reparacion_sifon,
    cubicacion_revestimiento_canal,
    cubicacion_tunel_shotcrete,
)
from .tablas import buscar_fila_por_dimensiones, valor_mas_cercano
