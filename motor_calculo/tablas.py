"""
Selección de filas en tablas de dimensiones estándar.

Reemplaza las búsquedas VBA sobre las hojas de Excel "CajonM", "Arco" y
"Compuerta" (FPortal.bas: ValorMasCercanoInteligente, BuscarRangoRepetidos,
ObtenerFila y buscarByH). Aquí la tabla es una lista de filas (secuencias o
diccionarios) ya cargada en memoria, por ejemplo desde un CSV.
"""


def valor_mas_cercano(valores, objetivo):
    """Selecciona el valor "más cercano inteligente" a un objetivo.

    Regla del original VBA: se prefiere el menor valor que sea mayor o igual
    al objetivo (la dimensión estándar que cubre lo requerido); si ninguno lo
    alcanza, se toma el más cercano en valor absoluto.

    Args:
        valores: valores numéricos candidatos.
        objetivo: valor buscado.

    Returns:
        El valor seleccionado.

    Raises:
        ValueError: si la secuencia está vacía.
    """
    valores = list(valores)
    if not valores:
        raise ValueError("No hay valores donde buscar")

    mayores_o_iguales = [v for v in valores if v >= objetivo]
    if mayores_o_iguales:
        return min(mayores_o_iguales, key=lambda v: v - objetivo)
    return min(valores, key=lambda v: abs(v - objetivo))


def buscar_fila_por_dimensiones(filas, base, altura, columna_base=0, columna_altura=1):
    """Selecciona la fila de una tabla de dimensiones estándar según base y altura.

    Replica buscarByH del VBA: primero se elige la base estándar más adecuada
    (ver valor_mas_cercano); luego, entre las filas con esa base, se elige la
    de altura más adecuada con la misma regla.

    Args:
        filas: tabla como lista de filas; cada fila es una secuencia o un
            diccionario del que se extraen base y altura.
        base: ancho requerido (m).
        altura: alto requerido (m).
        columna_base: índice o clave de la columna con la base estándar.
        columna_altura: índice o clave de la columna con la altura estándar.

    Returns:
        La fila seleccionada (el mismo objeto contenido en `filas`).
    """
    filas = list(filas)
    base_elegida = valor_mas_cercano((fila[columna_base] for fila in filas), base)

    candidatas = [fila for fila in filas if fila[columna_base] == base_elegida]
    altura_elegida = valor_mas_cercano(
        (fila[columna_altura] for fila in candidatas), altura
    )

    for fila in candidatas:
        if fila[columna_altura] == altura_elegida:
            return fila
    raise AssertionError("inalcanzable: la altura elegida proviene de las candidatas")
