"""
Valorización de obras: conecta el motor de cálculo con la tabla de precios.

Para cada tipología de obra define:
  - los campos que el usuario debe ingresar,
  - cómo cubicarla con motor_calculo,
  - qué código de precio unitario corresponde a cada cantidad cubicada
    (los códigos MTxxx replican los usados por la macro VBA original;
    los precios viven en precios.csv y son reemplazables por la CNR).

Solo usa la biblioteca estándar de Python.
"""

import csv
import os

from motor_calculo import (
    altura_normal_manning,
    buscar_fila_por_dimensiones,
    cubicacion_canoa,
    cubicacion_cajon,
    cubicacion_compuerta,
    cubicacion_desarenador,
    cubicacion_disipador,
    cubicacion_partidor,
    cubicacion_reja_sifon,
    cubicacion_reparacion_sifon,
    cubicacion_revestimiento_canal,
    cubicacion_tunel_shotcrete,
    espesor_revestimiento,
)

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_PRECIOS = os.path.join(DIRECTORIO_ACTUAL, "precios.csv")

# Valor de la UF usado para expresar el presupuesto en UF (referencial,
# mismo valor de la planilla original del 19-03-2026).
UF_CLP = 39841.72

# Parámetros hidráulicos fijos del modelo original (precioRevCanal, VBA):
PENDIENTE_CANAL = 0.001   # m/m
MANNING_HORMIGON = 0.018

# Porcentajes por defecto del presupuesto (los de la macro, btnVolver):
PORCENTAJES_DEFECTO = {"gastos_generales": 8.0, "utilidades": 15.0,
                       "imprevistos": 1.0, "iva": 19.0}

# Tabla referencial de cajones prefabricados estándar (base, alto, espesor, m).
# Reemplazar por la tabla real "CajonM" del libro Excel cuando esté disponible.
CAJONES_ESTANDAR = [
    (1.0, 1.0, 0.15),
    (1.5, 1.5, 0.15),
    (2.0, 1.5, 0.20),
    (2.0, 2.0, 0.20),
    (3.0, 2.0, 0.25),
]


PREFIJO_VECTOR_PRECIO = "precio_clp"


def listar_vectores_precio():
    """Detecta en precios.csv las columnas de precio disponibles.

    Cualquier columna que empiece con "precio_clp" se considera un vector
    de precios seleccionable (ej. "precio_clp", "precio_clp_zona_norte").
    Así, agregar un nuevo vector es solo agregar una columna al CSV: no
    requiere tocar este código.
    """
    with open(RUTA_PRECIOS, encoding="utf-8", newline="") as archivo:
        encabezado = next(csv.reader(archivo))
    columnas = [c for c in encabezado if c.startswith(PREFIJO_VECTOR_PRECIO)]
    vectores = []
    for col in columnas:
        resto = col[len(PREFIJO_VECTOR_PRECIO):].lstrip("_")
        etiqueta = resto.replace("_", " ").strip().capitalize() if resto else "Precios base"
        vectores.append({"id": col, "etiqueta": etiqueta})
    return vectores


def cargar_precios(vector_precio=PREFIJO_VECTOR_PRECIO):
    """Lee precios.csv y devuelve {codigo: {descripcion, unidad, precio_clp}}.

    vector_precio: nombre de la columna del CSV a usar como precio unitario
    (por defecto "precio_clp"). Permite tener varios vectores de precio
    (ej. por zona) en columnas distintas del mismo CSV.
    """
    precios = {}
    with open(RUTA_PRECIOS, encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        if vector_precio not in (lector.fieldnames or []):
            raise ValueError(f"Vector de precios desconocido: {vector_precio}")
        for fila in lector:
            precios[fila["codigo"]] = {
                "descripcion": fila["descripcion"],
                "unidad": fila["unidad"],
                "precio_clp": int(fila[vector_precio]),
            }
    return precios


# ---------------------------------------------------------------------------
# Cubicación por tipología
#
# Cada función recibe el dict de parámetros del usuario y devuelve:
#   partidas:     lista de (codigo_precio, cantidad)
#   informativos: lista de (nombre, valor, unidad) con datos calculados
#                 que no se valorizan pero ayudan a entender el resultado.
# ---------------------------------------------------------------------------

def _revestimiento_canal(p):
    altura_calculo = altura_normal_manning(
        p["caudal"], p["base"], p["talud"],
        PENDIENTE_CANAL, MANNING_HORMIGON, p["altura"],
    )
    espesor = espesor_revestimiento(altura_calculo)
    c = cubicacion_revestimiento_canal(
        p["largo"], p["base"], altura_calculo, espesor, p["talud"]
    )
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT033", c.excedentes_totales),
        ("MT001", c.emplantillado),
        ("MT026", c.base_granular),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT020", c.juntas_dilatacion),
        ("MT040", c.antisol),
    ]
    informativos = [
        ("Altura de calculo (Manning)", altura_calculo, "m"),
        ("Espesor de revestimiento", espesor, "m"),
    ]
    return partidas, informativos


def _disipador(p):
    c = cubicacion_disipador(p["caudal"], p["base"], p["altura"])
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT033", c.excedentes_totales),
        ("MT001", c.emplantillado),
        ("MT026", c.base_granular),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT040", c.antisol),
    ]
    return partidas, [("Largo del disipador", c.largo, "m")]


def _desarenador(p):
    c = cubicacion_desarenador(p["caudal"], p["ancho"], p["alto"])
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT033", c.excedentes_totales),
        ("MT001", c.emplantillado),
        ("MT026", c.base_granular),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT040", c.antisol),
    ]
    return partidas, [("Largo de decantacion", c.largo, "m")]


def _partidor(p):
    c = cubicacion_partidor(p["caudal"], p["base"], p["altura"])
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT033", c.excedentes_totales),
        ("MT001", c.emplantillado),
        ("MT026", c.base_granular),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT040", c.antisol),
    ]
    return partidas, []


def _compuerta(p):
    c = cubicacion_compuerta(p["base"], p["altura"])
    partidas = [
        ("MT035", 1),
        ("MT042", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT036", c.demolicion),
        ("MT033", c.excedentes_totales),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT040", c.antisol),
    ]
    return partidas, []


def _cajon(p):
    base_std, alto_std, espesor_std = buscar_fila_por_dimensiones(
        CAJONES_ESTANDAR, p["ancho_canal"], p["alto_canal"]
    )
    c = cubicacion_cajon(
        p["largo"], p["ancho_canal"], base_std, alto_std, espesor_std
    )
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT033", c.excedentes_totales),
        ("MT026", c.base_granular),
        ("MT041", c.largo_cajones),
        ("MT040", c.antisol),
    ]
    informativos = [
        ("Cajon estandar seleccionado (b x h x e)",
         f"{base_std} x {alto_std} x {espesor_std}", "m"),
    ]
    return partidas, informativos


def _canoa(p):
    c = cubicacion_canoa(p["largo"], p["base"], p["altura"])
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT036", c.demolicion),
        ("MT033", c.excedentes_totales),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT040", c.antisol),
    ]
    return partidas, []


def _reparacion_sifon(p):
    c = cubicacion_reparacion_sifon(
        p["largo"], p["base"], p["altura"], p["espesor"]
    )
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT021", c.excavacion),
        ("MT024", c.relleno),
        ("MT036", c.demolicion),
        ("MT033", c.excedentes_totales),
        ("MT003", c.hormigon),
        ("MT011", c.enfierradura),
        ("MT018", c.moldaje),
        ("MT040", c.antisol),
    ]
    return partidas, []


def _reja_sifon(p):
    c = cubicacion_reja_sifon(p["base"], p["altura"])
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT033", c.excedentes_totales),
        ("MT039", c.peso_reja),
    ]
    return partidas, [("Metros lineales de pletina", c.metros_pletina, "m")]


def _tunel_shotcrete(p):
    c = cubicacion_tunel_shotcrete(p["largo"], p["base"], p["altura"])
    partidas = [
        ("MT035", 1),
        ("MT027", c.escarpe),
        ("MT033", c.excedentes_totales),
        ("MT037", c.superficie_shotcrete),
        ("MT038", c.superficie_shotcrete),
    ]
    return partidas, []


def _campo(nombre, etiqueta, unidad, defecto):
    """Describe un campo de entrada para el formulario del frontend."""
    return {"nombre": nombre, "etiqueta": etiqueta, "unidad": unidad,
            "defecto": defecto}


# Registro de tipologías: define el formulario y la función de cubicación.
TIPOLOGIAS = {
    "revestimiento_canal": {
        "titulo": "Mejoramiento tramo canal mediante revestimiento",
        "campos": [
            _campo("caudal", "Caudal de diseno", "m3/s", 0.67),
            _campo("largo", "Largo del tramo", "m", 100.0),
            _campo("base", "Ancho de la base", "m", 1.0),
            _campo("altura", "Altura del canal existente", "m", 1.0),
            _campo("talud", "Talud de los muros (0 = verticales)", "-", 0.0),
        ],
        "cubicar": _revestimiento_canal,
    },
    "disipador": {
        "titulo": "Mejoramiento disipador de energia",
        "campos": [
            _campo("caudal", "Caudal de diseno", "m3/s", 0.67),
            _campo("base", "Ancho de la base", "m", 1.0),
            _campo("altura", "Altura de la caida", "m", 1.0),
        ],
        "cubicar": _disipador,
    },
    "desarenador": {
        "titulo": "Reposicion de bocatoma (desarenador)",
        "campos": [
            _campo("caudal", "Caudal de diseno", "m3/s", 0.67),
            _campo("ancho", "Ancho del canal de entrada", "m", 1.0),
            _campo("alto", "Altura de escurrimiento", "m", 1.0),
        ],
        "cubicar": _desarenador,
    },
    "partidor": {
        "titulo": "Reposicion marco partidor",
        "campos": [
            _campo("caudal", "Caudal de diseno", "m3/s", 0.67),
            _campo("base", "Ancho de la base", "m", 1.0),
            _campo("altura", "Altura del canal", "m", 1.0),
        ],
        "cubicar": _partidor,
    },
    "compuerta": {
        "titulo": "Reposicion de compuerta",
        "campos": [
            _campo("base", "Ancho del canal en la compuerta", "m", 1.0),
            _campo("altura", "Altura del canal en la compuerta", "m", 1.0),
        ],
        "cubicar": _compuerta,
    },
    "cajon": {
        "titulo": "Mejoramiento o construccion de cajon de hormigon",
        "campos": [
            _campo("largo", "Largo del tramo", "m", 20.0),
            _campo("ancho_canal", "Ancho del canal", "m", 1.5),
            _campo("alto_canal", "Alto del canal", "m", 1.5),
        ],
        "cubicar": _cajon,
    },
    "canoa": {
        "titulo": "Restauracion canoa",
        "campos": [
            _campo("largo", "Largo de la canoa", "m", 24.0),
            _campo("base", "Ancho interior", "m", 1.0),
            _campo("altura", "Altura interior", "m", 1.0),
        ],
        "cubicar": _canoa,
    },
    "reparacion_sifon": {
        "titulo": "Restauracion tramo sifon",
        "campos": [
            _campo("largo", "Largo del tramo", "m", 20.0),
            _campo("base", "Ancho de la caja", "m", 1.0),
            _campo("altura", "Altura de la caja", "m", 1.0),
            _campo("espesor", "Espesor de reposicion", "m", 0.2),
        ],
        "cubicar": _reparacion_sifon,
    },
    "reja_sifon": {
        "titulo": "Mejoramiento sifon en obra de entrada (reja)",
        "campos": [
            _campo("base", "Ancho de la boca", "m", 1.0),
            _campo("altura", "Alto de la boca", "m", 1.0),
        ],
        "cubicar": _reja_sifon,
    },
    "tunel_shotcrete": {
        "titulo": "Mejoramiento tramo tunel (shotcrete)",
        "campos": [
            _campo("largo", "Largo del tramo", "m", 50.0),
            _campo("base", "Ancho del tunel", "m", 2.0),
            _campo("altura", "Alto del tunel", "m", 2.0),
        ],
        "cubicar": _tunel_shotcrete,
    },
}


def listar_tipologias():
    """Devuelve las tipologías disponibles con sus formularios (para la UI)."""
    return [
        {"id": id_, "titulo": t["titulo"], "campos": t["campos"]}
        for id_, t in TIPOLOGIAS.items()
    ]


def valorizar(tipologia_id, parametros, porcentajes=None, vector_precio=PREFIJO_VECTOR_PRECIO):
    """Cubica una obra y arma su presupuesto valorizado.

    Args:
        tipologia_id: clave de TIPOLOGIAS.
        parametros: dict {nombre_campo: valor numérico} según los campos
            declarados por la tipología.
        porcentajes: dict opcional con gastos_generales, utilidades,
            imprevistos e iva (en %, ej. 8.0); si falta alguno se usa el
            valor por defecto de la macro original.
        vector_precio: columna de precios.csv a usar (ver listar_vectores_precio()).

    Returns:
        Dict con partidas valorizadas, datos informativos y resumen de
        costos (CLP y UF), listo para serializar a JSON.

    Raises:
        KeyError / ValueError: tipología desconocida o parámetros incompletos.
    """
    if tipologia_id not in TIPOLOGIAS:
        raise ValueError(f"Tipologia desconocida: {tipologia_id}")
    tipologia = TIPOLOGIAS[tipologia_id]

    faltantes = [c["nombre"] for c in tipologia["campos"]
                 if c["nombre"] not in parametros]
    if faltantes:
        raise ValueError(f"Faltan parametros: {', '.join(faltantes)}")

    valores = {c["nombre"]: float(parametros[c["nombre"]])
               for c in tipologia["campos"]}

    pct = dict(PORCENTAJES_DEFECTO)
    pct.update(porcentajes or {})

    precios = cargar_precios(vector_precio)
    cantidades, informativos = tipologia["cubicar"](valores)

    partidas = []
    costo_directo = 0.0
    for codigo, cantidad in cantidades:
        precio = precios[codigo]
        subtotal = cantidad * precio["precio_clp"]
        costo_directo += subtotal
        partidas.append({
            "codigo": codigo,
            "descripcion": precio["descripcion"],
            "unidad": precio["unidad"],
            "cantidad": round(cantidad, 2),
            "precio_clp": precio["precio_clp"],
            "subtotal_clp": round(subtotal),
            "subtotal_uf": round(subtotal / UF_CLP, 2),
        })

    gastos_generales = costo_directo * pct["gastos_generales"] / 100
    utilidades = costo_directo * pct["utilidades"] / 100
    imprevistos = costo_directo * pct["imprevistos"] / 100
    neto = costo_directo + gastos_generales + utilidades + imprevistos
    iva = neto * pct["iva"] / 100
    total = neto + iva

    def _monto(clp):
        return {"clp": round(clp), "uf": round(clp / UF_CLP, 2)}

    return {
        "tipologia": tipologia["titulo"],
        "partidas": partidas,
        "informativos": [
            {"nombre": n, "valor": v if isinstance(v, str) else round(v, 3),
             "unidad": u}
            for n, v, u in informativos
        ],
        "porcentajes": pct,
        "resumen": {
            "costo_directo": _monto(costo_directo),
            "gastos_generales": _monto(gastos_generales),
            "utilidades": _monto(utilidades),
            "imprevistos": _monto(imprevistos),
            "neto": _monto(neto),
            "iva": _monto(iva),
            "total": _monto(total),
        },
        "uf_clp": UF_CLP,
        "vector_precio": vector_precio,
    }
