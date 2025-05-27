import os
import json
import uuid
import argparse
from PyPDF2 import PdfReader
from tqdm import tqdm
import re
from collections import Counter
import fitz  # PyMuPDF

import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

# Argumento da linha de comando
parser = argparse.ArgumentParser(description="Extrai textos e gera chunks de arquivos PDF.")
parser.add_argument("pasta_pdf", help="Caminho da pasta com arquivos PDF")
args = parser.parse_args()

# Caminho e nome sanitizado da pasta
PASTA_PDF = args.pasta_pdf
nome_pasta = os.path.basename(os.path.normpath(PASTA_PDF))
nome_pasta_sanitizado = re.sub(r'\W+', '_', nome_pasta)  # Remove caracteres especiais

# Configurações
PASTA_SAIDA = "chunks"
PASTA_TXT = os.path.join(PASTA_SAIDA, "txt_limpo")
PASTA_PDF_sanitizado = re.sub(r'\W+', '_', PASTA_TXT)  # Remove caracteres especiais
ARQUIVO_JSONL = os.path.join(PASTA_SAIDA, f"pdf_chunks-{nome_pasta_sanitizado}.jsonl")
LIMITE_CARACTERES = 1000

# Garante que as pastas existam
os.makedirs(PASTA_SAIDA, exist_ok=True)
os.makedirs(PASTA_TXT, exist_ok=True)

def extrair_texto_pdf(caminho_pdf):
    try:
        doc = fitz.open(caminho_pdf)
        textos_paginas = [page.get_text("text") for page in doc]
        texto_bruto = "\n".join(textos_paginas)

        # 🔍 Detectar trechos que se repetem em muitas páginas (cabeçalhos ou rodapés)
        linhas = [linha.strip() for texto in textos_paginas for linha in texto.splitlines()]
        contagem_linhas = Counter(linhas)
        rodapes_cabecalhos = {linha for linha, freq in contagem_linhas.items() if freq >= len(doc) * 0.6 and len(linha) > 10}

        # 🧹 Remover essas linhas do texto completo
        for linha in rodapes_cabecalhos:
            texto_bruto = texto_bruto.replace(linha, "")

        # 🔧 Corrigir hifenização quebrada
        texto_bruto = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', texto_bruto)

        # 🧼 Limpeza adicional
        texto_bruto = re.sub(r'\s{2,}', ' ', texto_bruto)  # Espaços excessivos
        texto_bruto = re.sub(r'\n{2,}', '\n', texto_bruto)  # Quebras múltiplas

        texto = (
            texto_bruto
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

from nltk.tokenize import sent_tokenize

# Abreviações jurídicas comuns
ABREVIACOES_JURIDICAS = {
    "art.": "art§",
    "Art.": "Art§",
    "inc.": "inc§",
    "Inc.": "Inc§",
    "al.": "al§",
    "cf.": "cf§",
    "nº.": "nº§",
    "nº": "nº§",
    "ex.": "ex§"
}

def proteger_abreviacoes(texto):
    for k, v in ABREVIACOES_JURIDICAS.items():
        texto = texto.replace(k, v)
    return texto

def restaurar_abreviacoes(texto):
    for k, v in ABREVIACOES_JURIDICAS.items():
        texto = texto.replace(v, k)
    return texto

def detectar_categoria(texto):
    texto = texto.strip()
    if texto.startswith("Art."):
        return "artigo"
    if texto.startswith("§"):
        return "paragrafo"
    if re.match(r"^[IVXLCDM]+\s*[-–]", texto):  # Incisos romanos
        return "inciso"
    if re.match(r"^[a-z]\)", texto):           # Alíneas
        return "alinea"
    if "CAPÍTULO" in texto:
        return "capitulo"
    if "SEÇÃO" in texto:
        return "secao"
    return "texto_livre"

def categorizar_guia(texto: str) -> str:
    t = texto.lower()
    if "apresentação" in t or "apresentamos as orientações" in t:
        return "apresentacao"
    if "sumário" in t or "sumario" in t:
        return "sumario"
    if "introdução" in t:
        return "introducao"
    if "módulo siop" in t or "2.1 acesso" in t or "2.2 envio" in t:
        return "modulo"
    if "questionário de avaliação do programa – bloco" in t:
        return "questionario_bloco"
    if "passo a passo" in t:
        return "passo_a_passo"
    if "atributo" in t and "avaliado" in t:
        return "atributo_avaliado"
    if "clique em" in t or "voltar para o questionário" in t:
        return "procedimento"
    if "decreto" in t or "lei" in t or "12.066" in t:
        return "referencia_legal"
    if "ministério do planejamento" in t:
        return "capa_ou_autoria"
    return "conteudo"


def fazer_chunks(texto, limite=2000):
    texto = proteger_abreviacoes(texto)
    frases = sent_tokenize(texto)
    frases = [restaurar_abreviacoes(f.strip()) for f in frases]

    chunks = []
    buffer = ""

    for frase in frases:
        if len(buffer) + len(frase) + 1 <= limite:
            buffer += " " + frase if buffer else frase
        else:
            chunks.append(buffer.strip())
            buffer = frase

    if buffer:
        chunks.append(buffer.strip())

    return chunks


# Pipeline principal
todos_chunks = []
arquivos_pdf = [f for f in os.listdir(PASTA_PDF) if f.endswith(".pdf")]

# ... (imports e setup permanecem os mesmos)

print(f"📁 Pasta de entrada: {PASTA_PDF}")
print(f"📂 Salvando arquivos em: {PASTA_SAIDA}")
print(f"🔢 Limite de caracteres por chunk: {LIMITE_CARACTERES}")
print("🔄 Iniciando processamento de PDFs...\n")

total_chunks = 0

for arquivo in tqdm(arquivos_pdf, desc="📄 Processando PDFs"):
    caminho_pdf = os.path.join(PASTA_PDF, arquivo)
    texto_limpo = extrair_texto_pdf(caminho_pdf)

    if not texto_limpo.strip():
        print(f"⚠️ Texto vazio ignorado em: {arquivo}")
        continue

    with open(os.path.join(PASTA_TXT, arquivo.replace(".pdf", ".txt")), "w", encoding="utf-8") as f_txt:
        f_txt.write(texto_limpo)

    chunks = fazer_chunks(texto_limpo, LIMITE_CARACTERES)

    for chunk in chunks:
        categoria = categorizar_guia(chunk)
        todos_chunks.append({
            "text": f"<|start_header_id|>\n{chunk.strip()}\n<|end_header_id|>",
            "metadata": {
                "origem": arquivo,
                "categoria": categoria,
                "chunk_id": str(uuid.uuid4())
            }
        })


    print(f"✅ {len(chunks)} chunks extraídos de {arquivo}")
    total_chunks += len(chunks)

# Salva JSONL com todos os chunks
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for c in todos_chunks:
        f_out.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"\n🎉 Processamento concluído.")
print(f"💾 Arquivo salvo: {ARQUIVO_JSONL}")
print(f"📦 Total de arquivos processados: {len(arquivos_pdf)}")
print(f"🔹 Total de chunks gerados: {total_chunks}")


#python conversor_pdf.py pdf/normas
#python conversor_pdf.py pdf/agendas
#python conversor_pdf.py pdf/guias
#