"""
interface.py
Interface gráfica para o RSL Buscador
Tkinter — sem dependências extras
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import os
import io
from datetime import datetime

# Redireciona print para o log da interface
class LogRedirecionador(io.TextIOBase):
    def __init__(self, widget):
        self.widget = widget

    def write(self, texto):
        if texto.strip():
            self.widget.after(0, self._inserir, texto)
        return len(texto)

    def _inserir(self, texto):
        self.widget.config(state="normal")
        self.widget.insert(tk.END, texto + "\n")
        self.widget.see(tk.END)
        self.widget.config(state="disabled")


class RSLBuscadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RSL Buscador — Revisão Sistemática da Literatura")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        self.root.configure(bg="#F0F4F8")

        self._construir_interface()

    # ─────────────────────────────────────────────
    # CONSTRUÇÃO DA INTERFACE
    # ─────────────────────────────────────────────

    def _construir_interface(self):
        # ── Cabeçalho ──
        cabecalho = tk.Frame(self.root, bg="#1F3864", pady=12)
        cabecalho.pack(fill="x")

        tk.Label(
            cabecalho,
            text="RSL Buscador",
            font=("Helvetica", 20, "bold"),
            fg="white", bg="#1F3864"
        ).pack()

        tk.Label(
            cabecalho,
            text="Revisão Sistemática da Literatura — SciELO | BDTD | Periódicos CAPES",
            font=("Helvetica", 10),
            fg="#B8CCE4", bg="#1F3864"
        ).pack()

        # ── Frame principal com scroll ──
        canvas = tk.Canvas(self.root, bg="#F0F4F8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.frame_principal = tk.Frame(canvas, bg="#F0F4F8", padx=20, pady=10)

        self.frame_principal.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.frame_principal, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._secao_configuracao()
        self._secao_descritores()
        self._secao_bases()
        self._secao_log()
        self._secao_botoes()

    def _card(self, titulo):
        """Cria um card com título e retorna o frame interno."""
        frame_outer = tk.Frame(self.frame_principal, bg="#FFFFFF",
                               relief="flat", bd=1,
                               highlightbackground="#D1D9E6",
                               highlightthickness=1)
        frame_outer.pack(fill="x", pady=8)

        tk.Label(
            frame_outer,
            text=titulo,
            font=("Helvetica", 11, "bold"),
            fg="#1F3864", bg="#FFFFFF",
            anchor="w", padx=14, pady=8
        ).pack(fill="x")

        separador = tk.Frame(frame_outer, bg="#D1D9E6", height=1)
        separador.pack(fill="x")

        frame_inner = tk.Frame(frame_outer, bg="#FFFFFF", padx=14, pady=10)
        frame_inner.pack(fill="x")

        return frame_inner

    def _secao_configuracao(self):
        frame = self._card("⚙️  Configuração da Pesquisa")

        # Linha 1: Tema e anos
        linha1 = tk.Frame(frame, bg="#FFFFFF")
        linha1.pack(fill="x", pady=4)

        tk.Label(linha1, text="Tema da pesquisa:", bg="#FFFFFF",
                 font=("Helvetica", 10)).pack(side="left")
        self.entry_tema = tk.Entry(linha1, width=40, font=("Helvetica", 10))
        self.entry_tema.pack(side="left", padx=(8, 20))
        self.entry_tema.insert(0, "Vieses algorítmicos e racismo estrutural")

        tk.Label(linha1, text="Ano início:", bg="#FFFFFF",
                 font=("Helvetica", 10)).pack(side="left")
        self.entry_ano_ini = tk.Entry(linha1, width=6, font=("Helvetica", 10))
        self.entry_ano_ini.pack(side="left", padx=(4, 12))
        self.entry_ano_ini.insert(0, "2020")

        tk.Label(linha1, text="Ano fim:", bg="#FFFFFF",
                 font=("Helvetica", 10)).pack(side="left")
        self.entry_ano_fim = tk.Entry(linha1, width=6, font=("Helvetica", 10))
        self.entry_ano_fim.pack(side="left", padx=(4, 0))
        self.entry_ano_fim.insert(0, "2025")

        # Linha 2: Pasta de saída
        linha2 = tk.Frame(frame, bg="#FFFFFF")
        linha2.pack(fill="x", pady=4)

        tk.Label(linha2, text="Pasta de saída:", bg="#FFFFFF",
                 font=("Helvetica", 10)).pack(side="left")
        self.entry_pasta = tk.Entry(linha2, width=45, font=("Helvetica", 10))
        self.entry_pasta.pack(side="left", padx=(8, 8))
        self.entry_pasta.insert(0, os.path.expanduser("~/Downloads"))

        tk.Button(
            linha2, text="Escolher...",
            command=self._escolher_pasta,
            bg="#E8EDF5", relief="flat",
            font=("Helvetica", 9), padx=8
        ).pack(side="left")

    def _secao_descritores(self):
        frame = self._card("🔍  Descritores de Busca")

        instrucao = tk.Label(
            frame,
            text="Digite um descritor por linha. Use termos simples sem AND/OR — a busca é feita por todos os termos.",
            font=("Helvetica", 9), fg="#666666", bg="#FFFFFF",
            wraplength=820, justify="left"
        )
        instrucao.pack(anchor="w", pady=(0, 6))

        self.text_descritores = scrolledtext.ScrolledText(
            frame, height=10, font=("Courier", 10),
            wrap="word", relief="flat",
            highlightbackground="#D1D9E6", highlightthickness=1
        )
        self.text_descritores.pack(fill="x")

        descritores_padrao = """racismo algoritmo
racismo algorítmico
viés algorítmico
discriminação racial algoritmo
inteligência artificial população negra
algoritmo saúde raça
policiamento preditivo racismo
algoritmo mercado trabalho discriminação
algorithmic discrimination
algorithmic bias race
artificial intelligence racial discrimination
predictive policing racial bias
machine learning racism
algorithmic racism"""
        self.text_descritores.insert("1.0", descritores_padrao)

        # Botões auxiliares
        linha_btns = tk.Frame(frame, bg="#FFFFFF")
        linha_btns.pack(fill="x", pady=(6, 0))

        tk.Button(
            linha_btns, text="+ Adicionar linha",
            command=lambda: self.text_descritores.insert(tk.END, "\n"),
            bg="#E8EDF5", relief="flat", font=("Helvetica", 9), padx=8
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            linha_btns, text="Limpar tudo",
            command=lambda: self.text_descritores.delete("1.0", tk.END),
            bg="#FCE8E8", relief="flat", font=("Helvetica", 9), padx=8
        ).pack(side="left")

        tk.Label(
            linha_btns,
            text="Total de descritores: ",
            bg="#FFFFFF", font=("Helvetica", 9), fg="#666666"
        ).pack(side="right")

        self.label_total_desc = tk.Label(
            linha_btns, text="14",
            bg="#FFFFFF", font=("Helvetica", 9, "bold"), fg="#1F3864"
        )
        self.label_total_desc.pack(side="right")

        self.text_descritores.bind("<KeyRelease>", self._atualizar_contador)

    def _secao_bases(self):
        frame = self._card("🗄️  Bases de Dados")

        linha = tk.Frame(frame, bg="#FFFFFF")
        linha.pack(fill="x")

        self.var_scielo = tk.BooleanVar(value=True)
        self.var_bdtd = tk.BooleanVar(value=True)
        self.var_capes = tk.BooleanVar(value=True)

        for var, texto, cor in [
            (self.var_scielo, "SciELO  (automático)", "#E8F4FD"),
            (self.var_bdtd,   "BDTD  (automático)", "#EAF3DE"),
            (self.var_capes,  "Periódicos CAPES  (requer login manual)", "#FFF3CD"),
        ]:
            cb_frame = tk.Frame(linha, bg=cor, padx=10, pady=6,
                                highlightbackground="#D1D9E6", highlightthickness=1)
            cb_frame.pack(side="left", padx=(0, 10))
            tk.Checkbutton(
                cb_frame, text=texto, variable=var,
                bg=cor, font=("Helvetica", 10), activebackground=cor
            ).pack()

        aviso = tk.Label(
            frame,
            text="⚠️  O CAPES abrirá o navegador para você fazer login com seu gov.br. "
                 "Após o login, o script assume automaticamente.",
            font=("Helvetica", 9), fg="#856404", bg="#FFF3CD",
            wraplength=820, justify="left", padx=8, pady=6
        )
        aviso.pack(fill="x", pady=(8, 0))

    def _secao_log(self):
        frame = self._card("📋  Log de Execução")

        self.text_log = scrolledtext.ScrolledText(
            frame, height=12, font=("Courier", 9),
            bg="#1E1E1E", fg="#D4D4D4",
            wrap="word", state="disabled",
            relief="flat",
            highlightbackground="#D1D9E6", highlightthickness=1
        )
        self.text_log.pack(fill="x")

        self._log("Sistema iniciado. Configure os descritores e clique em 'Iniciar Busca'.")

    def _secao_botoes(self):
        frame = tk.Frame(self.frame_principal, bg="#F0F4F8", pady=10)
        frame.pack(fill="x")

        self.btn_iniciar = tk.Button(
            frame,
            text="▶  Iniciar Busca",
            command=self._iniciar_busca,
            bg="#1F3864", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", padx=20, pady=10,
            activebackground="#2E5497", activeforeground="white",
            cursor="hand2"
        )
        self.btn_iniciar.pack(side="left", padx=(0, 10))

        self.btn_parar = tk.Button(
            frame,
            text="⏹  Parar",
            command=self._parar_busca,
            bg="#C0392B", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", padx=20, pady=10,
            activebackground="#A93226", activeforeground="white",
            cursor="hand2",
            state="disabled"
        )
        self.btn_parar.pack(side="left", padx=(0, 20))

        self.label_status = tk.Label(
            frame,
            text="Aguardando...",
            font=("Helvetica", 10), fg="#666666", bg="#F0F4F8"
        )
        self.label_status.pack(side="left")

        self.progress = ttk.Progressbar(
            frame, mode="indeterminate", length=200
        )
        self.progress.pack(side="right", padx=(0, 10))

    # ─────────────────────────────────────────────
    # LÓGICA
    # ─────────────────────────────────────────────

    def _log(self, texto, cor=None):
        self.text_log.config(state="normal")
        self.text_log.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {texto}\n")
        self.text_log.see(tk.END)
        self.text_log.config(state="disabled")

    def _atualizar_contador(self, event=None):
        conteudo = self.text_descritores.get("1.0", tk.END)
        linhas = [l.strip() for l in conteudo.split("\n") if l.strip()]
        self.label_total_desc.config(text=str(len(linhas)))

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha a pasta de saída")
        if pasta:
            self.entry_pasta.delete(0, tk.END)
            self.entry_pasta.insert(0, pasta)

    def _pegar_descritores(self):
        conteudo = self.text_descritores.get("1.0", tk.END)
        return [l.strip() for l in conteudo.split("\n") if l.strip()]

    def _iniciar_busca(self):
        descritores = self._pegar_descritores()
        if not descritores:
            messagebox.showwarning("Atenção", "Adicione pelo menos um descritor!")
            return

        if not self.var_scielo.get() and not self.var_bdtd.get() and not self.var_capes.get():
            messagebox.showwarning("Atenção", "Selecione pelo menos uma base de dados!")
            return

        try:
            ano_ini = int(self.entry_ano_ini.get())
            ano_fim = int(self.entry_ano_fim.get())
        except ValueError:
            messagebox.showerror("Erro", "Anos inválidos!")
            return

        pasta_saida = self.entry_pasta.get()
        os.makedirs(pasta_saida, exist_ok=True)

        self.btn_iniciar.config(state="disabled")
        self.btn_parar.config(state="normal")
        self.progress.start(10)
        self.label_status.config(text="Buscando...", fg="#1F3864")

        self._log("=" * 50)
        self._log(f"Tema: {self.entry_tema.get()}")
        self._log(f"Recorte: {ano_ini}–{ano_fim}")
        self._log(f"Descritores: {len(descritores)}")
        self._log(f"Bases: " + ", ".join([
            b for b, v in [
                ("SciELO", self.var_scielo.get()),
                ("BDTD", self.var_bdtd.get()),
                ("CAPES", self.var_capes.get())
            ] if v
        ]))
        self._log("=" * 50)

        # Roda em thread separada para não travar a interface
        self._thread = threading.Thread(
            target=self._executar_busca,
            args=(descritores, ano_ini, ano_fim, pasta_saida),
            daemon=True
        )
        self._parar = False
        self._thread.start()

    def _parar_busca(self):
        self._parar = True
        self._log("⏹  Interrompendo busca...")
        self._finalizar_ui("Interrompido pelo usuário.")

    def _finalizar_ui(self, mensagem):
        self.btn_iniciar.config(state="normal")
        self.btn_parar.config(state="disabled")
        self.progress.stop()
        self.label_status.config(text=mensagem, fg="#27AE60")

    def _executar_busca(self, descritores, ano_ini, ano_fim, pasta_saida):
        """Executa as buscas em thread separada."""
        sys.stdout = LogRedirecionador(self.text_log)

        try:
            todos = []
            contagens = {d: {} for d in descritores}

            # Importa os módulos do projeto
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

            # ── SciELO ──
            if self.var_scielo.get() and not self._parar:
                self._log("\n[1/3] Iniciando busca na SciELO...")
                try:
                    from busca_scielo_selenium import buscar_scielo_todos
                    res, cnts = buscar_scielo_todos(descritores)
                    todos.extend(res)
                    for d, c in cnts.items():
                        contagens[d]["SciELO"] = c
                    self._log(f"✅ SciELO: {len(res)} resultados")
                except Exception as e:
                    self._log(f"❌ SciELO erro: {e}")

            # ── BDTD ──
            if self.var_bdtd.get() and not self._parar:
                self._log("\n[2/3] Iniciando busca na BDTD...")
                try:
                    from buscador_rsl import buscar_bdtd, deduplicar
                    for desc in descritores:
                        if self._parar:
                            break
                        self._log(f"  → {desc[:50]}...")
                        res = buscar_bdtd(desc)
                        contagens[desc]["BDTD"] = len(res)
                        todos.extend(res)
                    self._log(f"✅ BDTD concluída")
                except Exception as e:
                    self._log(f"❌ BDTD erro: {e}")

            # ── CAPES ──
            if self.var_capes.get() and not self._parar:
                self._log("\n[3/3] Iniciando busca no Periódicos CAPES...")
                self._log("  ℹ️  O navegador vai abrir para você fazer login.")
                try:
                    from busca_capes_selenium import buscar_capes_todos, parsear_ris, PASTA_RIS
                    import glob
                    res_capes, cnts_capes = buscar_capes_todos(descritores)
                    todos.extend(res_capes)
                    for d, c in cnts_capes.items():
                        contagens[d]["Periódicos CAPES"] = c
                    self._log(f"✅ CAPES concluída")
                except Exception as e:
                    self._log(f"❌ CAPES erro: {e}")

            if not todos:
                self._log("\n⚠️  Nenhum resultado encontrado.")
                self.root.after(0, self._finalizar_ui, "Nenhum resultado.")
                return

            # ── Deduplicação ──
            self._log(f"\n[Deduplicação] Total bruto: {len(todos)}")
            from buscador_rsl import deduplicar, gerar_excel
            unicos, duplicatas = deduplicar(todos)
            self._log(f"  Únicos: {len(unicos)} | Duplicatas: {len(duplicatas)}")

            # Garante contagens zeradas
            for desc in descritores:
                for base in ["SciELO", "BDTD", "Periódicos CAPES"]:
                    contagens[desc].setdefault(base, 0)

            # ── Gera Excel ──
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            nome_arquivo = f"RSL_{timestamp}.xlsx"
            caminho = os.path.join(pasta_saida, nome_arquivo)
            gerar_excel(todos, unicos, duplicatas, contagens, caminho)

            self._log(f"\n{'='*50}")
            self._log(f"✅ Planilha salva em: {caminho}")
            self._log(f"   SciELO: {sum(contagens[d].get('SciELO',0) for d in descritores)}")
            self._log(f"   BDTD: {sum(contagens[d].get('BDTD',0) for d in descritores)}")
            self._log(f"   CAPES: {sum(contagens[d].get('Periódicos CAPES',0) for d in descritores)}")
            self._log(f"   Total único: {len(unicos)}")
            self._log(f"{'='*50}")

            # Pergunta se quer abrir a pasta
            self.root.after(0, self._perguntar_abrir, pasta_saida)
            self.root.after(0, self._finalizar_ui, f"✅ Concluído! {len(unicos)} resultados únicos.")

        except Exception as e:
            self._log(f"\n❌ Erro inesperado: {e}")
            self.root.after(0, self._finalizar_ui, "Erro durante execução.")
        finally:
            sys.stdout = sys.__stdout__

    def _perguntar_abrir(self, pasta):
        if messagebox.askyesno(
            "Concluído!",
            "Busca finalizada com sucesso!\n\nDeseja abrir a pasta com a planilha?"
        ):
            import subprocess
            subprocess.Popen(["xdg-open", pasta])


# ─────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()

    # Estilo dos widgets ttk
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TScrollbar", background="#D1D9E6", troughcolor="#F0F4F8")
    style.configure("TProgressbar", background="#1F3864", troughcolor="#D1D9E6")

    app = RSLBuscadorApp(root)
    root.mainloop()