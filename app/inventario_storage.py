import json

from app.database import SessionLocal
from app.gui_data import PATENTE_PADRAO, PATENTES
from app.models import Personagem


def carregar_patente(personagem):
    patente = getattr(personagem, "patente", None)
    return patente if patente in PATENTES else PATENTE_PADRAO


def carregar_inventario(personagem):
    if not getattr(personagem, "inventario", None):
        return []

    try:
        itens = json.loads(personagem.inventario)
        if not isinstance(itens, list):
            return []
        return [item for item in itens if isinstance(item, dict) and isinstance(item.get("nome"), str)]
    except (TypeError, ValueError):
        return []


def salvar_inventario(personagem, itens):
    db = SessionLocal()
    try:
        personagem_db = db.query(Personagem).filter(Personagem.id == personagem.id).first()
        if personagem_db is None:
            return

        itens_json = json.dumps(itens, ensure_ascii=False)
        personagem_db.inventario = itens_json
        personagem.inventario = itens_json
        db.commit()
    finally:
        db.close()


def salvar_patente(personagem, patente):
    db = SessionLocal()
    try:
        personagem_db = db.query(Personagem).filter(Personagem.id == personagem.id).first()
        if personagem_db is None:
            return

        personagem_db.patente = patente
        personagem.patente = patente
        db.commit()
    finally:
        db.close()
