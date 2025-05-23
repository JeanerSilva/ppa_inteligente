import os
import json
import streamlit as st

st.set_page_config(page_title="Histórico de Sessões", page_icon="📜")
st.title("📜 Histórico de Sessões de Chat")

# Caminho dos arquivos
SESSIONS_DIR = "chat_sessions"

if not os.path.exists(SESSIONS_DIR):
    st.warning("Nenhuma sessão registrada ainda.")
    st.stop()

# Carrega sessões
arquivos = sorted(os.listdir(SESSIONS_DIR), reverse=True)
dados = []

for nome in arquivos:
    if nome.endswith(".json"):
        with open(os.path.join(SESSIONS_DIR, nome), encoding="utf-8") as f:
            try:
                dados.append(json.load(f))
            except Exception:
                continue

# Filtros
st.sidebar.header("🔎 Filtros")
llms = sorted(set(d["metadata"].get("modelo_llm", "") for d in dados))
embeddings = sorted(set(d["metadata"].get("modelo_embedding", "") for d in dados))

filtro_llm = st.sidebar.selectbox("Filtrar por modelo LLM:", ["Todos"] + llms)
filtro_emb = st.sidebar.selectbox("Filtrar por embedding:", ["Todos"] + embeddings)

# Aplica filtros
dados_filtrados = [
    d for d in dados
    if (filtro_llm == "Todos" or d["metadata"].get("modelo_llm") == filtro_llm)
    and (filtro_emb == "Todos" or d["metadata"].get("modelo_embedding") == filtro_emb)
]

# Interface principal
if not dados_filtrados:
    st.info("Nenhuma sessão corresponde aos filtros.")
else:
    for sessao in dados_filtrados:
        with st.expander(f"🗂️ Sessão: {sessao['session_id']} — {sessao['metadata'].get('timestamp')}"):
            st.markdown(f"**Modelo LLM:** {sessao['metadata'].get('modelo_llm')}")
            st.markdown(f"**Embedding:** {sessao['metadata'].get('modelo_embedding')}")
            st.markdown(f"**Retriever K:** {sessao['metadata'].get('retriever_k')}")
            st.markdown("---")
            for role, msg in sessao["chat_history"]:
                with st.chat_message("user" if role == "user" else "assistant"):
                    st.markdown(msg)
            st.download_button("📥 Baixar sessão", json.dumps(sessao, indent=2, ensure_ascii=False), file_name=f"{sessao['session_id']}.json")
