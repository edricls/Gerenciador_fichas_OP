import json

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.imagem_storage import apagar_arquivo_imagem
from app.models import Personagem


def listar_personagens():
    db = SessionLocal()
    try:
        return db.query(Personagem).all()
    finally:
        db.close()


class NomePersonagemDuplicadoError(Exception):
    """O nome escolhido já pertence a outro personagem."""


def existe_personagem_com_nome(nome):
    # Comparação em Python (casefold) para tratar acentos corretamente, o que o lower() do SQLite não faz.
    nome_normalizado = nome.strip().casefold()
    db = SessionLocal()
    try:
        return any(
            (nome_existente or "").strip().casefold() == nome_normalizado
            for (nome_existente,) in db.query(Personagem.nome)
        )
    finally:
        db.close()


def salvar_personagem(personagem):
    db = SessionLocal()
    try:
        db.add(personagem)
        db.commit()
    except IntegrityError as erro:
        # O nome é único no banco; qualquer violação aqui é um nome repetido.
        db.rollback()
        raise NomePersonagemDuplicadoError(personagem.nome) from erro
    finally:
        db.close()


def atualizar_personagem(
    personagem_id,
    nivel,
    nex,
    origem,
    atributos,
    historia,
    deslocamento="9m/6q",
    valores_editados=None,
):
    db = SessionLocal()
    try:
        personagem_db = db.query(Personagem).filter(Personagem.id == personagem_id).first()
        if personagem_db is None:
            return None

        personagem_db.nivel = nivel
        personagem_db.nex = nex
        personagem_db.origem = origem
        personagem_db.atributos = atributos
        personagem_db.historia = historia
        personagem_db.deslocamento = deslocamento
        if valores_editados is not None:
            personagem_db.valores_editados = valores_editados
        db.commit()
        return {
            "nivel": personagem_db.nivel,
            "nex": personagem_db.nex,
            "origem": personagem_db.origem,
            "atributos": personagem_db.atributos,
            "historia": personagem_db.historia,
            "deslocamento": personagem_db.deslocamento,
            "valores_editados": personagem_db.valores_editados,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def remover_personagem(personagem):
    db = SessionLocal()
    try:
        db.delete(personagem)
        db.commit()
    finally:
        db.close()
    apagar_arquivo_imagem(getattr(personagem, "imagem", None))


def _carregar_lista_json(texto):
    if not texto:
        return []

    try:
        dados = json.loads(texto)
    except (TypeError, ValueError):
        return []
    return dados if isinstance(dados, list) else []


def carregar_habilidades(personagem):
    habilidades = []
    for habilidade in _carregar_lista_json(personagem.habilidades):
        if isinstance(habilidade, str):
            habilidades.append({"nome": habilidade, "descricao": ""})
        elif isinstance(habilidade, dict) and isinstance(habilidade.get("nome"), str):
            habilidades.append({
                "nome": habilidade["nome"],
                "descricao": habilidade.get("descricao") or "",
            })
    return habilidades


def salvar_habilidades(personagem, habilidades):
    db = SessionLocal()
    try:
        personagem_db = db.query(Personagem).filter(Personagem.id == personagem.id).first()
        if personagem_db is None:
            return

        habilidades_json = json.dumps(habilidades, ensure_ascii=False)
        personagem_db.habilidades = habilidades_json
        personagem.habilidades = habilidades_json
        db.commit()
    finally:
        db.close()


def carregar_rituais(personagem):
    rituais = []
    for ritual in _carregar_lista_json(personagem.rituais):
        if isinstance(ritual, str):
            rituais.append({"nome": ritual, "simbolo": None, "descricao": ""})
        elif isinstance(ritual, dict) and isinstance(ritual.get("nome"), str):
            rituais.append({
                "nome": ritual["nome"],
                "simbolo": ritual.get("simbolo"),
                "descricao": ritual.get("descricao") or "",
            })
    return rituais


def salvar_rituais(personagem, rituais):
    db = SessionLocal()
    try:
        personagem_db = db.query(Personagem).filter(Personagem.id == personagem.id).first()
        if personagem_db is None:
            return

        rituais_json = json.dumps(rituais, ensure_ascii=False)
        personagem_db.rituais = rituais_json
        personagem.rituais = rituais_json
        db.commit()
    finally:
        db.close()
