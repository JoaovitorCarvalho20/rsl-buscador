# RSL Buscador

Ferramenta de automação para **Revisão Sistemática da Literatura (RSL)** desenvolvida como parte do TCC sobre **Vieses Algorítmicos e Racismo Estrutural**.

## Sobre o TCC

> Realizar uma revisão sistemática da literatura recente (2020–2025) sobre os impactos dos vieses algorítmicos na vida de pessoas negras, analisando como esses vieses reforçam o racismo estrutural em setores como saúde, segurança, mercado de trabalho e crédito.

## O que a ferramenta faz

| Etapa | Descrição |
|---|---|
| 🔍 **Buscar** | Consulta SciELO, BDTD e Periódicos CAPES com descritores em PT/EN |
| 🤖 **Filtrar** | Classifica artigos com IA local (Ollama/llama3) usando critérios I/E da RSL |
| 📥 **Baixar PDFs** | Tenta baixar PDFs via Unpaywall; salva metadados em Markdown quando indisponível |
| 🕸️ **Exportar Obsidian** | Gera notas interligadas por descritor no vault do Obsidian |

## Interface Web

Servidor Flask com interface web para execução de todas as etapas com logs em tempo real.

![Interface](https://img.shields.io/badge/Interface-Flask%20Web-blue)
![Python](https://img.shields.io/badge/Python-3.13-green)
![Ollama](https://img.shields.io/badge/IA-Ollama%20llama3-orange)

## Pré-requisitos

- Python 3.13+
- Chromium via Snap: `snap install chromium`
- Ollama com llama3: `ollama pull llama3`

## Instalação

```bash
git clone https://github.com/JoaovitorCarvalho20/rsl-buscador.git
cd rsl-buscador

python3 -m venv .venv
source .venv/bin/activate
pip install flask selenium undetected-chromedriver pandas openpyxl requests setuptools

# ChromeDriver gravável (necessário para busca no CAPES)
mkdir -p ~/.cache/rsl_buscador
cp /snap/chromium/current/usr/lib/chromium-browser/chromedriver ~/.cache/rsl_buscador/chromedriver
chmod 755 ~/.cache/rsl_buscador/chromedriver
```

## Como usar

```bash
# IMPORTANTE: usar terminal externo ao VS Code
source .venv/bin/activate

# Subir Ollama em modo CPU (para filtragem)
ollama serve > /tmp/ollama.log 2>&1 &

python3 app.py
# Acesse http://localhost:5000
```

## Estrutura do Projeto

```
rsl-buscador/
├── app.py                    # Servidor Flask
├── buscador_rsl.py           # Busca BDTD + geração do Excel
├── busca_scielo_selenium.py  # Busca SciELO via Selenium
├── busca_capes_selenium.py   # Busca CAPES via Selenium
├── exportar_obsidian.py      # Exporta notas para o Obsidian
├── baixar_pdfs.py            # Baixa PDFs via Unpaywall
├── templates/
│   └── index.html            # Interface web
└── DOCUMENTACAO.md           # Documentação técnica completa
```

## Descritores utilizados

**Português:** racismo algoritmo · racismo algorítmico · viés algorítmico · discriminação racial algoritmo · inteligência artificial população negra · algoritmo saúde raça · policiamento preditivo racismo · algoritmo mercado trabalho discriminação

**Inglês:** algorithmic discrimination · algorithmic bias race · artificial intelligence racial discrimination · predictive policing racial bias · machine learning racism · algorithmic racism

## Critérios de Filtragem (RSL)

**Inclusão:** recorte 2020–2025 · idioma PT/EN/ES · aderência temática a vieses algorítmicos e racismo · setor saúde/segurança/trabalho/crédito · metodologia explícita

**Exclusão:** fora do recorte temporal · sem dimensão racial · setor fora do escopo · duplicidade · sem metodologia

## Documentação

Consulte o arquivo [`DOCUMENTACAO.md`](DOCUMENTACAO.md) para detalhes técnicos completos sobre arquitetura, decisões de projeto e problemas resolvidos.

---

Desenvolvido por [João Vitor Carvalho](https://github.com/JoaovitorCarvalho20) · TCC · 2026
