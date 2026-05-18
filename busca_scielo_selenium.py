"""
busca_scielo_selenium.py
Busca na SciELO usando Selenium + Chromium (snap)
Correções: query sem AND, paginação robusta, WebDriverWait
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

ANO_INICIO = 2020
ANO_FIM = 2025

CHROME_BIN    = "/snap/chromium/current/usr/lib/chromium-browser/chrome"
CHROME_DRIVER = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"


def criar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )
    options.binary_location = CHROME_BIN
    service = Service(executable_path=CHROME_DRIVER)
    return webdriver.Chrome(service=service, options=options)


def montar_query(descritor: str) -> str:
    """
    SciELO não interpreta AND como operador booleano confiável.
    Convertemos para busca por termos simples separados por espaço.
    Ex: "viés algorítmico AND racismo" → "viés algorítmico racismo"
    """
    query = re.sub(r'\b(AND|OR|NOT)\b', ' ', descritor, flags=re.IGNORECASE)
    query = re.sub(r'\s+', ' ', query).strip()
    return query


def extrair_artigos_pagina(driver, descritor: str) -> list[dict]:
    """Extrai todos os artigos da página atual."""
    resultados = []

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.results div.item"))
        )
    except TimeoutException:
        print("    Timeout — sem resultados nesta página.")
        return resultados

    itens = driver.find_elements(By.CSS_SELECTOR, "div.results div.item")
    print(f"    Elementos encontrados na página: {len(itens)}")

    for item in itens:
        try:
            # Título
            try:
                titulo_el = item.find_element(By.CSS_SELECTOR, "strong.title")
                titulo = titulo_el.text.strip()
            except NoSuchElementException:
                continue
            if not titulo:
                continue

            # Link
            link = ""
            try:
                link_el = item.find_element(By.CSS_SELECTOR, "a[href*='scielo']")
                link = link_el.get_attribute("href") or ""
            except NoSuchElementException:
                pass

            # Ano — extrai do id do item e do link
            item_id = item.get_attribute("id") or ""
            ano = ""
            for padrao in [r'S\d{4}-\d{4}(\d{4})', r'-(\d{4})\d{5}-']:
                m = re.search(padrao, item_id)
                if m:
                    candidato = m.group(1)
                    if 2000 <= int(candidato) <= 2030:
                        ano = candidato
                        break
            if not ano and link:
                m = re.search(r'pid=S\d{4}-\d{4}(\d{4})', link)
                if m:
                    candidato = m.group(1)
                    if 2000 <= int(candidato) <= 2030:
                        ano = candidato

            # Filtra pelo recorte temporal
            if ano:
                try:
                    if not (ANO_INICIO <= int(ano) <= ANO_FIM):
                        continue
                except ValueError:
                    pass

            # Resumo — pega o primeiro não vazio
            resumo = ""
            for ab in item.find_elements(By.CSS_SELECTOR, "div.abstract"):
                texto = ab.text.strip()
                if texto:
                    resumo = texto
                    break

            # DOI
            doi = ""
            try:
                doi_href = item.find_element(
                    By.CSS_SELECTOR, "span.DOIResults a"
                ).get_attribute("href") or ""
                doi = re.sub(r'https?://doi\.org/', '', doi_href)
            except NoSuchElementException:
                pass

            # Link final — prefere DOI
            link_final = f"https://doi.org/{doi}" if doi else link

            # Revista
            revista = ""
            m2 = re.search(r'//(\w+)\.scielo\.', link)
            if m2:
                revista = m2.group(1).upper()

            resultados.append({
                "base": "SciELO",
                "descritor": descritor,
                "titulo": titulo,
                "autores": "",
                "ano": ano,
                "revista_repositorio": revista,
                "resumo": resumo,
                "doi": doi,
                "link": link_final,
                "tipo": "Artigo",
                "status_inclusao": "",
                "motivo_exclusao": "",
            })

        except Exception:
            continue

    return resultados


def buscar_scielo_selenium(descritor: str, driver=None) -> list[dict]:
    fechar = driver is None
    if fechar:
        driver = criar_driver()

    resultados = []
    titulos_vistos = set()

    try:
        query = montar_query(descritor)
        query_url = re.sub(r'\s+', '+', query)

        url = (
            f"https://search.scielo.org/?q={query_url}"
            f"&lang=pt&count=50&from=1&output=site&format=summary"
            f"&filter%5Bda%5D%5Bgte%5D={ANO_INICIO}"
            f"&filter%5Bda%5D%5Blte%5D={ANO_FIM}"
        )

        print(f"    Query enviada: '{query}'")
        driver.get(url)

        # Aguarda carregamento com WebDriverWait em vez de sleep fixo
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.results div.item, div#NoResults")
                )
            )
        except TimeoutException:
            print("    Página não carregou.")
            return resultados

        # Verifica total de resultados
        try:
            total_el = driver.find_element(By.CSS_SELECTOR, "strong#TotalHits")
            print(f"    Total reportado pela SciELO: {total_el.text} resultados")
        except NoSuchElementException:
            pass

        pagina = 1
        url_anterior = driver.current_url

        while pagina <= 10:
            novos = extrair_artigos_pagina(driver, descritor)

            # Deduplica entre páginas
            for r in novos:
                chave = r["titulo"][:60].lower()
                if chave not in titulos_vistos:
                    titulos_vistos.add(chave)
                    resultados.append(r)

            print(f"    Página {pagina}: {len(novos)} artigo(s) | Acumulado: {len(resultados)}")

            # Tenta avançar para próxima página
            try:
                btn_next = driver.find_element(By.CSS_SELECTOR, "a.pageNext")

                # Verifica se o botão leva a uma URL diferente
                href_next = btn_next.get_attribute("href") or ""
                if not href_next or href_next == url_anterior:
                    print("    Última página alcançada.")
                    break

                # Clica e aguarda nova página carregar
                btn_next.click()
                WebDriverWait(driver, 15).until(
                    EC.staleness_of(
                        driver.find_elements(By.CSS_SELECTOR, "div.results div.item")[0]
                        if driver.find_elements(By.CSS_SELECTOR, "div.results div.item")
                        else btn_next
                    )
                )
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.results div.item"))
                )

                url_atual = driver.current_url
                if url_atual == url_anterior:
                    print("    URL não mudou — última página.")
                    break

                url_anterior = url_atual
                pagina += 1

            except NoSuchElementException:
                print("    Botão 'próxima página' não encontrado — fim.")
                break
            except Exception as e:
                print(f"    Erro na paginação: {e}")
                break

    except Exception as e:
        print(f"  [SciELO] Erro: {e}")
    finally:
        if fechar:
            driver.quit()

    return resultados


def buscar_scielo_todos(descritores: list[str]) -> tuple[list[dict], dict]:
    """
    Busca todos os descritores reutilizando um único driver.
    Retorna (lista_de_resultados, dict_contagens_por_descritor).
    """
    todos = []
    contagens = {}

    print("  Iniciando Chromium...")
    driver = criar_driver()

    try:
        for desc in descritores:
            print(f"  → {desc[:55]}...")
            res = buscar_scielo_selenium(desc, driver=driver)
            contagens[desc] = len(res)
            todos.extend(res)
            print(f"     Total do descritor: {len(res)} resultado(s)")
            time.sleep(2)
    finally:
        driver.quit()
        print("  Chromium encerrado.")

    return todos, contagens

if __name__ == "__main__":
    print("=== Teste Selenium SciELO — PT + EN + ES ===")
    teste = [
        # Português
        "racismo algoritmo",
        "discriminação racial inteligência artificial",
        "viés algorítmico",
        # Inglês
        "algorithmic bias race",
        "algorithmic discrimination",
        "predictive policing racism",
        "artificial intelligence racial discrimination",
        # Espanhol
        "sesgo algorítmico raza",
        "discriminación racial algoritmo",
        "racismo algorítmico",
    ]
    res, cnts = buscar_scielo_todos(teste)
    print(f"\n{'='*40}")
    print(f"Total encontrado: {len(res)}")
    for desc, cnt in cnts.items():
        print(f"  {desc[:50]}: {cnt} resultado(s)")