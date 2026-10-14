import tempfile
import unittest
from pathlib import Path

from app.caminhos import NOME_BANCO, NOME_BANCO_ANTIGO, NOME_PASTA_IMAGENS, migrar_dados_antigos


class MigrarDadosAntigosTest(unittest.TestCase):
    def setUp(self):
        temporaria = tempfile.TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)
        self.origem = Path(temporaria.name) / "projeto"
        self.destino = Path(temporaria.name) / "dados"
        self.origem.mkdir()

    def test_copia_banco_e_fotos_mantendo_os_originais(self):
        (self.origem / NOME_BANCO).write_bytes(b"banco")
        (self.origem / NOME_PASTA_IMAGENS).mkdir()
        (self.origem / NOME_PASTA_IMAGENS / "foto.png").write_bytes(b"foto")

        self.assertTrue(migrar_dados_antigos(self.origem, self.destino))

        self.assertEqual((self.destino / NOME_BANCO).read_bytes(), b"banco")
        self.assertEqual((self.destino / NOME_PASTA_IMAGENS / "foto.png").read_bytes(), b"foto")
        self.assertTrue((self.origem / NOME_BANCO).exists())
        self.assertTrue((self.origem / NOME_PASTA_IMAGENS / "foto.png").exists())

    def test_usa_banco_com_nome_antigo(self):
        (self.origem / NOME_BANCO_ANTIGO).write_bytes(b"antigo")

        self.assertTrue(migrar_dados_antigos(self.origem, self.destino))
        self.assertEqual((self.destino / NOME_BANCO).read_bytes(), b"antigo")

    def test_prefere_o_banco_novo_ao_antigo(self):
        (self.origem / NOME_BANCO).write_bytes(b"novo")
        (self.origem / NOME_BANCO_ANTIGO).write_bytes(b"antigo")

        migrar_dados_antigos(self.origem, self.destino)
        self.assertEqual((self.destino / NOME_BANCO).read_bytes(), b"novo")

    def test_nao_sobrescreve_banco_que_ja_esta_no_destino(self):
        (self.origem / NOME_BANCO).write_bytes(b"velho")
        self.destino.mkdir()
        (self.destino / NOME_BANCO).write_bytes(b"atual")

        self.assertFalse(migrar_dados_antigos(self.origem, self.destino))
        self.assertEqual((self.destino / NOME_BANCO).read_bytes(), b"atual")

    def test_sem_dados_antigos_nao_faz_nada(self):
        self.assertFalse(migrar_dados_antigos(self.origem, self.destino))
        self.assertFalse(self.destino.exists())

    def test_nao_deixa_arquivo_temporario_para_tras(self):
        (self.origem / NOME_BANCO).write_bytes(b"banco")

        migrar_dados_antigos(self.origem, self.destino)
        self.assertEqual([arquivo.name for arquivo in self.destino.iterdir()], [NOME_BANCO])


if __name__ == "__main__":
    unittest.main()
