import os
import json
import uuid
from PyPDF2 import PdfReader
from tqdm import tqdm

# Configurações
PASTA_PDF = "pdf"
PASTA_SAIDA = "chunks"
PASTA_TXT = os.path.join(PASTA_SAIDA, "txt_limpo")
ARQUIVO_JSONL = os.path.join(PASTA_SAIDA, "chunks_pdf.jsonl")
LIMITE_CARACTERES = 800

# Garante que as pastas existam
os.makedirs(PASTA_SAIDA, exist_ok=True)
os.makedirs(PASTA_TXT, exist_ok=True)

# 1. Extrai e limpa o texto de um PDF
def extrair_texto_pdf(caminho_pdf):
    try:
        reader = PdfReader(caminho_pdf)
        texto_raw = "\n".join([page.extract_text() or "" for page in reader.pages])
        texto = (
            texto_raw
            .replace('\r', '')
            .replace('\n•', ' ||BULLET|| ')
            .replace('\n\n', ' ||PARAGRAFO|| ')
            .replace('\n', ' ')
            .replace(' ||PARAGRAFO|| ', '\n\n')
            .replace(' ||BULLET|| ', '\n•')
        )
        return texto.strip()
    except Exception as e:
        print(f"Erro ao extrair texto de {caminho_pdf}: {e}")
        return ""

# 2. Divide parágrafos grandes
def dividir_paragrafo(paragrafo, limite):
    partes = []
    while len(paragrafo) > limite:
        corte = paragrafo.rfind(" ", 0, limite)
        if corte == -1:
            corte = limite
        partes.append(paragrafo[:corte].strip())
        paragrafo = paragrafo[corte:].strip()
    if paragrafo:
        partes.append(paragrafo.strip())
    return partes

# 3. Gera chunks por parágrafos com agrupamento
def fazer_chunks(texto, limite=800):
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    chunks = []
    buffer = ""
    for p in paragrafos:
        if len(p) > limite:
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            partes = dividir_paragrafo(p, limite)
            chunks.extend(partes)
        elif len(buffer) + len(p) + 1 <= limite:
            buffer += " " + p if buffer else p
        else:
            chunks.append(buffer.strip())
            buffer = p
    if buffer:
        chunks.append(buffer.strip())
    return chunks

# 4. Pipeline principal
todos_chunks = []
arquivos_pdf = [f for f in os.listdir(PASTA_PDF) if f.endswith(".pdf")]

for arquivo in tqdm(arquivos_pdf, desc="📄 Processando PDFs"):
    caminho_pdf = os.path.join(PASTA_PDF, arquivo)
    texto_limpo = extrair_texto_pdf(caminho_pdf)

    # Salva versão .txt limpa
    with open(os.path.join(PASTA_TXT, arquivo.replace(".pdf", ".txt")), "w", encoding="utf-8") as f_txt:
        f_txt.write(texto_limpo)

    chunks = fazer_chunks(texto_limpo, LIMITE_CARACTERES)

    for chunk in chunks:
        todos_chunks.append({
            "text": chunk,
            "metadata": {
                "origem": arquivo,
                "chunk_id": str(uuid.uuid4())
            }
        })

# 5. Salva JSONL com chunks
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for c in todos_chunks:
        f_out.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"\n✅ {len(todos_chunks)} chunks salvos em '{ARQUIVO_JSONL}'")
