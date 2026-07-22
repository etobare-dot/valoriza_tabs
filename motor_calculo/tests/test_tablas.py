import unittest

from motor_calculo.tablas import buscar_fila_por_dimensiones, valor_mas_cercano


class TestValorMasCercano(unittest.TestCase):
    def test_prefiere_el_menor_mayor_o_igual(self):
        self.assertEqual(valor_mas_cercano([1.0, 2.0, 3.0], 1.4), 2.0)
        self.assertEqual(valor_mas_cercano([1.0, 2.0, 3.0], 2.0), 2.0)

    def test_si_ninguno_alcanza_toma_el_mas_cercano(self):
        self.assertEqual(valor_mas_cercano([1.0, 2.0, 3.0], 9.0), 3.0)

    def test_secuencia_vacia(self):
        with self.assertRaises(ValueError):
            valor_mas_cercano([], 1.0)


class TestBuscarFilaPorDimensiones(unittest.TestCase):
    # Tabla estilo "CajonM": (base, altura, espesor)
    TABLA = [
        (1.0, 1.0, 0.10),
        (1.0, 1.5, 0.12),
        (2.0, 1.0, 0.15),
        (2.0, 2.0, 0.18),
    ]

    def test_selecciona_base_y_altura_que_cubren(self):
        fila = buscar_fila_por_dimensiones(self.TABLA, base=0.8, altura=1.2)
        self.assertEqual(fila, (1.0, 1.5, 0.12))

    def test_base_exacta_altura_superior(self):
        fila = buscar_fila_por_dimensiones(self.TABLA, base=2.0, altura=1.8)
        self.assertEqual(fila, (2.0, 2.0, 0.18))

    def test_fuera_de_rango_toma_la_mas_cercana(self):
        fila = buscar_fila_por_dimensiones(self.TABLA, base=5.0, altura=5.0)
        self.assertEqual(fila, (2.0, 2.0, 0.18))

    def test_con_diccionarios(self):
        tabla = [
            {"b": 1.0, "h": 1.0, "e": 0.10},
            {"b": 1.0, "h": 2.0, "e": 0.12},
        ]
        fila = buscar_fila_por_dimensiones(
            tabla, base=1.0, altura=1.5, columna_base="b", columna_altura="h"
        )
        self.assertEqual(fila["e"], 0.12)


if __name__ == "__main__":
    unittest.main()
