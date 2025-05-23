# rag/chat_history.py

import os
import json
import uuid
from datetime import datetime

CHAT_DIR = "./chat_sessions"
os.makedirs(CHAT_DIR, exist_ok=True)

def generate_session_id():
    """Gera um ID único baseado em timestamp e UUID curto."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:8]

def save_chat(session_id, chat_history, metadata=None):
    """Salva histórico de chat com metadados opcionais."""
    data = {
        "session_id": session_id,
        "chat_history": chat_history,
        "metadata": metadata or {}
    }
    os.makedirs(CHAT_DIR, exist_ok=True)
    with open(os.path.join(CHAT_DIR, f"{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_chat(session_id):
    """Carrega uma sessão de chat salva, incluindo metadados."""
    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def list_sessions():
    """Lista todos os arquivos de sessão disponíveis (ordenado decrescente)."""
    return sorted([
        fname[:-5] for fname in os.listdir(CHAT_DIR)
        if fname.endswith(".json")
    ], reverse=True)
