import fitz  # PyMuPDF
import re
import json
import unicodedata
import uuid

ARQUIVO_PDF = "pdf/normas/anexo-iii-programas-finalisticos.pdf"
ARQUIVO_JSONL = "chunks/chunks_programas_finalisticos.jsonl"

def normalizar(texto):
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").lower()

def extrair_linhas(page):
    texto = page.get_text("text")
    linhas = texto.split("\n")
    return [{"text": linha.strip(), "index": i} for i, linha in enumerate(linhas) if linha.strip()]

def reconstruir_paragrafo(linhas):
    buffer = ""
    paragrafos = []

    for linha in linhas:
        l = linha.strip()
        if not l:
            continue

        if buffer:
            buffer += ' ' + l
        else:
            buffer = l

        if re.search(r'[.;!?…]$', l):
            paragrafos.append(buffer.strip())
            buffer = ""

    if buffer:
        paragrafos.append(buffer.strip())

    return paragrafos

def extrair_id_programa(texto):
    match = re.match(r"PROGRAMA:\s*(\d+)", texto)
    return match.group(1) if match else "desconhecido"

# Inicialização
doc = fitz.open(ARQUIVO_PDF)
resultados = []
programa_atual = None
secao_atual = None
buffer_secao = []

for page in doc:
    linhas = extrair_linhas(page)
    i = 0

    while i < len(linhas):
        l = linhas[i]["text"]
        l_norm = normalizar(l)

        if l_norm.startswith("programa:"):
            if programa_atual:
                if buffer_secao and secao_atual == "objetivos_especificos":
                    programa_atual["objetivos_especificos"].extend(reconstruir_paragrafo(buffer_secao))
                resultados.append(programa_atual)

            programa_atual = {
                "programa": l,
                "programa_id": extrair_id_programa(l),
                "objetivo_geral": "",
                "objetivos_estrategicos": [],
                "publico_alvo": [],
                "orgao_responsavel": "",
                "objetivos_especificos": []
            }
            secao_atual = None
            buffer_secao = []
            i += 1
            continue

        if "objetivo geral" in l_norm:
            secao_atual = "objetivo_geral"
            buffer_secao = []
            i += 1
            while i < len(linhas):
                prox = linhas[i]["text"].strip()
                prox_norm = normalizar(prox)

                if prox_norm.startswith(("objetivos estrategicos", "publico alvo", "orgao responsavel", "objetivos especificos")):
                    break
                if prox.startswith("•"):  # interrompe se encontrar bullet
                    break

                buffer_secao.append(prox)
                i += 1

            programa_atual["objetivo_geral"] = " ".join(buffer_secao).strip()
            continue

        elif "objetivo estrategico" in l_norm or "objetivos estrategicos" in l_norm:
            secao_atual = "objetivos_estrategicos"

        elif "publico alvo" in l_norm:
            secao_atual = "publico_alvo"

        elif "orgao responsavel" in l_norm:
            secao_atual = "orgao_responsavel"
            if i + 1 < len(linhas):
                linha_abaixo = linhas[i + 1]["text"].strip()
                if linha_abaixo:
                    programa_atual["orgao_responsavel"] = linha_abaixo
                    i += 1

        elif "objetivos especificos" in l_norm:
            if buffer_secao and secao_atual == "objetivos_especificos":
                programa_atual["objetivos_especificos"].extend(reconstruir_paragrafo(buffer_secao))
            buffer_secao = []
            secao_atual = "objetivos_especificos"

        elif secao_atual == "objetivos_estrategicos" and l.startswith("•"):
            programa_atual["objetivos_estrategicos"].append(l)

        elif secao_atual == "publico_alvo":
            if l.startswith("-") or len(programa_atual["publico_alvo"]) == 0:
                programa_atual["publico_alvo"].append(l)

        elif secao_atual == "objetivos_especificos":
            buffer_secao.append(l)

        i += 1

# Finaliza o último programa
if programa_atual:
    if buffer_secao and secao_atual == "objetivos_especificos":
        programa_atual["objetivos_especificos"].extend(reconstruir_paragrafo(buffer_secao))
    resultados.append(programa_atual)

print(f"✅ Extração concluída com {len(resultados)} programas.")

# Geração dos chunks formatados
chunks_formatados = []

def criar_chunk(base_programa, programa_id, categoria, conteudo):
    return {
        "text": f"{base_programa}\n\n{categoria.replace('_', ' ').title()}:\n{conteudo}",
        "metadata": {
            "origem": "programas_finalisticos.pdf",
            "chunk_id": str(uuid.uuid4()),
            "programa_id": programa_id,
            "categoria": categoria
        }
    }

for programa in resultados:
    base_programa = programa["programa"]
    programa_id = programa["programa_id"]

    if programa.get("objetivo_geral"):
        chunks_formatados.append(
            criar_chunk(base_programa, programa_id, "objetivo_geral", programa["objetivo_geral"])
        )

    if programa["objetivos_estrategicos"]:
        texto = "\n".join(programa["objetivos_estrategicos"])
        chunks_formatados.append(
            criar_chunk(base_programa, programa_id, "objetivos_estrategicos", texto)
        )

    if programa["publico_alvo"]:
        texto = "\n".join(programa["publico_alvo"])
        chunks_formatados.append(
            criar_chunk(base_programa, programa_id, "publico_alvo", texto)
        )

    if programa["orgao_responsavel"]:
        texto = programa["orgao_responsavel"]
        chunks_formatados.append(
            criar_chunk(base_programa, programa_id, "orgao_responsavel", texto)
        )

    if programa["objetivos_especificos"]:
        texto = "\n".join(programa["objetivos_especificos"])
        chunks_formatados.append(
            criar_chunk(base_programa, programa_id, "objetivos_especificos", texto)
        )

# Salvar os chunks como JSONL
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for chunk in chunks_formatados:
        f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✅ {len(chunks_formatados)} chunks salvos em '{ARQUIVO_JSONL}'")
