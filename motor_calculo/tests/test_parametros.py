import unittest

from motor_calculo.parametros import (
    cuantia_acero,
    espesor_revestimiento,
    numero_cajones_paralelos,
    numero_modulos_largo,
)


class TestCuantiaAcero(unittest.TestCase):
    def test_escalones(self):
        self.assertEqual(cuantia_acero(0), 0.0)
        self.assertEqual(cuantia_acero(0.5), 50.0)
        self.assertEqual(cuantia_acero(1.0), 50.0)
        self.assertEqual(cuantia_acero(1.5), 80.0)
        self.assertEqual(cuantia_acero(2.0), 80.0)
        self.assertEqual(cuantia_acero(2.5), 100.0)


class TestEspesorRevestimiento(unittest.TestCase):
    def test_tramo_constante(self):
        self.assertEqual(espesor_revestimiento(1.0), 0.13)
        self.assertEqual(espesor_revestimiento(1.6), 0.13)

    def test_tramo_intermedio(self):
        # h = 2.0 → 0.13 + (0.4/0.1)·0.008333
        self.assertAlmostEqual(espesor_revestimiento(2.0), 0.13 + 4 * 0.008333, places=9)

    def test_tramo_superior(self):
        # h = 3.0 → 0.2 + (0.6/0.1)·0.0066666
        self.assertAlmostEqual(espesor_revestimiento(3.0), 0.2 + 6 * 0.0066666, places=9)


class TestModulosEstandar(unittest.TestCase):
    def test_cajones_paralelos(self):
        self.assertEqual(numero_cajones_paralelos(1.0), 1)
        self.assertEqual(numero_cajones_paralelos(3.2), 2)
        self.assertEqual(numero_cajones_paralelos(6.2), 3)

    def test_modulos_largo(self):
        self.assertEqual(numero_modulos_largo(1.9), 1)
        self.assertEqual(numero_modulos_largo(2.0), 2)
        self.assertEqual(numero_modulos_largo(10.0), 6)


if __name__ == "__main__":
    unittest.main()
