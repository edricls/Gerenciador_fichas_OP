from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Cria a conexão com o banco de dados SQLite local
DATABASE_URL = "sqlite:///rpg.db"

# O engine é o motor que gerencia a comunicação com o arquivo .db
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# O sessionmaker é o que permite abrir "sessões" para salvar ou buscar dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# A classe Base será herdada por todos os modelos para o SQLAlchemy reconhecê-los
Base = declarative_base()


def ensure_database_schema():
    """Cria as tabelas e adiciona colunas novas em bancos já existentes."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "personagens" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("personagens")}
    if "pericias" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE personagens ADD COLUMN pericias VARCHAR"))

    if "origem" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE personagens ADD COLUMN origem VARCHAR"))

    if "habilidades" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE personagens ADD COLUMN habilidades VARCHAR"))

    if "rituais" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE personagens ADD COLUMN rituais VARCHAR"))

    if "deslocamento" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE personagens ADD COLUMN deslocamento VARCHAR DEFAULT '9m/6q'")
            )
    else:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE personagens SET deslocamento = '9m/6q' WHERE deslocamento IS NULL OR deslocamento = ''")
            )

    if "valores_editados" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE personagens ADD COLUMN valores_editados VARCHAR DEFAULT '{}'")
            )

    if "patente" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE personagens ADD COLUMN patente VARCHAR DEFAULT 'Recruta'")
            )

    if "inventario" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE personagens ADD COLUMN inventario VARCHAR DEFAULT '[]'")
            )

    if "imagem" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE personagens ADD COLUMN imagem VARCHAR DEFAULT ''")
            )

    if "imagem_ajuste" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE personagens ADD COLUMN imagem_ajuste VARCHAR DEFAULT ''")
            )


def get_db():
    """Função utilitária para abrir e fechar a sessão do banco com segurança"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
