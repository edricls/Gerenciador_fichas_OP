# Onde o app guarda os dados do usuário (banco e fotos).
# Fica na pasta de dados do usuário, e não na pasta do programa, porque um app instalado
# (ex.: em C:\Program Files) não tem permissão para gravar ao lado do próprio executável.
import os
import shutil
import sys
from pathlib import Path

NOME_APP = "Gerenciador de Fichas OP"
NOME_BANCO = "fichas_op.db"
NOME_BANCO_ANTIGO = "rpg.db"  # nome usado antes da renomeação do projeto
NOME_PASTA_IMAGENS = "imagens"

# Antes da versão 1.0 o banco e as fotos ficavam na raiz do projeto.
PASTA_PROJETO = Path(__file__).resolve().parent.parent


def pasta_dados():
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / NOME_APP
    return Path.home() / ".gerenciador_fichas_op"


PASTA_DADOS = pasta_dados()
PASTA_IMAGENS = PASTA_DADOS / NOME_PASTA_IMAGENS
CAMINHO_BANCO = PASTA_DADOS / NOME_BANCO


def _copiar(origem, destino):
    # Copia para um arquivo temporário e só depois renomeia: se a cópia for interrompida,
    # o destino não fica pela metade.
    temporario = destino.with_name(destino.name + ".copiando")
    shutil.copy2(origem, temporario)
    os.replace(temporario, destino)


def migrar_dados_antigos(origem=PASTA_PROJETO, destino=PASTA_DADOS):
    """Copia banco e fotos do local antigo para a pasta de dados, se ainda não houver banco lá.

    Os arquivos antigos são mantidos como cópia de segurança. Retorna True se migrou.
    """
    destino = Path(destino)
    origem = Path(origem)
    banco_destino = destino / NOME_BANCO
    if banco_destino.exists():
        return False

    banco_origem = next(
        (caminho for caminho in (origem / NOME_BANCO, origem / NOME_BANCO_ANTIGO) if caminho.is_file()),
        None,
    )
    if banco_origem is None:
        return False

    destino.mkdir(parents=True, exist_ok=True)

    # As fotos vão primeiro; o banco por último marca a migração como concluída.
    imagens_origem = origem / NOME_PASTA_IMAGENS
    if imagens_origem.is_dir():
        imagens_destino = destino / NOME_PASTA_IMAGENS
        imagens_destino.mkdir(exist_ok=True)
        for arquivo in imagens_origem.iterdir():
            if arquivo.is_file() and not (imagens_destino / arquivo.name).exists():
                _copiar(arquivo, imagens_destino / arquivo.name)

    _copiar(banco_origem, banco_destino)
    return True
