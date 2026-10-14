import json
import customtkinter as ctk
from tkinter import filedialog, messagebox, StringVar
from app.character_rules import (
    calcular_pv_pd,
    calcular_recursos,
    carregar_valores_editados,
    obter_limites_nivel,
    obter_nome_nivel,
    validar_nex_texto,
    calcular_capacidade_carga,
    calcular_peso_total,
    contar_itens_por_categoria,
    obter_forca,
    obter_limite_categoria,
)
from app.character_storage import (
    NomePersonagemDuplicadoError,
    existe_personagem_com_nome,
    atualizar_personagem,
    carregar_habilidades,
    carregar_rituais,
    listar_personagens,
    remover_personagem,
    salvar_personagem as salvar_personagem_no_banco,
    salvar_habilidades,
    salvar_rituais,
)
from app.gui_data import (
    ATRIBUTOS,
    ATRIBUTOS_PERICIAS,
    CLASSES,
    ORIGENS,
    PERICIAS,
    ELEMENTOS_RITUAIS,
    TRILHAS_POR_CLASSE,
    PATENTES,
    PATENTE_PADRAO,
    CATEGORIAS_ITENS,
    TIPOS_ITENS,
)
from app.icone import aplicar_icone, criar_imagem_icone
from app.imagem_storage import (
    AJUSTE_PADRAO,
    TIPOS_SUPORTADOS,
    ZOOM_MAXIMO,
    abrir_imagem,
    calcular_recorte,
    caminho_imagem,
    carregar_ajuste,
    carregar_imagem_circular,
    definir_imagem,
    recortar_circular,
    remover_imagem,
    salvar_ajuste,
)
from app.inventario_storage import (
    carregar_inventario,
    carregar_patente,
    salvar_inventario,
    salvar_patente,
)
from app.models import Personagem
from app.pericia_storage import (
    carregar_dados_pericias,
    dados_pericias_padrao,
    salvar_dados_pericias,
)

from app.theme import (
    CORES,
    CORES_ELEMENTOS,
    ESTILO_BOTAO_PERIGO,
    ESTILO_BOTAO_PERIGO_CONTORNO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_CARD,
    ESTILO_ITEM_LISTA,
    ESTILO_PAINEL,
    ESTILO_ROTULO,
    aplicar_tema,
    fonte,
    iniciais,
)

aplicar_tema()


def criar_avatar(master, nome, tamanho, caminho=None, ajuste=None):
    """Avatar circular com a foto do personagem ou, sem foto, as iniciais do nome."""
    avatar = ctk.CTkFrame(
        master,
        width=tamanho,
        height=tamanho,
        corner_radius=tamanho // 2,
        fg_color=CORES["destaque_suave"],
    )
    avatar.grid_propagate(False)
    avatar.pack_propagate(False)

    foto = None
    if caminho is not None:
        try:
            imagem = carregar_imagem_circular(caminho, tamanho, ajuste)
            foto = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(tamanho, tamanho))
        except (OSError, ValueError):
            foto = None

    if foto is not None:
        # Sem fundo próprio, para o recorte circular da foto não ganhar cantos quadrados.
        avatar.configure(fg_color="transparent")
        conteudo = ctk.CTkLabel(avatar, text="", image=foto, fg_color="transparent")
    else:
        conteudo = ctk.CTkLabel(
            avatar,
            text=iniciais(nome),
            text_color=CORES["destaque"],
            font=fonte(max(tamanho // 3, 14), "bold"),
        )
    conteudo.place(relx=0.5, rely=0.5, anchor="center")
    avatar.conteudo = conteudo
    return avatar


def criar_chip(master, texto, fg_color=None):
    return ctk.CTkLabel(
        master,
        text=texto,
        fg_color=fg_color or CORES["superficie_alt"],
        text_color=CORES["texto_suave"],
        corner_radius=8,
        height=24,
        font=fonte(12),
        padx=10,
    )


def criar_bloco_status(master, rotulo, valor="", cor=None, destaque=True, textvariable=None):
    bloco = ctk.CTkFrame(master, **ESTILO_PAINEL)
    ctk.CTkLabel(bloco, text=rotulo.upper(), font=fonte(11, "bold"), **ESTILO_ROTULO).pack(
        anchor="w", padx=12, pady=(8, 0)
    )
    valor_label = ctk.CTkLabel(
        bloco,
        text=valor,
        textvariable=textvariable,
        font=fonte(22 if destaque else 16, "bold"),
        text_color=cor or CORES["texto"],
    )
    valor_label.pack(anchor="w", padx=12, pady=(0, 8))
    return bloco, valor_label


def criar_rotulo_campo(master, texto, **kwargs):
    return ctk.CTkLabel(master, text=texto, font=fonte(12, "bold"), anchor="w", **ESTILO_ROTULO, **kwargs)


def criar_titulo_secao(master, texto):
    return ctk.CTkLabel(master, text=texto, font=fonte(15, "bold"), anchor="w")


def texto_resumo_personagem(personagem):
    origem_valor = getattr(personagem, "origem", None) or ""
    return f"{personagem.classe}  ·  Nível {personagem.nivel}  ·  NEX {personagem.nex}%  ·  {origem_valor or 'Origem não informada'}"


def formatar_peso(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "0"
    return f"{numero:g}".replace(".", ",")


def criar_tabview(master, **kwargs):
    # Ao trocar de aba, fecha dropdowns de Origem que ficaram abertos sobre a janela.
    tabview = ctk.CTkTabview(
        master,
        fg_color=CORES["superficie"],
        border_width=1,
        border_color=CORES["borda"],
        corner_radius=14,
        command=ScrollableOriginOptionMenu.fechar_dropdowns_abertos,
        **kwargs
    )
    tabview._segmented_button.configure(font=fonte(13, "bold"))
    return tabview


MENSAGEM_NOME_DUPLICADO = "Um personagem com este nome já existe."

CONFIG_HABILIDADES = {
    "titulo": "Habilidades",
    "singular": "Habilidade",
    "artigo": "uma",
    "do_registro": "da habilidade",
    "novo": "Nova Habilidade",
    "dica": "Cadastre as habilidades e poderes do seu personagem. Consulte o livro de regras e copie o nome e a descrição para cá.",
    "vazio": "Nenhuma habilidade cadastrada ainda.\nClique em \"+ Nova Habilidade\" para criar a primeira.",
    "selecione": "Selecione uma habilidade na lista.",
    "vazio_lista": "Nenhuma habilidade.",
    "carregar": carregar_habilidades,
    "salvar": salvar_habilidades,
    "usa_elemento": False,
}

CONFIG_RITUAIS = {
    "titulo": "Rituais",
    "singular": "Ritual",
    "artigo": "um",
    "do_registro": "do ritual",
    "novo": "Novo Ritual",
    "dica": "Cadastre os rituais que seu personagem conhece. Consulte o livro de regras e copie o nome, o elemento e a descrição para cá.",
    "vazio": "Nenhum ritual cadastrado ainda.\nClique em \"+ Novo Ritual\" para criar o primeiro.",
    "selecione": "Selecione um ritual na lista.",
    "vazio_lista": "Nenhum ritual.",
    "carregar": carregar_rituais,
    "salvar": salvar_rituais,
    "usa_elemento": True,
}


class ScrollableOriginOptionMenu(ctk.CTkOptionMenu):
    _menus_abertos = set()

    def __init__(self, master, values, width=560, height=32, command=None):
        super().__init__(master, values=values, width=width, height=height, command=command, dynamic_resizing=False)
        self._dropdown_frame = None

    @classmethod
    def fechar_dropdowns_abertos(cls):
        for menu in list(cls._menus_abertos):
            menu._close_dropdown_menu()

    def _open_dropdown_menu(self):
        if self._dropdown_frame is not None:
            self._close_dropdown_menu()
            return

        root = self.winfo_toplevel()
        self._dropdown_frame = ctk.CTkFrame(
            root,
            corner_radius=10,
            border_width=1,
            fg_color=CORES["superficie"],
            border_color=CORES["borda"]
        )

        x = self.winfo_rootx() - root.winfo_rootx()
        y = self.winfo_rooty() - root.winfo_rooty() + self.winfo_height() + 4
        self._dropdown_frame.place(x=x, y=y)
        self._dropdown_frame.lift()
        ScrollableOriginOptionMenu._menus_abertos.add(self)

        scroll_frame = ctk.CTkScrollableFrame(
            self._dropdown_frame,
            width=max(self._desired_width, 220),
            height=200,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=6, pady=6)

        for value in self._values:
            button = ctk.CTkButton(
                scroll_frame,
                text=value,
                width=max(self._desired_width, 220),
                height=30,
                fg_color=CORES["destaque_suave"] if value == self._current_value else "transparent",
                hover_color=CORES["item_hover"],
                text_color=CORES["texto"],
                corner_radius=6,
                anchor="w",
                command=lambda v=value: self._select_value(v)
            )
            button.pack(fill="x", padx=2, pady=1)

    def _select_value(self, value):
        self._current_value = value
        self._text_label.configure(text=value)

        if self._variable is not None:
            self._variable_callback_blocked = True
            self._variable.set(self._current_value)
            self._variable_callback_blocked = False

        if self._command is not None:
            self._command(self._current_value)

        self._close_dropdown_menu()

    def _close_dropdown_menu(self):
        ScrollableOriginOptionMenu._menus_abertos.discard(self)
        if self._dropdown_frame is not None:
            if self._dropdown_frame.winfo_exists():
                self._dropdown_frame.destroy()
            self._dropdown_frame = None

class GerenciadorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Fichas OP")
        aplicar_icone(self)
        self.geometry("1040x780")
        self.minsize(800, 600)

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=28, pady=(22, 0))
        simbolo = criar_imagem_icone(40)
        if simbolo is not None:
            ctk.CTkLabel(cabecalho, text="", image=simbolo).pack(side="left", padx=(0, 14))
        else:
            marca = ctk.CTkFrame(cabecalho, width=40, height=40, corner_radius=12, fg_color=CORES["destaque"])
            marca.pack(side="left", padx=(0, 14))
            marca.pack_propagate(False)
            ctk.CTkLabel(marca, text="◈", font=fonte(20, "bold"), text_color=CORES["texto_claro"]).place(
                relx=0.5, rely=0.5, anchor="center"
            )
        titulos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        titulos.pack(side="left")
        ctk.CTkLabel(titulos, text="Gerenciador de Fichas OP", font=fonte(20, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            titulos,
            text="Crie, consulte e edite as fichas dos seus personagens",
            font=fonte(12),
            anchor="w",
            **ESTILO_ROTULO
        ).pack(anchor="w")

        # Criar abas
        self.notebook = criar_tabview(self, width=900, height=640)
        self.notebook.pack(padx=20, pady=(8, 20), fill="both", expand=True)

        self.notebook.add("Criar Personagem")
        self.notebook.add("Listar Personagens")

        self.frame_criar = self.notebook.tab("Criar Personagem")
        self.frame_listar = self.notebook.tab("Listar Personagens")

        self.criar_aba_criar()
        self.criar_aba_listar()

    def criar_aba_criar(self):
        self.trilhas_por_classe = TRILHAS_POR_CLASSE

        self.entradas = {}

        formulario = ctk.CTkScrollableFrame(self.frame_criar, fg_color="transparent")
        formulario.pack(fill="both", expand=True, padx=4, pady=4)
        formulario.grid_columnconfigure(0, weight=1)

        # --- Identidade ---
        card_identidade = ctk.CTkFrame(formulario, **ESTILO_CARD)
        card_identidade.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 12))
        card_identidade.grid_columnconfigure((0, 1), weight=1, uniform="identidade")
        criar_titulo_secao(card_identidade, "Identidade").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 4)
        )

        criar_rotulo_campo(card_identidade, "Nome").grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(8, 4))
        nome_entrada = ctk.CTkEntry(card_identidade, width=560, height=36, placeholder_text="Nome do personagem")
        nome_entrada.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20)
        self.entradas["nome"] = nome_entrada

        criar_rotulo_campo(card_identidade, "Classe").grid(row=3, column=0, sticky="w", padx=(20, 8), pady=(14, 4))
        classe_entrada = ctk.CTkOptionMenu(
            card_identidade,
            values=CLASSES,
            width=260,
            height=36,
            command=self.atualizar_trilha_opcoes
        )
        classe_entrada.set("Combatente")
        classe_entrada.grid(row=4, column=0, sticky="ew", padx=(20, 8))
        self.entradas["classe"] = classe_entrada

        self.nivel_label = criar_rotulo_campo(card_identidade, "Nível")
        self.nivel_label.grid(row=5, column=0, sticky="w", padx=(20, 8), pady=(14, 4))
        nivel_entrada = ctk.CTkEntry(card_identidade, width=260, height=36, placeholder_text="1")
        nivel_entrada.grid(row=6, column=0, sticky="ew", padx=(20, 8))
        self.entradas["nivel"] = nivel_entrada

        criar_rotulo_campo(card_identidade, "NEX (%)").grid(row=5, column=1, sticky="w", padx=(8, 20), pady=(14, 4))
        nex_entrada = ctk.CTkEntry(card_identidade, width=260, height=36, placeholder_text="0")
        nex_entrada.grid(row=6, column=1, sticky="ew", padx=(8, 20))
        self.entradas["nex"] = nex_entrada

        self.nivel_erro_label = ctk.CTkLabel(
            card_identidade,
            text="",
            text_color=CORES["perigo"],
            anchor="w",
            height=18,
            font=fonte(12)
        )
        self.nivel_erro_label.grid(row=7, column=0, sticky="w", padx=(20, 8), pady=(2, 0))
        nivel_entrada.bind("<KeyRelease>", self.validar_nivel)
        nivel_entrada.bind("<FocusOut>", self.validar_nivel)

        self.nex_erro_label = ctk.CTkLabel(
            card_identidade,
            text="",
            text_color=CORES["perigo"],
            anchor="w",
            height=18,
            font=fonte(12)
        )
        self.nex_erro_label.grid(row=7, column=1, sticky="w", padx=(8, 20), pady=(2, 0))
        nex_entrada.bind("<KeyRelease>", self.validar_nex)
        nex_entrada.bind("<FocusOut>", self.validar_nex)

        criar_rotulo_campo(card_identidade, "Trilha").grid(row=3, column=1, sticky="w", padx=(8, 20), pady=(14, 4))
        trilha_entrada = ctk.CTkOptionMenu(
            card_identidade,
            values=self.trilhas_por_classe["Combatente"],
            width=260,
            height=36
        )
        trilha_entrada.set(self.trilhas_por_classe["Combatente"][0])
        trilha_entrada.grid(row=4, column=1, sticky="ew", padx=(8, 20))
        self.entradas["trilha"] = trilha_entrada
        self.atualizar_estado_trilha()

        criar_rotulo_campo(card_identidade, "Origem").grid(row=8, column=0, columnspan=2, sticky="w", padx=20, pady=(8, 4))
        origem_entrada = ScrollableOriginOptionMenu(
            card_identidade,
            values=ORIGENS,
            width=560,
            height=36
        )
        origem_entrada.set(ORIGENS[0])
        origem_entrada.grid(row=9, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        self.entradas["origem"] = origem_entrada

        # --- Atributos ---
        card_atributos = ctk.CTkFrame(formulario, **ESTILO_CARD)
        card_atributos.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 12))
        criar_titulo_secao(card_atributos, "Atributos").pack(anchor="w", padx=20, pady=(16, 8))

        atributos_frame = ctk.CTkFrame(card_atributos, fg_color="transparent")
        atributos_frame.pack(fill="x", padx=14, pady=(0, 18))

        for col, (texto, chave_attr) in enumerate(ATRIBUTOS):
            bloco = ctk.CTkFrame(atributos_frame, **ESTILO_PAINEL)
            bloco.grid(row=0, column=col, sticky="ew", padx=6)
            ctk.CTkLabel(bloco, text=texto.upper(), font=fonte(11, "bold"), **ESTILO_ROTULO).pack(pady=(10, 4))
            entrada_attr = ctk.CTkEntry(
                bloco,
                width=100,
                height=40,
                justify="center",
                font=fonte(18, "bold")
            )
            entrada_attr.pack(fill="x", padx=12, pady=(0, 12))
            entrada_attr.insert(0, "1")
            self.entradas[chave_attr] = entrada_attr
            atributos_frame.columnconfigure(col, weight=1, uniform="atributos")

        # --- História ---
        card_historia = ctk.CTkFrame(formulario, **ESTILO_CARD)
        card_historia.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 12))
        criar_titulo_secao(card_historia, "História").pack(anchor="w", padx=20, pady=(16, 8))
        historia_entrada = ctk.CTkTextbox(card_historia, width=560, height=140, wrap="word")
        historia_entrada.pack(fill="x", padx=20, pady=(0, 20))
        self.entradas["historia"] = historia_entrada

        ctk.CTkButton(
            formulario,
            text="Salvar Personagem",
            command=self.salvar_personagem,
            height=40,
            font=fonte(14, "bold")
        ).grid(row=3, column=0, sticky="e", padx=6, pady=(4, 16))

    def validar_nivel(self, event=None):
        nivel_texto = self.entradas["nivel"].get().strip()
        classe_selecionada = self.entradas["classe"].get().strip()
        limite_inferior, limite_superior = obter_limites_nivel(classe_selecionada)
        nome_nivel = obter_nome_nivel(classe_selecionada)

        # Limitar a no máximo 2 caracteres para o campo Nível/Estágio
        if len(nivel_texto) > 2:
            nivel_texto = nivel_texto[:2]
            self.entradas["nivel"].delete(0, "end")
            self.entradas["nivel"].insert(0, nivel_texto)
        if nivel_texto == "":
            self.nivel_erro_label.configure(text="")
            self.atualizar_estado_trilha()
            return True

        if not nivel_texto.isdigit():
            self.nivel_erro_label.configure(text=f"Digite um numero de {limite_inferior} a {limite_superior} para {nome_nivel}")
            self.atualizar_estado_trilha()
            return False

        nivel = int(nivel_texto)
        if nivel < limite_inferior or nivel > limite_superior:
            self.nivel_erro_label.configure(text=f"Digite um numero de {limite_inferior} a {limite_superior} para {nome_nivel}")
            self.atualizar_estado_trilha()
            return False

        self.nivel_erro_label.configure(text="")
        self.atualizar_estado_trilha()
        return True

    def validar_nex(self, event=None):
        nex_texto = self.entradas["nex"].get()
        _, _, erro = validar_nex_texto(nex_texto)
        if erro:
            self.nex_erro_label.configure(text=erro)
            return False

        self.nex_erro_label.configure(text="")
        return True

    def atualizar_trilha_opcoes(self, classe_selecionada, ajustar_nivel=True):
        trilha_menu = self.entradas.get("trilha")
        if trilha_menu is None:
            return

        self.nivel_label.configure(text="Estágio" if classe_selecionada == "Sobrevivente" else "Nível")
        nivel_texto = self.entradas["nivel"].get().strip()
        limite_inferior, limite_superior = obter_limites_nivel(classe_selecionada)
        if ajustar_nivel and (not nivel_texto.isdigit() or not limite_inferior <= int(nivel_texto) <= limite_superior):
            self.entradas["nivel"].delete(0, "end")
            self.entradas["nivel"].insert(0, str(limite_inferior))
            self.nivel_erro_label.configure(text="")

        nivel_texto = self.entradas["nivel"].get().strip()
        if nivel_texto.isdigit() and int(nivel_texto) < 2:
            return

        trilhas = self.trilhas_por_classe.get(classe_selecionada, [])
        trilha_menu.configure(values=trilhas)
        if trilhas:
            trilha_menu.set(trilhas[0])

    def atualizar_estado_trilha(self):
        trilha_menu = self.entradas.get("trilha")
        if trilha_menu is None:
            return

        nivel_texto = self.entradas["nivel"].get().strip()
        if nivel_texto.isdigit() and int(nivel_texto) < 2:
            trilha_menu.configure(values=["Nenhuma"], state="disabled")
            trilha_menu.set("Nenhuma")
            return

        trilha_menu.configure(state="normal")
        classe_selecionada = self.entradas["classe"].get().strip()
        self.atualizar_trilha_opcoes(classe_selecionada, ajustar_nivel=False)

    def criar_aba_listar(self):
        button_frame = ctk.CTkFrame(self.frame_listar, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(10, 0))

        criar_titulo_secao(button_frame, "Seus personagens").pack(side="left")
        ctk.CTkButton(
            button_frame,
            text="⟳  Atualizar Lista",
            command=self.atualizar_lista,
            width=150,
            **ESTILO_BOTAO_SECUNDARIO
        ).pack(side="right")

        self.lista_scroll = ctk.CTkScrollableFrame(self.frame_listar, width=900, height=520, fg_color="transparent")
        self.lista_scroll.pack(fill="both", expand=True, padx=4, pady=10)

        self.atualizar_lista()

    def salvar_personagem(self):
        try:
            nome = self.entradas["nome"].get().strip()
            classe = self.entradas["classe"].get().strip()

            if not nome or not classe:
                messagebox.showerror("Erro", "Nome e Classe são obrigatórios!")
                return

            if existe_personagem_com_nome(nome):
                messagebox.showerror("Erro", MENSAGEM_NOME_DUPLICADO)
                return

            nivel_texto = self.entradas["nivel"].get().strip()
            # Garantir que o texto do nível tenha no máximo 2 caracteres
            if len(nivel_texto) > 2:
                nivel_texto = nivel_texto[:2]
                self.entradas["nivel"].delete(0, "end")
                self.entradas["nivel"].insert(0, nivel_texto)
            if nivel_texto == "":
                nivel = 1
            else:
                classe_selecionada = self.entradas["classe"].get().strip()
                limite_inferior, limite_superior = obter_limites_nivel(classe_selecionada)
                nome_nivel = obter_nome_nivel(classe_selecionada)
                if not nivel_texto.isdigit() or not (limite_inferior <= int(nivel_texto) <= limite_superior):
                    self.nivel_erro_label.configure(
                        text=f"Digite um numero de {limite_inferior} a {limite_superior} para {nome_nivel}"
                    )
                    return
                nivel = int(nivel_texto)

            nex_texto, nex, erro_nex = validar_nex_texto(self.entradas["nex"].get())
            if erro_nex:
                self.nex_erro_label.configure(text=erro_nex)
                return

            atributos_valores = []
            for label, chave in ATRIBUTOS:
                valor_texto = self.entradas[chave].get().strip()
                if valor_texto == "":
                    valor_texto = "1"
                else:
                    int(valor_texto)
                atributos_valores.append(f"{label}={valor_texto}")
            atributos_texto = ", ".join(atributos_valores)

            novo_p = Personagem(
                nome=nome,
                classe=classe,
                nivel=nivel,
                nex=nex,
                atributos=atributos_texto,
                trilha=self.entradas["trilha"].get().strip(),
                origem=self.entradas["origem"].get().strip(),
                deslocamento="9m/6q",
                historia=self.entradas["historia"].get("1.0", "end").strip(),
                pericias=json.dumps(dados_pericias_padrao(PERICIAS, ATRIBUTOS_PERICIAS)),
                habilidades=json.dumps([]),
                rituais=json.dumps([]),
                patente=PATENTE_PADRAO,
                inventario=json.dumps([])
            )

            salvar_personagem_no_banco(novo_p)

            self._limpar_formulario()

            messagebox.showinfo("Sucesso", f"Personagem '{nome}' salvo com sucesso!")
            self.nivel_erro_label.configure(text="")
            self.nex_erro_label.configure(text="")
            self.atualizar_lista()

        except NomePersonagemDuplicadoError:
            messagebox.showerror("Erro", MENSAGEM_NOME_DUPLICADO)
        except ValueError:
            messagebox.showerror("Erro", "Nível, NEX e atributos devem ser números!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

    def _limpar_formulario(self):
        for chave, entrada in self.entradas.items():
            if isinstance(entrada, ctk.CTkTextbox):
                entrada.delete("1.0", "end")
            elif isinstance(entrada, ctk.CTkOptionMenu):
                if chave == "classe":
                    entrada.set("Combatente")
                elif chave == "trilha":
                    entrada.set(self.trilhas_por_classe["Combatente"][0])
            else:
                entrada.delete(0, "end")

    def _carregar_dados_pericias(self, personagem):
        return carregar_dados_pericias(personagem, PERICIAS, ATRIBUTOS_PERICIAS)

    def _salvar_pericias_personagem(self, personagem, dados_pericias):
        try:
            salvar_dados_pericias(personagem, dados_pericias)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar perícias: {str(e)}")

    def remover_personagem_confirm(self, personagem):
        confirmar = messagebox.askyesno(
            "Confirmar remoção",
            f"Deseja realmente remover o personagem '{personagem.nome}'?"
        )
        if not confirmar:
            return

        try:
            remover_personagem(personagem)
            messagebox.showinfo("Removido", f"Personagem '{personagem.nome}' removido com sucesso.")
            self.atualizar_lista()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover personagem: {str(e)}")

    def calcular_pv_pd(self, personagem, nivel=None, atributos=None):
        return calcular_pv_pd(personagem, nivel, atributos)

    def abrir_ficha(self, personagem):
        ficha = ctk.CTkToplevel(self)
        aplicar_icone(ficha)
        ficha.title(f"Ficha de {personagem.nome}")
        ficha.geometry("820x760")
        ficha.minsize(680, 560)
        ficha.grab_set()

        header_frame = ctk.CTkFrame(ficha, **ESTILO_CARD)
        header_frame.pack(fill="x", padx=20, pady=(20, 12))
        header_frame.grid_columnconfigure(1, weight=1)

        foto_widgets = {"avatar": None}
        foto_acoes = ctk.CTkFrame(header_frame, fg_color="transparent")
        foto_acoes.grid(row=0, column=2, rowspan=2, padx=20)
        botao_alterar_foto = ctk.CTkButton(
            foto_acoes,
            text="Alterar foto",
            width=120,
            command=lambda: escolher_foto(),
            **ESTILO_BOTAO_SECUNDARIO
        )
        botao_alterar_foto.pack(pady=(0, 6))
        botao_ajustar_foto = ctk.CTkButton(
            foto_acoes,
            text="Ajustar foto",
            width=120,
            command=lambda: ajustar_foto(),
            **ESTILO_BOTAO_SECUNDARIO
        )
        botao_remover_foto = ctk.CTkButton(
            foto_acoes,
            text="Remover foto",
            width=120,
            command=lambda: remover_foto(),
            **ESTILO_BOTAO_PERIGO_CONTORNO
        )

        def atualizar_foto():
            if foto_widgets["avatar"] is not None:
                foto_widgets["avatar"].destroy()
            caminho = caminho_imagem(personagem)
            avatar = criar_avatar(header_frame, personagem.nome, 84, caminho, carregar_ajuste(personagem))
            avatar.grid(row=0, column=0, rowspan=2, padx=(20, 16), pady=18)
            # Clicar no avatar ajusta a foto existente ou, sem foto, abre a escolha de uma.
            for widget in (avatar, avatar.conteudo):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda event: ajustar_foto() if caminho_imagem(personagem) else escolher_foto())
            foto_widgets["avatar"] = avatar
            botao_alterar_foto.configure(text="Alterar foto" if caminho else "Adicionar foto")
            if caminho:
                botao_ajustar_foto.pack(pady=(0, 6))
                botao_remover_foto.pack()
            else:
                botao_ajustar_foto.pack_forget()
                botao_remover_foto.pack_forget()

        def foto_alterada():
            atualizar_foto()
            self.atualizar_lista()

        def ajustar_foto():
            self._abrir_ajuste_foto(personagem, ficha, foto_alterada)

        def escolher_foto():
            arquivo = filedialog.askopenfilename(
                parent=ficha,
                title=f"Escolher foto de {personagem.nome}",
                filetypes=TIPOS_SUPORTADOS,
            )
            if not arquivo:
                return
            try:
                definir_imagem(personagem, arquivo)
            except ValueError as erro:
                messagebox.showerror("Erro", str(erro), parent=ficha)
                return
            except OSError as erro:
                messagebox.showerror("Erro", f"Não foi possível salvar a foto: {erro}", parent=ficha)
                return
            foto_alterada()
            ajustar_foto()

        def remover_foto():
            if not messagebox.askyesno("Remover foto", "Deseja remover a foto deste personagem?", parent=ficha):
                return
            remover_imagem(personagem)
            atualizar_foto()
            self.atualizar_lista()

        atualizar_foto()

        ctk.CTkLabel(header_frame, text=personagem.nome, font=fonte(24, "bold"), anchor="w").grid(
            row=0, column=1, sticky="sw", pady=(18, 0)
        )
        resumo_ficha = ctk.CTkLabel(
            header_frame,
            text=texto_resumo_personagem(personagem),
            anchor="w",
            **ESTILO_ROTULO
        )
        resumo_ficha.grid(row=1, column=1, sticky="nw", pady=(2, 18))

        tabview = criar_tabview(ficha)
        tabview.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        tab_dados = tabview.add("Dados Gerais")
        tab_pericias = tabview.add("Perícias")
        tab_habilidades = tabview.add("Habilidades")
        tab_rituais = tabview.add("Rituais")
        tab_inventario = tabview.add("Inventário")

        self._criar_aba_registros(tab_habilidades, personagem, CONFIG_HABILIDADES)
        self._criar_aba_registros(tab_rituais, personagem, CONFIG_RITUAIS)

        info_frame = ctk.CTkScrollableFrame(tab_dados, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        info_frame.grid_columnconfigure(0, weight=1)

        dados_pericias_iniciais = self._carregar_dados_pericias(personagem)
        recursos_iniciais = calcular_recursos(personagem, dados_pericias_iniciais)
        esquiva_var = StringVar(value=str(recursos_iniciais['esquiva']))
        bloqueio_var = StringVar(value=str(recursos_iniciais['bloqueio']))
        recursos_frame_ficha = ctk.CTkFrame(info_frame, fg_color="transparent")
        recursos_frame_ficha.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 12))
        recursos_frame_ficha.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="recursos")

        def posicionar_bloco(bloco, linha, coluna):
            bloco.grid(row=linha, column=coluna, sticky="ew", padx=4, pady=4)

        bloco, valor_pv_ficha = criar_bloco_status(recursos_frame_ficha, "PV", str(recursos_iniciais['pv']), CORES["vida"])
        posicionar_bloco(bloco, 0, 0)
        bloco, valor_pd_ficha = criar_bloco_status(recursos_frame_ficha, "PD", str(recursos_iniciais['pd']), CORES["esforco"])
        posicionar_bloco(bloco, 0, 1)
        bloco, pd_turno_ficha = criar_bloco_status(recursos_frame_ficha, "PD/Turno", str(recursos_iniciais['pd_turno']))
        posicionar_bloco(bloco, 0, 2)
        bloco, valor_defesa_ficha = criar_bloco_status(recursos_frame_ficha, "Defesa", str(recursos_iniciais['defesa']))
        posicionar_bloco(bloco, 0, 3)
        bloco, _ = criar_bloco_status(recursos_frame_ficha, "Esquiva", textvariable=esquiva_var, destaque=False)
        posicionar_bloco(bloco, 1, 0)
        bloco, _ = criar_bloco_status(recursos_frame_ficha, "Bloqueio", textvariable=bloqueio_var, destaque=False)
        posicionar_bloco(bloco, 1, 1)
        bloco, valor_deslocamento_ficha = criar_bloco_status(
            recursos_frame_ficha,
            "Deslocamento",
            getattr(personagem, 'deslocamento', None) or '9m/6q',
            destaque=False
        )
        posicionar_bloco(bloco, 1, 2)

        detalhes_card = ctk.CTkFrame(info_frame, **ESTILO_CARD)
        detalhes_card.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 12))
        detalhes_card.grid_columnconfigure(1, weight=1)
        criar_titulo_secao(detalhes_card, "Detalhes").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        def criar_linha_detalhe(linha, rotulo, valor):
            ultima = linha == 5
            criar_rotulo_campo(detalhes_card, rotulo).grid(
                row=linha, column=0, sticky="w", padx=20, pady=(4, 16 if ultima else 4)
            )
            valor_label = ctk.CTkLabel(detalhes_card, text=valor, anchor="e", font=fonte(13, "bold"))
            valor_label.grid(row=linha, column=1, sticky="e", padx=20, pady=(4, 16 if ultima else 4))
            return valor_label

        valor_classe = criar_linha_detalhe(1, "Classe", personagem.classe)
        valor_nivel = criar_linha_detalhe(2, "Nível", str(personagem.nivel))
        valor_nex = criar_linha_detalhe(3, "NEX", f"{personagem.nex}%")
        valor_trilha = criar_linha_detalhe(4, "Trilha", personagem.trilha)
        valor_origem = criar_linha_detalhe(5, "Origem", getattr(personagem, "origem", None) or "Não informada")

        atributos_card = ctk.CTkFrame(info_frame, **ESTILO_CARD)
        atributos_card.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 12))
        criar_titulo_secao(atributos_card, "Atributos").pack(anchor="w", padx=20, pady=(16, 8))
        atributos_frame_ficha = ctk.CTkFrame(atributos_card, fg_color="transparent")
        atributos_frame_ficha.pack(fill="x", padx=14, pady=(0, 18))
        atributos_frame_ficha.grid_columnconfigure(tuple(range(5)), weight=1, uniform="atributos")

        atributos_nomes_ficha = [nome for nome, _ in ATRIBUTOS]
        atributos_salvos_ficha = {}
        for atributo in (personagem.atributos or "").split(","):
            nome, separador, valor = atributo.partition("=")
            if separador:
                atributos_salvos_ficha[nome.strip()] = valor.strip()

        valores_atributos_ficha = {}
        for coluna, nome_atributo in enumerate(atributos_nomes_ficha):
            bloco_atributo = ctk.CTkFrame(atributos_frame_ficha, **ESTILO_PAINEL)
            bloco_atributo.grid(row=0, column=coluna, sticky="ew", padx=6)
            ctk.CTkLabel(
                bloco_atributo,
                text=nome_atributo.upper(),
                font=fonte(11, "bold"),
                **ESTILO_ROTULO
            ).pack(pady=(10, 0))
            valor_atributo = ctk.CTkLabel(
                bloco_atributo,
                text=atributos_salvos_ficha.get(nome_atributo, "1"),
                font=fonte(24, "bold")
            )
            valor_atributo.pack(pady=(0, 10))
            valores_atributos_ficha[nome_atributo] = valor_atributo

        historia_card = ctk.CTkFrame(info_frame, **ESTILO_CARD)
        historia_card.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 12))
        criar_titulo_secao(historia_card, "História").pack(anchor="w", padx=20, pady=(16, 8))
        historia_text = ctk.CTkTextbox(historia_card, width=460, height=180, wrap="word")
        historia_text.pack(fill="x", padx=20, pady=(0, 20))
        historia_text.insert("1.0", personagem.historia)
        historia_text.configure(state="disabled")

        atualizar_inventario = self._criar_aba_inventario(tab_inventario, personagem)

        tab_edicao = tabview.add("Editar Ficha")
        self._criar_aba_edicao(
            tabview,
            tab_edicao,
            personagem,
            {
                "valor_pv_ficha": valor_pv_ficha,
                "valor_pd_ficha": valor_pd_ficha,
                "pd_turno_ficha": pd_turno_ficha,
                "valor_defesa_ficha": valor_defesa_ficha,
                "valor_deslocamento_ficha": valor_deslocamento_ficha,
                "esquiva_var": esquiva_var,
                "bloqueio_var": bloqueio_var,
                "resumo_ficha": resumo_ficha,
                "valor_nivel": valor_nivel,
                "valor_nex": valor_nex,
                "valor_origem": valor_origem,
                "valores_atributos_ficha": valores_atributos_ficha,
                "historia_text": historia_text,
                "atualizar_inventario": atualizar_inventario,
            },
        )

        self._criar_aba_pericias(tab_pericias, personagem, ficha, esquiva_var, bloqueio_var)

    def _abrir_ajuste_foto(self, personagem, janela_pai, ao_salvar):
        """Janela para enquadrar a foto: arrastar move, roda do mouse/controle aproxima."""
        caminho = caminho_imagem(personagem)
        if caminho is None:
            return
        try:
            original = abrir_imagem(caminho)
        except (OSError, ValueError):
            messagebox.showerror("Erro", "Não foi possível abrir a foto.", parent=janela_pai)
            return

        _, ajuste = calcular_recorte(original.width, original.height, carregar_ajuste(personagem))
        tamanho_previa = 280

        janela = ctk.CTkToplevel(self)
        aplicar_icone(janela)
        janela.title(f"Ajustar foto - {personagem.nome}")
        janela.geometry("420x500")
        janela.resizable(False, False)
        janela.transient(janela_pai)
        janela.grab_set()

        ctk.CTkLabel(janela, text="Ajustar foto", font=fonte(17, "bold")).pack(pady=(20, 2))
        ctk.CTkLabel(
            janela,
            text="Arraste a imagem para posicionar e use a roda do mouse ou o controle abaixo para aproximar.",
            font=fonte(12),
            wraplength=360,
            **ESTILO_ROTULO
        ).pack(padx=20)

        moldura = ctk.CTkFrame(
            janela,
            width=tamanho_previa,
            height=tamanho_previa,
            fg_color="transparent",
        )
        moldura.pack(pady=16)
        moldura.pack_propagate(False)
        previa = ctk.CTkLabel(moldura, text="", fg_color="transparent", cursor="fleur")
        previa.place(relx=0.5, rely=0.5, anchor="center")

        controle_zoom = ctk.CTkFrame(janela, fg_color="transparent")
        controle_zoom.pack(fill="x", padx=40)
        ctk.CTkLabel(controle_zoom, text="−", font=fonte(16, "bold"), **ESTILO_ROTULO).pack(side="left")
        zoom_slider = ctk.CTkSlider(controle_zoom, from_=1.0, to=ZOOM_MAXIMO)
        zoom_slider.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(controle_zoom, text="+", font=fonte(16, "bold"), **ESTILO_ROTULO).pack(side="left")

        def renderizar():
            imagem = recortar_circular(original, tamanho_previa, ajuste)
            foto = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(tamanho_previa, tamanho_previa))
            previa.configure(image=foto)
            previa.foto = foto

        def aplicar(novo_ajuste):
            _, corrigido = calcular_recorte(original.width, original.height, novo_ajuste)
            ajuste.update(corrigido)
            renderizar()

        def definir_zoom(valor):
            aplicar({**ajuste, "zoom": float(valor)})

        arrasto = {"x": 0, "y": 0}

        def iniciar_arrasto(event):
            arrasto["x"], arrasto["y"] = event.x_root, event.y_root

        def arrastar(event):
            dx = event.x_root - arrasto["x"]
            dy = event.y_root - arrasto["y"]
            arrasto["x"], arrasto["y"] = event.x_root, event.y_root
            # Converte o movimento na tela em pixels da imagem original.
            lado_recorte = min(original.width, original.height) / ajuste["zoom"]
            pixels_por_ponto = lado_recorte / max(previa.winfo_width(), 1)
            aplicar({
                **ajuste,
                "x": ajuste["x"] - dx * pixels_por_ponto / original.width,
                "y": ajuste["y"] - dy * pixels_por_ponto / original.height,
            })

        def rolar(event):
            fator = 1.1 if event.delta > 0 else 1 / 1.1
            aplicar({**ajuste, "zoom": ajuste["zoom"] * fator})
            zoom_slider.set(ajuste["zoom"])

        def centralizar():
            aplicar(dict(AJUSTE_PADRAO))
            zoom_slider.set(ajuste["zoom"])

        def fechar():
            janela.destroy()
            if janela_pai.winfo_exists():
                janela_pai.grab_set()

        def salvar():
            salvar_ajuste(personagem, ajuste)
            fechar()
            ao_salvar()

        zoom_slider.configure(command=definir_zoom)
        zoom_slider.set(ajuste["zoom"])
        previa.bind("<ButtonPress-1>", iniciar_arrasto)
        previa.bind("<B1-Motion>", arrastar)
        previa.bind("<MouseWheel>", rolar)
        zoom_slider.bind("<MouseWheel>", rolar)
        janela.protocol("WM_DELETE_WINDOW", fechar)

        botoes = ctk.CTkFrame(janela, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(20, 20))
        ctk.CTkButton(botoes, text="Centralizar", width=110, command=centralizar, **ESTILO_BOTAO_SECUNDARIO).pack(side="left")
        ctk.CTkButton(botoes, text="Salvar", width=110, font=fonte(13, "bold"), command=salvar).pack(side="right")
        ctk.CTkButton(botoes, text="Cancelar", width=110, command=fechar, **ESTILO_BOTAO_SECUNDARIO).pack(side="right", padx=(0, 8))

        renderizar()

    def _criar_aba_registros(self, tab, personagem, config):
        """Aba de habilidades ou rituais cadastrados pelo próprio usuário."""
        selecionado = {"indice": None}

        cabecalho = ctk.CTkFrame(tab, **ESTILO_CARD)
        cabecalho.pack(fill="x", padx=8, pady=(8, 10))
        cabecalho.grid_columnconfigure(0, weight=1)
        criar_titulo_secao(cabecalho, config["titulo"]).grid(row=0, column=0, sticky="w", padx=20, pady=(14, 0))
        ctk.CTkLabel(
            cabecalho,
            text=config["dica"],
            font=fonte(12),
            anchor="w",
            justify="left",
            wraplength=520,
            **ESTILO_ROTULO
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(2, 14))
        ctk.CTkButton(
            cabecalho,
            text=f"+  {config['novo']}",
            font=fonte(13, "bold"),
            command=lambda: self._abrir_editor_registro(personagem, config, atualizar)
        ).grid(row=0, column=1, rowspan=2, padx=20)

        conteudo = ctk.CTkFrame(tab, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        conteudo.grid_columnconfigure(0, weight=2, uniform="registros")
        conteudo.grid_columnconfigure(1, weight=3, uniform="registros")
        conteudo.grid_rowconfigure(0, weight=1)

        # --- Lista ---
        lista_painel = ctk.CTkFrame(conteudo, **ESTILO_PAINEL)
        lista_painel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        busca_entrada = ctk.CTkEntry(
            lista_painel,
            height=34,
            placeholder_text="Buscar..."
        )
        busca_entrada.pack(fill="x", padx=10, pady=(10, 4))
        lista_frame = ctk.CTkScrollableFrame(lista_painel, fg_color="transparent")
        lista_frame.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        # --- Detalhes ---
        detalhes = ctk.CTkFrame(conteudo, **ESTILO_PAINEL)
        detalhes.grid(row=0, column=1, sticky="nsew")
        titulo = ctk.CTkLabel(detalhes, text="", font=fonte(19, "bold"), anchor="w", justify="left", wraplength=320)
        titulo.pack(fill="x", padx=20, pady=(18, 4))
        elemento_chip = criar_chip(detalhes, "", fg_color=CORES["superficie"])
        descricao = ctk.CTkTextbox(detalhes, wrap="word", fg_color="transparent", border_width=0)
        acoes = ctk.CTkFrame(detalhes, fg_color="transparent")
        ctk.CTkButton(
            acoes,
            text="Editar",
            width=90,
            command=lambda: self._abrir_editor_registro(personagem, config, atualizar, selecionado["indice"]),
            **ESTILO_BOTAO_SECUNDARIO
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            acoes,
            text="Remover",
            width=90,
            command=lambda: remover(),
            **ESTILO_BOTAO_PERIGO_CONTORNO
        ).pack(side="left")
        vazio = ctk.CTkLabel(detalhes, text="", font=fonte(13), justify="center", wraplength=300, **ESTILO_ROTULO)

        def mostrar_detalhes(indice):
            registros = config["carregar"](personagem)
            if indice is None or not 0 <= indice < len(registros):
                selecionado["indice"] = None
                titulo.pack_forget()
                elemento_chip.pack_forget()
                descricao.pack_forget()
                acoes.pack_forget()
                vazio.configure(text=config["vazio"] if not registros else config["selecione"])
                vazio.pack(expand=True, padx=20, pady=20)
                atualizar_lista()
                return

            selecionado["indice"] = indice
            registro = registros[indice]
            vazio.pack_forget()
            acoes.pack_forget()
            descricao.pack_forget()
            elemento_chip.pack_forget()
            titulo.pack(fill="x", padx=20, pady=(18, 4))
            titulo.configure(text=registro["nome"])
            if config["usa_elemento"] and registro.get("simbolo"):
                elemento_chip.configure(
                    text=registro["simbolo"],
                    text_color=CORES_ELEMENTOS.get(registro["simbolo"], CORES["texto_suave"])
                )
                elemento_chip.pack(anchor="w", padx=20, pady=(0, 4))
            acoes.pack(side="bottom", anchor="w", padx=20, pady=(4, 16))
            descricao.pack(fill="both", expand=True, padx=14, pady=(4, 4))
            descricao.configure(state="normal")
            descricao.delete("1.0", "end")
            descricao.insert("1.0", registro["descricao"] or "Sem descrição. Clique em Editar para adicionar.")
            descricao.configure(state="disabled")
            atualizar_lista()

        def remover():
            indice = selecionado["indice"]
            registros = config["carregar"](personagem)
            if indice is None or not 0 <= indice < len(registros):
                return
            if not messagebox.askyesno(
                f"Remover {config['singular'].lower()}",
                f"Deseja remover '{registros[indice]['nome']}'?"
            ):
                return
            registros.pop(indice)
            config["salvar"](personagem, registros)
            atualizar(None)

        def atualizar_lista():
            for widget in lista_frame.winfo_children():
                widget.destroy()

            registros = config["carregar"](personagem)
            termo = busca_entrada.get().strip().lower()
            visiveis = [(i, r) for i, r in enumerate(registros) if termo in r["nome"].lower()]
            if not visiveis:
                ctk.CTkLabel(
                    lista_frame,
                    text=config["vazio_lista"] if not registros else "Nada encontrado.",
                    **ESTILO_ROTULO
                ).pack(anchor="w", padx=10, pady=10)
                return

            for indice, registro in visiveis:
                estilo = dict(ESTILO_ITEM_LISTA)
                if indice == selecionado["indice"]:
                    estilo["fg_color"] = CORES["destaque_suave"]
                ctk.CTkButton(
                    lista_frame,
                    text=registro["nome"],
                    anchor="w",
                    command=lambda i=indice: mostrar_detalhes(i),
                    **estilo
                ).pack(fill="x", padx=4, pady=1)

        atualizar = mostrar_detalhes

        busca_entrada.bind("<KeyRelease>", lambda event: atualizar_lista())
        atualizar(None)

    def _abrir_editor_registro(self, personagem, config, atualizar, indice=None):
        registros = config["carregar"](personagem)
        registro_atual = registros[indice] if indice is not None and 0 <= indice < len(registros) else None

        janela = ctk.CTkToplevel(self)
        aplicar_icone(janela)
        janela.title(f"Editar {config['singular']}" if registro_atual else config["novo"])
        janela.geometry("560x560")
        janela.minsize(440, 440)
        janela.grab_set()

        conteudo = ctk.CTkFrame(janela, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        conteudo.grid_columnconfigure(0, weight=1)

        linha = 0
        criar_rotulo_campo(conteudo, "Nome").grid(row=linha, column=0, sticky="w", pady=(0, 4))
        nome_entrada = ctk.CTkEntry(conteudo, height=36, placeholder_text=f"Nome {config['do_registro']}")
        nome_entrada.grid(row=linha + 1, column=0, sticky="ew")
        linha += 2

        elemento_menu = None
        if config["usa_elemento"]:
            criar_rotulo_campo(conteudo, "Elemento").grid(row=linha, column=0, sticky="w", pady=(14, 4))
            elemento_menu = ctk.CTkOptionMenu(conteudo, values=ELEMENTOS_RITUAIS, height=36, dynamic_resizing=False)
            elemento_menu.grid(row=linha + 1, column=0, sticky="ew")
            elemento_menu.set(
                registro_atual.get("simbolo")
                if registro_atual and registro_atual.get("simbolo") in ELEMENTOS_RITUAIS
                else ELEMENTOS_RITUAIS[0]
            )
            linha += 2

        criar_rotulo_campo(conteudo, "Descrição").grid(row=linha, column=0, sticky="w", pady=(14, 4))
        ctk.CTkLabel(
            conteudo,
            text="Dica: copie o texto do livro de regras de Ordem Paranormal e cole aqui.",
            font=fonte(12),
            anchor="w",
            **ESTILO_ROTULO
        ).grid(row=linha + 1, column=0, sticky="w", pady=(0, 6))
        descricao_entrada = ctk.CTkTextbox(conteudo, wrap="word")
        descricao_entrada.grid(row=linha + 2, column=0, sticky="nsew")
        conteudo.grid_rowconfigure(linha + 2, weight=1)

        if registro_atual:
            nome_entrada.insert(0, registro_atual["nome"])
            descricao_entrada.insert("1.0", registro_atual["descricao"])

        def salvar():
            nome = nome_entrada.get().strip()
            if not nome:
                messagebox.showerror("Erro", "O nome é obrigatório.", parent=janela)
                return

            registros_atuais = config["carregar"](personagem)
            if any(
                i != indice and r["nome"].strip().lower() == nome.lower()
                for i, r in enumerate(registros_atuais)
            ):
                messagebox.showerror("Erro", f"Já existe {config['artigo']} {config['singular'].lower()} com esse nome.", parent=janela)
                return

            novo_registro = {"nome": nome, "descricao": descricao_entrada.get("1.0", "end").strip()}
            if elemento_menu is not None:
                novo_registro["simbolo"] = elemento_menu.get()

            if registro_atual:
                registros_atuais[indice] = novo_registro
                indice_salvo = indice
            else:
                registros_atuais.append(novo_registro)
                indice_salvo = len(registros_atuais) - 1
            config["salvar"](personagem, registros_atuais)
            janela.destroy()
            atualizar(indice_salvo)

        ctk.CTkButton(
            janela,
            text="Salvar",
            height=40,
            font=fonte(14, "bold"),
            command=salvar
        ).pack(anchor="e", padx=20, pady=(0, 20))
        nome_entrada.focus_set()

    def _criar_aba_inventario(self, tab_inventario, personagem):
        inventario_frame = ctk.CTkScrollableFrame(tab_inventario, fg_color="transparent")
        inventario_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        inventario_frame.grid_columnconfigure((0, 1), weight=1, uniform="inventario")

        filtro_tipo = {"valor": "Todos"}

        # --- Patente ---
        patente_card = ctk.CTkFrame(inventario_frame, **ESTILO_CARD)
        patente_card.grid(row=0, column=0, sticky="nsew", padx=(8, 6), pady=(8, 12))
        criar_titulo_secao(patente_card, "Patente").pack(anchor="w", padx=20, pady=(16, 8))

        def alterar_patente(patente):
            salvar_patente(personagem, patente)
            atualizar_inventario()

        patente_menu = ctk.CTkOptionMenu(
            patente_card,
            values=PATENTES,
            height=36,
            command=alterar_patente,
            dynamic_resizing=False
        )
        patente_menu.set(carregar_patente(personagem))
        patente_menu.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(
            patente_card,
            text="Define quantos itens de cada categoria o agente pode levar.",
            font=fonte(12),
            anchor="w",
            justify="left",
            wraplength=300,
            **ESTILO_ROTULO
        ).pack(fill="x", padx=20, pady=(0, 16))

        # --- Carga ---
        carga_card = ctk.CTkFrame(inventario_frame, **ESTILO_CARD)
        carga_card.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=(8, 12))
        criar_titulo_secao(carga_card, "Carga").pack(anchor="w", padx=20, pady=(16, 4))
        carga_valor = ctk.CTkLabel(carga_card, text="", font=fonte(22, "bold"), anchor="w")
        carga_valor.pack(anchor="w", padx=20)
        carga_barra = ctk.CTkProgressBar(carga_card, height=10)
        carga_barra.pack(fill="x", padx=20, pady=(6, 6))
        carga_status = ctk.CTkLabel(carga_card, text="", font=fonte(12), anchor="w")
        carga_status.pack(anchor="w", padx=20, pady=(0, 16))

        # --- Limites por categoria ---
        limites_card = ctk.CTkFrame(inventario_frame, **ESTILO_CARD)
        limites_card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 12))
        criar_titulo_secao(limites_card, "Itens por categoria").pack(anchor="w", padx=20, pady=(16, 8))
        limites_frame = ctk.CTkFrame(limites_card, fg_color="transparent")
        limites_frame.pack(fill="x", padx=14, pady=(0, 18))
        limites_frame.grid_columnconfigure(tuple(range(len(CATEGORIAS_ITENS))), weight=1, uniform="limites")
        valores_limites = {}
        for coluna, categoria in enumerate(CATEGORIAS_ITENS):
            bloco = ctk.CTkFrame(limites_frame, **ESTILO_PAINEL)
            bloco.grid(row=0, column=coluna, sticky="ew", padx=6)
            ctk.CTkLabel(bloco, text=f"CATEGORIA {categoria}", font=fonte(11, "bold"), **ESTILO_ROTULO).pack(pady=(10, 0))
            valor_limite = ctk.CTkLabel(bloco, text="", font=fonte(18, "bold"))
            valor_limite.pack(pady=(0, 10))
            valores_limites[categoria] = valor_limite

        # --- Itens ---
        itens_card = ctk.CTkFrame(inventario_frame, **ESTILO_CARD)
        itens_card.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 12))
        itens_header = ctk.CTkFrame(itens_card, fg_color="transparent")
        itens_header.pack(fill="x", padx=20, pady=(16, 8))
        criar_titulo_secao(itens_header, "Itens").pack(side="left")
        ctk.CTkButton(
            itens_header,
            text="+  Adicionar Item",
            font=fonte(13, "bold"),
            command=lambda: self._abrir_editor_item(personagem, atualizar_inventario)
        ).pack(side="right")

        def filtrar(valor):
            filtro_tipo["valor"] = valor
            atualizar_inventario()

        filtro = ctk.CTkSegmentedButton(itens_card, values=["Todos"] + TIPOS_ITENS, command=filtrar)
        filtro.set("Todos")
        filtro.pack(anchor="w", padx=20, pady=(0, 10))

        lista_itens = ctk.CTkFrame(itens_card, fg_color="transparent")
        lista_itens.pack(fill="x", padx=20, pady=(0, 16))
        lista_itens.grid_columnconfigure(0, weight=1)

        def remover_item(indice):
            itens = carregar_inventario(personagem)
            if not 0 <= indice < len(itens):
                return
            if not messagebox.askyesno("Remover item", f"Deseja remover '{itens[indice]['nome']}' do inventário?"):
                return
            itens.pop(indice)
            salvar_inventario(personagem, itens)
            atualizar_inventario()

        def atualizar_inventario():
            itens = carregar_inventario(personagem)
            patente = carregar_patente(personagem)

            capacidade = calcular_capacidade_carga(personagem.atributos)
            peso_total = calcular_peso_total(itens)
            sobrecarregado = peso_total > capacidade
            carga_valor.configure(
                text=f"{formatar_peso(peso_total)} / {formatar_peso(capacidade)}",
                text_color=CORES["perigo"] if sobrecarregado else CORES["texto"]
            )
            carga_barra.configure(progress_color=CORES["perigo"] if sobrecarregado else CORES["destaque"])
            carga_barra.set(min(peso_total / capacidade, 1) if capacidade else 1)
            if sobrecarregado:
                carga_status.configure(
                    text=f"Sobrecarregado: {formatar_peso(peso_total - capacidade)} acima da capacidade",
                    text_color=CORES["perigo"]
                )
            else:
                carga_status.configure(
                    text=f"Capacidade definida pela Força ({obter_forca(personagem.atributos)})",
                    text_color=CORES["texto_suave"]
                )

            contagem = contar_itens_por_categoria(itens)
            for categoria, valor_limite in valores_limites.items():
                quantidade = contagem.get(categoria, 0)
                limite = obter_limite_categoria(patente, categoria)
                if limite is None:
                    valor_limite.configure(text=f"{quantidade} / ∞", text_color=CORES["texto"])
                    continue
                if quantidade > limite:
                    cor = CORES["perigo"]
                elif limite == 0:
                    cor = CORES["texto_suave"]
                else:
                    cor = CORES["texto"]
                valor_limite.configure(text=f"{quantidade} / {limite}", text_color=cor)

            for widget in lista_itens.winfo_children():
                widget.destroy()

            itens_visiveis = [
                (indice, item) for indice, item in enumerate(itens)
                if filtro_tipo["valor"] == "Todos" or item.get("tipo") == filtro_tipo["valor"]
            ]
            if not itens_visiveis:
                ctk.CTkLabel(
                    lista_itens,
                    text="Nenhum item no inventário." if not itens else "Nenhum item deste tipo.",
                    **ESTILO_ROTULO
                ).grid(row=0, column=0, sticky="w", pady=8)
                return

            for linha, (indice, item) in enumerate(itens_visiveis):
                item_frame = ctk.CTkFrame(lista_itens, **ESTILO_PAINEL)
                item_frame.grid(row=linha, column=0, sticky="ew", pady=3)
                item_frame.grid_columnconfigure(0, weight=1)

                textos = ctk.CTkFrame(item_frame, fg_color="transparent")
                textos.grid(row=0, column=0, sticky="w", padx=14, pady=10)
                ctk.CTkLabel(textos, text=item["nome"], font=fonte(14, "bold"), anchor="w").pack(anchor="w")
                chips = ctk.CTkFrame(textos, fg_color="transparent")
                chips.pack(anchor="w", pady=(4, 0))
                for texto_chip in (
                    item.get("tipo", "Geral"),
                    f"Categoria {item.get('categoria', '0')}",
                    f"Peso {formatar_peso(item.get('peso', 0))}",
                ):
                    criar_chip(chips, texto_chip, fg_color=CORES["superficie"]).pack(side="left", padx=(0, 6))
                if item.get("descricao"):
                    ctk.CTkLabel(
                        textos,
                        text=item["descricao"],
                        font=fonte(12),
                        anchor="w",
                        justify="left",
                        wraplength=480,
                        **ESTILO_ROTULO
                    ).pack(anchor="w", pady=(6, 0))

                acoes = ctk.CTkFrame(item_frame, fg_color="transparent")
                acoes.grid(row=0, column=1, sticky="e", padx=14, pady=10)
                ctk.CTkButton(
                    acoes,
                    text="Editar",
                    width=70,
                    command=lambda i=indice: self._abrir_editor_item(personagem, atualizar_inventario, i),
                    **ESTILO_BOTAO_SECUNDARIO
                ).pack(side="left", padx=(0, 6))
                ctk.CTkButton(
                    acoes,
                    text="Remover",
                    width=80,
                    command=lambda i=indice: remover_item(i),
                    **ESTILO_BOTAO_PERIGO_CONTORNO
                ).pack(side="left")

        atualizar_inventario()
        return atualizar_inventario

    def _abrir_editor_item(self, personagem, atualizar_inventario, indice=None):
        itens = carregar_inventario(personagem)
        item_atual = itens[indice] if indice is not None and 0 <= indice < len(itens) else None

        janela = ctk.CTkToplevel(self)
        aplicar_icone(janela)
        janela.title("Editar Item" if item_atual else f"Adicionar Item - {personagem.nome}")
        janela.geometry("460x540")
        janela.minsize(400, 480)
        janela.grab_set()

        conteudo = ctk.CTkFrame(janela, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=20, pady=20)
        conteudo.grid_columnconfigure((0, 1), weight=1, uniform="item")

        criar_rotulo_campo(conteudo, "Nome").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        nome_entrada = ctk.CTkEntry(conteudo, height=36, placeholder_text="Nome do item")
        nome_entrada.grid(row=1, column=0, columnspan=2, sticky="ew")

        criar_rotulo_campo(conteudo, "Tipo").grid(row=2, column=0, columnspan=2, sticky="w", pady=(14, 4))
        tipo_menu = ctk.CTkOptionMenu(conteudo, values=TIPOS_ITENS, height=36, dynamic_resizing=False)
        tipo_menu.grid(row=3, column=0, columnspan=2, sticky="ew")

        criar_rotulo_campo(conteudo, "Categoria").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(14, 4))
        categoria_menu = ctk.CTkOptionMenu(conteudo, values=CATEGORIAS_ITENS, height=36, dynamic_resizing=False)
        categoria_menu.grid(row=5, column=0, sticky="ew", padx=(0, 8))

        criar_rotulo_campo(conteudo, "Peso").grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(14, 4))
        peso_entrada = ctk.CTkEntry(conteudo, height=36, placeholder_text="0")
        peso_entrada.grid(row=5, column=1, sticky="ew", padx=(8, 0))

        criar_rotulo_campo(conteudo, "Descrição").grid(row=6, column=0, columnspan=2, sticky="w", pady=(14, 4))
        descricao_entrada = ctk.CTkTextbox(conteudo, height=120, wrap="word")
        descricao_entrada.grid(row=7, column=0, columnspan=2, sticky="nsew")
        conteudo.grid_rowconfigure(7, weight=1)

        if item_atual:
            nome_entrada.insert(0, item_atual.get("nome", ""))
            tipo_menu.set(item_atual.get("tipo", "Geral") if item_atual.get("tipo") in TIPOS_ITENS else "Geral")
            categoria_menu.set(item_atual.get("categoria", "0") if item_atual.get("categoria") in CATEGORIAS_ITENS else "0")
            peso_entrada.insert(0, formatar_peso(item_atual.get("peso", 0)))
            descricao_entrada.insert("1.0", item_atual.get("descricao", ""))
        else:
            tipo_menu.set("Geral")
            categoria_menu.set("0")

        def salvar_item():
            nome = nome_entrada.get().strip()
            if not nome:
                messagebox.showerror("Erro", "O nome do item é obrigatório.", parent=janela)
                return

            peso_texto = peso_entrada.get().strip().replace(",", ".") or "0"
            try:
                peso = float(peso_texto)
            except ValueError:
                peso = -1
            if peso < 0:
                messagebox.showerror("Erro", "O peso deve ser um número maior ou igual a zero.", parent=janela)
                return

            # Passar do limite da patente é permitido; a aba destaca a categoria excedida em vermelho.
            itens_atuais = carregar_inventario(personagem)
            categoria = categoria_menu.get()

            novo_item = {
                "nome": nome,
                "tipo": tipo_menu.get(),
                "categoria": categoria,
                "peso": int(peso) if peso.is_integer() else peso,
                "descricao": descricao_entrada.get("1.0", "end").strip(),
            }
            if item_atual:
                itens_atuais[indice] = novo_item
            else:
                itens_atuais.append(novo_item)
            salvar_inventario(personagem, itens_atuais)
            atualizar_inventario()
            janela.destroy()

        ctk.CTkButton(
            janela,
            text="Salvar Item",
            height=40,
            font=fonte(14, "bold"),
            command=salvar_item
        ).pack(anchor="e", padx=20, pady=(0, 20))
        nome_entrada.focus_set()

    def _criar_aba_edicao(self, tabview, tab_edicao, personagem, ficha_widgets):
        valor_pv_ficha = ficha_widgets["valor_pv_ficha"]
        valor_pd_ficha = ficha_widgets["valor_pd_ficha"]
        pd_turno_ficha = ficha_widgets["pd_turno_ficha"]
        valor_defesa_ficha = ficha_widgets["valor_defesa_ficha"]
        valor_deslocamento_ficha = ficha_widgets["valor_deslocamento_ficha"]
        esquiva_var = ficha_widgets["esquiva_var"]
        bloqueio_var = ficha_widgets["bloqueio_var"]
        resumo_ficha = ficha_widgets["resumo_ficha"]
        valor_nivel = ficha_widgets["valor_nivel"]
        valor_nex = ficha_widgets["valor_nex"]
        valor_origem = ficha_widgets["valor_origem"]
        valores_atributos_ficha = ficha_widgets["valores_atributos_ficha"]
        historia_text = ficha_widgets["historia_text"]
        atualizar_inventario = ficha_widgets["atualizar_inventario"]

        edicao_frame = ctk.CTkScrollableFrame(tab_edicao, fg_color="transparent")
        edicao_frame.pack(fill="both", expand=True, padx=4, pady=4)
        edicao_frame.grid_columnconfigure(1, weight=1)

        dados_pericias_edicao = self._carregar_dados_pericias(personagem)
        valores_recursos_iniciais = calcular_recursos(personagem, dados_pericias_edicao)
        recursos_frame_edicao = ctk.CTkFrame(edicao_frame, **ESTILO_PAINEL)
        recursos_frame_edicao.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 12))
        recursos_frame_edicao.grid_columnconfigure((0, 1, 2), weight=1)
        nomes_recursos = {
            "pv": "PV",
            "pd": "PD",
            "pd_turno": "PD/Turno",
            "defesa": "Defesa",
            "esquiva": "Esquiva",
            "bloqueio": "Bloqueio",
        }
        campos_recursos = {}
        for indice, (chave, nome) in enumerate(nomes_recursos.items()):
            linha = (indice // 3) * 2
            coluna = indice % 3
            criar_rotulo_campo(recursos_frame_edicao, nome).grid(
                row=linha, column=coluna, sticky="w", padx=14, pady=(12, 4)
            )
            campo = ctk.CTkEntry(recursos_frame_edicao, width=100)
            campo.grid(row=linha + 1, column=coluna, sticky="w", padx=14, pady=(0, 4))
            campo.insert(0, str(valores_recursos_iniciais[chave]))
            campos_recursos[chave] = campo

        criar_rotulo_campo(recursos_frame_edicao, "Deslocamento").grid(
            row=4, column=0, sticky="w", padx=14, pady=(12, 4)
        )
        deslocamento_edicao = ctk.CTkEntry(recursos_frame_edicao, width=100)
        deslocamento_edicao.grid(row=5, column=0, sticky="w", padx=14, pady=(0, 14))
        deslocamento_edicao.insert(0, getattr(personagem, "deslocamento", None) or "9m/6q")

        criar_rotulo_campo(edicao_frame, "Classe").grid(
            row=1, column=0, sticky="w", padx=10, pady=10
        )
        ctk.CTkLabel(edicao_frame, text=personagem.classe, anchor="w", font=fonte(13, "bold")).grid(
            row=1, column=1, sticky="w", padx=10, pady=10
        )

        _, limite_nivel_edicao = obter_limites_nivel(personagem.classe)
        nome_nivel_edicao = obter_nome_nivel(personagem.classe)

        criar_rotulo_campo(edicao_frame, nome_nivel_edicao).grid(
            row=2, column=0, sticky="w", padx=10, pady=10
        )
        nivel_edicao = ctk.CTkOptionMenu(
            edicao_frame,
            values=[str(nivel) for nivel in range(1, limite_nivel_edicao + 1)],
            width=100
        )
        nivel_edicao.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        nivel_edicao.set(
            str(personagem.nivel)
            if 1 <= personagem.nivel <= limite_nivel_edicao
            else "1"
        )

        criar_rotulo_campo(edicao_frame, "NEX (%)").grid(
            row=3, column=0, sticky="w", padx=10, pady=10
        )
        nex_edicao = ctk.CTkEntry(edicao_frame, width=100)
        nex_edicao.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        nex_edicao.insert(0, str(personagem.nex))

        nex_edicao_erro = ctk.CTkLabel(edicao_frame, text="", text_color=CORES["perigo"], anchor="w", font=fonte(12))
        nex_edicao_erro.grid(row=4, column=1, sticky="w", padx=10, pady=(0, 4))

        def validar_nex_edicao(event=None):
            nex_texto = nex_edicao.get()
            _, _, erro = validar_nex_texto(nex_texto)
            if erro:
                nex_edicao_erro.configure(text=erro)
                return False
            nex_edicao_erro.configure(text="")
            return True

        nex_edicao.bind("<KeyRelease>", validar_nex_edicao)
        nex_edicao.bind("<FocusOut>", validar_nex_edicao)
        validar_nex_edicao()

        criar_rotulo_campo(edicao_frame, "Origem").grid(
            row=5, column=0, sticky="w", padx=10, pady=10
        )
        origem_edicao = ScrollableOriginOptionMenu(edicao_frame, values=ORIGENS, width=460)
        origem_edicao.grid(row=5, column=1, sticky="ew", padx=10, pady=10)
        origem_edicao.set(getattr(personagem, "origem", None) or ORIGENS[0])

        criar_rotulo_campo(edicao_frame, "Atributos").grid(
            row=6, column=0, sticky="nw", padx=10, pady=10
        )
        atributos_frame_edicao = ctk.CTkFrame(edicao_frame, **ESTILO_PAINEL)
        atributos_frame_edicao.grid(row=6, column=1, sticky="ew", padx=10, pady=10)
        atributos_frame_edicao.grid_columnconfigure(tuple(range(5)), weight=1)

        atributos_nomes = [nome for nome, _ in ATRIBUTOS]
        atributos_salvos = {}
        for atributo in (personagem.atributos or "").split(","):
            nome, separador, valor = atributo.partition("=")
            if separador:
                atributos_salvos[nome.strip()] = valor.strip()

        atributos_edicao = {}
        for coluna, nome_atributo in enumerate(atributos_nomes):
            ctk.CTkLabel(atributos_frame_edicao, text=nome_atributo.upper(), font=fonte(11, "bold"), **ESTILO_ROTULO).grid(
                row=0, column=coluna, padx=8, pady=(10, 4)
            )
            valor_atributo = ctk.CTkEntry(atributos_frame_edicao, width=70, justify="center", font=fonte(15, "bold"))
            valor_atributo.grid(row=1, column=coluna, sticky="ew", padx=8, pady=(0, 12))
            valor_atributo.insert(0, atributos_salvos.get(nome_atributo, "1"))
            atributos_edicao[nome_atributo] = valor_atributo

        criar_rotulo_campo(edicao_frame, "História").grid(
            row=7, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0)
        )
        historia_edicao = ctk.CTkTextbox(edicao_frame, height=260, wrap="word")
        historia_edicao.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        edicao_frame.grid_rowconfigure(8, weight=1)
        historia_edicao.insert("1.0", personagem.historia or "")

        def salvar_edicao():
            nivel_texto = nivel_edicao.get().strip()
            _, nex, erro_nex = validar_nex_texto(nex_edicao.get())
            if not nivel_texto.isdigit() or not 1 <= int(nivel_texto) <= limite_nivel_edicao:
                messagebox.showerror(
                    "Erro",
                    f"O {nome_nivel_edicao.lower()} deve ser um número entre 1 e {limite_nivel_edicao}."
                )
                return
            if erro_nex:
                messagebox.showerror("Erro", erro_nex + ".")
                return

            atributos_valores = []
            for nome_atributo in atributos_nomes:
                valor = atributos_edicao[nome_atributo].get().strip()
                if not valor.isdigit():
                    messagebox.showerror("Erro", f"O valor de {nome_atributo} deve ser numérico.")
                    return
                atributos_valores.append(f"{nome_atributo}={valor}")

            valores_recursos_informados = {}
            for chave, campo in campos_recursos.items():
                valor = campo.get().strip()
                if not valor.isdigit():
                    messagebox.showerror("Erro", f"O valor de {nomes_recursos[chave]} deve ser um número inteiro não negativo.")
                    return
                valores_recursos_informados[chave] = int(valor)

            try:
                atributos_texto = ", ".join(atributos_valores)
                dados_pericias = self._carregar_dados_pericias(personagem)
                ajustes_recursos = carregar_valores_editados(personagem)
                recursos_base = calcular_recursos(
                    personagem,
                    dados_pericias,
                    nivel=int(nivel_texto),
                    atributos=atributos_texto,
                    valores_editados={},
                )
                for chave, valor in valores_recursos_informados.items():
                    if valor != valores_recursos_iniciais[chave]:
                        ajustes_recursos[chave] = valor - recursos_base[chave]

                dados_atualizados = atualizar_personagem(
                    personagem.id,
                    int(nivel_texto),
                    nex,
                    origem_edicao.get().strip(),
                    atributos_texto,
                    historia_edicao.get("1.0", "end").strip(),
                    deslocamento_edicao.get().strip() or "9m/6q",
                    json.dumps(ajustes_recursos),
                )
                if dados_atualizados is None:
                    messagebox.showerror("Erro", "Personagem não encontrado no banco de dados.")
                    return

                personagem.nivel = dados_atualizados["nivel"]
                personagem.nex = dados_atualizados["nex"]
                personagem.origem = dados_atualizados["origem"]
                personagem.atributos = dados_atualizados["atributos"]
                personagem.historia = dados_atualizados["historia"]
                personagem.deslocamento = dados_atualizados["deslocamento"]
                personagem.valores_editados = dados_atualizados["valores_editados"]
                recursos_atualizados = calcular_recursos(
                    personagem,
                    dados_pericias,
                    valores_editados=ajustes_recursos,
                )
                valor_pv_ficha.configure(text=str(recursos_atualizados['pv']))
                valor_pd_ficha.configure(text=str(recursos_atualizados['pd']))
                pd_turno_ficha.configure(text=str(recursos_atualizados['pd_turno']))
                valor_defesa_ficha.configure(text=str(recursos_atualizados['defesa']))
                valor_deslocamento_ficha.configure(text=personagem.deslocamento)
                esquiva_var.set(str(recursos_atualizados['esquiva']))
                bloqueio_var.set(str(recursos_atualizados['bloqueio']))
                valores_recursos_iniciais.update(recursos_atualizados)
                for chave, campo in campos_recursos.items():
                    campo.delete(0, "end")
                    campo.insert(0, str(recursos_atualizados[chave]))
                resumo_ficha.configure(text=texto_resumo_personagem(personagem))
                valor_nivel.configure(text=str(personagem.nivel))
                valor_nex.configure(text=f"{personagem.nex}%")
                valor_origem.configure(text=personagem.origem or "Não informada")
                atributos_atualizados = {}
                for atributo in (personagem.atributos or "").split(","):
                    nome, separador, valor = atributo.partition("=")
                    if separador:
                        atributos_atualizados[nome.strip()] = valor.strip()
                for nome_atributo, valor_atributo in valores_atributos_ficha.items():
                    valor_atributo.configure(text=atributos_atualizados.get(nome_atributo, "1"))
                historia_text.configure(state="normal")
                historia_text.delete("1.0", "end")
                historia_text.insert("1.0", personagem.historia)
                historia_text.configure(state="disabled")
                atualizar_inventario()
                self.atualizar_lista()
                tabview.set("Dados Gerais")
                messagebox.showinfo("Sucesso", "Ficha atualizada com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar ficha: {str(e)}")

        ctk.CTkButton(
            edicao_frame,
            text="Salvar Alterações",
            height=40,
            font=fonte(14, "bold"),
            command=salvar_edicao
        ).grid(row=9, column=1, sticky="e", padx=10, pady=10)

    def _criar_aba_pericias(self, tab_pericias, personagem, ficha, esquiva_var, bloqueio_var):
        pericias_frame = ctk.CTkScrollableFrame(tab_pericias, **ESTILO_PAINEL)
        pericias_frame.pack(fill="both", expand=True, padx=8, pady=8)
        pericias_frame.grid_columnconfigure(0, weight=1)

        headers = ["Pericia", "Treino", "Atributo", "Extra", "Total"]
        for index, titulo in enumerate(headers):
            ctk.CTkLabel(pericias_frame, text=titulo.upper(), font=fonte(11, "bold"), **ESTILO_ROTULO).grid(
                row=0, column=index, padx=8, pady=(8, 6), sticky="w"
            )

        dados_pericias_salvos = self._carregar_dados_pericias(personagem)
        rows_state = []

        for row_index, (nome_pericia, atributo_pericia) in enumerate(zip(PERICIAS, ATRIBUTOS_PERICIAS), start=1):
            dados_pericia = next((item for item in dados_pericias_salvos if item.get("nome") == nome_pericia), None)
            if dados_pericia is None:
                dados_pericia = {
                    "nome": nome_pericia,
                    "atributo": atributo_pericia,
                    "treino": 0,
                    "extra": 0,
                    "total": 0,
                }

            ctk.CTkLabel(pericias_frame, text=nome_pericia, anchor="w").grid(
                row=row_index, column=0, padx=8, pady=2, sticky="w"
            )

            treino_menu = ctk.CTkOptionMenu(pericias_frame, values=["0", "5", "10", "15"], width=80)
            treino_menu.set(str(dados_pericia.get("treino", 0)))
            treino_menu.grid(row=row_index, column=1, padx=8, pady=2, sticky="w")

            ctk.CTkLabel(pericias_frame, text=atributo_pericia, anchor="w").grid(
                row=row_index, column=2, padx=8, pady=2, sticky="w"
            )

            extra_var = StringVar(value=str(dados_pericia.get("extra", 0)))
            ctk.CTkEntry(pericias_frame, textvariable=extra_var, width=80).grid(
                row=row_index, column=3, padx=8, pady=2, sticky="w"
            )

            total_var = StringVar(value=str(dados_pericia.get("total", 0)))
            ctk.CTkLabel(
                pericias_frame,
                textvariable=total_var,
                width=48,
                corner_radius=8,
                fg_color=CORES["destaque_suave"],
                text_color=CORES["destaque"],
                font=fonte(13, "bold")
            ).grid(
                row=row_index, column=4, padx=8, pady=2, sticky="w"
            )

            rows_state.append({
                "nome": nome_pericia,
                "atributo": atributo_pericia,
                "treino_menu": treino_menu,
                "extra_var": extra_var,
                "total_var": total_var,
            })

        def atualizar_todas_as_pericias(event=None):
            dados_para_salvar = []
            totais_pericias = {}
            for row_state in rows_state:
                try:
                    treino = int(row_state["treino_menu"].get())
                except ValueError:
                    treino = 0

                valor_extra = row_state["extra_var"].get().strip()
                if valor_extra == "":
                    valor_extra = "0"
                if not valor_extra.isdigit():
                    valor_extra = "".join(ch for ch in valor_extra if ch.isdigit()) or "0"
                    row_state["extra_var"].set(valor_extra)

                try:
                    extra = int(valor_extra)
                except ValueError:
                    extra = 0

                total = treino + extra
                row_state["total_var"].set(str(total))
                totais_pericias[row_state["nome"]] = total
                dados_para_salvar.append({
                    "nome": row_state["nome"],
                    "atributo": row_state["atributo"],
                    "treino": treino,
                    "extra": extra,
                    "total": total,
                })

            recursos_atualizados = calcular_recursos(personagem, dados_para_salvar)
            esquiva_var.set(str(recursos_atualizados['esquiva']))
            bloqueio_var.set(str(recursos_atualizados['bloqueio']))
            self._salvar_pericias_personagem(personagem, dados_para_salvar)

        def salvar_e_fechar():
            atualizar_todas_as_pericias()
            ficha.destroy()

        for row_state in rows_state:
            row_state["extra_var"].trace_add("write", lambda *args, state=row_state: atualizar_todas_as_pericias())
            row_state["treino_menu"].configure(command=lambda value=None: atualizar_todas_as_pericias())
            row_state["extra_var"].set(row_state["extra_var"].get())

        atualizar_todas_as_pericias()
        ctk.CTkButton(ficha, text="Fechar", width=140, command=salvar_e_fechar, **ESTILO_BOTAO_SECUNDARIO).pack(
            anchor="e", padx=20, pady=(0, 16)
        )

    def atualizar_lista(self):
        for widget in self.lista_scroll.winfo_children():
            widget.destroy()

        try:
            personagens = listar_personagens()

            if not personagens:
                vazio = ctk.CTkFrame(self.lista_scroll, **ESTILO_CARD)
                vazio.pack(fill="x", padx=6, pady=20)
                ctk.CTkLabel(vazio, text="◈", font=fonte(32), text_color=CORES["destaque"]).pack(pady=(28, 4))
                ctk.CTkLabel(vazio, text="Nenhum personagem encontrado no banco de dados.", font=fonte(15, "bold")).pack()
                ctk.CTkLabel(
                    vazio,
                    text="Crie um novo personagem na aba \"Criar Personagem\".",
                    **ESTILO_ROTULO
                ).pack(pady=(2, 28))
                return

            for personagem in personagens:
                card = ctk.CTkFrame(self.lista_scroll, **ESTILO_CARD)
                card.pack(fill="x", padx=6, pady=6)
                card.grid_columnconfigure(1, weight=1)

                criar_avatar(card, personagem.nome, 64, caminho_imagem(personagem), carregar_ajuste(personagem)).grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=16)

                ctk.CTkLabel(card, text=personagem.nome, font=fonte(17, "bold"), anchor="w").grid(
                    row=0, column=1, sticky="sw", pady=(16, 2)
                )
                origem_valor = getattr(personagem, "origem", None) or ""
                chips = ctk.CTkFrame(card, fg_color="transparent")
                chips.grid(row=1, column=1, sticky="nw", pady=(2, 16))
                for texto_chip in (
                    personagem.classe,
                    f"Nível {personagem.nivel}",
                    f"NEX {personagem.nex}%",
                    origem_valor or "Origem não informada",
                ):
                    criar_chip(chips, texto_chip).pack(side="left", padx=(0, 6))

                acoes = ctk.CTkFrame(card, fg_color="transparent")
                acoes.grid(row=0, column=2, rowspan=2, padx=18, pady=16)
                ctk.CTkButton(
                    acoes,
                    text="Acessar Ficha",
                    width=120,
                    command=lambda p=personagem: self.abrir_ficha(p)
                ).pack(side="left", padx=(0, 8))
                ctk.CTkButton(
                    acoes,
                    text="Remover",
                    width=90,
                    command=lambda p=personagem: self.remover_personagem_confirm(p),
                    **ESTILO_BOTAO_PERIGO_CONTORNO
                ).pack(side="left")

        except Exception as e:
            error_label = ctk.CTkLabel(self.lista_scroll, text=f"Erro ao carregar personagens: {str(e)}", text_color=CORES["perigo"])
            error_label.pack(pady=20)


def iniciar_gui():
    app = GerenciadorGUI()
    app.mainloop()


if __name__ == "__main__":
    iniciar_gui()
