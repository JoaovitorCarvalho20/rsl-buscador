# RSL Buscador — Documentação Técnica

## Visão Geral

O RSL Buscador é uma ferramenta desenvolvida para automatizar a coleta, filtragem e exportação de artigos científicos no contexto da Revisão Sistemática da Literatura (RSL) do TCC sobre **Vieses Algorítmicos e Racismo Estrutural**. A ferramenta substitui a busca manual repetitiva por um processo automatizado que consulta múltiplas bases, deduplica resultados, classifica artigos com IA local e exporta notas interligadas para o Obsidian.

---

## Arquitetura da Aplicação

```
RSL/
├── app.py                    # Servidor Flask — orquestra todos os módulos
├── buscador_rsl.py           # Busca BDTD (API REST) + geração do Excel
├── busca_scielo_selenium.py  # Busca SciELO via Selenium (headless)
├── busca_capes_selenium.py   # Busca CAPES via Selenium furtivo + login manual
├── exportar_obsidian.py      # Exporta notas Markdown interligadas para o Obsidian
├── baixar_pdfs.py            # Baixa PDFs via Unpaywall; fallback em Markdown
├── templates/
│   └── index.html            # Interface web (HTML + CSS + JS vanilla)
├── resultados/               # Planilhas Excel geradas
├── capes_exports/            # Arquivos RIS baixados do CAPES
├── historico.json            # Registro das buscas anteriores
└── .venv/                    # Ambiente virtual Python
```

### Fluxo geral de uso

1. **Buscar** — preenche descritores, escolhe bases e recorte temporal → gera `RSL_YYYYMMDD_HHMM.xlsx`
2. **Filtrar** — classifica cada artigo com llama3 (I/E/P) usando critérios do TCC → gera `*_filtrado_*.xlsx`
3. **Baixar PDFs** — tenta baixar PDFs via Unpaywall; salva metadados em Markdown quando indisponível
4. **Exportar Obsidian** — cria notas interligadas por descritor no vault `~/Meu cofre/RSL/`

Cada operação roda em **thread daemon** separada; logs chegam ao navegador em tempo real via **SSE**.

---

## Tecnologias Utilizadas

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.13 | Linguagem principal |
| Flask | 3.1 | Servidor web e roteamento |
| Selenium | 4.44 | Automação do navegador (SciELO) |
| undetected-chromedriver | 3.5.5 | Automação furtiva do Chrome (CAPES) |
| pandas | 3.0 | Leitura de CSV exportados |
| openpyxl | 3.1 | Geração e edição da planilha Excel |
| requests | 2.34 | Consultas à API REST (BDTD, Unpaywall, Ollama) |
| Ollama + llama3 | — | Classificação automática de artigos (local) |
| Unpaywall API | v2 | Localização de PDFs em acesso aberto |
| Chromium (Snap) | 147 | Navegador usado pelo Selenium |
| Server-Sent Events (SSE) | — | Streaming de logs em tempo real |

---

## Rotas da API Flask

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve a interface web (`index.html`) |
| `/buscar` | POST | Inicia busca nas bases selecionadas |
| `/filtrar` | POST | Classifica artigos com Ollama/llama3 |
| `/baixar-pdfs` | POST | Baixa PDFs via Unpaywall |
| `/exportar-obsidian` | POST | Exporta notas para o vault Obsidian |
| `/stream/<sid>` | GET | SSE — transmite logs da sessão em tempo real |
| `/confirmar/<sid>` | POST | Desbloqueia thread aguardando ação manual (CAPES) |
| `/listar-resultados` | GET | Lista planilhas Excel em `resultados/` |
| `/download/<nome>` | GET | Faz download de uma planilha |
| `/historico` | GET | Retorna histórico de buscas |
| `/historico/apagar` | POST | Remove entradas do histórico |

---

## Bases de Dados e Estratégias de Acesso

### SciELO
- **Estratégia:** Selenium com Chrome em modo headless.
- **Motivo:** A SciELO renderiza resultados com JavaScript, impossibilitando scraping simples com `requests`.
- **Paginação:** Detectada e percorrida automaticamente com `WebDriverWait`.

### BDTD (Biblioteca Digital Brasileira de Teses e Dissertações)
- **Estratégia:** API REST VuFind consultada diretamente com `requests`.
- **Endpoint:** `https://bdtd.ibict.br/vufind/api/v1/search`
- **Paginação:** Controlada por `page` e `limit`, limite de 5 páginas por descritor.

### Periódicos CAPES
- **Estratégia:** `undetected_chromedriver` com navegador visível (não headless).
- **Motivo:** O portal exige login via gov.br e aplica detecção de bots.
- **Exportação:** Resultados exportados em RIS pelo portal, depois parseados pelo módulo.

---

## Módulos de Pós-processamento

### `baixar_pdfs.py` — Download via Unpaywall

Consulta a API gratuita do Unpaywall (`https://api.unpaywall.org/v2/{doi}?email=...`) para cada artigo com DOI na planilha.

**Estratégia por caso:**

| Situação | Ação |
|---|---|
| PDF disponível e download OK | Salva `{título}.pdf` em `~/Meu cofre/RSL/pdfs/` |
| Unpaywall encontrou URL mas download falhou | Salva só o `.md` de metadados |
| Unpaywall não encontrou PDF livre | Salva só o `.md` de metadados |
| Artigo sem DOI | Salva só o `.md` de metadados |

**Formato do fallback em Markdown** (`.md`):
```markdown
---
titulo: "Título do artigo"
autores: "Autores"
ano: 2023
base: "SciELO"
doi: "10.xxx/xxxxx"
url_pdf: ""
tags:
  - RSL
  - sem-pdf
---

# Título do artigo

**Autores:** ...
**Ano:** 2023 | **Base:** SciELO

## Resumo
...

## Acesso
[Acessar via DOI](https://doi.org/10.xxx/xxxxx)

> ⚠️ PDF não disponível em acesso aberto via Unpaywall.
```

**Parâmetros configuráveis** (topo de `baixar_pdfs.py`):
```python
UNPAYWALL_EMAIL  = "rsl.tcc@pesquisa.br"   # qualquer e-mail válido
DELAY_ENTRE_DOIS = 0.25                     # seg — limite Unpaywall: 10 req/s
TIMEOUT_DOWNLOAD = 45                       # seg por PDF
```

---

### `exportar_obsidian.py` — Teia de conhecimento

Gera notas Markdown interligadas no vault do Obsidian a partir da planilha Excel.

**Estrutura gerada em `~/Meu cofre/RSL/`:**
```
artigos/
│   Um arquivo .md por artigo
│   Frontmatter YAML + resumo + links para artigos relacionados
descritores/
│   Um arquivo .md por descritor
│   Artigos listados por status (I / P / E)
MOC - RSL.md
    Mapa geral: estatísticas, descritores, teia de conexões
```

**Links gerados (graph view do Obsidian):**
- Cada nota de artigo contém `[[slug|Título do artigo]]` para cada outro artigo do **mesmo descritor** (seção "Artigos relacionados")
- Notas de descritor listam todos os artigos com alias: `[[slug|Título]]`
- O MOC inclui uma seção **"Teia de Conexões entre Descritores"** mostrando quais descritores compartilham artigos:

```
- [[Descritor - X|algorithmic bias]] ↔ [[Descritor - Y|racial bias AI]] (3 artigos em comum)
```

**Frontmatter YAML de cada artigo:**
```yaml
titulo: "..."
autores: "..."
ano: 2024
base: "SciELO"
descritor: "algorithmic bias"
tipo: "Artigo"
doi: "10.xxx/xxxxx"
status: "I"
tags: [RSL, SciELO, Artigo]
```

---

### `/filtrar` — Classificação automática com Ollama

Classifica cada artigo da planilha usando o modelo **llama3** rodando localmente via Ollama (`http://localhost:11434`).

**Critérios aplicados pelo prompt:**

| Código | Tipo | Descrição |
|---|---|---|
| I1 | Inclusão | Recorte temporal: 2020–2025 |
| I2 | Inclusão | Idioma: português, inglês ou espanhol |
| I3 | Inclusão | Aderência temática: vieses algorítmicos, racismo algorítmico, IA em populações negras |
| I4 | Inclusão | Setor: saúde, segurança pública, mercado de trabalho ou crédito financeiro |
| I5 | Inclusão | Disponibilidade: texto completo gratuito |
| I6 | Inclusão | Tipo: artigo, dissertação, tese ou relatório com metodologia |
| E1 | Exclusão | Fora do recorte temporal |
| E2 | Exclusão | Sem dimensão racial (puramente técnico) |
| E3 | Exclusão | Setor fora do escopo (entretenimento, educação, agro…) |
| E4 | Exclusão | Texto completo indisponível |
| E5 | Exclusão | Duplicidade entre bases |
| E6 | Exclusão | Inconsistência título × conteúdo |
| E7 | Exclusão | Sem metodologia explícita (editorial, resenha, resumo) |

**Saída por artigo:**
- O llama3 retorna JSON: `{"status": "I", "criterio": "I3, I4", "justificativa": "..."}`
- A extração usa regex `\{[^{}]+\}` para tolerar texto adicional em volta do JSON
- Coluna **Status (I/E/P)** recebe `I`, `E` ou `P`
- Coluna **Motivo Exclusão** recebe `[I3, I4] Trata de discriminação racial em sistemas de crédito`
- Em caso de falha no Ollama, o artigo é marcado como `P` (pendente)

**Preenchimento da Tabela 2 - Pós Filtragem:**
Após classificar todos os artigos, a aba "Tabela 2 - Pós Filtragem" é limpa e reescrita com **todos os artigos classificados** — uma linha por artigo, com as colunas:

`Base | Descritor | Título | Autores | Ano | DOI | Status (I/E/P) | Critério | Motivo Exclusão`

O campo **Critério** traz o código aplicado (ex: `I3, I4`) e **Motivo Exclusão** traz a justificativa em linguagem natural gerada pelo llama3. Use os filtros automáticos da aba para isolar incluídos, excluídos ou pendentes.

**Sobre o status P (Pendente):**
O llama3 atribui `P` quando não tem confiança suficiente para incluir ou excluir o artigo apenas com título e resumo. Ocorre em três situações:

| Situação | Exemplo |
|---|---|
| Título genérico, resumo vago | "Machine learning in public services" — pode ou não ter dimensão racial |
| Resumo ausente ou muito curto | Informação insuficiente para decidir |
| Conteúdo ambíguo | Trata de IA em saúde mas não menciona raça explicitamente |

Os artigos `P` formam a **fila de leitura manual**: abra o texto completo e decida inclusão ou exclusão — é o que o critério I5 prevê. Na planilha, filtre a coluna `Status (I/E/P)` por `P` para trabalhar esses casos.

**Arquivo de saída:** `{nome_original}_filtrado_YYYYMMDD_HHMM.xlsx` (sem duplo sufixo se já era filtrado).

**Pré-requisito:** Ollama rodando com llama3 instalado:
```bash
ollama serve          # em um terminal
ollama pull llama3    # uma única vez
```

---

## Estrutura da Planilha Excel

Gerada por `buscador_rsl.py` via `openpyxl`. Contém 8 abas:

| Aba | Gerada por | Conteúdo |
|---|---|---|
| Tabela 2 - Pós Filtragem | `/filtrar` | Lista de artigos classificados com Status, Critério e Motivo |
| Todos os Resultados | Busca | Todos os registros únicos + bloco de resumo por descritor/base no final |
| SciELO | Busca | Registros filtrados por base |
| BDTD | Busca | Registros filtrados por base |
| Periódicos CAPES | Busca | Registros filtrados por base |
| Duplicatas | Busca | Registros removidos na deduplicação |
| Quadro 1 - Estudos Finais | Busca | Template para codificação final (E1, E2…) |
| Critérios I-E | Busca | Definição dos critérios I1–I6 e E1–E7 |

> **Nota de design:** a antiga aba "Tabela 1 - Busca Inicial" (matriz de contagem) foi incorporada ao final da aba "Todos os Resultados" como bloco "Resumo — Busca Inicial por Descritor", eliminando a redundância de abas separadas.

**Colunas de "Todos os Resultados":**
`Base | Descritor | Título | Autores | Ano | Revista/Repositório | Tipo | Resumo | DOI | Link | Status (I/E/P) | Motivo Exclusão`

**Colunas de "Tabela 2 - Pós Filtragem":**
`Base | Descritor | Título | Autores | Ano | DOI | Status (I/E/P) | Critério | Motivo Exclusão`

---

## Problemas Encontrados e Soluções

### 1. VS Code rodando como Flatpak — binários Snap inacessíveis

**Problema:** O terminal integrado do VS Code é executado dentro de um sandbox Flatpak. Binários Snap (como o Chromium) ficam fora desse sandbox.

**Solução:** Executar o Flask a partir de um terminal externo ao VS Code (ex: GNOME Terminal).

---

### 2. Caminhos hardcoded com número de versão do Snap

**Problema:** Referências ao Chromium com versão exata (ex: `/snap/chromium/3423/...`) quebravam a cada atualização.

**Solução:** Uso do link simbólico `current` mantido pelo Snap:
```
/snap/chromium/current/usr/lib/chromium-browser/chrome
```

---

### 3. Python 3.13 removeu `distutils`

**Problema:** `undetected_chromedriver` dependia de `distutils.version.LooseVersion`, removido no Python 3.12+.

**Solução:**
```bash
pip install setuptools
```

---

### 4. `undetected_chromedriver` não conseguia modificar o ChromeDriver

**Problema:** O ChromeDriver do Snap fica em `squashfs` (somente-leitura); o `undetected_chromedriver` precisa modificar o binário.

**Solução:** O módulo copia o ChromeDriver para `~/.cache/rsl_buscador/chromedriver` antes de patcheá-lo:
```python
def _chromedriver_gravavel() -> str:
    shutil.copy2(_CHROMEDRIVER_SRC, _CHROMEDRIVER_LOCAL)
    os.chmod(_CHROMEDRIVER_LOCAL, 0o755)
    return _CHROMEDRIVER_LOCAL
```

---

### 5. Log em tempo real sem travar a interface

**Problema:** Buscas com Selenium demoram minutos; bloquear o Flask tornaria a interface inacessível.

**Solução:** Cada operação roda em thread daemon. `sys.stdout` é redirecionado para um `queue.Queue`; a rota `/stream/<id>` usa SSE para consumir essa fila e enviar cada linha ao navegador sem polling.

---

### 6. CAPES usa `input()` para aguardar ações manuais

**Problema:** `input("Pressione ENTER...")` não funciona em servidor web.

**Solução:** `sys.stdin` é substituído por `_WebInput`, que envia evento SSE `aguardar_confirmacao` ao navegador e bloqueia em `threading.Event`. O botão **Confirmar** da interface chama `/confirmar/<id>`, que seta o evento e desbloqueia a thread.

---

### 7. Chrome DevTools gerando erros 404

**Problema:** Chrome tenta acessar `/.well-known/appspecific/com.chrome.devtools.json` e gera 404 no log.

**Solução:** Rota dedicada que responde `204 No Content`.

---

### 8. Ollama trava com `llama runner process has terminated`

**Contexto da máquina:** AMD Ryzen 5 5500 · 16 GB RAM · NVIDIA GeForce GTX 960 (2 GB VRAM)

**Problema:** O Ollama tentava carregar o llama3 (8B / ~4.6 GB) na GTX 960, que não tem VRAM suficiente. O crash ocorria com o erro:
```
Error: 500 Internal Server Error: llama runner process has terminated: signal arrived during cgo execution
```
O problema se manteve após atualizar o Ollama (0.23.3 → atual), confirmando que não era bug de versão, mas incompatibilidade de hardware.

**Causa raiz:** A GTX 960 tem apenas 2 GB de VRAM. O llama3 precisa de ~5 GB. Além disso, o driver NVIDIA não estava instalado (`nvidia-smi: comando não encontrado`), então o runtime CUDA falhava em nível de sistema ao tentar inicializar.

**Solução:** Forçar modo CPU desativando a GPU via variáveis de ambiente:
```bash
export OLLAMA_NO_CUDA=1
export CUDA_VISIBLE_DEVICES=""
```

Para tornar permanente:
```bash
echo 'export OLLAMA_NO_CUDA=1' >> ~/.bashrc
echo 'export CUDA_VISIBLE_DEVICES=""' >> ~/.bashrc
source ~/.bashrc
sudo systemctl disable ollama   # evita que o serviço de sistema suba com GPU
```

**Observação:** Com o Ryzen 5 5500 (AVX2) e 6+ GB de RAM disponível, o llama3 roda normalmente em CPU — mais lento que GPU, mas funcional para a filtragem da RSL.

---

## Como Executar

### Pré-requisitos
- Python 3.13+
- Chromium via Snap: `snap install chromium`
- Ollama com llama3 (para filtragem): `ollama pull llama3`

### Primeira execução
```bash
cd ~/TCC/RLS
python3 -m venv .venv
source .venv/bin/activate
pip install flask selenium undetected-chromedriver pandas openpyxl requests setuptools

# ChromeDriver gravável para o CAPES
mkdir -p ~/.cache/rsl_buscador
cp /snap/chromium/current/usr/lib/chromium-browser/chromedriver ~/.cache/rsl_buscador/chromedriver
chmod 755 ~/.cache/rsl_buscador/chromedriver

# Desativa GPU no Ollama (GTX 960 tem VRAM insuficiente para llama3)
echo 'export OLLAMA_NO_CUDA=1' >> ~/.bashrc
echo 'export CUDA_VISIBLE_DEVICES=""' >> ~/.bashrc
source ~/.bashrc
sudo systemctl disable ollama
```

### Execuções seguintes
```bash
# IMPORTANTE: usar terminal externo ao VS Code
cd ~/TCC/RLS
source .venv/bin/activate

# Subir o Ollama em modo CPU (necessário para /filtrar):
ollama serve > /tmp/ollama.log 2>&1 &

python3 app.py
# Acesse http://localhost:5000
```

---

## Observações sobre o CAPES

1. O Chromium **abre visível** (não headless) para permitir interação manual.
2. Quando o login for solicitado, autentique com sua conta gov.br e clique **Confirmar** na interface.
3. Se um CAPTCHA aparecer, resolva no navegador e clique **Confirmar**.
4. Arquivos RIS ficam em `capes_exports/`.

---

*Última atualização: 2026-05-18 — reestruturação da planilha Excel: Tabela 2 passa a conter artigos classificados (Status/Critério/Motivo); resumo de contagem incorporado ao final de "Todos os Resultados".*
