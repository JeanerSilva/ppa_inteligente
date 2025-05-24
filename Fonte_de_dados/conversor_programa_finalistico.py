import fitz  # PyMuPDF
import re
import json
import unicodedata
import uuid

ARQUIVO_PDF = "pdf/normas/anexo-iii-programas-finalisticos.pdf"
ARQUIVO_JSONL = "chunks/chunks_programas_finalisticos.jsonl"

def normalizar(texto):
    """Remove acentos e coloca em minúsculas para comparação robusta."""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").lower()

def extrair_linhas(page):
    """Extrai todas as linhas visíveis do PDF (modo texto simples)."""
    texto = page.get_text("text")
    linhas = texto.split("\n")
    return [{"text": linha.strip(), "index": i} for i, linha in enumerate(linhas) if linha.strip()]

def is_objetivo_especifico(texto):
    return re.match(r"^\d{4} - ", texto)

# Inicialização
doc = fitz.open(ARQUIVO_PDF)
resultados = []
programa_atual = None
secao_atual = None

for page in doc:
    linhas = extrair_linhas(page)
    i = 0

    while i < len(linhas):
        l = linhas[i]["text"]
        l_norm = normalizar(l)

        # Novo programa
        if l_norm.startswith("programa:"):
            if programa_atual:
                resultados.append(programa_atual)
            programa_atual = {
                "programa": l,
                "objetivos_estrategicos": [],
                "publico_alvo": [],
                "orgao_responsavel": "",
                "objetivos_especificos": []
            }
            secao_atual = None
            i += 1
            continue

        # Detecção de seções com texto normalizado
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
                    i += 1  # pula a linha que já usamos

        elif "objetivos especificos do programa" in l_norm:
            secao_atual = "objetivos_especificos"

        # Captura conteúdo das seções
        elif secao_atual == "objetivos_estrategicos" and l.startswith("•"):
            programa_atual["objetivos_estrategicos"].append(l)

        elif secao_atual == "publico_alvo":
            if l.startswith("-"):
                programa_atual["publico_alvo"].append(l)
            elif len(programa_atual["publico_alvo"]) == 0:
                # Assume que é uma linha única de público-alvo
                programa_atual["publico_alvo"].append(l)


        elif secao_atual == "objetivos_especificos" and is_objetivo_especifico(l):
            programa_atual["objetivos_especificos"].append(l)

        i += 1

# Adiciona o último programa
if programa_atual:
    resultados.append(programa_atual)

## Exporta JSON
#with open("chunks/programas_finalisticos.json", "w", encoding="utf-8") as f_json:
#    json.dump(resultados, f_json, indent=2, ensure_ascii=False)

# Exporta TXT
#with open("pdf/programas_final.txt", "w", encoding="utf-8") as f_txt:
#    for prog in resultados:
#        f_txt.write(f"{prog['programa']}\n\n")
#        f_txt.write("Objetivos Estratégicos:\n")
#        for o in prog["objetivos_estrategicos"]:
#            f_txt.write(f"  - {o}\n")
#        f_txt.write("\nPúblico Alvo:\n")
#        for p in prog["publico_alvo"]:
#            f_txt.write(f"  - {p}\n")
#        f_txt.write(f"\nÓrgão Responsável:\n  {prog['orgao_responsavel']}\n")
#        f_txt.write("\nObjetivos Específicos:\n")
#        for oe in prog["objetivos_especificos"]:
#            f_txt.write(f"  - {oe}\n")
#        f_txt.write("\n" + "="*60 + "\n\n")

print(f"✅ Extração concluída com {len(resultados)} programas.")

# Converter estrutura para chunks formatados
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

# Salvar em JSONL
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for chunk in chunks_formatados:
        f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✅ {len(chunks_formatados)} chunks salvos em '{ARQUIVO_JSONL}'")
