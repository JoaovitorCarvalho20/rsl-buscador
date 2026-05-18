"""
busca_capes_selenium.py
Busca no Periódicos CAPES via Selenium furtivo.
- undetected-chromedriver para evitar detecção
- Login manual pelo usuário (sem armazenar credenciais)
- Detecção automática de CAPTCHA com pausa para resolução manual
- Exportação em RIS por descritor
- Cliques via JavaScript para evitar ElementClickInterceptedException
- Move arquivos RIS de Downloads para capes_exports automaticamente
"""

import time
import os
import re
import glob
import random
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

ANO_INICIO = 2020
ANO_FIM    = 2025
PASTA_RIS  = "capes_exports"

DESCRITORES = [
    "racismo algoritmo",
    "racismo algorítmico",
    "viés algorítmico",
    "discriminação racial algoritmo",
    "inteligência artificial população negra",
    "algoritmo saúde raça",
    "policiamento preditivo racismo",
    "algoritmo mercado trabalho discriminação",
    "algorithmic discrimination",
    "algorithmic bias race",
    "artificial intelligence racial discrimination",
    "predictive policing racial bias",
    "machine learning racism",
    "algorithmic racism",
]

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7422.114 Safari/537.36",
]


_CHROMEDRIVER_SRC = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"
_CHROMEDRIVER_LOCAL = os.path.expanduser("~/.cache/rsl_buscador/chromedriver")


def _chromedriver_gravavel() -> str:
    """Copia o chromedriver do Snap (somente-leitura) para um caminho gravável.
    O undetected_chromedriver precisa modificar o binário para bypassar detecção."""
    os.makedirs(os.path.dirname(_CHROMEDRIVER_LOCAL), exist_ok=True)
    shutil.copy2(_CHROMEDRIVER_SRC, _CHROMEDRIVER_LOCAL)
    os.chmod(_CHROMEDRIVER_LOCAL, 0o755)
    return _CHROMEDRIVER_LOCAL


def pausa_humana(minimo=2.0, maximo=5.0):
    time.sleep(random.uniform(minimo, maximo))


def js_click(driver, elemento):
    """Clica via JavaScript — evita ElementClickInterceptedException."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
    pausa_humana(0.5, 1.0)
    driver.execute_script("arguments[0].click();", elemento)


def criar_driver():
    pasta_abs = os.path.abspath(PASTA_RIS)
    os.makedirs(pasta_abs, exist_ok=True)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": pasta_abs,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
        "browser.download.folderList": 2,
        "browser.download.dir": pasta_abs,
    }
    options.add_experimental_option("prefs", prefs)
    options.binary_location = "/snap/chromium/current/usr/lib/chromium-browser/chrome"

    driver = uc.Chrome(
        options=options,
        driver_executable_path=_chromedriver_gravavel(),
        version_main=147,
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def verificar_captcha(driver) -> bool:
    fonte = driver.page_source.lower()
    return any(ind in fonte for ind in ["captcha", "recaptcha", "g-recaptcha", "hcaptcha", "robot"])


def resolver_captcha_manual(driver):
    print("\n" + "!"*60)
    print("  ⚠️  CAPTCHA DETECTADO!")
    print("  Resolva o CAPTCHA no navegador aberto.")
    print("  Quando terminar, volte aqui e pressione ENTER.")
    print("!"*60)
    input("\n  Pressione ENTER após resolver o CAPTCHA...")
    pausa_humana(2, 4)
    print("  ✅ Continuando após resolução do CAPTCHA.")


def aguardar_login(driver):
    print("\n" + "="*60)
    print("  LOGIN MANUAL — PERIÓDICOS CAPES")
    print("="*60)
    print("  1. O navegador vai abrir a página de login")
    print("  2. Clique em gov.br e entre com seu CPF e senha")
    print("  3. Resolva qualquer verificação que aparecer")
    print("  4. Quando estiver na página inicial do CAPES logado,")
    print("     volte aqui e pressione ENTER")
    print("="*60 + "\n")

    driver.get(
        "https://sso.capes.gov.br/sso/oauth"
        "?client_id=periodicos"
        "&response_type=code"
        "&state=capes_oauth"
        "&redirect_uri=https://www.periodicos.capes.gov.br"
    )
    pausa_humana(3, 5)

    if verificar_captcha(driver):
        resolver_captcha_manual(driver)

    input("  Pressione ENTER após completar o login no navegador...")

    if "periodicos.capes.gov.br" in driver.current_url:
        print("  ✅ Login confirmado!")
    else:
        print("  ⚠️  URL inesperada — continuando mesmo assim...")

    pausa_humana(2, 3)


def aceitar_cookies(driver):
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Aceitar']"))
        )
        btn.click()
        print("  Cookies aceitos.")
        pausa_humana(1, 2)
    except TimeoutException:
        pass


def buscar_descritor(driver, descritor: str, indice: int) -> int:
    print(f"\n  [{indice}] Buscando: '{descritor}'")

    query = re.sub(r'\s+', '+', descritor.strip())
    url = (
        f"https://www.periodicos.capes.gov.br/index.php/acervo/buscador.html"
        f"?q=all%3Acontains%28{query}%29&mode=advanced"
    )

    driver.get(url)
    pausa_humana(3, 6)

    if verificar_captcha(driver):
        resolver_captcha_manual(driver)

    # ── Lê total de resultados ──
    total = 0
    for seletor in ["strong#total-results", ".total-results", "span.total", "div.results-count"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, seletor)
            m = re.search(r'(\d[\d.]*)', el.text)
            if m:
                total = int(m.group(1).replace('.', ''))
                break
        except NoSuchElementException:
            continue

    if total == 0:
        m = re.search(r'(\d+)\s+resultados?', driver.page_source, re.IGNORECASE)
        if m:
            total = int(m.group(1))

    print(f"    Total: {total} resultados")

    if total == 0:
        print(f"    Nenhum resultado — pulando.")
        return 0

    # ── Rola para o topo antes de interagir ──
    driver.execute_script("window.scrollTo(0, 0);")
    pausa_humana(1, 2)

    # ── Clica em "Selecionar tudo" via JavaScript ──
    selecionou = False
    for xpath in [
        "//label[contains(text(),'Selecionar tudo')]",
        "//span[contains(text(),'Selecionar tudo')]",
        "//input[@type='checkbox'][contains(@class,'select-all')]",
        "//input[@type='checkbox'][@id='selectAll']",
    ]:
        try:
            el = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            js_click(driver, el)
            print(f"    ✅ 'Selecionar tudo' clicado")
            selecionou = True
            pausa_humana(1, 2)
            break
        except TimeoutException:
            continue

    if not selecionou:
        print(f"    ⚠️  'Selecionar tudo' não encontrado")

    # ── Clica em "Exportar" pelo dropdown-toggle ──
    try:
        el = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a.dropdown-toggle[data-bs-toggle='dropdown']")
            )
        )
        js_click(driver, el)
        print(f"    ✅ 'Exportar' clicado")
        pausa_humana(1.5, 2.5)
    except TimeoutException:
        print(f"    ⚠️  Botão 'Exportar' não encontrado")
        return total

    # ── Clica em "RIS" pelo id direto ──
    try:
        el = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.ID, "exportRIS"))
        )
        js_click(driver, el)
        print(f"    ✅ RIS selecionado — download iniciado")
        pausa_humana(5, 8)
    except TimeoutException:
        print(f"    ⚠️  Botão exportRIS não encontrado")

    return total


def mover_ris_de_downloads():
    """Move arquivos RIS baixados em Downloads para capes_exports."""
    pasta = os.path.abspath(PASTA_RIS)
    downloads = os.path.expanduser("~/Downloads")
    movidos = 0

    for arquivo in sorted(
        glob.glob(os.path.join(downloads, "*.ris")),
        key=os.path.getmtime
    ):
        nome = os.path.basename(arquivo)
        destino = os.path.join(pasta, nome)
        if os.path.exists(destino):
            base, ext = os.path.splitext(nome)
            destino = os.path.join(pasta, f"{base}_{int(time.time())}{ext}")
        os.rename(arquivo, destino)
        print(f"  Movido: Downloads/{nome} → capes_exports/{os.path.basename(destino)}")
        movidos += 1

    return movidos


def renomear_ris_baixados(descritores_processados: list[str]):
    """Renomeia arquivos RIS para associar ao descritor correto."""
    pasta = os.path.abspath(PASTA_RIS)

    # Primeiro move arquivos de Downloads
    mover_ris_de_downloads()

    # Lista todos os RIS em ordem de modificação
    arquivos = sorted(
        glob.glob(os.path.join(pasta, "*.ris")),
        key=os.path.getmtime
    )

    for i, arquivo in enumerate(arquivos):
        nome_base = os.path.basename(arquivo)
        if re.match(r'^(Periodicos-CAPES-RIS|export|download)', nome_base, re.IGNORECASE):
            if i < len(descritores_processados):
                desc = descritores_processados[i]
                novo_nome = re.sub(r'\W+', '_', desc)[:40] + f"_{i+1}.ris"
                novo_caminho = os.path.join(pasta, novo_nome)
                if not os.path.exists(novo_caminho):
                    os.rename(arquivo, novo_caminho)
                    print(f"  Renomeado: {nome_base} → {novo_nome}")


def parsear_ris(caminho_ris: str, descritor: str) -> list[dict]:
    if not os.path.exists(caminho_ris):
        return []

    resultados = []
    registro = {}
    mapa = {
        "TI": "titulo",   "T1": "titulo",
        "AU": "autores",  "A1": "autores",
        "PY": "ano",      "Y1": "ano",
        "JO": "revista_repositorio",
        "JF": "revista_repositorio",
        "T2": "revista_repositorio",
        "AB": "resumo",   "N2": "resumo",
        "DO": "doi",
        "UR": "link",
    }

    with open(caminho_ris, encoding="utf-8", errors="ignore") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue

            if linha == "ER  -":
                if registro.get("titulo"):
                    ano = str(registro.get("ano", ""))[:4]
                    doi = registro.get("doi", "")
                    link = f"https://doi.org/{doi}" if doi else registro.get("link", "")
                    try:
                        if ano and not (ANO_INICIO <= int(ano) <= ANO_FIM):
                            registro = {}
                            continue
                    except ValueError:
                        pass
                    resultados.append({
                        "base": "Periódicos CAPES",
                        "descritor": descritor,
                        "titulo": registro.get("titulo", ""),
                        "autores": registro.get("autores", ""),
                        "ano": ano,
                        "revista_repositorio": registro.get("revista_repositorio", ""),
                        "resumo": registro.get("resumo", ""),
                        "doi": doi,
                        "link": link,
                        "tipo": "Artigo",
                        "status_inclusao": "",
                        "motivo_exclusao": "",
                    })
                registro = {}
                continue

            if len(linha) >= 6 and linha[2:4] == "  " and linha[4] == "-":
                tag = linha[:2].strip()
                valor = linha[6:].strip()
                if tag in mapa:
                    campo = mapa[tag]
                    if campo == "autores" and "autores" in registro:
                        registro["autores"] += f"; {valor}"
                    else:
                        registro[campo] = valor

    return resultados


def buscar_capes_todos(descritores: list[str]) -> tuple[list[dict], dict]:
    os.makedirs(PASTA_RIS, exist_ok=True)
    todos = []
    contagens = {}
    descritores_processados = []

    print("\n  Iniciando driver furtivo...")
    driver = criar_driver()

    try:
        aguardar_login(driver)
        aceitar_cookies(driver)

        for i, desc in enumerate(descritores, 1):
            total = buscar_descritor(driver, desc, i)
            contagens[desc] = total
            descritores_processados.append(desc)
            pausa_humana(3, 6)

        print("\n  Aguardando downloads finalizarem...")
        time.sleep(5)
        renomear_ris_baixados(descritores_processados)

    finally:
        driver.quit()
        print("\n  Navegador fechado.")

    print("\n  Processando arquivos RIS...")
    for arquivo in glob.glob(os.path.join(PASTA_RIS, "*.ris")):
        nome = os.path.basename(arquivo).replace(".ris", "").replace("_", " ")
        desc_match = next(
            (d for d in descritores if d[:15].lower() in nome.lower()),
            nome
        )
        registros = parsear_ris(arquivo, desc_match)
        todos.extend(registros)
        print(f"    {os.path.basename(arquivo)}: {len(registros)} registros")

    return todos, contagens


if __name__ == "__main__":
    print("=== Buscador CAPES — Selenium Furtivo ===")
    res, cnts = buscar_capes_todos(DESCRITORES)