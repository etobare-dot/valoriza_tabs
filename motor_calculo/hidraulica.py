"""
Cálculos hidráulicos de apoyo al dimensionamiento de obras.

Origen VBA: AlturaCal.bas (CalcularAlturaNormal) y la fórmula de altura
crítica repetida en Caida.bas y Partidor.bas.
"""

import math

GRAVEDAD = 9.81  # aceleración de gravedad (m/s²)


def altura_critica_rectangular(caudal: float, base: float) -> float:
    """Altura crítica de escurrimiento en un canal rectangular (m).

    hc = (Q² / (g·b²))^(1/3)

    Args:
        caudal: caudal de diseño Q (m³/s).
        base: ancho de la base del canal b (m).
    """
    return (caudal ** 2 / (GRAVEDAD * base ** 2)) ** (1 / 3)


def altura_normal_manning(
    caudal: float,
    base: float,
    talud: float,
    pendiente: float,
    manning: float,
    altura_inicial: float,
) -> float:
    """Altura normal de escurrimiento por Manning, resuelta con Newton-Raphson.

    Itera sobre la altura h hasta que el caudal calculado con la ecuación de
    Manning coincide con el caudal de diseño (tolerancia 0.0001 m³/s, máximo
    100 iteraciones).

    Se preservan dos decisiones del modelo VBA original:
    - El área se calcula como sección rectangular (A = h·b) aunque el
      perímetro mojado sí incorpora el talud.
    - Si la altura inicial entregada supera en más de 0.2 m a la altura
      convergida, se devuelve la altura inicial (el diseñador manda sobre
      el cálculo).

    Args:
        caudal: caudal de diseño Q (m³/s).
        base: ancho de la base del canal b (m).
        talud: talud de los muros m (horizontal/vertical, 0 = muros verticales).
        pendiente: pendiente longitudinal del canal S (m/m).
        manning: coeficiente de rugosidad de Manning n.
        altura_inicial: altura semilla de la iteración (m); habitualmente la
            altura existente del canal.

    Returns:
        Altura normal (m), o la altura inicial según la regla descrita.
    """
    tolerancia = 0.0001
    h = altura_inicial
    h_convergida = 0.0

    for _ in range(101):
        area = h * base
        perimetro = base + 2 * h * math.sqrt(1 + talud ** 2)
        radio_hidraulico = area / perimetro
        caudal_calculado = (
            (1 / manning) * area * radio_hidraulico ** (2 / 3) * math.sqrt(pendiente)
        )

        if abs(caudal - caudal_calculado) < tolerancia:
            h_convergida = h
            break

        # Paso de Newton-Raphson con derivada aproximada dQ/dh ≈ Q/h
        h = h - (caudal_calculado - caudal) / (caudal_calculado / h)

    if altura_inicial > h_convergida + 0.2:
        return altura_inicial
    return h
