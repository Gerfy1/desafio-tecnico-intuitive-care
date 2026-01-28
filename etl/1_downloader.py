import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

# config
BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
OUTPUT_DIR = Path("data/raw")
TIMEOUT = 30

def setup_dirs():
    if not OUTPUT_DIR.exists():
        os.makedirs(OUTPUT_DIR)

def get_soup(url):
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao acessar {url}: {e}")
        return None

def find_latest_quarters(base_url, limit=3):
    soup = get_soup(base_url)
    if not soup:
        return []

    # forma de encontrar anos
    years = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(r'^\d{4}/?$', href): # aceita com ou sem barra final
            years.append(href.strip('/'))
    
    years.sort(key=int, reverse=True)
    quarters_found = [] 

    print(f"[INFO] Anos encontrados: {years[:5]}...")

    for year in years:
        if len(quarters_found) >= limit:
            break
            
        year_url = urljoin(base_url, f"{year}/")
        year_soup = get_soup(year_url)
        
        if not year_soup:
            continue

        # jeito hibrido, aqui procura tanto pastas (1T/) quanto os arquivos zip diretos (1T2023.zip)
        # vamos usar um dicionario pra evitar duplicidade
        found_in_year = {} 

        for link in year_soup.find_all('a'):
            href = link.get('href')
            if not href: continue

            # padrao A: pasta de Trimestre (ex: "1T/", "2T")
            match_folder = re.match(r'^([1-4])T/?$', href, re.IGNORECASE)
            
            # padrao B: Arquivo zip direto (ex: "1T2024.zip", "2T24.zip")
            match_file = re.match(r'^([1-4])T\d*\.zip$', href, re.IGNORECASE)

            if match_folder:
                q = f"{match_folder.group(1)}T"
                found_in_year[q] = {
                    "type": "folder",
                    "url": urljoin(year_url, href)
                }
            elif match_file:
                q = f"{match_file.group(1)}T"
                # se encontramos o arquivo direto, a URL é o proprio arquivo
                found_in_year[q] = {
                    "type": "file",
                    "url": urljoin(year_url, href),
                    "filename": href
                }

        # forma de ordenar trimestres encontrados neste ano (4T -> 1T)
        sorted_qs = sorted(found_in_year.keys(), reverse=True)
        
        for q in sorted_qs:
            if len(quarters_found) >= limit:
                break
            
            data = found_in_year[q]
            quarters_found.append({
                "ano": year,
                "trimestre": q,
                "url": data['url'],
                "type": data['type'], # tipos de dados: 'folder' ou 'file'
                "filename": data.get('filename')
            })

    return quarters_found

def download_item(item):
    
    # case 1: é um arquivo ZIP direto (praticamente se refere a nova estrutura da ANS)
    if item['type'] == 'file':
        file_url = item['url']
        filename = item['filename'] or f"{item['ano']}_{item['trimestre']}.zip"
        # organiza o nome/normaliza
        save_name = f"{item['ano']}_{item['trimestre']}.zip"
        save_path = OUTPUT_DIR / save_name
        
        if save_path.exists():
            print(f"[SKIP] Já existe: {save_name}")
            return

        print(f"[BAIXANDO] {save_name} (Direto)...")
        try:
            r = requests.get(file_url, stream=True, timeout=TIMEOUT)
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[SUCESSO] Download concluído")
        except Exception as e:
            print(f"[ERRO] {e}")

    # case 2: é uma pasta (praticamente se refere a estrutura antiga da ANS)
    elif item['type'] == 'folder':
        soup = get_soup(item['url'])
        if not soup: return
        
        # aqui baixa o primeiro zip que encontrar dentro da pasta
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.lower().endswith('.zip'):
                file_url = urljoin(item['url'], href)
                save_name = f"{item['ano']}_{item['trimestre']}.zip"
                save_path = OUTPUT_DIR / save_name
                
                if save_path.exists():
                    print(f"[SKIP] Já existe: {save_name}")
                    continue

                print(f"[BAIXANDO] {save_name} (Da pasta)...")
                r = requests.get(file_url, stream=True)
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[SUCESSO]")
                return # baixa apenas um por trimestre

def main():
    print("=== Crawler ANS v2.0 (Resiliente) ===")
    setup_dirs()
    
    targets = find_latest_quarters(BASE_URL, limit=3)
    
    if not targets:
        print("[ERRO] Nada encontrado. A estrutura do site mudou drasticamente(?)")
        return

    print(f"[INFO] Alvos: {[f'{t['ano']}/{t['trimestre']} ({t['type']})' for t in targets]}")
    
    for target in targets:
        download_item(target)
        
    print(f"\nVerifique os arquivos em: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    main()