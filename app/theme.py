# Tema visual da aplicação: paleta de cores, tipografia e estilos reutilizáveis.
# Cada cor é uma tupla (modo claro, modo escuro), como o CustomTkinter espera.
import sys

import customtkinter as ctk

CORES = {
    "fundo": ("#F3F2F8", "#0E0E13"),
    "superficie": ("#FFFFFF", "#16161E"),
    "superficie_alt": ("#EEECF5", "#1D1D28"),
    "borda": ("#DEDAEA", "#2A2A38"),
    "entrada": ("#F8F7FC", "#111118"),
    "entrada_borda": ("#D2CEE0", "#2F2F40"),
    "texto": ("#1B1A24", "#ECEBF5"),
    "texto_suave": ("#6A6680", "#9A97B0"),
    "texto_claro": ("#FFFFFF", "#FFFFFF"),
    "destaque": ("#6A48F0", "#7C5CFF"),
    "destaque_hover": ("#5734D9", "#6745EE"),
    "destaque_suave": ("#E9E3FF", "#251E44"),
    "perigo": ("#D63447", "#E5484D"),
    "perigo_hover": ("#B52637", "#C7383D"),
    "item_hover": ("#ECE8F8", "#242432"),
    "aba_inativa": ("#8C88A2", "#1D1D28"),
    "aba_inativa_hover": ("#77738E", "#2A2A38"),
    "vida": ("#D63447", "#F06272"),
    "esforco": ("#6A48F0", "#9C83FF"),
}

RAIO = 10


def _familia_fonte():
    if sys.platform.startswith("win"):
        return "Segoe UI"
    if sys.platform == "darwin":
        return "SF Display"
    return "Roboto"


def aplicar_tema():
    """Carrega o tema base do CustomTkinter e sobrescreve com a paleta do app."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    tema = ctk.ThemeManager.theme

    tema["CTk"]["fg_color"] = CORES["fundo"]
    tema["CTkToplevel"]["fg_color"] = CORES["fundo"]
    tema["CTkFrame"].update(
        corner_radius=RAIO,
        fg_color=CORES["superficie"],
        top_fg_color=CORES["superficie_alt"],
        border_color=CORES["borda"],
    )
    tema["CTkButton"].update(
        corner_radius=8,
        fg_color=CORES["destaque"],
        hover_color=CORES["destaque_hover"],
        border_color=CORES["borda"],
        text_color=CORES["texto_claro"],
        text_color_disabled=CORES["texto_suave"],
    )
    tema["CTkLabel"]["text_color"] = CORES["texto"]
    tema["CTkEntry"].update(
        corner_radius=8,
        border_width=1,
        fg_color=CORES["entrada"],
        border_color=CORES["entrada_borda"],
        text_color=CORES["texto"],
        placeholder_text_color=CORES["texto_suave"],
    )
    tema["CTkCheckBox"].update(
        corner_radius=6,
        border_width=2,
        fg_color=CORES["destaque"],
        hover_color=CORES["destaque_hover"],
        border_color=CORES["entrada_borda"],
        checkmark_color=CORES["texto_claro"],
        text_color=CORES["texto"],
    )
    tema["CTkOptionMenu"].update(
        corner_radius=8,
        fg_color=CORES["superficie_alt"],
        button_color=CORES["superficie_alt"],
        button_hover_color=CORES["item_hover"],
        text_color=CORES["texto"],
        text_color_disabled=CORES["texto_suave"],
    )
    tema["CTkScrollbar"].update(
        button_color=CORES["borda"],
        button_hover_color=CORES["texto_suave"],
    )
    tema["CTkSegmentedButton"].update(
        corner_radius=8,
        fg_color=CORES["aba_inativa"],
        selected_color=CORES["destaque"],
        selected_hover_color=CORES["destaque_hover"],
        unselected_color=CORES["aba_inativa"],
        unselected_hover_color=CORES["aba_inativa_hover"],
        text_color=CORES["texto_claro"],
    )
    tema["CTkTextbox"].update(
        corner_radius=8,
        border_width=1,
        fg_color=CORES["entrada"],
        border_color=CORES["entrada_borda"],
        text_color=CORES["texto"],
        scrollbar_button_color=CORES["borda"],
        scrollbar_button_hover_color=CORES["texto_suave"],
    )
    tema["CTkScrollableFrame"]["label_fg_color"] = CORES["superficie_alt"]
    tema["DropdownMenu"].update(
        fg_color=CORES["superficie"],
        hover_color=CORES["item_hover"],
        text_color=CORES["texto"],
    )
    tema["CTkFont"].update(family=_familia_fonte(), size=13, weight="normal")


def fonte(tamanho=13, peso="normal"):
    return ctk.CTkFont(size=tamanho, weight=peso)


def iniciais(nome):
    partes = [parte for parte in (nome or "").split() if parte]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


# Estilos reutilizáveis, aplicados com **ESTILO nos widgets.
ESTILO_CARD = {
    "fg_color": CORES["superficie"],
    "corner_radius": 14,
    "border_width": 1,
    "border_color": CORES["borda"],
}

ESTILO_PAINEL = {
    "fg_color": CORES["superficie_alt"],
    "corner_radius": 12,
}

ESTILO_BOTAO_SECUNDARIO = {
    "fg_color": "transparent",
    "hover_color": CORES["item_hover"],
    "border_width": 1,
    "border_color": CORES["entrada_borda"],
    "text_color": CORES["texto"],
}

ESTILO_BOTAO_PERIGO = {
    "fg_color": CORES["perigo"],
    "hover_color": CORES["perigo_hover"],
    "text_color": CORES["texto_claro"],
}

ESTILO_BOTAO_PERIGO_CONTORNO = {
    "fg_color": "transparent",
    "hover_color": CORES["item_hover"],
    "border_width": 1,
    "border_color": CORES["perigo"],
    "text_color": CORES["perigo"],
}

ESTILO_ITEM_LISTA = {
    "fg_color": "transparent",
    "hover_color": CORES["item_hover"],
    "text_color": CORES["texto"],
    "corner_radius": 8,
    "height": 34,
}

ESTILO_ROTULO = {
    "text_color": CORES["texto_suave"],
}
