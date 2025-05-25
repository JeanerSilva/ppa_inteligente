# app/historico_embed.py
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

    st.markdown("## 📜 Histórico de Sessões")

    llms = sorted(set(d.get("metadata", {}).get("modelo_llm", "") for d in dados if isinstance(d, dict)))
    embeddings = sorted(set(d.get("metadata", {}).get("modelo_embedding", "") for d in dados if isinstance(d, dict)))

    filtro_llm = st.selectbox("Filtrar por modelo LLM:", ["Todos"] + llms)
    filtro_emb = st.selectbox("Filtrar por embedding:", ["Todos"] + embeddings)

    dados_filtrados = [
        d for d in dados
        if isinstance(d, dict)
        and (filtro_llm == "Todos" or d.get("metadata", {}).get("modelo_llm") == filtro_llm)
        and (filtro_emb == "Todos" or d.get("metadata", {}).get("modelo_embedding") == filtro_emb)
    ]

    if not dados_filtrados:
        st.info("Nenhuma sessão corresponde aos filtros.")
        return

    for sessao in dados_filtrados:
        with st.expander(f"🗂️ Sessão: {sessao.get('session_id', 'ID desconhecido')} — {sessao.get('metadata', {}).get('timestamp', 'Sem data')}"):
            st.markdown(f"**Modelo LLM:** {sessao.get('metadata', {}).get('modelo_llm', 'N/A')}")
            st.markdown(f"**Embedding:** {sessao.get('metadata', {}).get('modelo_embedding', 'N/A')}")
            st.markdown(f"**Retriever K:** {sessao.get('metadata', {}).get('retriever_k', 'N/A')}")
            st.markdown("---")

            for item in sessao.get("chat_history", []):
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    role, msg = item
                elif isinstance(item, dict) and "role" in item and "msg" in item:
                    role = item["role"]
                    msg = item["msg"]
                else:
                    continue

                with st.chat_message("user" if role == "user" else "assistant"):
                    st.markdown(msg)

            safe_json_str = json.dumps(sessao, indent=2, ensure_ascii=False).encode('utf-16', errors='surrogatepass').decode('utf-16')

            st.download_button(
                "📥 Baixar sessão",
                safe_json_str,
                file_name=f"{sessao.get('session_id', 'sessao')}.json"
            )
