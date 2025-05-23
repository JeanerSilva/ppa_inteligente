# app/logic.py
import time
import streamlit as st
from rag.chat_history import save_chat

def process_query(user_input, qa_chain):
    logging = st.session_state.get("log", None)

    # Limita a 3 turnos (cada turno = user + bot)
    chat_history = st.session_state.chat_history[-6:]
    history = "\n".join([f"{role}: {msg}" for role, msg in chat_history])
    full_query = f"Histórico:\n{history}\n\nNova pergunta:\n{user_input}"

    start = time.time()
    result = qa_chain.invoke({"query": full_query})
    elapsed = time.time() - start

    resposta = result["result"]
    fontes = result["source_documents"]

    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("bot", resposta))
    st.session_state.last_contexts = fontes

    chat_metadata = {
        "modelo_llm": st.session_state["modelo_llm"],
        "modelo_embedding": st.session_state["embedding_model"],
        "retriever_k": st.session_state["retriever_k"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_chat(
        st.session_state.chat_session_id,
        st.session_state.chat_history,
        metadata=chat_metadata
    )

    return resposta, fontes, elapsed
