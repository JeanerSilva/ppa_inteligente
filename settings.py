# settings.py

RETRIEVER_TOP_K = 2
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TEMPERATURE = 0.0

EMBEDDING_OPTIONS = {
    "E5 (multilingual)": "intfloat/multilingual-e5-large",
    "BGE (small EN)": "BAAI/bge-small-en-v1.5",
    "MiniLM (leve)": "sentence-transformers/all-MiniLM-L6-v2"
}

LLM_MODEL = "llama3.2"  # usado para ollama
OPENAI_MODEL = "gpt-4.1"  # pode trocar para gpt-4

LLM_GGUF = "./.models/mistral-7b-instruct-v0.1.Q4_K_M.gguf" 
PROMPT_FILE = "./config/saved_prompt.txt"
VECTORS_FOLDER = "./vectors"
DOCS_PATH = "./chunks"
INDEXED_LIST_PATH = "./chunks/indexed/indexed_files.json"


# Meta-Llama-3-8B-Instruct.Q5_K_M
# multilingual-e5-large-instruct-q8_0.gguf 
# mistral-7b-instruct-v0.1.Q4_K_M