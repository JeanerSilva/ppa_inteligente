import fitz
import re
import json
import uuid
import unicodedata

ARQUIVO_PDF = "pdf/programas/anexo-iii-programas-finalisticos.pdf"
ARQUIVO_JSONL = "chunks/chunks_programas_finalisticos.jsonl"

def normalizar(texto):
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").lower()

def criar_chunk(texto, programa_id, categoria):
    return {
        "text": f"<|start_header_id|>\n{texto.strip()}\n<|end_header_id|>",
        "metadata": {
            "origem": "programas_finalisticos.pdf",
            "chunk_id": str(uuid.uuid4()),
            "programa_id": programa_id,
            "categoria": categoria
        }
    }

def limpar_quebras(texto):
    # Remove hífen + quebra de linha (palavras cortadas)
    texto = re.sub(r'-\n\s*', '', texto)
    # Junta linhas quebradas dentro de frases
    texto = re.sub(r'\n(?=\w)', ' ', texto)
    return texto

# 1. Carrega texto completo
doc = fitz.open(ARQUIVO_PDF)
texto = ""
paginas = []
for page in doc:
    page_text = limpar_quebras(page.get_text())
    texto += page_text
    paginas.append(page_text)

# 2. Extrai blocos por programa
blocos = re.split(r"(?=PROGRAMA:\s*\d{4}\s*-)", texto)
chunks = []

for bloco in blocos:
    if not bloco.strip():
        continue

    # Programa ID e título
    match = re.search(r"PROGRAMA:\s*(\d{4})\s*-\s*(.+?)(?=\n|Objetivo Geral:)", bloco)

    if not match:
        continue

    programa_id = match.group(1)
    programa_nome = f"PROGRAMA: {programa_id} - {match.group(2)}"

    # Objetivo Geral
    match_og = re.search(r"Objetivo Geral:\s*(.+?)(?=(\n•|-|Público Alvo:|Órgão Responsável:|Objetivos Específicos:|$))", bloco, flags=re.DOTALL)
    if match_og:
        texto_og = match_og.group(1).strip().replace("\n", " ")
        chunks.append(criar_chunk(f"{programa_nome}\n\nObjetivo Geral:\n{texto_og}", programa_id, "objetivo_geral"))

    # Objetivos Estratégicos: cada linha com •
    bloco_limpo = bloco.split("Público Alvo:")[0]
    estrategicos = re.findall(r"^•\s*.+", bloco_limpo, flags=re.MULTILINE)


    for item in estrategicos:
        chunks.append(criar_chunk(f"{programa_nome}\n\nObjetivos Estratégicos:\n{item.strip()}", programa_id, "objetivos_estrategicos"))

    # Público Alvo: cada linha com - ou primeira após título
    match_pa = re.search(r"Público Alvo:(.+?)(?=([OÓ]rg[ãa]o Respons[áa]vel:|Objetivos Específicos:|PROGRAMA:|$))", bloco, flags=re.DOTALL | re.IGNORECASE)

    if match_pa:
        bloco_pa = match_pa.group(1).strip()
        linhas_pa = [l.strip() for l in bloco_pa.split("\n") if l.strip()]
        for i, linha in enumerate(linhas_pa):
            if linha.startswith("-") or i == 0:
                chunks.append(criar_chunk(f"{programa_nome}\n\nPúblico Alvo:\n{linha}", programa_id, "publico_alvo"))

    # Órgão Responsável
    match_or = re.search(
        r"[OÓ]rg[ãa]o Respons[áa]vel:\s*(.+)",
        bloco,
        flags=re.IGNORECASE
    )
    if match_or:
        linha_orgao = match_or.group(1).strip()
        # Captura somente até a primeira quebra de linha (sem pegar tabelas)
        primeira_linha = linha_orgao.splitlines()[0].strip()
        # Remove qualquer dado numérico ou valores suspeitos após o nome do órgão
        primeira_linha = re.split(r"\d", primeira_linha)[0].strip()
        chunks.append(criar_chunk(f"{programa_nome}\n\nÓrgão Responsável:\n{primeira_linha}", programa_id, "orgao_responsavel"))

# 4. Exporta como JSONL
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✅ {len(chunks)} chunks salvos com sucesso em '{ARQUIVO_JSONL}'")
