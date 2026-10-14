# Guarda as fotos dos personagens numa pasta própria, ao lado do banco de dados.
# A imagem escolhida é copiada (e reduzida) para que a ficha não dependa do arquivo original.
import json
import time
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

from app.database import SessionLocal
from app.models import Personagem

PASTA_IMAGENS = Path("imagens")
TAMANHO_MAXIMO = 1024
ZOOM_MAXIMO = 4.0
AJUSTE_PADRAO = {"x": 0.5, "y": 0.5, "zoom": 1.0}
TIPOS_SUPORTADOS = [
    ("Imagens", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"),
    ("Todos os arquivos", "*.*"),
]


def caminho_imagem(personagem):
    nome_arquivo = getattr(personagem, "imagem", None)
    if not nome_arquivo:
        return None
    caminho = PASTA_IMAGENS / nome_arquivo
    return caminho if caminho.is_file() else None


def apagar_arquivo_imagem(nome_arquivo):
    if not nome_arquivo:
        return
    caminho = PASTA_IMAGENS / nome_arquivo
    try:
        caminho.unlink(missing_ok=True)
    except OSError:
        pass


def _atualizar_colunas(personagem, **valores):
    db = SessionLocal()
    try:
        personagem_db = db.query(Personagem).filter(Personagem.id == personagem.id).first()
        if personagem_db is None:
            return False
        for coluna, valor in valores.items():
            setattr(personagem_db, coluna, valor)
            setattr(personagem, coluna, valor)
        db.commit()
        return True
    finally:
        db.close()


def definir_imagem(personagem, caminho_origem):
    """Copia a imagem escolhida para a pasta do app e associa ao personagem.

    Lança ValueError se o arquivo não for uma imagem válida.
    """
    try:
        with Image.open(caminho_origem) as imagem:
            imagem = ImageOps.exif_transpose(imagem)
            imagem = imagem.convert("RGBA")
            imagem.thumbnail((TAMANHO_MAXIMO, TAMANHO_MAXIMO))
    except (OSError, ValueError) as erro:
        raise ValueError("O arquivo escolhido não é uma imagem válida.") from erro

    PASTA_IMAGENS.mkdir(exist_ok=True)
    # Nome único a cada troca, para não reaproveitar uma imagem antiga já carregada.
    nome_arquivo = f"personagem_{personagem.id}_{int(time.time() * 1000)}.png"
    imagem.save(PASTA_IMAGENS / nome_arquivo, "PNG")

    nome_anterior = getattr(personagem, "imagem", None)
    # Foto nova começa centralizada.
    if not _atualizar_colunas(personagem, imagem=nome_arquivo, imagem_ajuste=""):
        apagar_arquivo_imagem(nome_arquivo)
        return
    if nome_anterior and nome_anterior != nome_arquivo:
        apagar_arquivo_imagem(nome_anterior)


def remover_imagem(personagem):
    nome_anterior = getattr(personagem, "imagem", None)
    if _atualizar_colunas(personagem, imagem="", imagem_ajuste=""):
        apagar_arquivo_imagem(nome_anterior)


def carregar_ajuste(personagem):
    """Enquadramento salvo da foto: centro (x, y de 0 a 1) e zoom."""
    try:
        dados = json.loads(getattr(personagem, "imagem_ajuste", None) or "{}")
    except (TypeError, ValueError):
        dados = {}
    if not isinstance(dados, dict):
        dados = {}

    ajuste = dict(AJUSTE_PADRAO)
    for chave in ajuste:
        try:
            ajuste[chave] = float(dados.get(chave, ajuste[chave]))
        except (TypeError, ValueError):
            pass
    return ajuste


def salvar_ajuste(personagem, ajuste):
    dados = {chave: round(float(ajuste[chave]), 4) for chave in AJUSTE_PADRAO}
    _atualizar_colunas(personagem, imagem_ajuste=json.dumps(dados))


def calcular_recorte(largura, altura, ajuste):
    """Retorna a área quadrada da imagem a recortar e o ajuste corrigido para não sair da imagem."""
    zoom = min(max(float(ajuste.get("zoom", 1.0)), 1.0), ZOOM_MAXIMO)
    meio = min(largura, altura) / zoom / 2
    centro_x = min(max(float(ajuste.get("x", 0.5)) * largura, meio), largura - meio)
    centro_y = min(max(float(ajuste.get("y", 0.5)) * altura, meio), altura - meio)
    caixa = (centro_x - meio, centro_y - meio, centro_x + meio, centro_y + meio)
    return caixa, {"x": centro_x / largura, "y": centro_y / altura, "zoom": zoom}


@lru_cache(maxsize=8)
def _mascara_circular(lado):
    # Desenhada em resolução maior e reduzida, para suavizar a borda do círculo.
    mascara = Image.new("L", (lado * 4, lado * 4), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, lado * 4, lado * 4), fill=255)
    return mascara.resize((lado, lado), Image.LANCZOS)


def recortar_circular(imagem, tamanho, ajuste=None):
    """Recorta a imagem (já aberta, em RGBA) em círculo, em resolução dobrada para telas com escala."""
    lado = tamanho * 2
    caixa, _ = calcular_recorte(imagem.width, imagem.height, ajuste or AJUSTE_PADRAO)
    recorte = imagem.resize((lado, lado), Image.LANCZOS, box=caixa)
    recorte.putalpha(ImageChops.multiply(recorte.getchannel("A"), _mascara_circular(lado)))
    return recorte


def abrir_imagem(caminho):
    with Image.open(caminho) as imagem:
        return imagem.convert("RGBA")


def carregar_imagem_circular(caminho, tamanho, ajuste=None):
    return recortar_circular(abrir_imagem(caminho), tamanho, ajuste)
