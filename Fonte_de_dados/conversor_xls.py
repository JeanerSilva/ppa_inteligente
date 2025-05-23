import os
import json
import uuid
import pandas as pd
from tqdm import tqdm

# CONFIGURAÇÕES
PASTA_EXCEL = "xls"
PASTA_SAIDA = "chunks"
ARQUIVO_JSONL = os.path.join(PASTA_SAIDA, "chunks_excel.jsonl")

# Garante que a pasta exista
os.makedirs(PASTA_SAIDA, exist_ok=True)

# Lista de arquivos .xls (formato antigo)
arquivos_excel = [f for f in os.listdir(PASTA_EXCEL) if f.endswith(".xls")]

todos_chunks = []

for arquivo in tqdm(arquivos_excel, desc="📊 Processando arquivos XLS"):
    caminho_excel = os.path.join(PASTA_EXCEL, arquivo)

    try:
        # Lê todas as planilhas com engine específico
        planilhas = pd.read_excel(caminho_excel, sheet_name=None, engine="xlrd")

        for nome_aba, df in planilhas.items():
            df = df.dropna(how="all")  # remove linhas completamente vazias
            df = df.fillna("")         # substitui NaN por string vazia

            for _, row in df.iterrows():
                metadata = {col.strip(): str(row[col]).strip() for col in df.columns}
                texto_base = " | ".join(f"{chave}: {valor}" for chave, valor in metadata.items())

                todos_chunks.append({
                    "text": texto_base,
                    "metadata": {
                        "origem": arquivo,
                        "aba": nome_aba,
                        **metadata,
                        "chunk_id": str(uuid.uuid4())
                    }
                })

    except Exception as e:
        print(f"⚠️ Erro ao processar '{arquivo}': {e}")

# Salva como JSONL
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for chunk in todos_chunks:
        f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"\n✅ {len(todos_chunks)} chunks de Excel (.xls) salvos em '{ARQUIVO_JSONL}'")
