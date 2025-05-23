import os
import glob
import traceback
import logging
import time
import streamlit as st

from settings import DOCS_PATH
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader, UnstructuredHTMLLoader
)
from langchain.schema import Document
import json
from rag.embeddings import load_embeddings
from rag.utils import save_indexed_files
from langchain.text_splitter import TokenTextSplitter
from transformers import AutoTokenizer

from settings import CHUNK_SIZE, CHUNK_OVERLAP, VECTORS_FOLDER

# Configuração de log
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def get_vectordb_path(model_name):
    """Cria caminho seguro baseado no nome do modelo."""
    safe_name = model_name.split("/")[-1].replace("-", "_")
    path = f"./{VECTORS_FOLDER}/vectordb_{safe_name}"
    os.makedirs(path, exist_ok=True)
    return path


def create_vectorstore(model_name):
    """Cria um novo índice FAISS a partir dos documentos usando o modelo de embedding fornecido."""
    start_time = time.time()
    vectordb_path = get_vectordb_path(model_name)
    sidebar_status = st.sidebar.empty()
    sidebar_progress = st.sidebar.progress(0)

    sidebar_status.info("🔄 Reindexando documentos...")

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
            elif ext == ".txt":
                loader = TextLoader(file, encoding="utf-8")
            elif ext == ".docx":
                loader = UnstructuredWordDocumentLoader(file)
            elif ext == ".xlsx":
                loader = UnstructuredExcelLoader(file)
            elif ext == ".html":
                loader = UnstructuredHTMLLoader(file)
            elif ext == ".json" or ext == ".jsonl":
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        linha = json.loads(line)
                        texto = linha.get("text", "")
                        metadados = linha.get("metadata", {})
                        doc = Document(page_content=texto, metadata=metadados)
                        docs.append(doc)
                sucesso += 1
                continue
            else:
                continue

            docs.extend(loader.load())
            sucesso += 1
        except Exception as e:
            falha += 1
            sidebar_progress.markdown(f"⚠️ Erro ao processar `{filename}`: {e}")
            logging.error(f"Erro ao processar `{filename}`: {e}")
            logging.debug(traceback.format_exc())

        sidebar_progress.progress((i + 1) / total)

    if not docs:
        sidebar_progress.markdown("❌ Nenhum documento válido.")
        logging.warning("Nenhum documento válido.")
        sidebar_progress.empty()
        st.stop()
        return None, {}

    sidebar_status.markdown(f"✂️ Fazendo o splitting com o tokenizer do modelo `{model_name}`...")
    logging.info(f"Fazendo o splitting com o tokenizer do modelo `{model_name}`...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    splitter = TokenTextSplitter.from_huggingface_tokenizer(
        tokenizer=tokenizer,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(docs)
    for chunk in chunks:
        chunk.page_content = f"passage: {chunk.page_content.strip()}"

    sidebar_status.markdown(f"📦 Gerando embeddings com modelo {model_name}...")
    logging.info(f"Gerando embeddings com modelo {model_name}...")
    sidebar_progress.progress(0.0)

    embeddings = load_embeddings(model_name)

    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        sidebar_progress.progress((i + 1) / total_chunks)

    logging.info("Criando FAISS diretamente com documentos e embeddings...")
    db = FAISS.from_documents(chunks, embeddings)

    logging.info(f"Salvando FAISS em: {vectordb_path}")
    db.save_local(vectordb_path)
    logging.info("Salvo com sucesso!")

    indexed_files = [os.path.basename(f) for f in files]
    st.session_state["indexed_files"] = indexed_files
    save_indexed_files(indexed_files)

    sidebar_status.markdown("✅ Documentos indexados com sucesso!")
    sidebar_progress.empty()

    # Retornar métricas de indexação
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
        return None

    embeddings = load_embeddings(model_name)
    return FAISS.load_local(vectordb_path, embeddings, allow_dangerous_deserialization=True)
