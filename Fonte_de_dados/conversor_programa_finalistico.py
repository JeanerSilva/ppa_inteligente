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

def is_objetivo_especifico(texto):
    return re.match(r"^\d{4} - ", texto)

def reconstruir_paragrafo(linhas):
    """ Junta linhas que terminam sem pontuação final, como ponto final. """
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
                if buffer_secao and secao_atual:
                    if secao_atual == "objetivos_especificos":
                        programa_atual["objetivos_especificos"].extend(reconstruir_paragrafo(buffer_secao))
                    buffer_secao = []
                resultados.append(programa_atual)

            programa_atual = {
                "programa": l,
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

        elif "objetivos especificos do programa" in l_norm:
            if buffer_secao and secao_atual == "objetivos_especificos":
                programa_atual["objetivos_especificos"].extend(reconstruir_paragrafo(buffer_secao))
            buffer_secao = []
            secao_atual = "objetivos_especificos"

        # Captura seções com estrutura apropriada
        elif secao_atual == "objetivos_estrategicos" and l.startswith("•"):
            programa_atual["objetivos_estrategicos"].append(l)

        elif secao_atual == "publico_alvo":
            if l.startswith("-"):
                programa_atual["publico_alvo"].append(l)
            elif len(programa_atual["publico_alvo"]) == 0:
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

# Converter para JSONL com metadados
chunks_formatados = []
for programa in resultados:
    texto = f"{programa['programa']}\n\n"
    if programa["objetivos_estrategicos"]:
        texto += "Objetivos Estratégicos:\n" + "\n".join(programa["objetivos_estrategicos"]) + "\n\n"
    if programa["publico_alvo"]:
        texto += "Público Alvo:\n" + "\n".join(programa["publico_alvo"]) + "\n\n"
    if programa["orgao_responsavel"]:
        texto += f"Órgão Responsável: {programa['orgao_responsavel']}\n\n"
    if programa["objetivos_especificos"]:
        texto += "Objetivos Específicos:\n" + "\n".join(programa["objetivos_especificos"]) + "\n\n"

    chunks_formatados.append({
        "text": texto.strip(),
        "metadata": {
            "origem": "programas_finalisticos.pdf",
            "chunk_id": str(uuid.uuid4())
        }
    })

with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for chunk in chunks_formatados:
        f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✅ {len(chunks_formatados)} chunks salvos em '{ARQUIVO_JSONL}'")
