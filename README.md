# ◈ Project Manager

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/UI-CustomTkinter-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/IA-Gemini%20%7C%20Ollama-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/DB-SQLite-lightgrey?style=for-the-badge">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=for-the-badge">
</p>

Gerenciador de projetos com IA integrada, importação do GitHub e dark theme.

## Features

- 🗂 **Gerenciamento de projetos** com tarefas, notas e progresso
- ⬇ **Importar do GitHub** — puxa todos os seus repos com um clique
- 🤖 **IA integrada** — Gemini Flash ou modelos locais via Ollama
- 📋 **Tarefas inteligentes** — a IA cria e prioriza tarefas automaticamente
- 💬 **Chat com contexto** — a IA conhece o projeto, tarefas e notas
- 🌑 **Dark theme** com hover effects e design limpo
- 💾 **Persistência local** via SQLite

## Instalação

```bash
git clone https://github.com/seu-usuario/project-manager
cd project-manager

pip install -r requirements.txt

cp .env.example .env
# edite .env e coloque sua GEMINI_API_KEY

python app.py
```

## Configuração

Abra o app e vá em **⚙ Configurações**:

| Campo | Onde obter |
|---|---|
| GitHub Token | github.com/settings/tokens → New token → scope `repo` |
| Gemini API Key | aistudio.google.com → Get API Key (grátis) |
| Ollama Model | `ollama pull phi3:mini` → use `phi3:mini` |

## IA — Gemini vs Ollama

| | Gemini Flash | Ollama (phi3:mini) |
|---|---|---|
| Velocidade | Rápido | Depende do hardware |
| Privacidade | Cloud | 100% local |
| Custo | Grátis (cota generosa) | Grátis |
| Qualidade | Alta | Boa para tarefas simples |

## Uso da IA

A IA tem acesso ao contexto completo do projeto:
- Nome, descrição, linguagem
- Lista de tarefas (pendentes, em progresso, concluídas)
- Notas do projeto
- Progresso geral

Exemplos de prompts:
- *"Crie uma lista de tarefas para implementar autenticação JWT"*
- *"Quais são os próximos passos mais importantes?"*
- *"Revise o status do projeto e me dê um resumo"*

Quando a IA listar tarefas, um botão aparece para adicioná-las automaticamente ao projeto.

## Estrutura

```
.
├── app.py          # UI principal (CustomTkinter)
├── database.py     # SQLite — projetos, tarefas, notas, chat
├── ai_client.py    # Gemini + Ollama com streaming
├── github_api.py   # GitHub REST API
├── requirements.txt
└── .env.example
```

## Licença

MIT
