import unittest
from types import SimpleNamespace

from PIL import Image

from app.imagem_storage import (
    AJUSTE_PADRAO,
    ZOOM_MAXIMO,
    calcular_recorte,
    carregar_ajuste,
    recortar_circular,
)


class CalcularRecorteTest(unittest.TestCase):
    def test_padrao_recorta_quadrado_central(self):
        caixa, ajuste = calcular_recorte(200, 100, AJUSTE_PADRAO)
        self.assertEqual(caixa, (50, 0, 150, 100))
        self.assertEqual(ajuste, {"x": 0.5, "y": 0.5, "zoom": 1.0})

    def test_zoom_reduz_a_area_recortada(self):
        caixa, _ = calcular_recorte(200, 100, {"x": 0.5, "y": 0.5, "zoom": 2.0})
        self.assertEqual(caixa, (75, 25, 125, 75))

    def test_centro_nao_deixa_o_recorte_sair_da_imagem(self):
        caixa, ajuste = calcular_recorte(200, 100, {"x": 0.0, "y": 1.0, "zoom": 2.0})
        self.assertEqual(caixa, (0, 50, 50, 100))
        self.assertEqual(ajuste["x"], 0.125)
        self.assertEqual(ajuste["y"], 0.75)

    def test_zoom_fica_entre_um_e_o_maximo(self):
        self.assertEqual(calcular_recorte(100, 100, {"zoom": 0.2})[1]["zoom"], 1.0)
        self.assertEqual(calcular_recorte(100, 100, {"zoom": 99})[1]["zoom"], ZOOM_MAXIMO)


class AjusteSalvoTest(unittest.TestCase):
    def test_sem_ajuste_usa_padrao(self):
        self.assertEqual(carregar_ajuste(SimpleNamespace(imagem_ajuste="")), AJUSTE_PADRAO)

    def test_ajuste_invalido_usa_padrao(self):
        self.assertEqual(carregar_ajuste(SimpleNamespace(imagem_ajuste="{quebrado")), AJUSTE_PADRAO)

    def test_ajuste_salvo_e_lido(self):
        ajuste = carregar_ajuste(SimpleNamespace(imagem_ajuste='{"x": 0.3, "y": 0.2, "zoom": 2}'))
        self.assertEqual(ajuste, {"x": 0.3, "y": 0.2, "zoom": 2.0})


class RecortarCircularTest(unittest.TestCase):
    def test_gera_imagem_em_resolucao_dobrada_com_cantos_transparentes(self):
        imagem = Image.new("RGBA", (300, 200), (255, 0, 0, 255))
        recorte = recortar_circular(imagem, 40)
        self.assertEqual(recorte.size, (80, 80))
        self.assertEqual(recorte.getpixel((0, 0))[3], 0)
        self.assertEqual(recorte.getpixel((40, 40))[3], 255)


if __name__ == "__main__":
    unittest.main()
