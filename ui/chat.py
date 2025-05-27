# ui/chat.py

import os
import streamlit as st
from PIL import Image
from rag.llm_loader import load_llm
from rag.qa_chain import build_qa_chain
from rag.embeddings import load_embeddings
from logic import process_query
from multi_faiss import MultiFAISSRetriever
from historico_embed import render_historico
import logging

from rag.prompt import get_saved_prompts, save_prompt
from langchain_community.vectorstores import FAISS

def render_header():
    img = Image.open("ppa.png")
    st.image(img.resize((150, 75)))
    st.title("🧐 Pergunte ao PPA")

def render_prompt_editor():
    st.subheader("🛠️ Prompts personalizados")
    prompts = get_saved_prompts()
    prompt_names = list(prompts.keys()) or ["default"]

    prompt_selecionado = st.selectbox("Escolha um prompt para editar ou criar:", prompt_names + ["<novo>"], key="prompt_selector")
    logging.info(f"Selecionado prompt {prompt_selecionado} para edição")
    st.session_state["prompt_selecionado"] = prompt_selecionado

    if prompt_selecionado == "<novo>":
        novo_nome = st.text_input("Nome do novo prompt:", key="novo_nome_prompt")
        prompt_conteudo = ""
    else:
        novo_nome = prompt_selecionado
        prompt_conteudo = prompts.get(prompt_selecionado, "")

    edited_prompt = st.text_area(
        "Conteúdo do prompt (use {context} e {question}):",
        value=prompt_conteudo,
        height=400,
        key="prompt_editor"        
    )

    if st.button("💾 Salvar prompt"):
        if novo_nome.strip() == "":
            st.warning("Nome do prompt não pode estar vazio.")
        else:
            save_prompt(novo_nome.strip(), edited_prompt)
            st.session_state["prompt_template"] = edited_prompt
            st.session_state["prompt_name"] = novo_nome
            st.success(f"Prompt '{novo_nome}' salvo com sucesso!")
            logging.info(f"Prompt '{novo_nome}' salvo com sucesso!")

    st.session_state["prompt_template"] = edited_prompt

def render_chat():
    embed_model = st.session_state["embedding_model"]
    modelo_llm = st.session_state["modelo_llm"]
    faiss_paths = st.session_state.get("faiss_selecionados", [])
    vectorstores = []

    for path in faiss_paths:
        index_file = os.path.join(path, "index.faiss")
        if os.path.exists(index_file):
            embeddings = load_embeddings(embed_model)
            try:
                store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
                vectorstores.append(store)
            except Exception as e:
                st.warning(f"Erro ao carregar índice FAISS em {path}: {e}")

    if not vectorstores:
        st.warning("⚠️ Nenhum índice FAISS válido selecionado.")
        logging.info("⚠️ Nenhum índice FAISS válido selecionado.")
        st.stop()

    retrievers = [
        store.as_retriever(search_kwargs={"k": st.session_state["retriever_k"]})
        for store in vectorstores
    ]

    k=st.session_state["retriever_k"]
    retriever = MultiFAISSRetriever(retrievers=retrievers, k=st.session_state["retriever_k"])
    logging.info(f"retriever usando k {k}")
    
    # quando estiver em condições de buscar por categorias
    #retriever = vectorstore.as_retriever(search_kwargs={
    #    "k": 8,
    #    "filter": {"categoria": "artigo"}  # Exemplo: só buscar artigos
    #})

    prompt_selecionado = st.session_state.get("prompt_selecionado")
    llm = load_llm(modelo_llm, temperature=st.session_state["llm_temperature"])
    qa_chain = build_qa_chain(retriever, llm, st.session_state.get("prompt_selecionado"))
    logging.info(f"promtp_selecionado {prompt_selecionado}")

    # Primeiro renderiza o histórico do chat
    for role, msg in st.session_state.chat_history:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(msg)

    # Depois renderiza a caixa de entrada
    with st.form("chat-form", clear_on_submit=True):
        user_input = st.text_input("Digite sua pergunta:", value="")
        submitted = st.form_submit_button("Enviar")

    if submitted and user_input:
        resposta, fontes, elapsed = process_query(user_input, qa_chain)
        st.session_state["resposta_gerada"] = True  # marcador opcional
        st.rerun()  # força recarregamento com novo estado


    if "last_contexts" in st.session_state:
        with st.expander("📚 Trechos usados na resposta"):
            for doc in st.session_state.last_contexts:
                source = doc.metadata.get("origem", "desconhecido")
                nome = os.path.basename(source)
                tipo = os.path.splitext(nome)[1].replace(".", "").upper()
                st.markdown(f"**Fonte:** `{nome}` ({tipo})")
                st.markdown(doc.page_content.strip())
                st.markdown("---")

    if st.button("🧹 Limpar conversa"):
        st.session_state.chat_history = []
        st.session_state.last_contexts = []
        st.rerun()

    if st.session_state.chat_history:
        for role, msg in reversed(st.session_state.chat_history):
            if role == "bot":
                st.download_button("📅 Baixar última resposta", msg, file_name="resposta.txt")
                break

    if st.session_state.get("reranker_comparacao"):
        comparacao = st.session_state["reranker_comparacao"]
        with st.expander("🔬 Comparação com Reranker (Antes vs Depois)"):
            st.markdown("### 🟡 Antes do Reranker")
            for i, doc in enumerate(comparacao["antes"], 1):
                source = doc.metadata.get("origem", "desconhecido")
                nome = os.path.basename(source)
                st.markdown(f"**[{i}] Fonte:** `{nome}`")
                st.markdown(doc.page_content[:500].strip() + "...")
                st.markdown("---")

            st.markdown("### 🟢 Depois do Reranker")
            for i, doc in enumerate(comparacao["depois"], 1):
                source = doc.metadata.get("origem", "desconhecido")
                nome = os.path.basename(source)
                st.markdown(f"**[{i}] Fonte:** `{nome}`")
                st.markdown(doc.page_content[:500].strip() + "...")
                st.markdown("---")



def render_interface():
    from ui.sidebar import render_sidebar
    render_sidebar()
    render_header()

    container = st.container()
    with container:
        col1, col2 = st.columns([2, 1], gap="large")
        with col1:
            render_prompt_editor()
            render_chat()
        with col2:
            render_historico()
