import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import time

# config do docker (precisa tá certinho)
DB_USER = "user"
DB_PASS = "password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ans_database"

#conexão com o SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#arquivos
CONSOLIDADO_FILE = Path("data/processed/consolidado_despesas.csv")
AGREGADO_FILE = Path("data/processed/despesas_agregadas.csv")

def get_engine():
    return create_engine(DATABASE_URL)

def load_dimensao_operadoras(df, engine):
    """
    popula a tabela dim_operadoras extraindo dados unicos do CSV de despesas
    trade-off: usamos 'ON CONFLICT DO NOTHING' para evitar erros de duplicaçao
    """
    print("[LOAD] Carregando Dimensão Operadoras...")
    
    #aqui seleciona colunas unicas de operadoras
    #mapeia colunas do CSV -> Colunas do Banco
    df_ops = df[['REG_ANS', 'CNPJ', 'RazaoSocial', 'UF', 'Modalidade']].drop_duplicates(subset=['REG_ANS'])
    
    #renomeia para bater com o banco
    df_ops = df_ops.rename(columns={
        'REG_ANS': 'registro_ans',
        'CNPJ': 'cnpj',
        'RazaoSocial': 'razao_social',
        'UF': 'uf',
        'Modalidade': 'modalidade'
    })
    
    #inserção
    try:
        df_ops.to_sql('dim_operadoras', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print(f"   [SUCESSO] {len(df_ops)} operadoras inseridas.")
    except Exception as e:
        #se der erro (por ex: chave duplicada), assumimos que já foi carregado
        print(f"   [INFO] Tabela já populada ou erro de integridade ignorável: {e}")

def load_fato_despesas(df, engine):
    """
    carrega a tabela fato_despesas.
    """
    print("[LOAD] Carregando Fato Despesas (isso pode demorar um pouquinho)...")
    
    #prepara o DataFrame
    df_fato = df.copy()
    
    # ajusta nomes
    df_fato = df_fato.rename(columns={
        'REG_ANS': 'registro_ans',
        'Ano': 'ano',
        'Trimestre': 'trimestre',
        'CONTA': 'conta',
        'VALOR': 'valor'
    })
    
    #seleciona apenas colunas que existem na tabela fato
    cols_banco = ['registro_ans', 'ano', 'trimestre', 'conta', 'valor']
    df_fato = df_fato[cols_banco]
    
    #o bulk Insert
    #chunksize=10000 é um bom meio termo entre memória e performance
    start = time.time()
    df_fato.to_sql('fato_despesas', engine, if_exists='append', index=False, method='multi', chunksize=5000)
    end = time.time()
    
    print(f"   [SUCESSO] Despesas carregadas em {end - start:.2f} segundos.")

def load_analise_agregada(engine):
    """
    carrega a tabela analise_agregada.
    """
    if not AGREGADO_FILE.exists():
        print("[SKIP] Arquivo agregado não encontrado.")
        return

    print("[LOAD] Carregando Análise Agregada...")
    df = pd.read_csv(AGREGADO_FILE)
    
    #renomeia
    df = df.rename(columns={
        'RazaoSocial': 'razao_social',
        'UF': 'uf',
        'Valor_Total': 'valor_total',
        'Media_Trimestral': 'media_trimestral',
        'Desvio_Padrao': 'desvio_padrao',
        'Qtd_Trimestres': 'qtd_trimestres'
    })
    
    df.to_sql('analise_agregada', engine, if_exists='replace', index=False) # Replace recria a tabela analítica
    print("   [SUCESSO] Tabela de análise atualizada.")

def main():
    print("=== Iniciando Carga no Banco de Dados ===")
    
    if not CONSOLIDADO_FILE.exists():
        print("[ERRO] CSV consolidado não encontrado.")
        return

    engine = get_engine()
    
    try:
        #testa conexao
        with engine.connect() as conn:
            print("[CONEXÃO] Banco de dados conectado com sucesso!")
            
            # limpa tabelas para evitar duplicaçao em testes repetidos (Opcional mas é muito bom em ambiente dev)
            # conn.execute(text("TRUNCATE TABLE fato_despesas CASCADE;"))
            # conn.execute(text("TRUNCATE TABLE dim_operadoras CASCADE;"))
            # conn.commit()
            
    except Exception as e:
        print(f"[ERRO] Falha ao conectar no Docker: {e}")
        print("Dica: Verifique se rodou 'docker-compose up -d'")
        return

    # le o CSV
    print("[LENDO] Carregando CSV em memória...")
    df_consolidado = pd.read_csv(CONSOLIDADO_FILE, dtype={'REG_ANS': str, 'CNPJ': str, 'CONTA': str})
    
    #1.carrega dimensão (Operadoras)
    load_dimensao_operadoras(df_consolidado, engine)
    
    # 2. carrega fato (Despesas)
    load_fato_despesas(df_consolidado, engine)
    
    # 3 carrega tabela agregada (Data Mart)
    load_analise_agregada(engine)
    
    print("\n=== Carga Finalizada ===")

if __name__ == "__main__":
    main()