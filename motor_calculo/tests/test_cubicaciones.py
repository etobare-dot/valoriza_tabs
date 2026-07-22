import unittest

from motor_calculo.cubicaciones import (
    cubicacion_cajon,
    cubicacion_canoa,
    cubicacion_compuerta,
    cubicacion_desarenador,
    cubicacion_disipador,
    cubicacion_partidor,
    cubicacion_reja_sifon,
    cubicacion_reparacion_sifon,
    cubicacion_revestimiento_canal,
    cubicacion_tunel_shotcrete,
)


class TestRevestimientoCanal(unittest.TestCase):
    """Valores de referencia calculados a mano con las fórmulas de CubCanal.bas."""

    def setUp(self):
        # L=10, b=1, h=1, e=0.1, talud=0 (muros verticales)
        self.c = cubicacion_revestimiento_canal(
            largo=10, base=1, altura=1, espesor=0.1, talud=0
        )

    def test_hormigon(self):
        # 0.1·(10·1.2) + 0.1·2·(10·1) = 1.2 + 2 = 3.2
        self.assertAlmostEqual(self.c.hormigon, 3.2)

    def test_enfierradura_usa_cuantia(self):
        self.assertAlmostEqual(self.c.enfierradura, 3.2 * 50)

    def test_moldaje(self):
        self.assertAlmostEqual(self.c.moldaje, 32.0)

    def test_emplantillado_y_base_granular(self):
        self.assertAlmostEqual(self.c.emplantillado, 0.05 * 12)  # 0.6
        self.assertAlmostEqual(self.c.base_granular, 0.1 * 12)   # 1.2

    def test_juntas_y_antisol(self):
        self.assertAlmostEqual(self.c.juntas_dilatacion, 2 * (1 + 2))  # (10/5)·3
        self.assertAlmostEqual(self.c.antisol, 40.0)                   # 2·10·2

    def test_movimiento_de_tierras(self):
        self.assertAlmostEqual(self.c.roce_faja, 70.0)      # 10·7
        self.assertAlmostEqual(self.c.escarpe, 10.5)        # 70·0.15
        self.assertAlmostEqual(self.c.excavacion, 10.0)     # 10·1
        self.assertAlmostEqual(self.c.relleno, 12.5)        # 10·1.25·0.5·2

    def test_excedentes_sin_saldo_negativo(self):
        # excavación (10) < relleno (12.5) → solo escarpe esponjado
        self.assertAlmostEqual(self.c.excedente_excavacion, 0.0)
        self.assertAlmostEqual(self.c.excedentes_totales, 10.5 * 1.1)

    def test_talud_aumenta_hormigon(self):
        con_talud = cubicacion_revestimiento_canal(10, 1, 1, 0.1, talud=1)
        self.assertGreater(con_talud.hormigon, self.c.hormigon)


class TestDisipador(unittest.TestCase):
    def test_largo_compuesto_de_caida_y_resalto(self):
        c = cubicacion_disipador(caudal=1.0, base=1.0, altura=1.0)
        self.assertGreater(c.largo, 0)
        self.assertGreater(c.hormigon, 0)
        self.assertGreater(c.excedentes_totales, 0)

    def test_enfierradura_usa_altura_final(self):
        # altura final = h + 1.1·hc supera 1 m → cuantía 80 en vez de 50
        c = cubicacion_disipador(caudal=1.0, base=1.0, altura=1.0)
        self.assertAlmostEqual(c.enfierradura, c.hormigon * 80)


class TestDesarenador(unittest.TestCase):
    def setUp(self):
        self.c = cubicacion_desarenador(caudal=1.0, ancho=1.0, alto=1.0)

    def test_largo_de_decantacion(self):
        # b=3, h=1.5, v=1/4.5, w=0.051193 → L = (v·1.5)/w + 1
        v = 1.0 / 4.5
        w = (0.0088 + 10.221 * 0.5) / 100
        self.assertAlmostEqual(self.c.largo, (v * 1.5) / w + 1)

    def test_hormigon(self):
        largo = self.c.largo
        esperado = 0.2 * (largo * 3.4) + 0.2 * 2 * (largo * 1.5)
        self.assertAlmostEqual(self.c.hormigon, esperado)

    def test_coeficientes_fijos(self):
        self.assertAlmostEqual(self.c.enfierradura, self.c.hormigon * 80)
        self.assertAlmostEqual(self.c.moldaje, self.c.hormigon * 12)


class TestPartidor(unittest.TestCase):
    def test_respeta_altura_minima(self):
        # Con un canal muy bajo, la altura de cálculo sube a hc + a + 0.15,
        # lo que se refleja en más hormigón que el canal bajo por sí solo.
        bajo = cubicacion_partidor(caudal=1.0, base=1.0, altura=0.1)
        alto = cubicacion_partidor(caudal=1.0, base=1.0, altura=2.0)
        self.assertGreater(alto.hormigon, bajo.hormigon)
        self.assertGreater(bajo.hormigon, 0)


class TestCompuerta(unittest.TestCase):
    def setUp(self):
        self.c = cubicacion_compuerta(base=1.0, altura=1.0)

    def test_hormigon(self):
        # L=2, e=0.3: 2·1·0.3 + 2·2·1·0.3 + 1·1·0.3 = 0.6 + 1.2 + 0.3 = 2.1
        self.assertAlmostEqual(self.c.hormigon, 2.1)

    def test_demolicion_y_antisol(self):
        self.assertAlmostEqual(self.c.demolicion, 1.05)
        self.assertAlmostEqual(self.c.antisol, self.c.moldaje)

    def test_excedentes_incluyen_demolicion(self):
        # escarpe = 6·5·0.15 = 4.5; exc = 2·1.3·0.5 = 1.3; rell = 2·1·0.5 = 1.0
        exc_totales = 4.5 * 1.1 + (1.3 - 1.0) * 1.1 + 1.05
        self.assertAlmostEqual(self.c.excedentes_totales, exc_totales)


class TestCajon(unittest.TestCase):
    def test_metros_lineales_por_cajones_paralelos(self):
        c = cubicacion_cajon(
            largo=10, ancho_canal=3.2, base_estandar=2.0,
            altura_estandar=2.0, espesor_estandar=0.2,
        )
        self.assertAlmostEqual(c.largo_cajones, 20.0)  # 10 m × 2 cajones

    def test_movimiento_de_tierras(self):
        c = cubicacion_cajon(
            largo=10, ancho_canal=1.0, base_estandar=2.0,
            altura_estandar=2.0, espesor_estandar=0.2,
        )
        self.assertAlmostEqual(c.escarpe, 10 * 8 * 0.15)          # 12
        self.assertAlmostEqual(c.excavacion, 10 * 2.8 * 0.7)      # 19.6
        self.assertAlmostEqual(c.relleno, 10 * 2.5 * 2 * 0.4)     # 20
        # excavación < relleno → solo escarpe esponjado
        self.assertAlmostEqual(c.excedentes_totales, 12 * 1.1)


class TestCanoa(unittest.TestCase):
    def test_valores_basicos(self):
        c = cubicacion_canoa(largo=10, base=1.0, altura=1.0)
        self.assertAlmostEqual(c.hormigon, 0.3 * (10 + 10))       # 6
        self.assertAlmostEqual(c.enfierradura, 6 * 50)
        self.assertAlmostEqual(c.demolicion, 3.0)
        self.assertAlmostEqual(c.escarpe, 10 * 5 * 0.15)          # 7.5
        self.assertAlmostEqual(c.excedentes_totales, 7.5 * 1.1 + 3.0)


class TestReparacionSifon(unittest.TestCase):
    def test_valores_basicos(self):
        c = cubicacion_reparacion_sifon(largo=10, base=1.0, altura=1.0, espesor=0.2)
        self.assertAlmostEqual(c.hormigon, 10 * 2 * 0.2)          # 4
        self.assertAlmostEqual(c.enfierradura, 400.0)
        self.assertAlmostEqual(c.escarpe, 14 * 5 * 0.15)          # 10.5
        # exc = 1.3·2·0.5 = 1.3; rell = 2·1·0.5 = 1.0; demolición = 2
        self.assertAlmostEqual(
            c.excedentes_totales, 10.5 * 1.1 + 0.3 * 1.1 + 2.0, places=9
        )


class TestRejaSifon(unittest.TestCase):
    def test_peso_de_la_reja(self):
        c = cubicacion_reja_sifon(base=1.0, altura=1.0)
        # 11 pletinas verticales de 1 m + 2 horizontales de 1 m, +10% = 14.3 m
        self.assertAlmostEqual(c.metros_pletina, 14.3)
        self.assertAlmostEqual(c.peso_pletinas, 14.3 * 0.003 * 0.08 * 7900)
        self.assertAlmostEqual(c.peso_reja, c.peso_pletinas * 2)


class TestTunelShotcrete(unittest.TestCase):
    def test_superficie(self):
        c = cubicacion_tunel_shotcrete(largo=10, base=2.0, altura=2.0)
        self.assertAlmostEqual(c.superficie_shotcrete, 80.0)      # 2·10·2 + 2·10·2
        self.assertAlmostEqual(c.escarpe, 5 * 6 * 0.15)           # 4.5
        self.assertAlmostEqual(c.excedentes_totales, 4.5 * 1.1)


if __name__ == "__main__":
    unittest.main()
