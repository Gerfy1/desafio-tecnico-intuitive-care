import pandas as pd
import numpy as np
from pathlib import Path

#configss
INPUT_FILE = Path("data/processed/consolidado_despesas.csv")
OUTPUT_FILE = Path("data/processed/despesas_agregadas.csv")

def setup_dirs():
    #garante que exista o diretorio de saida/OUTPUT
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def remove_accounting_duplication(df):
    """
    aqui trata a hierarquia do plano de contas para evitar dupla contagem
    a estratégia: Prioriza a conta sintética de nível 1 ('4') que representa o total
    """
    print("[FILTRO] Aplicando filtro de duplicidade contábil...")
    
    # garante ordenação dos dados
    df = df.sort_values(by='CONTA')
    
    # filtra apenas o grupo de Despesas (iniciadas em 4)
    # O teste menciona "Eventos" (41), mas pede valores totais em outras partes
    df_despesas = df[df['CONTA'].astype(str).str.startswith('4')]
    
    # aqui tenta isolar apenas a conta '4' (Total Geral)
    # pelo motivo: Somar a conta '4' com a conta '41' duplicaria os valores.
    totals = df_despesas[df_despesas['CONTA'].astype(str) == '4']
    
    if len(totals) > 0:
        print(f"   [INFO] Utilizando conta sintética '4' (Total) para agregação segura. ({len(totals)} registros)")
        return totals
    else:
        # fallback: se a operadora não reportou a conta '4', mantemos as analíticas para nao perder dados
        print("   [WARN] Conta totalizadora '4' não encontrada. Mantendo dados brutos.")
        return df_despesas

def clean_data(df):
    """validações do Teste 2.1"""
    print("[VALIDAÇÃO] Limpando dados...")
    initial_len = len(df)
    
    #1.remover valores negativos (1.3/2.1)
    df = df[df['VALOR'] >= 0]
    
    # 2 remover CNPJs vazios (decisão de Trade-off: Sem CNPJ nao dá para agrupar por operadora confiavelmente)
    df = df.dropna(subset=['CNPJ'])
    
    # 3. tratamento de CNPJ inválido (a forma opcional: validar dígitos)
    # por enquanto, acredito que se veio do Cadop é válido!
    
    dropped = initial_len - len(df)
    if dropped > 0:
        print(f"   [INFO] {dropped} registros removidos (valores negativos ou sem CNPJ).")
    
    return df

def aggregate_data(df):
    """
    aqui executa a agregação complexa (Teste 2.3):
    - Total por Operadora/UF
    - Média trimestral
    - Desvio Padrao
    """
    print("[AGREGAÇÃO] Calculando estatísticas...")
    
    #step 1: Calcular o TOTAL de despesas por Operadora + UF + Trimestre + Ano
    # isso garante que temos um único valor por trimestre para calcular a média depois
    df_quarterly = df.groupby(['RazaoSocial', 'UF', 'Ano', 'Trimestre'])['VALOR'].sum().reset_index()
    
    # step 2: agora agrupamos por Operadora + UF para tirar as estatísticas entre os trimestres
    # agregações:
    # - sum: soma dos totais de todos os trimestres
    # - mean: Média dos valores trimestrais
    # - std: Desvio padrao entre os trimestres
    df_final = df_quarterly.groupby(['RazaoSocial', 'UF']).agg(
        Valor_Total=('VALOR', 'sum'),
        Media_Trimestral=('VALOR', 'mean'),
        Desvio_Padrao=('VALOR', 'std'),
        Qtd_Trimestres=('Trimestre', 'count') # aqui é utilizado para saber se tem dados suficientes
    ).reset_index()
    
    # aqui preenche NaN no desvio padrão (caso só tenha 1 trimestre, std é NaN) com 0
    df_final['Desvio_Padrao'] = df_final['Desvio_Padrao'].fillna(0)
    
    #ordenação (trade-off: Maior despesa primeiro)
    df_final = df_final.sort_values(by='Valor_Total', ascending=False)
    
    return df_final

def main():
    if not INPUT_FILE.exists():
        print(f"[ERRO] Arquivo de entrada nao encontrado: {INPUT_FILE}")
        return

    print("=== Iniciando Agregador de despesas ===")
    
    # carrega definindo tipos para economizar memoria, focando em desempenho
    df = pd.read_csv(INPUT_FILE, dtype={'CNPJ': str, 'CONTA': str, 'Trimestre': str})
    
    # 1.limpeza basica
    df = clean_data(df)
    
    # 2. filtro de Duplicidade contabil
    df = remove_accounting_duplication(df)
    
    # 3 agregação estatística
    df_agregado = aggregate_data(df)
    
    #salvamento
    df_agregado.to_csv(OUTPUT_FILE, index=False, float_format='%.2f')
    print(f"\n[SUCESSO] Arquivo gerado: {OUTPUT_FILE}")
    print("Top 5 Maiores Despesas por Operadora/UF:")
    print(df_agregado.head())

if __name__ == "__main__":
    main()