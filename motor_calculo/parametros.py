"""
Parámetros de diseño derivados de la geometría de la obra.

Origen VBA: Cuantia.bas (cuant), Espes.bas (Espesor),
Num2.bas (enedo) y Num3.bas (enetr).
"""


def cuantia_acero(altura: float) -> float:
    """Cuantía de enfierradura (kg de acero por m³ de hormigón) según altura.

    Escalones definidos por la CNR para muros de obras de riego:
    hasta 1 m → 50 kg/m³; hasta 2 m → 80 kg/m³; sobre 2 m → 100 kg/m³.

    Args:
        altura: altura del muro o revestimiento (m).
    """
    if altura <= 0:
        return 0.0
    if altura <= 1:
        return 50.0
    if altura <= 2:
        return 80.0
    return 100.0


def espesor_revestimiento(altura: float) -> float:
    """Espesor del revestimiento de hormigón (m) según altura de escurrimiento.

    Bajo 1.6 m el espesor es constante (0.13 m); entre 1.6 y 2.4 m crece
    8.333 mm por cada 0.1 m; sobre 2.4 m crece 6.667 mm por cada 0.1 m.

    Args:
        altura: altura de escurrimiento (m).
    """
    if altura <= 1.6:
        return 0.13
    if altura <= 2.4:
        return 0.13 + ((altura - 1.6) / 0.1) * 0.008333
    return 0.2 + ((altura - 2.4) / 0.1) * 0.0066666


def numero_cajones_paralelos(ancho: float) -> int:
    """Número de cajones estándar (módulos de 3 m) para cubrir un ancho de canal.

    Args:
        ancho: ancho del canal (m).
    """
    return int((ancho - 0.15) / 3) + 1


def numero_modulos_largo(largo: float) -> int:
    """Número de módulos estándar de 2 m para cubrir un largo dado.

    Args:
        largo: largo a cubrir (m).
    """
    return int(largo / 2) + 1
