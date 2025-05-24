import os
import glob
import traceback
import logging
import time
import json
import asyncio
import streamlit as st

from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader, UnstructuredHTMLLoader
)
from langchain.schema import Document
from transformers import AutoTokenizer

from settings import DOCS_PATH, CHUNK_SIZE, CHUNK_OVERLAP, VECTORS_FOLDER
from rag.embeddings import load_embeddings
from rag.utils import save_indexed_files
from langchain.text_splitter import TokenTextSplitter

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def get_vectordb_path(model_name):
    safe_name = model_name.split("/")[-1].replace("-", "_")
    path = f"./{VECTORS_FOLDER}/vectordb_{safe_name}"
    os.makedirs(path, exist_ok=True)
    return path

def get_tokenizer(model_name):
    try:
        return AutoTokenizer.from_pretrained(model_name)
    except RuntimeError as e:
        if "no running event loop" in str(e):
            return asyncio.run(load_tokenizer_async(model_name))
        raise

async def load_tokenizer_async(model_name):
    return AutoTokenizer.from_pretrained(model_name)

def create_vectorstore(model_name):
    start_time = time.time()
    vectordb_path = get_vectordb_path(model_name)

    sidebar_status = st.sidebar.empty()
    sidebar_progress = st.sidebar.progress(0)
    log_display = st.sidebar.empty()
    log_lines = []

    def log_to_streamlit(msg):
        log_lines.append(msg)
        log_display.text("\n".join(log_lines[-20:]))

    log_to_streamlit("🔄 Iniciando reindexação de documentos...")
    logging.info("Iniciando reindexação...")

    docs = []
    files = sorted(glob.glob(f"{DOCS_PATH}/*"))
    total = len(files)
    sucesso, falha = 0, 0

    for i, file in enumerate(files):
        ext = os.path.splitext(file)[1].lower()
        filename = os.path.basename(file)
        sidebar_progress.markdown(f"📄 Processando: `{filename}`")

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file)
                docs.extend(loader.load())

            elif ext == ".txt":
                loader = TextLoader(file, encoding="utf-8")
                docs.extend(loader.load())

            elif ext == ".docx":
                loader = UnstructuredWordDocumentLoader(file)
                docs.extend(loader.load())

            elif ext == ".xlsx":
                loader = UnstructuredExcelLoader(file)
                docs.extend(loader.load())

            elif ext == ".html":
                loader = UnstructuredHTMLLoader(file)
                docs.extend(loader.load())

            elif ext in [".json", ".jsonl"]:
                sidebar_status.markdown(f"📑 Lendo `{filename}`...")
                with open(file, 'r', encoding='utf-8') as f:
                    try:
                        content = json.load(f)
                        if isinstance(content, list):
                            for linha in content:
                                texto = linha.get("text", "")
                                if not texto:
                                    texto = " ".join(str(v) for v in linha.values() if isinstance(v, (str, int, float)))
                                metadados = linha.get("metadata", {})
                                docs.append(Document(page_content=texto, metadata=metadados))
                        elif isinstance(content, dict):
                            texto = content.get("text", "")
                            metadados = content.get("metadata", {})
                            docs.append(Document(page_content=texto, metadata=metadados))
                    except json.JSONDecodeError:
                        f.seek(0)
                        for idx, line in enumerate(f, 1):
                            if line.strip():
                                try:
                                    linha = json.loads(line)
                                    texto = linha.get("text", "")
                                    if not texto:
                                        texto = " ".join(str(v) for v in linha.values() if isinstance(v, (str, int, float)))
                                    metadados = linha.get("metadata", {})
                                    docs.append(Document(page_content=texto, metadata=metadados))
                                except Exception as e:
                                    msg = f"⚠️ Linha {idx} inválida em `{filename}`: {e}"
                                    sidebar_status.markdown(msg)
                                    log_to_streamlit(msg)
                sucesso += 1
                continue
            else:
                continue

            sucesso += 1
        except Exception as e:
            falha += 1
            msg = f"⚠️ Erro ao processar `{filename}`: {e}"
            sidebar_status.markdown(msg)
            log_to_streamlit(msg)
            logging.error(msg)
            logging.debug(traceback.format_exc())

        sidebar_progress.progress((i + 1) / total)

    if not docs:
        sidebar_status.markdown("❌ Nenhum documento válido.")
        log_to_streamlit("Nenhum documento válido.")
        sidebar_progress.empty()
        st.stop()
        return None, {}

    log_to_streamlit("✂️ Tokenizando documentos...")
    sidebar_status.markdown(f"✂️ Fazendo o splitting com o tokenizer do modelo `{model_name}`.")
    tokenizer = get_tokenizer(model_name)

    splitter = TokenTextSplitter.from_huggingface_tokenizer(
        tokenizer=tokenizer,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )


        # Filtrar documentos com conteúdo vazio
    docs = [d for d in docs if d.page_content and d.page_content.strip()]
    log_to_streamlit(f"📄 Documentos válidos após limpeza: {len(docs)}")
    logging.info(f"Documentos válidos após limpeza: {len(docs)}")

    if not docs:
        log_to_streamlit("❌ Nenhum documento com conteúdo válido após limpeza.")
        sidebar_status.markdown("❌ Nenhum documento com conteúdo válido após limpeza.")
        st.stop()

    chunks = splitter.split_documents(docs)

    if not chunks:
        log_to_streamlit("❌ Nenhum chunk foi gerado — verifique o conteúdo dos documentos.")
        sidebar_status.markdown("❌ Nenhum chunk foi gerado.")
        st.stop()


    for chunk in chunks:
        chunk.page_content = f"passage: {chunk.page_content.strip()}"

    log_to_streamlit(f"📦 Gerando embeddings com modelo {model_name}...")
    sidebar_status.markdown(f"📦 Gerando embeddings com modelo {model_name}...")
    embeddings = load_embeddings(model_name)

    for i, chunk in enumerate(chunks):
        sidebar_progress.progress((i + 1) / len(chunks))

    log_to_streamlit("💾 Criando e salvando base FAISS...")
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(vectordb_path)

    indexed_files = [os.path.basename(f) for f in files]
    st.session_state["indexed_files"] = indexed_files
    save_indexed_files(indexed_files)

    sidebar_status.markdown("✅ Documentos indexados com sucesso!")
    sidebar_progress.empty()

    metrics = {
        "tempo_total": time.time() - start_time,
        "arquivos_processados": len(files),
        "sucesso": sucesso,
        "falha": falha,
        "chunks_gerados": len(chunks),
        "arquivos": indexed_files
    }

    return db, metrics

def load_vectorstore(model_name):
    """Carrega índice FAISS de embedding model específico."""
    vectordb_path = get_vectordb_path(model_name)
    index_file = os.path.join(vectordb_path, "index.faiss")

    if not os.path.exists(index_file):
        logging.warning(f"Índice FAISS não encontrado em: {vectordb_path}")
        return None

    log_msg = f"📂 Carregando índice FAISS do caminho: {vectordb_path}"
    logging.info(log_msg)
    st.sidebar.text(log_msg)

    embeddings = load_embeddings(model_name)
    return FAISS.load_local(vectordb_path, embeddings, allow_dangerous_deserialization=True)
