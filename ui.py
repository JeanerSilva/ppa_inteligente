# app/ui.py
import os
import time
import logging
import streamlit as st
from PIL import Image
from settings import RETRIEVER_TOP_K, EMBEDDING_OPTIONS, TEMPERATURE
from rag.llm_loader import load_llm
from rag.qa_chain import build_qa_chain
from rag.prompt import get_saved_prompts, save_prompt
from logic import process_query
from handlers.file_handler import handle_upload_and_reindex, display_indexed_files
from rag.embeddings import load_embeddings
from langchain_community.vectorstores import FAISS
from multi_faiss import MultiFAISSRetriever

from historico_embed import render_historico  # importe a nova função

def render_interface():
    render_sidebar()  # mantém à esquerda
    render_header()



    # Criar layout com largura máxima
    container = st.container()
    with container:
        col1, col2 = st.columns([2, 1], gap="large")  # coluna principal (chat) mais larga

        with col1:
            render_prompt_editor()
            render_chat()

        with col2:
            render_historico()



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

    if st.button("💾 Salvar prompt"):
        if novo_nome.strip() == "":
            st.warning("Nome do prompt não pode estar vazio.")
        else:
            save_prompt(novo_nome.strip(), edited_prompt)
            st.session_state["prompt_template"] = edited_prompt
            st.session_state["prompt_name"] = novo_nome
            st.success(f"Prompt '{novo_nome}' salvo com sucesso!")

    st.session_state["prompt_template"] = edited_prompt

def render_sidebar():
    st.sidebar.markdown("⚙️ **Configurações**")
    st.session_state["retriever_k"] = st.sidebar.slider(
        label="Número de trechos a considerar:",
        min_value=1,
        max_value=20,
        value=st.session_state.get("retriever_k", RETRIEVER_TOP_K),
        step=1
    )

    st.sidebar.markdown("🌡️ **Temperatura**")
    st.session_state["llm_temperature"] = st.sidebar.slider(
        "Temperatura da resposta:",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("llm_temperature", TEMPERATURE),
        step=0.1
    )

    modelo_llm = st.sidebar.radio("Modo de execução:", ["Ollama (servidor)", "OpenAI (API)"])
    st.session_state["modelo_llm"] = modelo_llm

    embed_model_label = st.sidebar.selectbox("Escolha o modelo:", list(EMBEDDING_OPTIONS.keys()))
    embed_model_name = EMBEDDING_OPTIONS[embed_model_label]
    st.session_state["embedding_model"] = embed_model_name

    # Novidade: seleção de múltiplos índices FAISS
    st.sidebar.markdown("📂 **Índices FAISS disponíveis**")
    base_path = r"C:\SEPLAN\rag_ollama_home\vectors\vectordb_multilingual_e5_large"
    faiss_list = [name for name in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, name))]
    selecionados = st.sidebar.multiselect("Escolha os índices:", faiss_list)
    st.session_state["faiss_selecionados"] = [os.path.join(base_path, nome) for nome in selecionados]

    handle_upload_and_reindex(embed_model_name)
    display_indexed_files()

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
        st.stop()

    retrievers = [
        store.as_retriever(search_kwargs={"k": st.session_state["retriever_k"]})
        for store in vectorstores
    ]

    retriever = MultiFAISSRetriever(retrievers=retrievers, k=st.session_state["retriever_k"])

    llm = load_llm(modelo_llm, temperature=st.session_state["llm_temperature"])
    qa_chain = build_qa_chain(retriever, llm, st.session_state.get("prompt_name", "teste"))

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
        st.rerun()

    if st.session_state.chat_history:
        for role, msg in reversed(st.session_state.chat_history):
            if role == "bot":
                st.download_button("📅 Baixar última resposta", msg, file_name="resposta.txt")
                break
