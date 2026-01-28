import pandas as pd
import zipfile
import os
import requests
import io
from pathlib import Path

#configs
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "consolidado_despesas.csv"
CADASTRO_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

COLUMN_MAP = {
    "VALOR": ["VL_SALDO_FINAL", "VALOR", "Valor", "DESPESA"],
    "CONTA": ["CD_CONTA_CONTABIL", "CD_CONTA", "Conta"],
    "REG_ANS": ["REG_ANS", "RegistroANS"]
}
ACCOUNT_FILTER_START = '4' 

def setup_dirs():
    if not PROCESSED_DIR.exists():
        os.makedirs(PROCESSED_DIR)

def get_cadop_map():
    print("[CADASTRO] Baixando dados cadastrais para lookup...")
    try:
        r = requests.get(CADASTRO_URL, timeout=30)
        r.raise_for_status()
        
        try:
            df_cadop = pd.read_csv(io.BytesIO(r.content), sep=';', encoding='utf-8', dtype=str)
            print("[CADASTRO] Detectado UTF-8.")
        except:
            print("[CADASTRO] Fallback para Latin-1.")
            df_cadop = pd.read_csv(io.BytesIO(r.content), sep=';', encoding='latin-1', dtype=str)
            
        df_cadop.columns = [c.upper().replace('_', '') for c in df_cadop.columns]
        
        # udentificacao dinâmica das colunas
        reg_col = next((c for c in df_cadop.columns if 'REGISTRO' in c), None)
        cnpj_col = next((c for c in df_cadop.columns if 'CNPJ' in c), None)
        razao_col = next((c for c in df_cadop.columns if 'RAZAO' in c), None)
        uf_col = next((c for c in df_cadop.columns if 'UF' in c), None)
        mod_col = next((c for c in df_cadop.columns if 'MODALIDADE' in c), None)

        if not (reg_col and cnpj_col and razao_col):
            print(f"[ERRO] Colunas chave não encontradas. Disp: {df_cadop.columns}")
            return {}

        lookup = {}
        for _, row in df_cadop.iterrows():
            reg = str(row[reg_col]).strip()
            lookup[reg] = {
                'CNPJ': row[cnpj_col],
                'RazaoSocial': row[razao_col],
                'UF': row[uf_col] if uf_col else 'ND',
                'Modalidade': row[mod_col] if mod_col else 'ND'
            }
        
        print(f"[CADASTRO] Mapa criado: {len(lookup)} operadoras com UF/Modalidade.")
        return lookup

    except Exception as e:
        print(f"[ERRO] Falha no cadastro: {e}")
        return {}

def load_csv_robust(file_stream):
    sample = file_stream.read(4096)
    file_stream.seek(0)
    encodings = ['latin-1', 'utf-8', 'cp1252']
    separators = [';', ',', '\t']
    
    for enc in encodings:
        try:
            text_sample = sample.decode(enc)
            first_line = text_sample.split('\n')[0]
            sep = max(separators, key=lambda s: first_line.count(s))
            df = pd.read_csv(file_stream, sep=sep, encoding=enc, dtype=str)
            return df
        except Exception:
            file_stream.seek(0)
            continue
    return None

def normalize_columns(df):
    found_map = {}
    for target, candidates in COLUMN_MAP.items():
        for cand in candidates:
            if cand in df.columns:
                found_map[cand] = target
                break
    return df.rename(columns=found_map)

def process_quarter_zip(zip_path, cadop_map):
    print(f"\n[PROCESSANDO] {zip_path.name}...")
    try:
        parts = zip_path.stem.split('_')
        ano = parts[0]
        trimestre = parts[1]
    except:
        ano, trimestre = "0000", "0T"

    processed_data = []

    with zipfile.ZipFile(zip_path, 'r') as z:
        for filename in z.namelist():
            if (filename.lower().endswith('.csv') or filename.endswith('.txt')) and 'leia' not in filename.lower():
                with z.open(filename) as f:
                    df = load_csv_robust(f)
                    if df is None: continue
                    
                    df = normalize_columns(df)
                    if 'VALOR' not in df.columns: continue
                    if 'CONTA' in df.columns:
                        df = df[df["CONTA"].str.startswith(ACCOUNT_FILTER_START, na=False)]
                    if df.empty: continue

                    if 'REG_ANS' in df.columns:
                        # os 4 campos
                        def get_meta(reg):
                            d = cadop_map.get(str(reg), {})
                            return pd.Series([d.get('CNPJ'), d.get('RazaoSocial'), d.get('UF'), d.get('Modalidade')])
                        
                        df[['CNPJ', 'RazaoSocial', 'UF', 'Modalidade']] = df['REG_ANS'].apply(get_meta)
                    
                    df['Trimestre'] = trimestre
                    df['Ano'] = ano
                    
                    cols = ['REG_ANS', 'CNPJ', 'RazaoSocial', 'UF', 'Modalidade', 'Trimestre', 'Ano', 'VALOR', 'CONTA']
                    for c in cols:
                        if c not in df.columns: df[c] = None
                        
                    processed_data.append(df[cols])

    if not processed_data: return None
    return pd.concat(processed_data, ignore_index=True)

def main():
    setup_dirs()
    cadop_map = get_cadop_map()
    all_zips = list(RAW_DIR.glob('*.zip'))
    dfs = []
    
    for zip_file in all_zips:
        df_quarter = process_quarter_zip(zip_file, cadop_map)
        if df_quarter is not None:
            dfs.append(df_quarter)
    
    if dfs:
        print("\n[CONSOLIDANDO] Unindo trimestres...")
        final_df = pd.concat(dfs, ignore_index=True)
        
        final_df['VALOR'] = final_df['VALOR'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        final_df['VALOR'] = pd.to_numeric(final_df['VALOR'], errors='coerce')
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"Arquivo salvo: {OUTPUT_FILE}")
        # aqui mostra UF e Modalidade na amostra para confirmar se tá tudo ok
        print("Amostra:\n", final_df[['RazaoSocial', 'UF', 'VALOR']].head())
    else:
        print("Falha geral.")

if __name__ == "__main__":
    main()