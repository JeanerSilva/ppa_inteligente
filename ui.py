# app/ui.py
import os
import time
import logging
import streamlit as st
from PIL import Image
from settings import RETRIEVER_TOP_K, EMBEDDING_OPTIONS, TEMPERATURE
from rag.vectorstore import load_vectorstore
from rag.llm_loader import load_llm
from rag.qa_chain import build_qa_chain
from rag.prompt import get_saved_prompts, save_prompt
from logic import process_query
from handlers.file_handler import handle_upload_and_reindex, display_indexed_files

def render_interface():
    render_header()
    render_prompt_editor()
    render_sidebar()
    render_chat()

def render_header():
    img = Image.open("ppa.png")
    st.image(img.resize((150, 75)))
    st.title("🧐 Pergunte ao PPA")

def render_prompt_editor():
    st.subheader("🛠️ Prompts personalizados")
    prompts = get_saved_prompts()
    prompt_names = list(prompts.keys()) or ["default"]

    prompt_selecionado = st.selectbox("Escolha um prompt para editar ou criar:", prompt_names + ["<novo>"], key="prompt_selector")

    if prompt_selecionado == "<novo>":
        novo_nome = st.text_input("Nome do novo prompt:", key="novo_nome_prompt")
        prompt_conteudo = ""
        logging.info("Criando novo prompt.")

    else:
        novo_nome = prompt_selecionado
        prompt_conteudo = prompts.get(prompt_selecionado, "")

    edited_prompt = st.text_area(
        "Conteúdo do prompt (use {context} e {question}):",
        value=prompt_conteudo,
        height=400,
        key="prompt_editor"        
    )
    logging.info("Editando prompt: %s", novo_nome)

    if st.button("💾 Salvar prompt"):
        if novo_nome.strip() == "":
            st.warning("Nome do prompt não pode estar vazio.")
            logging.info("Nome do prompt vazio.")
        else:
            save_prompt(novo_nome.strip(), edited_prompt)
            st.session_state["prompt_template"] = edited_prompt
            st.session_state["prompt_name"] = novo_nome
            st.success(f"Prompt '{novo_nome}' salvo com sucesso!")
            #st.rerun()

    st.session_state["prompt_template"] = edited_prompt

def render_sidebar():
    st.sidebar.markdown("⚙️ **Configurações**")
    logging.info("Iniciando configuração da interface.")

     # Sidebar: k (quantidade de trechos)
    st.sidebar.markdown("📑 **Número de trechos (k)**")
    st.sidebar.markdown("🔍 1 = Mais específico | 20 = Mais genérico")
    st.session_state["retriever_k"] = st.sidebar.slider(
        label="Número de trechos a considerar:",
        min_value=1,
        max_value=20,
        value=st.session_state.get("retriever_k", RETRIEVER_TOP_K),
        step=1
    )

    # Sidebar: Temperatura do modelo
    st.sidebar.markdown("🌡️ **Temperatura**")
    st.sidebar.markdown("🧊 0.0 = Mais direto | 🔥 1.0 = Mais criativo")
    st.session_state["llm_temperature"] = st.sidebar.slider(
        "Temperatura da resposta:",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("llm_temperature", TEMPERATURE),
        step=0.1
    )


    st.sidebar.markdown("🧠 **Modelo de linguagem**")
    modelo_llm = st.sidebar.radio("Modo de execução:", ["Ollama (servidor)", "OpenAI (API)"])
    st.session_state["modelo_llm"] = modelo_llm
    logging.info("Modelo de linguagem selecionado: %s", modelo_llm)

    st.sidebar.markdown("🧬 **Modelo de embedding**")
    embed_model_label = st.sidebar.selectbox("Escolha o modelo:", list(EMBEDDING_OPTIONS.keys()))
    embed_model_name = EMBEDDING_OPTIONS[embed_model_label]
    st.session_state["embedding_model"] = embed_model_name
    logging.info("Modelo de embedding selecionado: %s", embed_model_name)

    handle_upload_and_reindex(embed_model_name)
    display_indexed_files()

def render_chat():
    embed_model = st.session_state["embedding_model"]
    modelo_llm = st.session_state["modelo_llm"]

    vectorstore = load_vectorstore(embed_model)
    if not vectorstore:
        st.warning("⚠️ Nenhum índice encontrado. Reindexe primeiro.")
        st.stop()

    llm = load_llm(modelo_llm, temperature=st.session_state["llm_temperature"])

    qa_chain = build_qa_chain(vectorstore, llm, st.session_state.get("prompt_name", "teste"))

    if not qa_chain:
        st.warning("⚠️ A chain não está carregada.")
        logging.info("⚠️ A chain não está carregada.")
        st.stop()

    with st.form("chat-form", clear_on_submit=True):
        user_input = st.text_input("Digite sua pergunta:", value="")
        submitted = st.form_submit_button("Enviar")

    if submitted and user_input:
        resposta, fontes, elapsed = process_query(user_input, qa_chain)
        st.sidebar.success(f"⏱️ Resposta em {elapsed:.2f} segundos")

        with st.expander("🔌 Depuração: Chunks retornados pelo retriever"):
            for doc in fontes:
                st.markdown(doc.page_content)

    for role, msg in st.session_state.chat_history:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(msg)

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
        logging.info("Conversa limpa.")
        st.rerun()

    if st.session_state.chat_history:
        for role, msg in reversed(st.session_state.chat_history):
            if role == "bot":
                st.download_button("📅 Baixar última resposta", msg, file_name="resposta.txt")
                break
