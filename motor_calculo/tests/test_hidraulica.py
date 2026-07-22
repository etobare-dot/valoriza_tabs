import math
import unittest

from motor_calculo.hidraulica import (
    GRAVEDAD,
    altura_critica_rectangular,
    altura_normal_manning,
)


class TestAlturaCritica(unittest.TestCase):
    def test_valor_conocido(self):
        # hc = (1² / (9.81·1²))^(1/3)
        self.assertAlmostEqual(
            altura_critica_rectangular(1.0, 1.0), (1 / GRAVEDAD) ** (1 / 3), places=9
        )

    def test_crece_con_caudal(self):
        self.assertGreater(
            altura_critica_rectangular(2.0, 1.0), altura_critica_rectangular(1.0, 1.0)
        )


class TestAlturaNormal(unittest.TestCase):
    def test_satisface_manning_al_converger(self):
        # Semilla baja para que la regla "altura inicial manda" no aplique.
        q, b, m, s, n = 0.67, 1.0, 0.0, 0.001, 0.018
        h = altura_normal_manning(q, b, m, s, n, altura_inicial=0.3)

        area = h * b
        perimetro = b + 2 * h * math.sqrt(1 + m ** 2)
        radio = area / perimetro
        q_calculado = (1 / n) * area * radio ** (2 / 3) * math.sqrt(s)
        self.assertAlmostEqual(q_calculado, q, places=3)

    def test_altura_inicial_manda_si_es_mucho_mayor(self):
        # Con una semilla muy por sobre la altura normal, se respeta la semilla.
        q, b, m, s, n = 0.1, 1.0, 0.0, 0.001, 0.018
        h_convergida = altura_normal_manning(q, b, m, s, n, altura_inicial=0.1)
        h = altura_normal_manning(q, b, m, s, n, altura_inicial=h_convergida + 1.0)
        self.assertEqual(h, h_convergida + 1.0)


if __name__ == "__main__":
    unittest.main()
