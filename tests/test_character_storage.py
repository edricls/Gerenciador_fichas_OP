import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import character_storage
from app.database import Base
from app.models import Personagem


class NomeDuplicadoTest(unittest.TestCase):
    def setUp(self):
        # Banco em memória, para os testes não tocarem no rpg.db.
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        patcher = mock.patch.object(character_storage, "SessionLocal", sessao)
        patcher.start()
        self.addCleanup(patcher.stop)

        character_storage.salvar_personagem(Personagem(nome="Ágata", classe="Combatente"))

    def test_nome_existente_e_encontrado_sem_diferenciar_maiusculas(self):
        self.assertTrue(character_storage.existe_personagem_com_nome("Ágata"))
        self.assertTrue(character_storage.existe_personagem_com_nome("  ágata "))
        self.assertTrue(character_storage.existe_personagem_com_nome("ÁGATA"))

    def test_nome_novo_nao_e_encontrado(self):
        self.assertFalse(character_storage.existe_personagem_com_nome("Agata Silva"))

    def test_banco_recusa_nome_repetido_com_erro_proprio(self):
        with self.assertRaises(character_storage.NomePersonagemDuplicadoError):
            character_storage.salvar_personagem(Personagem(nome="Ágata", classe="Ocultista"))

    def test_depois_do_erro_e_possivel_salvar_outro_personagem(self):
        with self.assertRaises(character_storage.NomePersonagemDuplicadoError):
            character_storage.salvar_personagem(Personagem(nome="Ágata", classe="Ocultista"))
        character_storage.salvar_personagem(Personagem(nome="Bento", classe="Especialista"))
        self.assertTrue(character_storage.existe_personagem_com_nome("Bento"))


if __name__ == "__main__":
    unittest.main()
