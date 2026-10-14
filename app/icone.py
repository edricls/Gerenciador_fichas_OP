# Ícone do app: o símbolo do Medo, usado na barra de título das janelas e no cabeçalho.
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from app.theme import CORES, CORES_ELEMENTOS

ICONE_PNG = Path(__file__).parent / "assets" / "medo.png"
PASTA_ICO = Path(tempfile.gettempdir())
# Tamanho do ícone -> quanto engrossar o traço (em pixels, numa base de 256 px).
# O traço do PNG é fino; sem isso o símbolo some nos tamanhos pequenos da barra de título.
ENGROSSAR_ICO = {16: 7, 24: 5, 32: 5, 48: 3, 64: 3, 128: 1, 256: 1}

# O CustomTkinter coloca o próprio ícone nas janelas 200 ms depois de criá-las;
# o nosso precisa ser aplicado depois disso para não ser sobrescrito.
ATRASO_ICONE_MS = 250


def icone_disponivel():
    return ICONE_PNG.exists()


def _quadrado(imagem):
    """Corta as bordas vazias e centraliza num quadrado transparente, sem distorcer o símbolo."""
    caixa = imagem.getchannel("A").getbbox()
    if caixa:
        imagem = imagem.crop(caixa)
    lado = max(imagem.size)
    quadro = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    quadro.paste(imagem, ((lado - imagem.width) // 2, (lado - imagem.height) // 2))
    return quadro


def _mascara(imagem):
    """Só a parte clara do traço, descartando o contorno escuro do PNG,
    que viraria um borrão ao ser pintado de uma cor só."""
    return ImageChops.multiply(imagem.getchannel("A"), imagem.convert("L"))


def _imagem_ico(base, tamanho, cor):
    mascara = _mascara(base).resize((256, 256), Image.LANCZOS)
    if ENGROSSAR_ICO[tamanho] > 1:
        mascara = mascara.filter(ImageFilter.MaxFilter(ENGROSSAR_ICO[tamanho]))
    imagem = Image.new("RGBA", (256, 256), cor)
    imagem.putalpha(mascara)
    return imagem.resize((tamanho, tamanho), Image.LANCZOS)


@lru_cache(maxsize=2)
def _caminho_ico(modo):
    """Gera o .ico a partir do PNG (o Windows só aceita .ico na barra de título),
    com o símbolo escuro na barra clara e branco na barra escura."""
    if not icone_disponivel():
        return None
    caminho = PASTA_ICO / f"gerenciador_fichas_op_medo_{modo.lower()}.ico"
    if not caminho.exists() or caminho.stat().st_mtime < ICONE_PNG.stat().st_mtime:
        with Image.open(ICONE_PNG) as arquivo:
            base = _quadrado(arquivo.convert("RGBA"))
        cor = CORES_ELEMENTOS["Medo"][0 if modo == "Light" else 1]
        imagens = [_imagem_ico(base, tamanho, cor) for tamanho in ENGROSSAR_ICO]
        imagens[-1].save(caminho, sizes=[i.size for i in imagens], append_images=imagens[:-1])
    return str(caminho)


def _ladrilho(base, tamanho):
    """Símbolo branco sobre um quadrado escuro arredondado, legível em qualquer fundo."""
    lado = 256
    ladrilho = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    ImageDraw.Draw(ladrilho).rounded_rectangle((0, 0, lado - 1, lado - 1), radius=56, fill=CORES["superficie"][1])
    interno = int(lado * 0.74)
    mascara = _mascara(base).resize((interno, interno), Image.LANCZOS)
    if ENGROSSAR_ICO[tamanho] > 1:
        mascara = mascara.filter(ImageFilter.MaxFilter(ENGROSSAR_ICO[tamanho]))
    simbolo = Image.new("RGBA", (interno, interno), "#FFFFFF")
    simbolo.putalpha(mascara)
    ladrilho.alpha_composite(simbolo, ((lado - interno) // 2, (lado - interno) // 2))
    return ladrilho.resize((tamanho, tamanho), Image.LANCZOS)


def gerar_ico_executavel(destino):
    """Gera o .ico do executável e do instalador (usado no build, não pelo app em execução)."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(ICONE_PNG) as arquivo:
        base = _quadrado(arquivo.convert("RGBA"))
    imagens = [_ladrilho(base, tamanho) for tamanho in ENGROSSAR_ICO]
    imagens[-1].save(destino, sizes=[i.size for i in imagens], append_images=imagens[:-1])
    return destino


def aplicar_icone(janela):
    """Troca o ícone padrão do CustomTkinter pelo símbolo do Medo na janela."""
    if not sys.platform.startswith("win"):
        return
    try:
        caminho = _caminho_ico(ctk.get_appearance_mode())
    except OSError:
        return
    if caminho is None:
        return
    # Na janela principal, chamar iconbitmap já impede o CustomTkinter de trocar o ícone;
    # nas CTkToplevel ele troca de qualquer jeito, então reaplicamos depois do atraso.
    janela.iconbitmap(caminho)
    if isinstance(janela, ctk.CTkToplevel):
        janela.after(ATRASO_ICONE_MS, lambda: janela.winfo_exists() and janela.iconbitmap(caminho))


def _pintar(imagem, cor):
    """Pinta o símbolo com uma cor só."""
    pintada = Image.new("RGBA", imagem.size, cor)
    pintada.putalpha(_mascara(imagem))
    return pintada


def criar_imagem_icone(tamanho):
    """CTkImage do símbolo, escuro no modo claro e branco no modo escuro."""
    if not icone_disponivel():
        return None
    with Image.open(ICONE_PNG) as arquivo:
        original = arquivo.convert("RGBA")
    imagem = _quadrado(original)
    # Sem transparência não dá para separar o símbolo do fundo; usa a imagem como veio.
    if original.getchannel("A").getextrema()[0] == 255:
        return ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(tamanho, tamanho))
    cor_clara, cor_escura = CORES_ELEMENTOS["Medo"]
    return ctk.CTkImage(
        light_image=_pintar(imagem, cor_clara),
        dark_image=_pintar(imagem, cor_escura),
        size=(tamanho, tamanho),
    )
