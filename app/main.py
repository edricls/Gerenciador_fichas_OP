#Este é o arquivo principal, o "ponto de entrada" do seu programa.
#É o arquivo que você vai executar no terminal usando o comando python -m app.main.
from app.database import engine, Base, SessionLocal, ensure_database_schema
from app.models import Personagem
from app.character_storage import (
    NomePersonagemDuplicadoError,
    existe_personagem_com_nome,
    salvar_personagem,
)
from rich.console import Console # Usando a biblioteca Rich que você instalou
from app.gui import iniciar_gui

console = Console()

def iniciar_sistema():
    # Isso roda sempre, mas o SQLAlchemy é inteligente: se as tabelas 
    # já existirem no arquivo .db, ele não faz nada e não apaga seus dados.
    ensure_database_schema()

    # LOOP do jogo
    while True:
        console.print("\n[bold blue]=== GERENCIADOR DE INVENTÁRIO RPG ===[/bold blue]")
        print("1. Criar Novo Personagem")
        print("2. Listar Personagens Existentes")
        print("3. Sair")
        
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            # O sistema SÓ vai criar o personagem se o usuário digitar 1
            try:
                nome_input = input("Digite o nome do personagem: ")
                classe_input = input("Digite a classe: ")
                
                # Validar se nome e classe não estão vazios
                if not nome_input.strip() or not classe_input.strip():
                    console.print("[bold red]Erro: Nome e Classe não podem estar vazios![/bold red]")
                    continue

                if existe_personagem_com_nome(nome_input):
                    console.print("[bold red]Erro: Um personagem com este nome já existe.[/bold red]")
                    continue
                
                nivel_input = int(input("Digite o nível: "))
                nex_input = int(input("Digite o NEX: "))
                atributos_input = input("Digite os atributos (ex: força=2, agilidade=1, vigor=2, presença=3, inteligencia=4): ")
                trilha_input = input("Digite a trilha: ")
                historia_input = input("Digite a história do personagem: ")

                # Cria o molde dinamicamente com o que foi digitado no teclado
                novo_p = Personagem(nome=nome_input, classe=classe_input, nivel=nivel_input, nex=nex_input, atributos=atributos_input, trilha=trilha_input, historia=historia_input)

                # Salva no banco
                salvar_personagem(novo_p)

                console.print(f"[bold green]Sucesso:[/] {nome_input} foi salvo no banco de dados!")

            except NomePersonagemDuplicadoError:
                console.print("[bold red]Erro: Um personagem com este nome já existe.[/bold red]")
            except ValueError:
                console.print("[bold red]Erro: Nível e NEX devem ser números inteiros![/bold red]")
            except Exception as e:
                console.print(f"[bold red]Erro ao criar personagem: {str(e)}[/bold red]")

        elif opcao == "2":
            # Busca todos os personagens no banco
            db = SessionLocal()
            personagens = db.query(Personagem).all()
            db.close()

            if not personagens:
                console.print("[bold yellow]Nenhum personagem encontrado no banco de dados.[/bold yellow]")
            else:
                console.print(f"\n[bold cyan]=== {len(personagens)} PERSONAGEM(NS) ENCONTRADO(S) ===[/bold cyan]\n")
                
                # Exibe cada personagem com formatação
                for p in personagens:
                    console.print(f"[bold green]Nome:[/bold green] {p.nome}")
                    console.print(f"[bold green]Classe:[/bold green] {p.classe}")
                    console.print(f"[bold green]Nível:[/bold green] {p.nivel}")
                    console.print(f"[bold green]NEX:[/bold green] {p.nex}%")
                    console.print(f"[bold green]Trilha:[/bold green] {p.trilha}")
                    console.print(f"[bold green]Atributos:[/bold green] {p.atributos}")
                    console.print(f"[bold green]História:[/bold green] {p.historia}")
                    console.print("[dim]─" * 40 + "[/dim]")

    
        elif opcao == "3":
            print("Saindo do sistema... Até logo!")
            break # Quebra o loop 'while True' e encerra o programa
            
        else:
            console.print("[bold red]Opção inválida![/]")

def escolher_modo():
    """Permite ao usuário escolher entre modo terminal ou GUI"""
    # Cria as tabelas do banco de dados se não existirem
    Base.metadata.create_all(bind=engine)
    
    print("\n=== ESCOLHA O MODO DE EXECUÇÃO ===")
    print("1. Interface Gráfica (Janela)")
    print("2. Terminal (Modo Texto)")
    
    escolha = input("Escolha uma opção: ").strip()
    
    if escolha == "1":    
        iniciar_gui()
    elif escolha == "2":
        iniciar_sistema()
    else:
        print("Opção inválida!")
        escolher_modo()

if __name__ == "__main__":
    # Criar tabelas do banco (se ainda não existirem) e abrir a interface gráfica diretamente
    ensure_database_schema()
    iniciar_gui()