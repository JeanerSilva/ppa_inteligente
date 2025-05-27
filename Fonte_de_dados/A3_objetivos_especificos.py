import fitz
import re
import json
import uuid

ARQUIVO_PDF = "pdf/programas/anexo-iii-programas-finalisticos.pdf"
ARQUIVO_SAIDA = "chunks/objetivos_especificos.jsonl"

def criar_chunk(texto, programa_id):
    return {
        "text": f"<|start_header_id|>\n{texto.strip()}\n<|end_header_id|>",
        "metadata": {
            "chunk_id": str(uuid.uuid4()),
            "categoria": "objetivos_especificos",
            "programa_id": programa_id,
            "origem": ARQUIVO_PDF
        }
    }

def limpar_quebras(texto):
    # Remove hífen + quebra de linha (palavras cortadas)
    texto = re.sub(r'-\n\s*', '', texto)
    # Junta quebras de linha que ocorrem no meio de frases (ex: entre palavras)
    texto = re.sub(r'\n(?=[a-záéíóúâêôãõç])', ' ', texto)
    return texto


# 1. Lê o PDF inteiro
doc = fitz.open(ARQUIVO_PDF)
texto_total = limpar_quebras("\n".join(page.get_text() for page in doc))


# 2. Mapeia todos os programas com nome
programas = list(re.finditer(r"PROGRAMA:\s*(\d{4})\s*-\s*(.+)", texto_total))
programa_map = {m.group(1): m.group(2).strip() for m in programas}

# 3. Captura os objetivos específicos (globalmente)
objetivos = list(re.finditer(r"^(\d{4})\s*-\s+(.+)", texto_total, flags=re.MULTILINE))
chunks = []

# 4. Para cada objetivo, vincula ao programa mais próximo anterior
for match in objetivos:
    linha = match.group(0).strip()
    pos = match.start()

    # Busca o último programa anterior à posição
    programa_id = "desconhecido"
    for prog in reversed(programas):
        if prog.start() < pos:
            programa_id = prog.group(1)
            break

    nome_programa = programa_map.get(programa_id, "Programa desconhecido")
    texto_final = f"PROGRAMA: {programa_id} - {nome_programa} \n\nObjetivos Específicos:\n{linha}"
    chunks.append(criar_chunk(texto_final, programa_id))

# 5. Salvar
with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"✅ {len(chunks)} objetivos específicos extraídos com programa nomeado para {ARQUIVO_SAIDA}")
