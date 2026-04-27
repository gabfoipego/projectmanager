# ◈ Project Manager — Architecture

## Overview

Project Manager is a desktop application built with Python and CustomTkinter that lets developers manage projects, tasks, and notes with GitHub integration and an AI assistant (Gemini or Ollama).

---

## Tech Stack

| Layer       | Technology                     |
|-------------|-------------------------------|
| UI          | CustomTkinter (Tkinter-based) |
| Database    | SQLite (via `sqlite3`)        |
| AI          | Google Gemini Flash / Ollama  |
| GitHub      | GitHub REST API v3            |
| Language    | Python 3.10+                  |

---

## Module Structure

```
projectmanager/
├── app.py          # UI principal — janelas, cards, painéis
├── database.py     # Camada de dados — SQLite, CRUD
├── ai_client.py    # Clientes de IA — Gemini e Ollama com streaming
├── github_api.py   # Cliente GitHub REST API
├── requirements.txt
└── .env.example
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    app.py (UI Layer)                │
│                                                     │
│  App (CTk root)                                     │
│   ├── Sidebar (navegação)                           │
│   └── Main Area                                     │
│        ├── ProjectsView (grid de cards)             │
│        └── ProjectView (detalhe do projeto)         │
│             ├── TasksPanel                          │
│             ├── NotesPanel                          │
│             └── AIPanel                            │
│                                                     │
│  Dialogs                                            │
│   ├── AddTaskDialog                                 │
│   ├── SettingsDialog                               │
│   └── ImportReposDialog                            │
└──────────┬──────────────┬──────────────────────────┘
           │              │
           ▼              ▼
┌──────────────┐  ┌───────────────┐  ┌──────────────┐
│ database.py  │  │ ai_client.py  │  │ github_api.py│
│              │  │               │  │              │
│ SQLite CRUD  │  │ GeminiAI      │  │ GitHubClient │
│  - projects  │  │ OllamaAI      │  │  - test_auth │
│  - tasks     │  │               │  │  - get_repos │
│  - notes     │  │ get_ai_client │  │  - format... │
│  - chat      │  │ parse_ai_tasks│  │              │
│  - settings  │  │ build_context │  └──────┬───────┘
└──────────────┘  └───────┬───────┘         │
                          │                 │
                          ▼                 ▼
                   ┌─────────────┐  ┌──────────────┐
                   │ Gemini API  │  │  GitHub API  │
                   │ (cloud)     │  │  (cloud)     │
                   └─────────────┘  └──────────────┘
                   ┌─────────────┐
                   │ Ollama      │
                   │ (localhost) │
                   └─────────────┘
```

---

## Data Model (SQLite)

### `projects`
| Campo        | Tipo    | Descrição                            |
|--------------|---------|--------------------------------------|
| `id`         | INTEGER | Chave primária                       |
| `name`       | TEXT    | Nome do projeto                      |
| `description`| TEXT    | Descrição opcional                   |
| `github_url` | TEXT    | URL do repositório                   |
| `local_path` | TEXT    | Caminho local (não usado na UI)      |
| `language`   | TEXT    | Linguagem principal                  |
| `stars`      | INTEGER | Estrelas no GitHub                   |
| `status`     | TEXT    | `active` (padrão)                    |
| `color`      | TEXT    | Cor hex para o card                  |
| `created_at` | TEXT    | ISO datetime                         |
| `updated_at` | TEXT    | ISO datetime (atualizado em tarefas) |

### `tasks`
| Campo          | Tipo    | Descrição                            |
|----------------|---------|--------------------------------------|
| `id`           | INTEGER | Chave primária                       |
| `project_id`   | INTEGER | FK → projects (CASCADE DELETE)       |
| `title`        | TEXT    | Título da tarefa                     |
| `description`  | TEXT    | Detalhe opcional                     |
| `status`       | TEXT    | `todo` / `doing` / `done`            |
| `priority`     | TEXT    | `low` / `medium` / `high`            |
| `created_at`   | TEXT    | ISO datetime                         |
| `completed_at` | TEXT    | Preenchido ao marcar como `done`     |

### `notes`
| Campo        | Tipo    | Descrição                      |
|--------------|---------|-------------------------------|
| `id`         | INTEGER | Chave primária                 |
| `project_id` | INTEGER | FK → projects (CASCADE DELETE) |
| `content`    | TEXT    | Conteúdo livre                 |
| `created_at` | TEXT    | ISO datetime                   |

### `chat_history`
| Campo        | Tipo    | Descrição                      |
|--------------|---------|-------------------------------|
| `id`         | INTEGER | Chave primária                 |
| `project_id` | INTEGER | FK → projects                  |
| `role`       | TEXT    | `user` / `assistant`           |
| `content`    | TEXT    | Conteúdo da mensagem           |
| `created_at` | TEXT    | ISO datetime                   |

### `settings`
| Campo   | Tipo | Descrição                                              |
|---------|------|-------------------------------------------------------|
| `key`   | TEXT | Chave única (`github_token`, `ai_provider`, etc.)     |
| `value` | TEXT | Valor como string                                     |

---

## Key Modules

### `database.py`

Responsável por toda a persistência. Cria o banco em `~/.projectmanager/data.db`.

Funções principais:

| Função                   | Descrição                                     |
|--------------------------|-----------------------------------------------|
| `init_db()`              | Cria todas as tabelas se não existirem        |
| `get_conn()`             | Retorna conexão com `row_factory = Row`       |
| `add_project(...)`       | Insere projeto e retorna o ID                 |
| `get_projects()`         | Lista projetos ordenados por `updated_at`     |
| `update_project(id, **)`| UPDATE dinâmico via kwargs                    |
| `delete_project(id)`    | DELETE em cascade (tasks, notes, chat)        |
| `add_task(...)`          | Insere tarefa e atualiza `updated_at` do proj |
| `update_task(id, **)`   | UPDATE dinâmico; seta `completed_at` se done  |
| `get_task_stats(pid)`   | Retorna `(total, done)` para barra de progresso|
| `get_setting(key, def)` | Busca configuração com fallback               |
| `set_setting(key, val)` | Upsert em `settings`                         |

### `ai_client.py`

Abstrai dois backends de IA com interface comum de streaming.

```python
class GeminiAI:
    def stream_chat(messages, system) -> Generator[str]

class OllamaAI:
    def stream_chat(messages, system) -> Generator[str]
    def list_models() -> list[str]

def get_ai_client() -> GeminiAI | OllamaAI  # factory por setting
def build_project_context(project, tasks, notes) -> str  # contexto para o prompt
def parse_ai_tasks(text) -> list[dict]  # extrai tarefas da resposta da IA
```

**Streaming**: a UI lê os chunks do generator em uma thread separada e atualiza o label via `self.after(0, ...)` para thread-safety no Tkinter.

### `github_api.py`

Cliente REST para a GitHub API v3.

| Método              | Descrição                                      |
|---------------------|------------------------------------------------|
| `test_auth()`       | Testa token com `GET /user`                    |
| `get_repos()`       | Paginação automática de todos os repos do user |
| `get_repo_contents()`| Árvore de arquivos do repo (para contexto IA)|
| `get_file_content()`| Conteúdo de arquivo (base64 decode)           |
| `format_repo()`     | Normaliza dados do repo para o banco           |

`get_lang_color()` retorna cor hex por linguagem para uso nos cards.

### `app.py`

Camada de apresentação pura. Não contém lógica de negócio.

| Componente           | Descrição                                                 |
|----------------------|------------------------------------------------------------|
| `App`                | Janela raiz; gerencia sidebar e área principal            |
| `ProjectCard`        | Card com cor da linguagem, progresso, hover effects       |
| `ProjectView`        | View com tabs: Tarefas / Notas / IA                       |
| `TasksPanel`         | Lista de tarefas com filtros e barra de progresso         |
| `TaskRow`            | Linha de tarefa com checkbox, prioridade e ações          |
| `NotesPanel`         | Editor split: lista à esquerda, editor à direita          |
| `AIPanel`            | Chat com streaming, quick prompts e botão "Adicionar tarefas" |
| `AddTaskDialog`      | Modal para criar tarefa                                   |
| `SettingsDialog`     | Modal para tokens/API keys com toggle Gemini/Ollama       |
| `ImportReposDialog`  | Modal com lista checkboxável de repos do GitHub           |
| `HoverButton`        | CTkButton com hover color customizável                    |
| `CardFrame`          | CTkFrame com estilo de card padrão                        |
| `Tag`                | Label de chip colorido (linguagem, prioridade, status)    |

---

## Threading Model

O Tkinter não é thread-safe. Para chamadas bloqueantes (IA, GitHub), a aplicação usa:

```python
threading.Thread(target=funcao_bloqueante, daemon=True).start()
# dentro da thread:
self.after(0, lambda: widget.configure(...))  # atualização segura da UI
```

Isso evita que a UI trave durante chamadas de rede ou streaming de IA.

---

## Configuration Flow

```
App start
  └─ db.init_db()
  └─ db.get_setting("ai_provider")  →  "gemini" | "ollama"
  └─ db.get_setting("github_token")

SettingsDialog.save()
  └─ db.set_setting("github_token", ...)
  └─ db.set_setting("gemini_key", ...)
  └─ db.set_setting("ai_provider", ...)
  └─ callback → App._update_ai_label()
```

As configurações ficam no SQLite, mas `GEMINI_API_KEY` pode ser sobrescrita via `.env` (python-dotenv).

---

## Potential Improvements

- [ ] **Separação de responsabilidades**: `app.py` acessa `db` e `ai` diretamente — uma camada de serviço reduziria o acoplamento
- [ ] **Sem testes automatizados** — `database.py` e `ai_client.py` são facilmente testáveis com `unittest` e SQLite em memória
- [ ] **`update_project`/`update_task`** usam SQL construído via f-string com kwargs — preferível usar um ORM leve (e.g. SQLModel) para maior segurança
- [ ] **`local_path`** existe no schema mas não é usado na UI
- [ ] **Sem validação de entrada** nos diálogos além de checar campo vazio
- [ ] **Chat history** não tem limite de tokens — pode crescer indefinidamente e exceder o contexto da IA