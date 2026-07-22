"""
Cubicación de obras de riego: cantidades de obra por tipología.

Cada función migra una función VBA de cubicación (módulos CubCanal, Caida,
Desarenador, Partidor, Compuerta, CCaj, CPort, RepCanoa, RepSifon, SifonReja
y TunelShot) y devuelve una dataclass con las partidas nombradas, en lugar
del patrón original `arr(indice)` que obligaba a conocer índices mágicos.

Convenciones de unidades:
- volúmenes en m³, superficies en m², longitudes en m, acero en kg.
- "moldaje" es la superficie de moldaje en m² (en el VBA se estimaba como
  ~10 o 12 m² por m³ de hormigón).
- "excedentes" son los volúmenes a retirar a botadero, esponjados un 10%.
"""

from dataclasses import dataclass

from .hidraulica import GRAVEDAD, altura_critica_rectangular
from .parametros import cuantia_acero, numero_cajones_paralelos

ESPONJAMIENTO = 0.10        # aumento de volumen del material excavado
ESPESOR_ESCARPE = 0.15      # espesor de escarpe del terreno (m)
DENSIDAD_ACERO = 7900       # kg/m³


def _excedentes(escarpe: float, excavacion: float, relleno: float):
    """Excedentes a botadero: escarpe esponjado + saldo de excavación esponjado.

    El saldo excavación - relleno solo aporta si es positivo (si el relleno
    supera a la excavación no hay material sobrante que retirar).

    Returns:
        Tupla (excedente de escarpe, excedente de excavación, total).
    """
    excedente_escarpe = escarpe * (1 + ESPONJAMIENTO)
    saldo = excavacion - relleno
    excedente_excavacion = saldo * (1 + ESPONJAMIENTO) if saldo > 0 else 0.0
    return excedente_escarpe, excedente_excavacion, excedente_escarpe + excedente_excavacion


# ---------------------------------------------------------------------------
# Revestimiento de canal (CubCanal.bas: cubicar)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionRevestimientoCanal:
    """Cantidades de obra del revestimiento de un tramo de canal."""

    hormigon: float             # m³ hormigón del revestimiento (losa + muros)
    enfierradura: float         # kg de acero de refuerzo
    moldaje: float              # m² de moldaje
    emplantillado: float        # m³ hormigón de limpieza G05 (5 cm bajo la losa)
    base_granular: float        # m³ de base granular (10 cm bajo la losa)
    juntas_dilatacion: float    # m de juntas (una sección cada 5 m)
    antisol: float              # m² de aplicación de curado químico
    roce_faja: float            # m² de roce y despeje de la faja (3 m a cada lado)
    escarpe: float              # m³ de escarpe de la faja
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado a botadero
    excedente_excavacion: float # m³ de saldo de excavación esponjado a botadero
    excedentes_totales: float   # m³ totales a botadero


def cubicacion_revestimiento_canal(
    largo: float, base: float, altura: float, espesor: float, talud: float
) -> CubicacionRevestimientoCanal:
    """Cubica el revestimiento de hormigón de un tramo de canal trapezoidal.

    La sección se compone de una losa de fondo de ancho (b + 2e) y dos muros
    inclinados de desarrollo h·√(1+m²), todos de espesor e.

    En el flujo original, la altura y el espesor provienen del cálculo
    hidráulico: h = altura_normal_manning(...) y e = espesor_revestimiento(h).

    Args:
        largo: largo del tramo L (m).
        base: ancho de la base del canal b (m).
        altura: altura de revestimiento h (m).
        espesor: espesor del revestimiento e (m).
        talud: talud de los muros m (0 = muros verticales).
    """
    desarrollo_muro = altura * (1 + talud ** 2) ** 0.5

    hormigon = espesor * (largo * (base + 2 * espesor)) + espesor * 2 * (largo * desarrollo_muro)
    superficie_fondo = largo * (base + 2 * espesor)

    roce_faja = largo * (base + 3 + 3)
    escarpe = roce_faja * ESPESOR_ESCARPE
    excavacion = largo * base
    relleno = largo * (altura + espesor + 0.1 + 0.05) * 0.5 * 2
    exc_escarpe, exc_excavacion, exc_totales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionRevestimientoCanal(
        hormigon=hormigon,
        enfierradura=hormigon * cuantia_acero(altura),
        moldaje=hormigon * 10,
        emplantillado=0.05 * superficie_fondo,
        base_granular=0.1 * superficie_fondo,
        juntas_dilatacion=(largo / 5) * (base + 2 * desarrollo_muro),
        antisol=2 * (largo * desarrollo_muro) * 2,
        roce_faja=roce_faja,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_totales,
    )


# ---------------------------------------------------------------------------
# Disipador de energía / caída (Caida.bas: CubCaida)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionDisipador:
    """Cantidades de obra de un disipador de energía (caída con resalto)."""

    hormigon: float             # m³ hormigón (losa + muros de altura h + grada)
    enfierradura: float         # kg de acero de refuerzo
    moldaje: float              # m² de moldaje
    emplantillado: float        # m³ hormigón de limpieza G05
    base_granular: float        # m³ de base granular
    antisol: float              # m² de curado químico
    roce_faja: float            # m² de roce y despeje de la faja
    escarpe: float              # m³ de escarpe
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ totales a botadero
    largo: float                # m, largo total del disipador (caída + resalto)


def cubicacion_disipador(caudal: float, base: float, altura: float) -> CubicacionDisipador:
    """Cubica un disipador de energía dimensionado desde el caudal.

    El largo de la obra se deduce con fórmulas empíricas de caída vertical:
    altura crítica hc, grada a = 1.1·hc, alturas conjugadas hi e ho, longitud
    de caída Ld y de resalto Lr. Espesor de muros y losa fijo en 0.2 m.

    Args:
        caudal: caudal de diseño Q (m³/s).
        base: ancho de la base del canal b (m).
        altura: altura de la caída h (m).
    """
    espesor = 0.2
    hc = altura_critica_rectangular(caudal, base)
    grada = 1.1 * hc
    h_ingreso = 0.54 * grada * (altura / grada) ** 1.275
    h_salida = 1.66 * grada * (altura / grada) ** 0.81
    largo_caida = 4.3 * grada * (altura / grada) ** 0.81
    largo_resalto = 6.9 * (h_salida - h_ingreso)
    largo = largo_caida + largo_resalto

    altura_final = altura + grada     # altura de los muros en la zona de caída
    altura_muro = altura + espesor

    hormigon = (
        espesor * (largo * (base + 2 * espesor))
        + espesor * 2 * (largo * altura_final)
    )
    superficie_fondo = largo * (base + 2 * espesor)

    roce_faja = largo * (base + 3 + 3)
    escarpe = roce_faja * ESPESOR_ESCARPE
    excavacion = largo * base
    relleno = largo * (altura_muro + 0.1 + 0.05) * 0.5 * 2
    exc_escarpe, exc_excavacion, exc_totales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionDisipador(
        hormigon=hormigon,
        enfierradura=hormigon * cuantia_acero(altura_final),
        moldaje=hormigon * 10,
        emplantillado=0.05 * superficie_fondo,
        base_granular=0.1 * superficie_fondo,
        antisol=(2 * (largo * altura_final)) * 2,
        roce_faja=roce_faja,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_totales,
        largo=largo,
    )


# ---------------------------------------------------------------------------
# Desarenador (Desarenador.bas: CubDesarenador)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionDesarenador:
    """Cantidades de obra de un desarenador."""

    hormigon: float             # m³ hormigón (losa + muros verticales)
    enfierradura: float         # kg de acero (80 kg/m³ fijo)
    moldaje: float              # m² de moldaje (12 m²/m³)
    emplantillado: float        # m³ hormigón de limpieza G05
    base_granular: float        # m³ de base granular
    antisol: float              # m² de curado químico
    roce_faja: float            # m² de roce y despeje (2 m a cada lado)
    escarpe: float              # m³ de escarpe
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ totales a botadero
    largo: float                # m, largo de decantación calculado


def cubicacion_desarenador(caudal: float, ancho: float, alto: float) -> CubicacionDesarenador:
    """Cubica un desarenador dimensionado desde el caudal del canal.

    La cámara se ensancha a 3 veces el ancho del canal y se profundiza 0.5 m
    sobre la altura de escurrimiento. El largo de decantación se calcula con
    la velocidad de paso y una velocidad de sedimentación de referencia
    (w ≈ 0.0512 m/s), más 1 m de transición. Espesor fijo de 0.2 m.

    Args:
        caudal: caudal de diseño Q (m³/s).
        ancho: ancho del canal de entrada (m).
        alto: altura de escurrimiento del canal (m).
    """
    espesor = 0.2
    base = ancho * 3
    altura = alto + 0.5

    velocidad_paso = caudal / (altura * base)
    velocidad_sedimentacion = (0.0088 + 10.221 * 0.5) / 100
    largo = (velocidad_paso * altura) / velocidad_sedimentacion + 1

    hormigon = (
        espesor * (largo * (base + 2 * espesor))
        + espesor * 2 * (largo * altura)
    )
    superficie_fondo = largo * (base + 2 * espesor)

    roce_faja = largo * (base + 2 + 2)
    escarpe = roce_faja * ESPESOR_ESCARPE
    excavacion = largo * base
    relleno = largo * (altura + espesor + 0.1 + 0.05) * 0.5 * 2
    exc_escarpe, exc_excavacion, exc_totales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionDesarenador(
        hormigon=hormigon,
        enfierradura=hormigon * 80,
        moldaje=hormigon * 12,
        emplantillado=0.05 * superficie_fondo,
        base_granular=0.1 * superficie_fondo,
        antisol=2 * 2 * (largo * altura),
        roce_faja=roce_faja,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_totales,
        largo=largo,
    )


# ---------------------------------------------------------------------------
# Marco partidor (Partidor.bas: CubPartidor)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionPartidor:
    """Cantidades de obra de un marco partidor."""

    hormigon: float             # m³ hormigón (losa, muros, grada y zona de salida)
    enfierradura: float         # kg de acero de refuerzo
    moldaje: float              # m² de moldaje
    emplantillado: float        # m³ hormigón de limpieza G05
    base_granular: float        # m³ de base granular
    antisol: float              # m² de curado químico
    roce_faja: float            # m² de roce y despeje de la faja
    escarpe: float              # m³ de escarpe
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ totales a botadero


def cubicacion_partidor(caudal: float, base: float, altura: float) -> CubicacionPartidor:
    """Cubica un marco partidor dimensionado desde el caudal.

    Desde la altura crítica hc se definen la grada a = max(0.4·hc, 0.1),
    el largo de la zona de vertido Lv = 3.5·hc y la zona de salida Ls = 2·Lv.
    La altura de los muros se eleva a hc + a + 0.15 si la altura del canal
    no alcanza esa revancha mínima. Espesor fijo de 0.2 m.

    Args:
        caudal: caudal de diseño Q (m³/s).
        base: ancho de la base del canal b (m).
        altura: altura del canal h (m).
    """
    espesor = 0.2
    hc = altura_critica_rectangular(caudal, base)
    grada = max(0.4 * hc, 0.1)
    largo_vertido = 3.5 * hc
    largo_salida = largo_vertido * 2
    largo = largo_vertido + largo_salida

    altura = max(altura, hc + grada + 0.15)

    hormigon = (
        espesor * (largo * (base + 2 * espesor))
        + espesor * 2 * (largo * altura)
        + base * grada * largo_vertido
        + largo_salida * altura * espesor
    )
    superficie_fondo = largo * (base + 2 * espesor)

    roce_faja = largo * (base + 3 + 3)
    escarpe = roce_faja * ESPESOR_ESCARPE
    excavacion = largo * base
    relleno = largo * (altura + espesor + 0.1 + 0.05) * 0.5 * 2
    exc_escarpe, exc_excavacion, exc_totales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionPartidor(
        hormigon=hormigon,
        enfierradura=hormigon * cuantia_acero(altura),
        moldaje=hormigon * 10,
        emplantillado=0.05 * superficie_fondo,
        base_granular=0.1 * superficie_fondo,
        antisol=2 * (2 * (largo * altura) + largo_salida * altura),
        roce_faja=roce_faja,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_totales,
    )


# ---------------------------------------------------------------------------
# Reposición de compuerta (Compuerta.bas: CubCompuerta)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionCompuerta:
    """Cantidades de obra civil para la reposición de una compuerta.

    La compuerta misma (elemento metálico) se selecciona por dimensiones
    estándar desde una tabla; ver tablas.buscar_fila_por_dimensiones.
    """

    hormigon: float             # m³ hormigón del machón (losa, muros y dintel)
    enfierradura: float         # kg de acero (80 kg/m³ fijo)
    moldaje: float              # m² de moldaje (12 m²/m³)
    demolicion: float           # m³ de demolición del hormigón existente
    antisol: float              # m² de curado químico
    escarpe: float              # m³ de escarpe
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ a botadero incluida la demolición


def cubicacion_compuerta(base: float, altura: float) -> CubicacionCompuerta:
    """Cubica la obra civil de reposición de una compuerta en el canal.

    Se repone un tramo estándar de 2 m de largo con espesor de 0.3 m.

    Args:
        base: ancho del canal en la compuerta b (m).
        altura: altura del canal en la compuerta h (m).
    """
    espesor = 0.3
    largo = 2.0

    hormigon = (
        largo * base * espesor
        + 2 * largo * altura * espesor
        + altura * base * espesor
    )
    demolicion = hormigon * 0.5
    moldaje = hormigon * 12

    escarpe = (largo + 4) * (base + 4) * ESPESOR_ESCARPE
    excavacion = (base + 2 * 0.5) * (altura + 0.3) * 0.5
    relleno = (base + 0.5 + 0.5) * altura * 0.5
    exc_escarpe, exc_excavacion, exc_parciales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionCompuerta(
        hormigon=hormigon,
        enfierradura=hormigon * 80,
        moldaje=moldaje,
        demolicion=demolicion,
        antisol=moldaje,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=demolicion + exc_parciales,
    )


# ---------------------------------------------------------------------------
# Cajón de hormigón (CCaj.bas: cubiCajon)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionCajon:
    """Cantidades de obra para el reemplazo por cajones prefabricados."""

    largo_cajones: float        # m lineales de cajón (largo × cajones en paralelo)
    roce_faja: float            # m² de roce y despeje (3 m a cada lado)
    escarpe: float              # m³ de escarpe
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ totales a botadero
    base_granular: float        # m³ de cama granular bajo los cajones
    antisol: float              # m² de curado químico


def cubicacion_cajon(
    largo: float,
    ancho_canal: float,
    base_estandar: float,
    altura_estandar: float,
    espesor_estandar: float,
) -> CubicacionCajon:
    """Cubica el reemplazo de un tramo de canal por cajones de hormigón.

    Las dimensiones estándar del cajón (base, altura y espesor comerciales)
    se obtienen de la tabla de cajones tipo con
    tablas.buscar_fila_por_dimensiones a partir del ancho y alto del canal.

    Args:
        largo: largo del tramo a reemplazar L (m).
        ancho_canal: ancho del canal existente (m); define cuántos cajones
            en paralelo se necesitan.
        base_estandar: ancho exterior del cajón estándar seleccionado (m).
        altura_estandar: altura exterior del cajón estándar seleccionado (m).
        espesor_estandar: espesor de pared del cajón estándar (m).
    """
    escarpe_superficie = largo * (base_estandar + 6)
    escarpe = escarpe_superficie * ESPESOR_ESCARPE
    excavacion = largo * (base_estandar + 0.4 + 0.4) * 0.7
    relleno = largo * ((altura_estandar + 2 * espesor_estandar) + 0.1) * 2 * 0.4
    exc_escarpe, exc_excavacion, exc_totales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionCajon(
        largo_cajones=largo * numero_cajones_paralelos(ancho_canal),
        roce_faja=escarpe_superficie,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_totales,
        base_granular=largo * base_estandar * 0.1,
        antisol=2 * largo * altura_estandar + largo * base_estandar,
    )


# ---------------------------------------------------------------------------
# Portal de túnel (CPort.bas: cubiPortal)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionPortal:
    """Cantidades de obra para la reposición de los dos portales de un túnel.

    Todas las cantidades consideran ambos portales (entrada y salida),
    de ahí el factor 2 sobre los valores unitarios de la tabla de arcos.
    """

    hormigon_g05: float         # m³ hormigón de emplantillado G05
    hormigon_g25: float         # m³ hormigón estructural G25
    enfierradura: float         # kg de acero de refuerzo
    moldaje: float              # m² de moldaje
    superficie_emplantillado: float  # m² de emplantillado
    antisol: float              # m² de curado químico
    escarpe: float              # m³ de escarpe
    relleno_muro_ala: float     # m³ de relleno tras los muros ala
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno total
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ totales a botadero


def cubicacion_portal(
    ancho_arco: float,
    alto_arco: float,
    largo_muro_ala: float,
    ancho_base_muro_ala: float,
    altura_zapata: float,
    espesor: float,
    hormigon_g05_unitario: float,
    hormigon_g25_unitario: float,
    enfierradura_unitaria: float,
) -> CubicacionPortal:
    """Cubica la reposición de los portales (entrada y salida) de un túnel.

    Los parámetros provienen de la fila de la tabla de arcos tipo ("Arco")
    seleccionada con tablas.buscar_fila_por_dimensiones según el ancho y alto
    del túnel. Los volúmenes unitarios de hormigón y enfierradura ya vienen
    cubicados por portal en esa tabla; aquí se duplican (dos portales) y se
    agrega el movimiento de tierras.

    Args:
        ancho_arco: ancho del arco estándar (m).
        alto_arco: alto del arco estándar (m).
        largo_muro_ala: largo de los muros ala (m).
        ancho_base_muro_ala: ancho total de la base de los muros ala (m);
            en la tabla original se compone como 2·c11 + 2·c12 + c10.
        altura_zapata: altura de la zapata de fundación (m).
        espesor: espesor del arco (m).
        hormigon_g05_unitario: m³ de emplantillado G05 por portal (tabla).
        hormigon_g25_unitario: m³ de hormigón G25 por portal (tabla).
        enfierradura_unitaria: kg de acero por portal (tabla).
    """
    hormigon_g05 = hormigon_g05_unitario * 2
    hormigon_g25 = hormigon_g25_unitario * 2
    moldaje = hormigon_g25 * 12

    ancho_faja = ancho_arco + 2 * largo_muro_ala + 2 + 2
    escarpe = (largo_muro_ala + 1 + 1) * ancho_faja * 2 * ESPESOR_ESCARPE

    relleno_muro_ala = (2 * largo_muro_ala) * alto_arco * 0.5
    excavacion = (
        (espesor * 0.5 + 0.8 * 0.25 + 1 * 0.25) * ancho_faja * (ancho_base_muro_ala + 2 * 0.5)
        + (0.5 + espesor) * (altura_zapata + 0.1 + 0.05) * (largo_muro_ala * 2)
    ) * 2
    relleno = ((altura_zapata + 0.1 + 0.05) * (2 * largo_muro_ala) * 0.5 + relleno_muro_ala) * 2
    exc_escarpe, exc_excavacion, exc_totales = _excedentes(escarpe, excavacion, relleno)

    return CubicacionPortal(
        hormigon_g05=hormigon_g05,
        hormigon_g25=hormigon_g25,
        enfierradura=enfierradura_unitaria * 2,
        moldaje=moldaje,
        superficie_emplantillado=hormigon_g05 / 0.05,
        antisol=moldaje,
        escarpe=escarpe,
        relleno_muro_ala=relleno_muro_ala,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_totales,
    )


# ---------------------------------------------------------------------------
# Restauración de canoa (RepCanoa.bas: CubCanoa)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionCanoa:
    """Cantidades de obra para la restauración de una canoa de hormigón."""

    hormigon: float             # m³ hormigón de reposición (losa + un muro)
    enfierradura: float         # kg de acero de refuerzo
    moldaje: float              # m² de moldaje
    demolicion: float           # m³ de demolición del hormigón dañado
    antisol: float              # m² de curado químico
    roce_faja: float            # m² de roce y despeje (2 m a cada lado)
    escarpe: float              # m³ de escarpe
    excedentes_totales: float   # m³ a botadero (escarpe esponjado + demolición)


def cubicacion_canoa(largo: float, base: float, altura: float) -> CubicacionCanoa:
    """Cubica la restauración de una canoa de hormigón armado.

    Se repone hormigón con espesor de 0.3 m sobre la losa de fondo y el
    desarrollo del muro; la demolición se estima como la mitad del hormigón
    repuesto.

    Args:
        largo: largo de la canoa L (m).
        base: ancho interior de la canoa b (m).
        altura: altura interior de la canoa h (m).
    """
    espesor = 0.3
    hormigon = espesor * ((largo * base) + (largo * altura))
    demolicion = hormigon * 0.5
    moldaje = hormigon * 10

    roce_faja = largo * (base + 4)
    escarpe = roce_faja * ESPESOR_ESCARPE

    return CubicacionCanoa(
        hormigon=hormigon,
        enfierradura=hormigon * cuantia_acero(altura),
        moldaje=moldaje,
        demolicion=demolicion,
        antisol=moldaje,
        roce_faja=roce_faja,
        escarpe=escarpe,
        excedentes_totales=escarpe * (1 + ESPONJAMIENTO) + demolicion,
    )


# ---------------------------------------------------------------------------
# Restauración de tramo de sifón (RepSifon.bas: SifonRep)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionReparacionSifon:
    """Cantidades de obra para la restauración de un tramo de sifón."""

    hormigon: float             # m³ hormigón de reposición
    enfierradura: float         # kg de acero (100 kg/m³ fijo)
    moldaje: float              # m² de moldaje
    demolicion: float           # m³ de demolición del hormigón existente
    antisol: float              # m² de curado químico
    roce_faja: float            # m² de roce y despeje (2 m por lado)
    escarpe: float              # m³ de escarpe
    excavacion: float           # m³ de excavación
    relleno: float              # m³ de relleno
    excedente_escarpe: float    # m³ de escarpe esponjado
    excedente_excavacion: float # m³ de saldo de excavación esponjado
    excedentes_totales: float   # m³ a botadero incluida la demolición


def cubicacion_reparacion_sifon(
    largo: float, base: float, altura: float, espesor: float
) -> CubicacionReparacionSifon:
    """Cubica la restauración de un tramo de sifón de hormigón.

    Se repone el ancho de la caja por ambas caras (b·2) a lo largo del tramo.

    Args:
        largo: largo del tramo a restaurar L (m).
        base: ancho de la caja del sifón b (m).
        altura: altura de la caja del sifón h (m).
        espesor: espesor de reposición e (m).
    """
    hormigon = largo * (base * 2) * espesor
    demolicion = 0.5 * hormigon
    moldaje = hormigon * 10

    roce_faja = (largo + 2 + 2) * (base + 2 + 2)
    escarpe = roce_faja * ESPESOR_ESCARPE
    excavacion = (altura + 0.3) * (base + 0.5 + 0.5) * 0.5
    relleno = (base + 0.5 + 0.5) * altura * 0.5
    exc_escarpe, exc_excavacion, _ = _excedentes(escarpe, excavacion, relleno)

    return CubicacionReparacionSifon(
        hormigon=hormigon,
        enfierradura=hormigon * 100,
        moldaje=moldaje,
        demolicion=demolicion,
        antisol=moldaje,
        roce_faja=roce_faja,
        escarpe=escarpe,
        excavacion=excavacion,
        relleno=relleno,
        excedente_escarpe=exc_escarpe,
        excedente_excavacion=exc_excavacion,
        excedentes_totales=exc_escarpe + exc_excavacion + demolicion,
    )


# ---------------------------------------------------------------------------
# Reja de entrada de sifón (SifonReja.bas: SiReja)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionRejaSifon:
    """Cantidades para la reconstrucción de la reja de entrada de un sifón."""

    pletinas_verticales: float  # cantidad de pletinas verticales
    pletinas_horizontales: float  # cantidad de pletinas horizontales
    metros_pletina: float       # m lineales de pletina (con 10% de pérdidas)
    peso_pletinas: float        # kg de pletinas
    peso_reja: float            # kg totales de la reja (pletinas + refuerzos)
    escarpe: float              # m³ de escarpe de la faja de acceso
    excedentes_totales: float   # m³ de escarpe esponjado a botadero


def cubicacion_reja_sifon(base: float, altura: float) -> CubicacionRejaSifon:
    """Cubica la reja metálica de protección de la entrada de un sifón.

    Pletinas de 80×3 mm separadas cada 0.1 m en vertical, con dos pletinas
    horizontales de amarre; el peso de la reja completa duplica el de las
    pletinas para incluir refuerzos y marco.

    Args:
        base: ancho de la boca del sifón b (m).
        altura: alto de la boca del sifón h (m).
    """
    separacion = 0.1        # m entre pletinas verticales
    espesor_pletina = 3     # mm
    alto_pletina = 80       # mm

    pletinas_verticales = base / separacion + 1
    pletinas_horizontales = 2.0
    metros_pletina = (pletinas_verticales * altura + pletinas_horizontales * base) * 1.1
    peso_pletinas = (
        metros_pletina * (espesor_pletina / 1000) * (alto_pletina / 1000) * DENSIDAD_ACERO
    )

    escarpe = ((base + 2 + 2) * 5) * ESPESOR_ESCARPE

    return CubicacionRejaSifon(
        pletinas_verticales=pletinas_verticales,
        pletinas_horizontales=pletinas_horizontales,
        metros_pletina=metros_pletina,
        peso_pletinas=peso_pletinas,
        peso_reja=peso_pletinas * 2,
        escarpe=escarpe,
        excedentes_totales=escarpe * (1 + ESPONJAMIENTO),
    )


# ---------------------------------------------------------------------------
# Mejoramiento de túnel con shotcrete (TunelShot.bas: cubTunelShot)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CubicacionTunelShotcrete:
    """Cantidades para el refuerzo de un tramo de túnel con shotcrete."""

    superficie_shotcrete: float # m² de shotcrete (misma superficie de malla ACMA)
    escarpe: float              # m³ de escarpe de la faja de acceso
    excedentes_totales: float   # m³ de escarpe esponjado a botadero


def cubicacion_tunel_shotcrete(
    largo: float, base: float, altura: float
) -> CubicacionTunelShotcrete:
    """Cubica el refuerzo con shotcrete de un tramo de túnel.

    Se proyecta sobre las paredes y bóveda/fondo: 2·L·b + 2·L·h. La faja de
    acceso considera solo el frente de trabajo (5 m de largo).

    Args:
        largo: largo del tramo de túnel L (m).
        base: ancho del túnel b (m).
        altura: alto del túnel h (m).
    """
    escarpe = 5 * (base + 4) * ESPESOR_ESCARPE

    return CubicacionTunelShotcrete(
        superficie_shotcrete=2 * largo * base + 2 * largo * altura,
        escarpe=escarpe,
        excedentes_totales=escarpe * (1 + ESPONJAMIENTO),
    )
