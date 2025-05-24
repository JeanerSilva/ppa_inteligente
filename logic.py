import time
import logging
import streamlit as st
from rag.chat_history import save_chat
from rag.reranker_local import rerank_local_reranker 

def process_query(user_input, qa_chain):
    # Recupera os últimos 3 turnos (user + bot) do histórico
    chat_history = st.session_state.chat_history[-6:]
    history = "\n".join([f"{role}: {msg}" for role, msg in chat_history])
    full_query = f"Histórico:\n{history}\n\nNova pergunta:\n{user_input}"

    logging.info(f"Usuário perguntou: {user_input}")

    start = time.time()

    # Etapa de geração com recuperação de contexto
    result = qa_chain.invoke({"query": full_query})
    resposta = result["result"]
    fontes = result["source_documents"]

    # Aplicar rerank com modelo local
    fontes = rerank_local_reranker(user_input, fontes, top_k=st.session_state["retriever_k"])


    elapsed = time.time() - start
    logging.info(f"Resposta gerada em {elapsed:.2f}s")

    # Atualizar histórico
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("bot", resposta))
    st.session_state.last_contexts = fontes

    # Metadados para salvamento do chat
    chat_metadata = {
        "modelo_llm": st.session_state["modelo_llm"],
        "modelo_embedding": st.session_state["embedding_model"],
        "retriever_k": st.session_state["retriever_k"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt_template": st.session_state.get("prompt_template", "")
    }

    save_chat(
        st.session_state.chat_session_id,
        st.session_state.chat_history,
        metadata=chat_metadata
    )

    return resposta, fontes, elapsed
