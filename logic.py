import time
import logging
import streamlit as st
from rag.chat_history import save_chat
from rag.reranker_local import rerank_local_reranker
from transformers import AutoTokenizer

# Inicializar tokenizer Hugging Face para modelos LLaMA-like
tokenizer = AutoTokenizer.from_pretrained("NousResearch/Llama-2-7b-chat-hf")

def contar_tokens_llama(texto: str) -> int:
    return len(tokenizer.encode(texto))

def process_query(user_input, qa_chain):
    # Recuperar os últimos turnos do histórico
    chat_history = st.session_state.chat_history[-6:]
    history = "\n".join([f"{role}: {msg}" for role, msg in chat_history])
    full_query = f"Histórico:\n{history}\n\nNova pergunta:\n{user_input}"

    logging.info(f"Usuário perguntou: {user_input}")
    start = time.time()

    # Recuperar contexto manualmente
    context_docs = qa_chain.retriever.invoke(user_input)

    context_text = "\n\n".join([doc.page_content for doc in context_docs])

    # Renderizar prompt final
    prompt_template = st.session_state.get("prompt_template", "")
    prompt_final = prompt_template.format(context=context_text, question=user_input)

    # Contar tokens com tokenizador Hugging Face
    total_tokens = contar_tokens_llama(prompt_final)
    token_msg = f"🔢 Tokens estimados enviados à LLM (HuggingFace tokenizer): {total_tokens}"
    logging.info(token_msg)
    st.sidebar.info(token_msg)

    # Geração
    result = qa_chain.invoke({"query": full_query})
    resposta = result["result"]
    fontes = result["source_documents"]

    # Reranker local se ativado
    if st.session_state.get("usar_reranker_debug", False):
        fontes = rerank_local_reranker(user_input, fontes, top_k=st.session_state["retriever_k"])
    else:
        fontes = result["source_documents"]

    elapsed = time.time() - start
    logging.info(f"Resposta gerada em {elapsed:.2f}s")

    # Atualiza o histórico da sessão
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("bot", resposta))
    st.session_state.last_contexts = fontes

    chat_metadata = {
        "modelo_llm": st.session_state["modelo_llm"],
        "modelo_embedding": st.session_state["embedding_model"],
        "retriever_k": st.session_state["retriever_k"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt_template": prompt_template
    }

    save_chat(
        st.session_state.chat_session_id,
        st.session_state.chat_history,
        metadata=chat_metadata
    )

    # DEBUG: mostrar chunks antes e depois do reranker
    if st.session_state.get("usar_reranker_debug", False):
        st.session_state["reranker_comparacao"] = {
            "antes": result["source_documents"],
            "depois": fontes
        }
    else:
        st.session_state["reranker_comparacao"] = None

    return resposta, fontes, elapsed
