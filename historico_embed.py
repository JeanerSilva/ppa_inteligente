# historico_embed.py
import os
import json
import streamlit as st

def render_historico():
    SESSIONS_DIR = "chat_sessions"
    if not os.path.exists(SESSIONS_DIR):
        st.warning("Nenhuma sessão registrada ainda.")
        return

    arquivos = sorted(os.listdir(SESSIONS_DIR), reverse=True)
    dados = []

    for nome in arquivos:
        if nome.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, nome), encoding="utf-8") as f:
                try:
                    sessao = json.load(f)
                    if isinstance(sessao, dict):
                        dados.append(sessao)
                except Exception:
                    continue

    st.markdown("### 📜 Histórico de Sessões")
    llms = sorted(set(d.get("metadata", {}).get("modelo_llm", "") for d in dados))
    embeddings = sorted(set(d.get("metadata", {}).get("modelo_embedding", "") for d in dados))

    filtro_llm = st.selectbox("Modelo LLM", ["Todos"] + llms)
    filtro_emb = st.selectbox("Embedding", ["Todos"] + embeddings)

    dados_filtrados = [
        d for d in dados
        if (filtro_llm == "Todos" or d.get("metadata", {}).get("modelo_llm") == filtro_llm)
        and (filtro_emb == "Todos" or d.get("metadata", {}).get("modelo_embedding") == filtro_emb)
    ]

    for sessao in dados_filtrados:
        with st.expander(f"{sessao.get('session_id', 'Sessão')} — {sessao.get('metadata', {}).get('timestamp', '')}"):
            st.markdown(f"**LLM:** {sessao.get('metadata', {}).get('modelo_llm', '')}")
            st.markdown(f"**Embedding:** {sessao.get('metadata', {}).get('modelo_embedding', '')}")
            for item in sessao.get("chat_history", []):
                if isinstance(item, list) and len(item) == 2:
                    st.markdown(f"**{item[0]}**: {item[1]}")
