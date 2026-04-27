import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import json
from datetime import datetime
from typing import Optional
import database as db
import ai_client as ai
from github_api import GitHubClient, get_lang_color
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
BG       = "#0d0d0d"
BG2      = "#141414"
BG3      = "#1a1a1a"
CARD     = "#1e1e1e"
CARD2    = "#252525"
BORDER   = "#2a2a2a"
ACCENT   = "#4a9eff"
ACCENT2  = "#6bb3ff"
SUCCESS  = "#22c55e"
WARNING  = "#f59e0b"
DANGER   = "#ef4444"
TEXT     = "#e8e8e8"
TEXT2    = "#a0a0a0"
TEXT3    = "#606060"
PRIORITY_COLORS = {"high": DANGER, "medium": WARNING, "low": SUCCESS}
STATUS_COLORS   = {"todo": TEXT3, "doing": ACCENT, "done": SUCCESS}
FONT_H1   = ("Inter", 22, "bold")
FONT_H2   = ("Inter", 16, "bold")
FONT_H3   = ("Inter", 13, "bold")
FONT_BODY = ("Inter", 12)
FONT_SM   = ("Inter", 11)
FONT_MONO = ("JetBrains Mono", 11)
class HoverButton(ctk.CTkButton):
    def __init__(self, master, hover_color=ACCENT2, **kwargs):
        kwargs.setdefault("fg_color", CARD2)
        kwargs.setdefault("text_color", TEXT)
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("border_width", 0)
        self._base_color = kwargs["fg_color"]
        self._hover_color = hover_color
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    def _on_enter(self, e=None):
        self.configure(fg_color=self._hover_color)
    def _on_leave(self, e=None):
        self.configure(fg_color=self._base_color)
class CardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", CARD)
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", BORDER)
        super().__init__(master, **kwargs)
class SectionLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        kwargs.setdefault("font", FONT_H3)
        kwargs.setdefault("text_color", TEXT2)
        super().__init__(master, text=text.upper(), **kwargs)
class Tag(ctk.CTkLabel):
    def __init__(self, master, text, color=ACCENT, **kwargs):
        kwargs.setdefault("font", FONT_SM)
        kwargs.setdefault("text_color", color)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 6)
        kwargs.setdefault("padx", 8)
        kwargs.setdefault("pady", 2)
        super().__init__(master, text=text, **kwargs)
class AddTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Nova Tarefa")
        self.geometry("480x380")
        self.configure(fg_color=BG2)
        self.resizable(False, False)
        self.after(100, self.grab_set)
        self.on_save = on_save
        ctk.CTkLabel(self, text="Nova Tarefa", font=FONT_H2, text_color=TEXT).pack(pady=(20, 4), padx=24, anchor="w")
        ctk.CTkLabel(self, text="Título", font=FONT_SM, text_color=TEXT2).pack(padx=24, anchor="w")
        self.title_entry = ctk.CTkEntry(self, placeholder_text="Ex: Adicionar token de autenticação",
                                         fg_color=BG3, border_color=BORDER, text_color=TEXT,
                                         font=FONT_BODY, height=38)
        self.title_entry.pack(fill="x", padx=24, pady=(2, 10))
        ctk.CTkLabel(self, text="Descrição (opcional)", font=FONT_SM, text_color=TEXT2).pack(padx=24, anchor="w")
        self.desc_entry = ctk.CTkTextbox(self, height=80, fg_color=BG3, border_color=BORDER,
                                          text_color=TEXT, font=FONT_BODY, border_width=1)
        self.desc_entry.pack(fill="x", padx=24, pady=(2, 10))
        ctk.CTkLabel(self, text="Prioridade", font=FONT_SM, text_color=TEXT2).pack(padx=24, anchor="w")
        self.priority = ctk.CTkSegmentedButton(self, values=["low", "medium", "high"],
                                                fg_color=BG3, selected_color=ACCENT,
                                                text_color=TEXT, font=FONT_SM)
        self.priority.set("medium")
        self.priority.pack(padx=24, pady=(2, 16), anchor="w")
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24)
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color=CARD2, text_color=TEXT2,
                       command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_frame, text="Adicionar", fg_color=ACCENT, text_color="white",
                       command=self._save, width=100).pack(side="right")
        self.title_entry.focus()
    def _save(self):
        title = self.title_entry.get().strip()
        if not title:
            return
        desc = self.desc_entry.get("1.0", "end").strip()
        priority = self.priority.get()
        self.on_save(title, desc, priority)
        self.destroy()
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Configurações")
        self.geometry("520x540")
        self.configure(fg_color=BG2)
        self.resizable(False, False)
        self.after(100, self.grab_set)
        self.on_save = on_save
        ctk.CTkLabel(self, text="Configurações", font=FONT_H2, text_color=TEXT).pack(pady=(20, 4), padx=24, anchor="w")
        ctk.CTkLabel(self, text="GitHub Token", font=FONT_H3, text_color=TEXT2).pack(padx=24, anchor="w", pady=(12, 0))
        self.gh_token = ctk.CTkEntry(self, placeholder_text="ghp_...", show="*",
                                      fg_color=BG3, border_color=BORDER, text_color=TEXT,
                                      font=FONT_MONO, height=38)
        self.gh_token.pack(fill="x", padx=24, pady=(4, 4))
        saved_token = db.get_setting("github_token", "")
        if saved_token:
            self.gh_token.insert(0, saved_token)
        ctk.CTkLabel(self, text="github.com/settings/tokens → New token → repo scope",
                      font=FONT_SM, text_color=TEXT3).pack(padx=24, anchor="w")
        ctk.CTkLabel(self, text="Provedor de IA", font=FONT_H3, text_color=TEXT2).pack(padx=24, anchor="w", pady=(16, 0))
        self.provider = ctk.CTkSegmentedButton(self, values=["gemini", "ollama"],
                                                fg_color=BG3, selected_color=ACCENT,
                                                text_color=TEXT, font=FONT_SM,
                                                command=self._toggle_provider)
        self.provider.set(db.get_setting("ai_provider", "gemini"))
        self.provider.pack(padx=24, pady=(4, 8), anchor="w")
        self.gemini_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.gemini_frame.pack(fill="x", padx=24)
        ctk.CTkLabel(self.gemini_frame, text="Gemini API Key", font=FONT_SM, text_color=TEXT2).pack(anchor="w")
        self.gemini_key = ctk.CTkEntry(self.gemini_frame, placeholder_text="AIza...", show="*",
                                        fg_color=BG3, border_color=BORDER, text_color=TEXT,
                                        font=FONT_MONO, height=38)
        self.gemini_key.pack(fill="x", pady=(2, 0))
        saved_gkey = db.get_setting("gemini_key", "")
        if saved_gkey:
            self.gemini_key.insert(0, saved_gkey)
        ctk.CTkLabel(self.gemini_frame, text="aistudio.google.com → Get API Key (grátis)",
                      font=FONT_SM, text_color=TEXT3).pack(anchor="w")
        self.ollama_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ollama_frame.pack(fill="x", padx=24)
        ctk.CTkLabel(self.ollama_frame, text="Modelo Ollama", font=FONT_SM, text_color=TEXT2).pack(anchor="w", pady=(8, 0))
        self.ollama_model = ctk.CTkEntry(self.ollama_frame, placeholder_text="phi3:mini",
                                          fg_color=BG3, border_color=BORDER, text_color=TEXT,
                                          font=FONT_MONO, height=38)
        self.ollama_model.pack(fill="x", pady=(2, 0))
        saved_model = db.get_setting("ollama_model", "phi3:mini")
        self.ollama_model.insert(0, saved_model)
        ctk.CTkLabel(self.ollama_frame, text="Recomendados: phi3:mini, mistral, llama3.2:3b",
                      font=FONT_SM, text_color=TEXT3).pack(anchor="w")
        ctk.CTkLabel(self.ollama_frame, text="Ollama URL", font=FONT_SM, text_color=TEXT2).pack(anchor="w", pady=(8, 0))
        self.ollama_url = ctk.CTkEntry(self.ollama_frame, placeholder_text="http://localhost:11434",
                                        fg_color=BG3, border_color=BORDER, text_color=TEXT,
                                        font=FONT_MONO, height=38)
        self.ollama_url.pack(fill="x", pady=(2, 0))
        self.ollama_url.insert(0, db.get_setting("ollama_url", "http://localhost:11434"))
        self._toggle_provider(self.provider.get())
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=20, side="bottom")
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color=CARD2, text_color=TEXT2,
                       command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_frame, text="Salvar", fg_color=ACCENT, text_color="white",
                       command=self._save, width=100).pack(side="right")
    def _toggle_provider(self, val):
        if val == "gemini":
            self.gemini_frame.pack(fill="x", padx=24)
            self.ollama_frame.pack_forget()
        else:
            self.gemini_frame.pack_forget()
            self.ollama_frame.pack(fill="x", padx=24)
    def _save(self):
        db.set_setting("github_token", self.gh_token.get().strip())
        db.set_setting("ai_provider", self.provider.get())
        db.set_setting("gemini_key", self.gemini_key.get().strip())
        db.set_setting("ollama_model", self.ollama_model.get().strip() or "phi3:mini")
        db.set_setting("ollama_url", self.ollama_url.get().strip() or "http://localhost:11434")
        self.on_save()
        self.destroy()
class ImportReposDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_import):
        super().__init__(parent)
        self.title("Importar do GitHub")
        self.geometry("620x560")
        self.configure(fg_color=BG2)
        self.after(100, self.grab_set)
        self.on_import = on_import
        self.repos = []
        self.selected = set()
        self.checkboxes = []
        ctk.CTkLabel(self, text="Importar Repositórios", font=FONT_H2, text_color=TEXT).pack(pady=(20, 4), padx=24, anchor="w")
        token = db.get_setting("github_token", "")
        if not token:
            ctk.CTkLabel(self, text="⚠ Configure seu GitHub Token em Configurações primeiro.",
                          font=FONT_BODY, text_color=WARNING).pack(padx=24, pady=20)
            return
        self.status_label = ctk.CTkLabel(self, text="Carregando repositórios...",
                                          font=FONT_BODY, text_color=TEXT2)
        self.status_label.pack(pady=8)
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=24, pady=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter)
        ctk.CTkEntry(search_frame, placeholder_text="Filtrar repos...", textvariable=self.search_var,
                      fg_color=BG3, border_color=BORDER, text_color=TEXT, height=36).pack(fill="x")
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG3, corner_radius=8)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 16))
        self.select_all_btn = ctk.CTkButton(btn_frame, text="Selecionar Todos", fg_color=CARD2,
                                             text_color=TEXT2, width=140, command=self._select_all)
        self.select_all_btn.pack(side="left")
        self.count_label = ctk.CTkLabel(btn_frame, text="", font=FONT_SM, text_color=TEXT2)
        self.count_label.pack(side="left", padx=12)
        ctk.CTkButton(btn_frame, text="Importar Selecionados", fg_color=ACCENT,
                       text_color="white", command=self._do_import).pack(side="right")
        threading.Thread(target=self._load_repos, args=(token,), daemon=True).start()
    def _load_repos(self, token):
        try:
            client = GitHubClient(token)
            ok, info = client.test_auth()
            if not ok:
                self.after(0, lambda: self.status_label.configure(text=f"❌ {info}", text_color=DANGER))
                return
            repos = client.get_repos()
            self.repos = [client.format_repo(r) for r in repos]
            existing = {p["github_url"] for p in db.get_projects() if p.get("github_url")}
            self.repos = [r for r in self.repos if r["github_url"] not in existing]
            self.after(0, self._populate)
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"❌ Erro: {e}", text_color=DANGER))
    def _populate(self, filter_text=""):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.checkboxes = []
        shown = [r for r in self.repos if filter_text.lower() in r["name"].lower()] if filter_text else self.repos
        if not shown:
            ctk.CTkLabel(self.scroll, text="Nenhum repo encontrado.", text_color=TEXT2).pack(pady=20)
            self.status_label.configure(text="")
            return
        self.status_label.configure(text=f"{len(shown)} repositórios disponíveis")
        for repo in shown:
            row = ctk.CTkFrame(self.scroll, fg_color=CARD, corner_radius=8)
            row.pack(fill="x", pady=3)
            var = tk.BooleanVar()
            cb = ctk.CTkCheckBox(row, text="", variable=var, fg_color=ACCENT,
                                  command=self._update_count, width=20)
            cb.pack(side="left", padx=8, pady=8)
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, pady=6)
            ctk.CTkLabel(info_frame, text=repo["name"], font=FONT_H3, text_color=TEXT, anchor="w").pack(anchor="w")
            desc = repo["description"][:60] + "..." if len(repo["description"]) > 60 else repo["description"]
            if desc:
                ctk.CTkLabel(info_frame, text=desc, font=FONT_SM, text_color=TEXT2, anchor="w").pack(anchor="w")
            tag_frame = ctk.CTkFrame(row, fg_color="transparent")
            tag_frame.pack(side="right", padx=12)
            Tag(tag_frame, repo["language"], repo["color"]).pack(side="right", padx=2)
            if repo["stars"] > 0:
                Tag(tag_frame, f"★ {repo['stars']}", WARNING).pack(side="right", padx=2)
            self.checkboxes.append((var, repo))
            self._update_count()
    def _filter(self, *_):
        self._populate(self.search_var.get())
    def _update_count(self):
        n = sum(1 for v, _ in self.checkboxes if v.get())
        self.count_label.configure(text=f"{n} selecionados" if n else "")
    def _select_all(self):
        all_sel = all(v.get() for v, _ in self.checkboxes)
        for v, _ in self.checkboxes:
            v.set(not all_sel)
        self._update_count()
    def _do_import(self):
        selected = [r for v, r in self.checkboxes if v.get()]
        if not selected:
            return
        for repo in selected:
            db.add_project(
                name=repo["name"],
                description=repo["description"],
                github_url=repo["github_url"],
                language=repo["language"],
                stars=repo["stars"],
                color=repo["color"]
            )
        self.on_import()
        self.destroy()
class ProjectCard(ctk.CTkFrame):
    def __init__(self, master, project: dict, on_click, on_delete, **kwargs):
        super().__init__(master, fg_color=CARD, corner_radius=12, border_width=1,
                          border_color=BORDER, **kwargs)
        self.project = project
        self.on_click = on_click
        self._hovered = False
        total, done = db.get_task_stats(project["id"])
        progress = done / total if total > 0 else 0
        color_bar = ctk.CTkFrame(self, fg_color=project.get("color", ACCENT),
                                  corner_radius=0, height=4)
        color_bar.pack(fill="x")
        color_bar.configure(corner_radius=12)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=10)
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text=project["name"], font=FONT_H3, text_color=TEXT,
                      anchor="w").pack(side="left", fill="x", expand=True)
        if project.get("language"):
            Tag(header, project["language"], project.get("color", ACCENT)).pack(side="right")
        desc = project.get("description", "")
        if desc:
            short = desc[:70] + "..." if len(desc) > 70 else desc
            ctk.CTkLabel(content, text=short, font=FONT_SM, text_color=TEXT2,
                          anchor="w", wraplength=220).pack(anchor="w", pady=(4, 0))
        prog_frame = ctk.CTkFrame(content, fg_color="transparent")
        prog_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(prog_frame, text=f"{done}/{total} tarefas",
                      font=FONT_SM, text_color=TEXT3).pack(side="right")
        bar_bg = ctk.CTkFrame(prog_frame, fg_color=BG3, corner_radius=4, height=6)
        bar_bg.pack(fill="x", side="left", expand=True, padx=(0, 8), pady=6)
        if progress > 0:
            bar_fg = ctk.CTkFrame(bar_bg, fg_color=SUCCESS if progress == 1 else ACCENT,
                                   corner_radius=4, height=6)
            bar_fg.place(relwidth=progress, relheight=1)
        if project.get("stars", 0) > 0:
            ctk.CTkLabel(content, text=f"★ {project['stars']}", font=FONT_SM,
                          text_color=WARNING).pack(anchor="w")
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8, 0))
        HoverButton(btn_row, text="Abrir →", hover_color=ACCENT,
                     command=lambda: on_click(project), height=30,
                     font=FONT_SM).pack(side="left")
        HoverButton(btn_row, text="✕", hover_color=DANGER, width=30, height=30,
                     command=lambda: on_delete(project), font=FONT_SM).pack(side="right")
        self.bind("<Enter>", self._hover_on)
        self.bind("<Leave>", self._hover_off)
        for child in self.winfo_children():
            child.bind("<Enter>", self._hover_on)
            child.bind("<Leave>", self._hover_off)
    def _hover_on(self, e):
        self.configure(border_color=ACCENT)
    def _hover_off(self, e):
        self.configure(border_color=BORDER)
class ProjectView(ctk.CTkFrame):
    def __init__(self, master, project: dict, on_back):
        super().__init__(master, fg_color=BG)
        self.project = project
        self.on_back = on_back
        self._build()
    def _build(self):
        header = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0)
        header.pack(fill="x", pady=(0, 1))
        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=12)
        HoverButton(inner, text="← Projetos", hover_color=CARD2, fg_color="transparent",
                     text_color=TEXT2, font=FONT_SM, command=self.on_back, width=100).pack(side="left")
        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.pack(side="left", padx=16, fill="x", expand=True)
        ctk.CTkLabel(title_frame, text=self.project["name"], font=FONT_H2,
                      text_color=TEXT).pack(anchor="w")
        if self.project.get("github_url"):
            ctk.CTkLabel(title_frame, text=self.project["github_url"], font=FONT_SM,
                          text_color=ACCENT).pack(anchor="w")
        self.tab_var = tk.StringVar(value="tasks")
        tab_bar = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0)
        tab_bar.pack(fill="x")
        tab_inner = ctk.CTkFrame(tab_bar, fg_color="transparent")
        tab_inner.pack(padx=24)
        for tab, label in [("tasks", "Tarefas"), ("notes", "Notas"), ("ai", "IA")]:
            btn = ctk.CTkButton(tab_inner, text=label, font=FONT_SM,
                                  fg_color="transparent", text_color=TEXT2,
                                  hover_color=CARD, corner_radius=0, height=40,
                                  command=lambda t=tab: self._switch_tab(t))
            btn.pack(side="left", padx=4)
        self.content = ctk.CTkFrame(self, fg_color=BG)
        self.content.pack(fill="both", expand=True)
        self._switch_tab("tasks")
    def _switch_tab(self, tab):
        for w in self.content.winfo_children():
            w.destroy()
        self.tab_var.set(tab)
        if tab == "tasks":
            TasksPanel(self.content, self.project).pack(fill="both", expand=True)
        elif tab == "notes":
            NotesPanel(self.content, self.project).pack(fill="both", expand=True)
        elif tab == "ai":
            AIPanel(self.content, self.project).pack(fill="both", expand=True)
class TasksPanel(ctk.CTkFrame):
    def __init__(self, master, project):
        super().__init__(master, fg_color=BG)
        self.project = project
        self._build()
    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=12)
        SectionLabel(toolbar, "Tarefas").pack(side="left")
        self.filter_var = ctk.StringVar(value="all")
        filter_btn = ctk.CTkSegmentedButton(toolbar, values=["all", "todo", "doing", "done"],
                                             variable=self.filter_var, fg_color=BG3,
                                             selected_color=ACCENT, text_color=TEXT,
                                             font=FONT_SM, command=self._refresh)
        filter_btn.pack(side="left", padx=12)
        HoverButton(toolbar, text="+ Tarefa", hover_color=ACCENT, fg_color=ACCENT,
                     text_color="white", font=FONT_SM, command=self._add_task).pack(side="right")
        total, done = db.get_task_stats(self.project["id"])
        pct = int(done / total * 100) if total > 0 else 0
        prog_card = CardFrame(self)
        prog_card.pack(fill="x", padx=24, pady=(0, 12))
        prog_inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(prog_inner, text=f"Progresso: {done}/{total} tarefas ({pct}%)",
                      font=FONT_BODY, text_color=TEXT).pack(side="left")
        bar_bg = ctk.CTkFrame(prog_inner, fg_color=BG3, corner_radius=6, height=10)
        bar_bg.pack(side="right", fill="x", expand=True, padx=(16, 0))
        if pct > 0:
            bar_fg = ctk.CTkFrame(bar_bg, fg_color=SUCCESS if pct == 100 else ACCENT,
                                   corner_radius=6, height=10)
            bar_fg.place(relwidth=pct / 100, relheight=1)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24)
        self._refresh()
    def _refresh(self, *_):
        for w in self.scroll.winfo_children():
            w.destroy()
        tasks = db.get_tasks(self.project["id"])
        f = self.filter_var.get()
        if f != "all":
            tasks = [t for t in tasks if t["status"] == f]
        if not tasks:
            ctk.CTkLabel(self.scroll, text="Nenhuma tarefa encontrada.",
                          font=FONT_BODY, text_color=TEXT3).pack(pady=40)
            return
        for task in tasks:
            TaskRow(self.scroll, task, self._refresh).pack(fill="x", pady=3)
    def _add_task(self):
        def save(title, desc, priority):
            db.add_task(self.project["id"], title, desc, priority)
            self._refresh()
        AddTaskDialog(self, save)
class TaskRow(ctk.CTkFrame):
    def __init__(self, master, task: dict, on_change):
        super().__init__(master, fg_color=CARD, corner_radius=10, border_width=1,
                          border_color=BORDER)
        self.task = task
        self.on_change = on_change
        color_bar = ctk.CTkFrame(self, fg_color=PRIORITY_COLORS.get(task["priority"], TEXT3),
                                  width=4, corner_radius=10)
        color_bar.pack(side="left", fill="y", padx=(0, 0))
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x")
        done_var = tk.BooleanVar(value=task["status"] == "done")
        cb = ctk.CTkCheckBox(row1, text="", variable=done_var, fg_color=SUCCESS,
                               width=20, command=lambda: self._toggle_done(done_var.get()))
        cb.pack(side="left")
        title_color = TEXT3 if task["status"] == "done" else TEXT
        ctk.CTkLabel(row1, text=task["title"], font=FONT_BODY,
                      text_color=title_color, anchor="w").pack(side="left", padx=8, fill="x", expand=True)
        Tag(row1, task["priority"], PRIORITY_COLORS.get(task["priority"], TEXT3)).pack(side="right", padx=2)
        Tag(row1, task["status"], STATUS_COLORS.get(task["status"], TEXT3)).pack(side="right", padx=2)
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x", pady=(4, 0))
        if task["status"] != "doing":
            HoverButton(actions, text="Em progresso", hover_color=ACCENT, height=24,
                         font=FONT_SM, fg_color=BG3,
                         command=lambda: self._set_status("doing")).pack(side="left", padx=(0, 4))
        HoverButton(actions, text="✕ Remover", hover_color=DANGER, height=24,
                     font=FONT_SM, fg_color=BG3,
                     command=self._delete).pack(side="left")
        if task.get("description"):
            ctk.CTkLabel(content, text=task["description"], font=FONT_SM,
                          text_color=TEXT3, anchor="w").pack(anchor="w")
        self.bind("<Enter>", lambda e: self.configure(border_color=ACCENT))
        self.bind("<Leave>", lambda e: self.configure(border_color=BORDER))
    def _toggle_done(self, val):
        db.update_task(self.task["id"], status="done" if val else "todo")
        self.on_change()
    def _set_status(self, status):
        db.update_task(self.task["id"], status=status)
        self.on_change()
    def _delete(self):
        if messagebox.askyesno("Remover", f"Remover tarefa '{self.task['title']}'?"):
            db.delete_task(self.task["id"])
            self.on_change()
class NotesPanel(ctk.CTkFrame):
    def __init__(self, master, project):
        super().__init__(master, fg_color=BG)
        self.project = project
        self._build()
    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=12)
        SectionLabel(toolbar, "Notas").pack(side="left")
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)
        left = CardFrame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(left, text="Notas salvas", font=FONT_H3,
                      text_color=TEXT2).pack(padx=12, pady=8, anchor="w")
        self.note_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.note_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        right = CardFrame(main)
        right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="Nova nota", font=FONT_H3,
                      text_color=TEXT2).pack(padx=12, pady=8, anchor="w")
        self.editor = ctk.CTkTextbox(right, fg_color=BG3, border_color=BORDER,
                                      text_color=TEXT, font=FONT_MONO, border_width=1)
        self.editor.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        HoverButton(right, text="Salvar Nota", hover_color=ACCENT, fg_color=ACCENT,
                     text_color="white", command=self._save_note).pack(padx=12, pady=(0, 12))
        self._refresh_notes()
    def _refresh_notes(self):
        for w in self.note_scroll.winfo_children():
            w.destroy()
        notes = db.get_notes(self.project["id"])
        if not notes:
            ctk.CTkLabel(self.note_scroll, text="Nenhuma nota.", text_color=TEXT3,
                          font=FONT_SM).pack(pady=20)
            return
        for note in notes:
            card = CardFrame(self.note_scroll, fg_color=BG3)
            card.pack(fill="x", pady=3)
            preview = note["content"][:80] + "..." if len(note["content"]) > 80 else note["content"]
            ctk.CTkLabel(card, text=preview, font=FONT_SM, text_color=TEXT,
                          wraplength=200, justify="left", anchor="w").pack(padx=10, pady=(6, 2), anchor="w")
            ctk.CTkLabel(card, text=note["created_at"][:16], font=FONT_SM,
                          text_color=TEXT3).pack(padx=10, anchor="w")
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=(2, 6))
            HoverButton(row, text="Ver", hover_color=ACCENT, height=24, font=FONT_SM,
                         command=lambda n=note: self._view_note(n)).pack(side="left", padx=(0, 4))
            HoverButton(row, text="✕", hover_color=DANGER, width=28, height=24, font=FONT_SM,
                         command=lambda nid=note["id"]: self._delete_note(nid)).pack(side="left")
    def _view_note(self, note):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", note["content"])
    def _save_note(self):
        content = self.editor.get("1.0", "end").strip()
        if content:
            db.add_note(self.project["id"], content)
            self.editor.delete("1.0", "end")
            self._refresh_notes()
    def _delete_note(self, note_id):
        db.delete_note(note_id)
        self._refresh_notes()
class AIPanel(ctk.CTkFrame):
    def __init__(self, master, project):
        super().__init__(master, fg_color=BG)
        self.project = project
        self._build()
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=12)
        SectionLabel(header, "Assistente IA").pack(side="left")
        provider = db.get_setting("ai_provider", "gemini")
        model = db.get_setting("ollama_model", "phi3:mini") if provider == "ollama" else "Gemini Flash"
        Tag(header, f"{provider} · {model}", ACCENT).pack(side="left", padx=8)
        HoverButton(header, text="Limpar", hover_color=DANGER, fg_color=BG3,
                     font=FONT_SM, height=28,
                     command=self._clear_chat).pack(side="right")
        quick = ctk.CTkFrame(self, fg_color="transparent")
        quick.pack(fill="x", padx=24, pady=(0, 8))
        prompts = [
            ("📋 Criar tarefas", "Analise este projeto e crie uma lista de tarefas prioritárias que eu deveria fazer agora."),
            ("🔍 Revisar status", "Me dê um resumo do status atual do projeto e o que falta para finalizar."),
            ("💡 Próximos passos", "Quais são os próximos passos mais importantes para avançar neste projeto?"),
            ("🐛 Problemas comuns", "Quais problemas ou bugs comuns eu deveria verificar neste tipo de projeto?"),
        ]
        for label, prompt in prompts:
            HoverButton(quick, text=label, hover_color=ACCENT, fg_color=BG3,
                         font=FONT_SM, height=30, text_color=TEXT2,
                         command=lambda p=prompt: self._quick_send(p)).pack(side="left", padx=(0, 6))
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color=BG2, corner_radius=8)
        self.chat_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        input_frame = CardFrame(self)
        input_frame.pack(fill="x", padx=24, pady=(0, 16))
        self.input_box = ctk.CTkTextbox(input_frame, height=70, fg_color=BG3,
                                         border_color=BORDER, text_color=TEXT,
                                         font=FONT_BODY, border_width=0)
        self.input_box.pack(fill="x", padx=8, pady=8)
        self.input_box.bind("<Control-Return>", self._send)
        btn_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(btn_row, text="Ctrl+Enter para enviar",
                      font=FONT_SM, text_color=TEXT3).pack(side="left")
        self.send_btn = HoverButton(btn_row, text="Enviar →", hover_color=ACCENT,
                                     fg_color=ACCENT, text_color="white",
                                     font=FONT_SM, command=self._send)
        self.send_btn.pack(side="right")
        history = db.get_chat_history(self.project["id"])
        for msg in history:
            self._render_message(msg["role"], msg["content"])
    def _render_message(self, role, content):
        is_user = role == "user"
        bubble = ctk.CTkFrame(self.chat_scroll,
                               fg_color=CARD2 if is_user else CARD,
                               corner_radius=10)
        bubble.pack(fill="x", pady=4,
                    padx=(60, 0) if is_user else (0, 60),
                    anchor="e" if is_user else "w")
        label_text = "Você" if is_user else "IA"
        label_color = ACCENT if is_user else SUCCESS
        ctk.CTkLabel(bubble, text=label_text, font=FONT_SM,
                      text_color=label_color).pack(padx=12, pady=(6, 0), anchor="w")
        msg_label = ctk.CTkLabel(bubble, text=content, font=FONT_BODY,
                                  text_color=TEXT, wraplength=480,
                                  justify="left", anchor="w")
        msg_label.pack(padx=12, pady=(2, 8), fill="x")
        if role == "assistant" and "- " in content:
            tasks = ai.parse_ai_tasks(content)
            if tasks:
                def add_tasks():
                    for t in tasks:
                        db.add_task(self.project["id"], t["title"], priority=t["priority"])
                    messagebox.showinfo("Tarefas", f"{len(tasks)} tarefas adicionadas ao projeto!")
                HoverButton(bubble, text=f"+ Adicionar {len(tasks)} tarefas ao projeto",
                             hover_color=SUCCESS, fg_color=BG3,
                             text_color=SUCCESS, font=FONT_SM, height=28,
                             command=add_tasks).pack(padx=12, pady=(0, 8), anchor="w")
        return bubble
    def _scroll_bottom(self):
        self.chat_scroll._parent_canvas.yview_moveto(1.0)
    def _send(self, event=None):
        msg = self.input_box.get("1.0", "end").strip()
        if not msg:
            return
        self.input_box.delete("1.0", "end")
        self._render_message("user", msg)
        db.add_chat_message(self.project["id"], "user", msg)
        self.after(50, self._scroll_bottom)
        self.send_btn.configure(state="disabled", text="...")
        ai_bubble = ctk.CTkFrame(self.chat_scroll, fg_color=CARD, corner_radius=10)
        ai_bubble.pack(fill="x", pady=4, padx=(0, 60), anchor="w")
        ctk.CTkLabel(ai_bubble, text="IA", font=FONT_SM, text_color=SUCCESS).pack(
            padx=12, pady=(6, 0), anchor="w")
        resp_label = ctk.CTkLabel(ai_bubble, text="▋", font=FONT_BODY,
                                   text_color=TEXT, wraplength=480,
                                   justify="left", anchor="w")
        resp_label.pack(padx=12, pady=(2, 8), fill="x")
        def stream():
            tasks = db.get_tasks(self.project["id"])
            notes = db.get_notes(self.project["id"])
            context = ai.build_project_context(self.project, tasks, notes)
            system = ai.SYSTEM_PROMPT.format(context=context)
            history = db.get_chat_history(self.project["id"], limit=20)
            messages = [{"role": m["role"], "content": m["content"]} for m in history]
            client = ai.get_ai_client()
            full_response = ""
            for chunk in client.stream_chat(messages, system):
                full_response += chunk
                self.after(0, lambda t=full_response: resp_label.configure(text=t + "▋"))
                self.after(0, self._scroll_bottom)
            self.after(0, lambda: resp_label.configure(text=full_response))
            db.add_chat_message(self.project["id"], "assistant", full_response)
            parsed = ai.parse_ai_tasks(full_response)
            if parsed:
                def add_tasks():
                    for t in parsed:
                        db.add_task(self.project["id"], t["title"], priority=t["priority"])
                    messagebox.showinfo("Tarefas", f"{len(parsed)} tarefas adicionadas!")
                self.after(0, lambda: HoverButton(
                    ai_bubble, text=f"+ Adicionar {len(parsed)} tarefas",
                    hover_color=SUCCESS, fg_color=BG3,
                    text_color=SUCCESS, font=FONT_SM, height=28,
                    command=add_tasks).pack(padx=12, pady=(0, 8), anchor="w"))
            self.after(0, lambda: self.send_btn.configure(state="normal", text="Enviar →"))
            self.after(0, self._scroll_bottom)
        threading.Thread(target=stream, daemon=True).start()
    def _quick_send(self, prompt):
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", prompt)
        self._send()
    def _clear_chat(self):
        if messagebox.askyesno("Limpar", "Limpar histórico de conversa?"):
            db.clear_chat_history(self.project["id"])
            for w in self.chat_scroll.winfo_children():
                w.destroy()
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Project Manager")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        db.init_db()
        self._current_view = None
        self._build_sidebar()
        self._build_main()
        self._show_projects()
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=BG2, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=16, pady=(20, 8))
        ctk.CTkLabel(logo, text="◈", font=("Inter", 28), text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(logo, text="Projects", font=FONT_H2, text_color=TEXT).pack(side="left", padx=8)
        ctk.CTkFrame(self.sidebar, fg_color=BORDER, height=1).pack(fill="x", padx=16, pady=8)
        nav_items = [
            ("🗂  Projetos", self._show_projects),
            ("+ Novo Projeto", self._new_project),
            ("⬇  Importar GitHub", self._import_github),
        ]
        for label, cmd in nav_items:
            HoverButton(self.sidebar, text=label, hover_color=CARD,
                         fg_color="transparent", text_color=TEXT2,
                         font=FONT_BODY, anchor="w", height=40,
                         command=cmd).pack(fill="x", padx=8, pady=2)
        ctk.CTkFrame(self.sidebar, fg_color=BORDER, height=1).pack(fill="x", padx=16, pady=8)
        HoverButton(self.sidebar, text="⚙  Configurações", hover_color=CARD,
                     fg_color="transparent", text_color=TEXT2,
                     font=FONT_BODY, anchor="w", height=40,
                     command=self._open_settings).pack(fill="x", padx=8, pady=2, side="bottom")
        self.ai_label = ctk.CTkLabel(self.sidebar, text="", font=FONT_SM, text_color=TEXT3)
        self.ai_label.pack(side="bottom", pady=4)
        self._update_ai_label()
    def _update_ai_label(self):
        provider = db.get_setting("ai_provider", "gemini")
        model = db.get_setting("ollama_model", "phi3:mini") if provider == "ollama" else "gemini-flash"
        self.ai_label.configure(text=f"IA: {provider} · {model}")
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)
    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()
    def _show_projects(self):
        self._clear_main()
        projects = db.get_projects()
        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(20, 4))
        ctk.CTkLabel(header, text="Projetos", font=FONT_H1, text_color=TEXT).pack(side="left")
        ctk.CTkLabel(header, text=f"{len(projects)} projetos",
                      font=FONT_BODY, text_color=TEXT3).pack(side="left", padx=12)
        search_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        search_frame.pack(fill="x", padx=28, pady=(0, 12))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_projects(projects))
        ctk.CTkEntry(search_frame, placeholder_text="Buscar projetos...",
                      textvariable=self.search_var, fg_color=BG3,
                      border_color=BORDER, text_color=TEXT, height=38,
                      font=FONT_BODY).pack(fill="x")
        self.proj_scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.proj_scroll.pack(fill="both", expand=True, padx=28)
        if not projects:
            empty = ctk.CTkFrame(self.proj_scroll, fg_color="transparent")
            empty.pack(expand=True, pady=80)
            ctk.CTkLabel(empty, text="◈", font=("Inter", 48), text_color=TEXT3).pack()
            ctk.CTkLabel(empty, text="Nenhum projeto ainda.",
                          font=FONT_H2, text_color=TEXT3).pack(pady=8)
            ctk.CTkLabel(empty, text="Importe do GitHub ou crie um novo projeto.",
                          font=FONT_BODY, text_color=TEXT3).pack()
            HoverButton(empty, text="⬇ Importar do GitHub", hover_color=ACCENT,
                         fg_color=ACCENT, text_color="white", font=FONT_BODY,
                         command=self._import_github).pack(pady=16)
            return
        self._render_project_grid(projects)
    def _filter_projects(self, projects):
        query = self.search_var.get().lower()
        filtered = [p for p in projects if query in p["name"].lower() or query in (p.get("description") or "").lower()]
        self._render_project_grid(filtered)
    def _render_project_grid(self, projects):
        for w in self.proj_scroll.winfo_children():
            w.destroy()
        if not projects:
            ctk.CTkLabel(self.proj_scroll, text="Nenhum resultado.",
                          font=FONT_BODY, text_color=TEXT3).pack(pady=40)
            return
        grid = ctk.CTkFrame(self.proj_scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        cols = 3
        for i, project in enumerate(projects):
            col = i % cols
            row = i // cols
            grid.columnconfigure(col, weight=1)
            card = ProjectCard(grid, project,
                                on_click=self._open_project,
                                on_delete=self._delete_project)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
    def _open_project(self, project):
        self._clear_main()
        ProjectView(self.main, project, on_back=self._show_projects).pack(fill="both", expand=True)
    def _delete_project(self, project):
        if messagebox.askyesno("Remover", f"Remover projeto '{project['name']}'? Isso apagará todas as tarefas e notas."):
            db.delete_project(project["id"])
            self._show_projects()
    def _new_project(self):
        name = simpledialog.askstring("Novo Projeto", "Nome do projeto:", parent=self)
        if name and name.strip():
            db.add_project(name.strip())
            self._show_projects()
    def _import_github(self):
        ImportReposDialog(self, on_import=self._show_projects)
    def _open_settings(self):
        SettingsDialog(self, on_save=self._update_ai_label)
def main():
    app = App()
    app.mainloop()
if __name__ == "__main__":
    main()
