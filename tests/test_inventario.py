import unittest

from app.character_rules import (
    calcular_capacidade_carga,
    calcular_peso_total,
    contar_itens_por_categoria,
    obter_limite_categoria,
    validar_limite_categoria,
)


def atributos(forca):
    return f"Força={forca}, Agilidade=1, Intelecto=1, Presença=1, Vigor=1"


class CapacidadeCargaTest(unittest.TestCase):
    def test_forca_zero_tem_capacidade_dois(self):
        self.assertEqual(calcular_capacidade_carga(atributos(0)), 2)

    def test_forca_um_comeca_com_cinco(self):
        self.assertEqual(calcular_capacidade_carga(atributos(1)), 5)

    def test_cada_ponto_de_forca_soma_cinco(self):
        self.assertEqual(calcular_capacidade_carga(atributos(2)), 10)
        self.assertEqual(calcular_capacidade_carga(atributos(4)), 20)

    def test_sem_forca_informada_usa_capacidade_minima(self):
        self.assertEqual(calcular_capacidade_carga(""), 2)


class LimitesPatenteTest(unittest.TestCase):
    def test_categoria_zero_nao_tem_limite(self):
        self.assertIsNone(obter_limite_categoria("Mundano", "0"))

    def test_tabela_de_limites(self):
        esperado = {
            "Mundano": (1, 0, 0, 0),
            "Recruta": (2, 0, 0, 0),
            "Operador": (3, 1, 0, 0),
            "Agente Especial": (3, 2, 1, 0),
            "Oficial de Operações": (3, 3, 2, 1),
            "Agente de Elite": (3, 3, 3, 2),
        }
        for patente, limites in esperado.items():
            for categoria, limite in zip(("I", "II", "III", "IV"), limites):
                self.assertEqual(obter_limite_categoria(patente, categoria), limite, (patente, categoria))

    def test_bloqueia_quando_limite_atingido(self):
        itens = [{"nome": "A", "categoria": "I"}, {"nome": "B", "categoria": "I"}]
        self.assertIsNotNone(validar_limite_categoria(itens, "Recruta", "I"))
        self.assertIsNone(validar_limite_categoria(itens, "Operador", "I"))

    def test_bloqueia_categoria_nao_permitida(self):
        self.assertIsNotNone(validar_limite_categoria([], "Recruta", "II"))

    def test_edicao_ignora_o_proprio_item(self):
        itens = [{"nome": "A", "categoria": "I"}, {"nome": "B", "categoria": "I"}]
        self.assertIsNone(validar_limite_categoria(itens, "Recruta", "I", ignorar_indice=1))

    def test_categoria_zero_nunca_bloqueia(self):
        itens = [{"nome": str(i), "categoria": "0"} for i in range(50)]
        self.assertIsNone(validar_limite_categoria(itens, "Mundano", "0"))


class ContagemTest(unittest.TestCase):
    def test_peso_total_e_contagem(self):
        itens = [
            {"nome": "A", "categoria": "0", "peso": 1},
            {"nome": "B", "categoria": "I", "peso": 2.5},
            {"nome": "C", "categoria": "I", "peso": "x"},
        ]
        self.assertEqual(calcular_peso_total(itens), 3.5)
        self.assertEqual(contar_itens_por_categoria(itens), {"0": 1, "I": 2})


if __name__ == "__main__":
    unittest.main()
