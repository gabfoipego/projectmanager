import json
import re
import requests
from typing import Generator

import database as db


def get_ai_provider():
    return db.get_setting("ai_provider", "gemini")


def get_ollama_model():
    return db.get_setting("ollama_model", "phi3:mini")


def get_gemini_key():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("GEMINI_API_KEY", db.get_setting("gemini_key", ""))


def build_project_context(project: dict, tasks: list, notes: list) -> str:
    total, done = db.get_task_stats(project["id"])
    progress = f"{done}/{total}" if total > 0 else "0/0"

    tasks_text = ""
    if tasks:
        todo = [t for t in tasks if t["status"] == "todo"]
        doing = [t for t in tasks if t["status"] == "doing"]
        done_tasks = [t for t in tasks if t["status"] == "done"]
        if todo:
            tasks_text += "\nPendentes:\n" + "\n".join(f"  - [{t['priority']}] {t['title']}" for t in todo)
        if doing:
            tasks_text += "\nEm progresso:\n" + "\n".join(f"  - [{t['priority']}] {t['title']}" for t in doing)
        if done_tasks:
            tasks_text += "\nConcluídas:\n" + "\n".join(f"  - ✓ {t['title']}" for t in done_tasks[:5])
    else:
        tasks_text = "\n  (nenhuma tarefa ainda)"

    notes_text = "\n".join(f"  - {n['content'][:100]}" for n in notes[:3]) if notes else "  (nenhuma nota)"

    return f"""Projeto: {project['name']}
Linguagem: {project.get('language', 'Desconhecida')}
Descrição: {project.get('description', 'Sem descrição')}
GitHub: {project.get('github_url', 'N/A')}
Progresso: {progress} tarefas concluídas
Tarefas:{tasks_text}
Notas recentes:
{notes_text}"""

def trim_history(messages: list, max_chars: int = 8000) -> list:
    total = 0
    trimmed = []
    for msg in reversed(messages):
        total += len(msg["content"])
        if total > max_chars:
            break
        trimmed.append(msg)
    return list(reversed(trimmed))

def parse_ai_tasks(text: str) -> list:
    tasks = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^[-•*]\s*(?:\[.\]\s*)?(.+)$', line) or re.match(r'^\d+\.\s+(.+)$', line)
        if not m:
            continue
        title = m.group(1).strip()
        if len(title) <= 5:
            continue
        priority = "medium"
        if any(w in title.lower() for w in ["urgente", "crítico", "importante", "high", "critical"]):
            priority = "high"
        elif any(w in title.lower() for w in ["opcional", "low", "baixa"]):
            priority = "low"
        tasks.append({"title": title, "priority": priority})
    return tasks


class GeminiAI:
    def __init__(self):
        self.key = get_gemini_key()

    def stream_chat(self, messages: list, system: str) -> Generator[str, None, None]:
        if not self.key:
            yield "❌ Chave do Gemini não configurada. Vá em Configurações e adicione sua GEMINI_API_KEY."
            return

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.key)

            messages = trim_history(messages)
            history = []
            for m in messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

            last_msg = messages[-1]["content"] if messages else ""

            response = client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=history + [types.Content(role="user", parts=[types.Part(text=last_msg)])],
                config=types.GenerateContentConfig(system_instruction=system)
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"❌ Erro Gemini: {str(e)}"


class OllamaAI:
    def __init__(self):
        self.model = get_ollama_model()
        self.base_url = db.get_setting("ollama_url", "http://localhost:11434")

    def stream_chat(self, messages: list, system: str) -> Generator[str, None, None]:
        try:
            msgs = [{"role": "system", "content": system}] + trim_history(messages)
            r = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": msgs, "stream": True},
                stream=True,
                timeout=60
            )
            if r.status_code != 200:
                try:
                    detail = r.json().get("error", "")
                except Exception:
                    detail = r.text.strip()[:200]
                if r.status_code == 404 and "not found" in detail.lower():
                    available = self.list_models()
                    if available:
                        yield (f"❌ Modelo '{self.model}' não encontrado no Ollama. "
                               f"Você tem instalado: {', '.join(available)}. "
                               f"Troque em Configurações ou rode: `ollama pull {self.model}`")
                    else:
                        yield f"❌ Modelo '{self.model}' não encontrado no Ollama. Rode: `ollama pull {self.model}`"
                else:
                    yield f"❌ Ollama erro {r.status_code}: {detail or 'verifique se o Ollama está rodando.'}"
                return
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done"):
                            break
                    except Exception:
                        continue
        except requests.exceptions.ConnectionError:
            yield "❌ Não consegui conectar ao Ollama. Rode: `ollama serve`"
        except Exception as e:
            yield f"❌ Erro Ollama: {str(e)}"

    def list_models(self) -> list:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []


def get_ai_client():
    provider = get_ai_provider()
    if provider == "ollama":
        return OllamaAI()
    return GeminiAI()


SYSTEM_PROMPT = """Você é um assistente de gerenciamento de projetos. Você ajuda desenvolvedores a organizar tarefas, entender código, planejar features e resolver problemas.

Quando o usuário pedir para criar tarefas, liste-as em formato de lista com hífens (-).
Seja direto, técnico e útil. Responda em português.

Contexto do projeto atual:
{context}"""
