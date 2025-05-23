import os
import time
import logging
import streamlit as st
from settings import RETRIEVER_TOP_K, EMBEDDING_OPTIONS

from PIL import Image
from rag.vectorstore import load_vectorstore, create_vectorstore
from rag.qa_chain import build_qa_chain
from rag.utils import save_uploaded_files, load_indexed_files
from rag.llm_loader import load_llm
from rag.chat_history import generate_session_id, save_chat
from rag.prompt import get_saved_prompts, save_prompt, get_prompt


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("ppa.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

st.set_page_config(page_title="PPA Inteligente", page_icon="🧐")
logging.info("Aplicativo iniciado.")

img = Image.open("ppa.png")
img_resized = img.resize((150, 75))
st.image(img_resized)
st.title("🧐 Pergunte ao PPA")

# Estado inicial
if "indexed_files" not in st.session_state:
    st.session_state["indexed_files"] = load_indexed_files()
    logging.info("Arquivos indexados carregados do estado inicial.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = generate_session_id()
    logging.info(f"Sessão iniciada: {st.session_state.chat_session_id}")

# Prompt personalizado
st.subheader("🛠️ Prompts personalizados")
prompt_text = get_prompt("teste")


prompts = get_saved_prompts()
prompt_names = list(prompts.keys()) or ["default"]

prompt_selecionado = st.selectbox("Escolha um prompt para editar ou criar:", prompt_names + ["<novo>"], key="prompt_selector")

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
        st.rerun()

# Atualiza para uso no QA
st.session_state["prompt_template"] = edited_prompt


# Sidebar: Configurações
st.sidebar.markdown("⚙️ **Configurações**")
st.session_state["retriever_k"] = st.sidebar.number_input(
    label="Número de trechos a considerar (k)",
    min_value=1,
    max_value=20,
    value=st.session_state.get("retriever_k", RETRIEVER_TOP_K),
    step=1
)

# Sidebar: LLM
st.sidebar.markdown("🧠 **Modelo de linguagem**")
modelo_llm = st.sidebar.radio(
    "Modo de execução:",
    ["Ollama (servidor)", "OpenAI (API)"]
)
st.session_state["modelo_llm"] = modelo_llm
logging.info(f"Modo de execução selecionado: {modelo_llm}")

# Sidebar: Embedding
st.sidebar.markdown("🧬 **Modelo de embedding**")
embed_model_label = st.sidebar.selectbox("Escolha o modelo:", list(EMBEDDING_OPTIONS.keys()))
embed_model_name = EMBEDDING_OPTIONS[embed_model_label]
st.session_state["embedding_model"] = embed_model_name
logging.info(f"Modelo de embedding selecionado: {embed_model_name}")

# Sidebar: Reindexar
if st.sidebar.button("🔁 Reindexar agora"):
    logging.info("Iniciando reindexação manual...")
    try:
        with st.spinner("🔄 Indexando documentos e criando vetor..."):
            db, metrics = create_vectorstore(embed_model_name)
            if db is None:
                st.error("❌ A indexação falhou. Nenhum vetor foi criado.")
            else:
                st.success("✅ Vetor criado com sucesso!")
                st.session_state["index_metrics"] = metrics
    except Exception as e:
        st.error(f"❌ Erro ao criar o vetor: {e}")
        logging.exception("Erro durante criação da base vetorial.")

# Painel de métricas de indexação
if "index_metrics" in st.session_state:
    st.subheader("📊 Métricas da última indexação")

    m = st.session_state["index_metrics"]
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱️ Tempo (s)", f"{m['tempo_total']:.2f}")
    col2.metric("📄 Arquivos", m["arquivos_processados"])
    col3.metric("🔎 Chunks", m["chunks_gerados"])

    st.markdown(f"✅ Sucesso: `{m['sucesso']}` &nbsp;&nbsp;&nbsp;&nbsp; ❌ Falha: `{m['falha']}`")

    with st.expander("📁 Arquivos processados"):
        for f in m["arquivos"]:
            st.markdown(f"- `{f}`")

# Sidebar: arquivos indexados
indexed_files = st.session_state.get("indexed_files", [])
if indexed_files:
    st.sidebar.markdown("📂 **Arquivos indexados:**", unsafe_allow_html=True)
    st.sidebar.markdown(
        "<ul style='padding-left:1.2em;'>"
        + "".join(f"<li style='font-size:0.8em;'>{f}</li>" for f in indexed_files)
        + "</ul>", unsafe_allow_html=True
    )
else:
    st.sidebar.info("Nenhum arquivo indexado.")

# Sidebar: Upload
st.sidebar.header("📄 Enviar documentos")
uploaded_files = st.sidebar.file_uploader(
    "Arquivos: .pdf, .txt, .docx, .xlsx, .html",
    type=["pdf", "txt", "docx", "xlsx", "html"],
    accept_multiple_files=True,
)
if uploaded_files:
    save_uploaded_files(uploaded_files)
    st.sidebar.success("✅ Arquivos enviados com sucesso.")
    logging.info(f"{len(uploaded_files)} arquivos enviados e salvos.")

# Carregar index e LLM
vectorstore = load_vectorstore(embed_model_name)
if not vectorstore:
    st.warning("⚠️ Nenhum índice encontrado para esse modelo. Reindexe primeiro.")
    logging.warning("Nenhum índice encontrado. Solicitação de reindexação.")
    st.stop()

llm = load_llm(modelo_llm)
#qa_chain = build_qa_chain(vectorstore, llm, st.session_state["prompt_template"])
qa_chain = build_qa_chain(vectorstore, llm, st.session_state.get("prompt_name", "teste"))

if not qa_chain:
    st.warning("⚠️ A chain não está carregada.")
    logging.error("Falha ao carregar a chain.")
    st.stop()

# Formulário de pergunta
with st.form("chat-form", clear_on_submit=True):
    user_input = st.text_input("Digite sua pergunta:", value="")
    submitted = st.form_submit_button("Enviar")

if submitted and user_input:
    query = f"query: {user_input}"
    logging.info(f"Pergunta enviada: {user_input}")
    start = time.time()
    result = qa_chain.invoke({"query": query})
    elapsed = time.time() - start

    resposta = result["result"]
    fontes = result["source_documents"]

    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("bot", resposta))
    st.session_state.last_contexts = fontes

    # Metadados da sessão
    chat_metadata = {
        "modelo_llm": modelo_llm,
        "modelo_embedding": embed_model_name,
        "retriever_k": st.session_state["retriever_k"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_chat(
        st.session_state.chat_session_id,
        st.session_state.chat_history,
        metadata=chat_metadata
    )

    logging.info(f"Resposta gerada em {elapsed:.2f} segundos.")
    st.sidebar.success(f"⏱️ Resposta em {elapsed:.2f} segundos")

    with st.expander("🔌 Depuração: Chunks retornados pelo retriever"):
        for doc in fontes:
            st.markdown(doc.page_content)

# Exibição estilo chat
for role, msg in st.session_state.chat_history:
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(msg)

# Fontes da resposta
if "last_contexts" in st.session_state:
    with st.expander("📚 Trechos usados na resposta"):
        for doc in st.session_state.last_contexts:
            source = doc.metadata.get("source", "desconhecido")
            nome = os.path.basename(source)
            tipo = os.path.splitext(nome)[1].replace(".", "").upper()
            st.markdown(f"**Fonte:** `{nome}` ({tipo})")
            st.markdown(doc.page_content.strip())
            st.markdown("---")

# Limpar conversa
if st.button("🧹 Limpar conversa"):
    st.session_state.chat_history = []
    st.session_state.last_contexts = []
    logging.info("Conversa limpa pelo usuário.")
    st.rerun()

# Download da resposta
if st.session_state.chat_history:
    for role, msg in reversed(st.session_state.chat_history):
        if role == "bot":
            st.download_button("📅 Baixar última resposta", msg, file_name="resposta.txt")
            break
