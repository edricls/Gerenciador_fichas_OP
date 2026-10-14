# Configuração do PyInstaller para gerar o executável do Gerenciador de Fichas OP.
# Uso: python -m PyInstaller GerenciadorFichasOP.spec
# Resultado: dist/GerenciadorFichasOP/GerenciadorFichasOP.exe (pasta inteira é o app)
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

sys.path.insert(0, SPECPATH)
from app.icone import gerar_ico_executavel  # noqa: E402

NOME = "GerenciadorFichasOP"
ICONE = gerar_ico_executavel(Path(workpath) / "GerenciadorFichasOP.ico")

a = Analysis(
    ["app/main.py"],
    pathex=[SPECPATH],
    datas=[
        ("app/assets/medo.png", "app/assets"),
        # Temas e fontes do CustomTkinter, que o PyInstaller não encontra sozinho
        *collect_data_files("customtkinter"),
    ],
    excludes=["unittest", "pytest", "PyInstaller"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOME,
    icon=str(ICONE),
    console=False,  # app de janela: não abre o terminal junto
)

coll = COLLECT(exe, a.binaries, a.datas, name=NOME)
