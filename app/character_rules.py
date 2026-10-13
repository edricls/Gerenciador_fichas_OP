import json


def obter_limites_nivel(classe):
    return 1, 4 if classe == "Sobrevivente" else 20


def obter_nome_nivel(classe):
    return "Estágio" if classe == "Sobrevivente" else "Nível"


def validar_nex_texto(texto):
    texto_normalizado = str(texto).strip()
    if texto_normalizado == "":
        return texto_normalizado, 0, None

    if not texto_normalizado.isdigit() or not 0 <= int(texto_normalizado) <= 99:
        return texto_normalizado, None, "O valor de NEX deve ser entre 0 e 99"

    return texto_normalizado, int(texto_normalizado), None


def calcular_pv_pd(personagem, nivel=None, atributos=None):
    nivel_atual = nivel if nivel is not None else personagem.nivel
    nivel_atual = int(nivel_atual) if str(nivel_atual).isdigit() else 1
    atributos_texto = atributos if atributos is not None else personagem.atributos
    valores_atributos = {}
    for atributo in (atributos_texto or "").split(","):
        nome, separador, valor = atributo.partition("=")
        if separador:
            try:
                valores_atributos[nome.strip()] = int(valor.strip())
            except ValueError:
                valores_atributos[nome.strip()] = 0

    vigor = valores_atributos.get("Vigor", 0)
    presenca = valores_atributos.get("Presença", 0)
    niveis_adicionais = max(nivel_atual - 1, 0)

    if personagem.classe == "Combatente":
        pv = 20 + vigor + niveis_adicionais * (4 + vigor)
        pd = 6 + presenca + niveis_adicionais * (3 + presenca)
    elif personagem.classe == "Especialista":
        pv = 16 + vigor + niveis_adicionais * (3 + vigor)
        pd = 8 + presenca + niveis_adicionais * (4 + presenca)
    elif personagem.classe == "Ocultista":
        pv = 12 + vigor + niveis_adicionais * (2 + vigor)
        pd = 10 + presenca + niveis_adicionais * (5 + presenca)
    else:
        pv = 8 + vigor + niveis_adicionais * 2
        pd = 4 + presenca + niveis_adicionais * 2

    return pv, pd


def calcular_defesa(personagem, atributos=None):
    atributos_texto = atributos if atributos is not None else personagem.atributos
    agilidade = 0
    for atributo in (atributos_texto or "").split(","):
        nome, separador, valor = atributo.partition("=")
        if separador and nome.strip() == "Agilidade":
            try:
                agilidade = int(valor.strip())
            except ValueError:
                agilidade = 0
            break

    return 10 + agilidade


def carregar_valores_editados(personagem):
    try:
        valores = json.loads(getattr(personagem, "valores_editados", None) or "{}")
        if isinstance(valores, dict):
            return {
                chave: int(valor)
                for chave, valor in valores.items()
                if isinstance(valor, (int, float, str)) and str(valor).lstrip("-").isdigit()
            }
    except (TypeError, ValueError):
        pass
    return {}


def calcular_recursos(personagem, pericias=None, nivel=None, atributos=None, valores_editados=None):
    nivel_atual = nivel if nivel is not None else personagem.nivel
    pv, pd = calcular_pv_pd(personagem, nivel_atual, atributos)
    defesa = calcular_defesa(personagem, atributos)
    totais_pericias = {
        item.get("nome"): item.get("total", 0)
        for item in (pericias or [])
        if isinstance(item, dict)
    }

    def obter_total(nome):
        try:
            return int(totais_pericias.get(nome, 0))
        except (TypeError, ValueError):
            return 0

    bases = {
        "pv": pv,
        "pd": pd,
        "pd_turno": int(nivel_atual),
        "defesa": defesa,
        "esquiva": defesa + obter_total("Reflexos"),
        "bloqueio": obter_total("Fortitude"),
    }
    ajustes = valores_editados if valores_editados is not None else carregar_valores_editados(personagem)
    return {
        nome: valor + int(ajustes.get(nome, 0))
        for nome, valor in bases.items()
    }


LIMITES_ITENS_POR_PATENTE = {
    "Mundano": {"I": 1, "II": 0, "III": 0, "IV": 0},
    "Recruta": {"I": 2, "II": 0, "III": 0, "IV": 0},
    "Operador": {"I": 3, "II": 1, "III": 0, "IV": 0},
    "Agente Especial": {"I": 3, "II": 2, "III": 1, "IV": 0},
    "Oficial de Operações": {"I": 3, "II": 3, "III": 2, "IV": 1},
    "Agente de Elite": {"I": 3, "II": 3, "III": 3, "IV": 2},
}


def obter_limite_categoria(patente, categoria):
    """Retorna o limite de itens da categoria para a patente; None significa sem limite (categoria 0)."""
    if categoria == "0":
        return None
    limites = LIMITES_ITENS_POR_PATENTE.get(patente, LIMITES_ITENS_POR_PATENTE["Recruta"])
    return limites.get(categoria, 0)


def obter_forca(atributos_texto):
    for atributo in (atributos_texto or "").split(","):
        nome, separador, valor = atributo.partition("=")
        if separador and nome.strip() == "Força":
            try:
                return int(valor.strip())
            except ValueError:
                return 0
    return 0


def calcular_capacidade_carga(atributos_texto):
    forca = obter_forca(atributos_texto)
    if forca <= 0:
        return 2
    return forca * 5


def contar_itens_por_categoria(itens):
    contagem = {}
    for item in itens:
        categoria = item.get("categoria", "0")
        contagem[categoria] = contagem.get(categoria, 0) + 1
    return contagem


def calcular_peso_total(itens):
    total = 0
    for item in itens:
        try:
            total += float(item.get("peso", 0))
        except (TypeError, ValueError):
            pass
    return total


def validar_limite_categoria(itens, patente, categoria, ignorar_indice=None):
    """Retorna uma mensagem de erro se adicionar um item da categoria ultrapassar o limite da patente."""
    limite = obter_limite_categoria(patente, categoria)
    if limite is None:
        return None
    quantidade = sum(
        1
        for indice, item in enumerate(itens)
        if indice != ignorar_indice and item.get("categoria", "0") == categoria
    )
    if quantidade >= limite:
        if limite == 0:
            return f"A patente {patente} não permite itens de categoria {categoria}."
        return f"A patente {patente} permite no máximo {limite} item(ns) de categoria {categoria}."
    return None
