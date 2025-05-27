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

print(f"📁 Pasta de entrada: {PASTA_EXCEL}")
print(f"📂 Salvando em: {PASTA_SAIDA}")
print("🔄 Iniciando processamento de arquivos .xls...\n")

total_chunks = 0

for arquivo in tqdm(arquivos_excel, desc="📊 Processando arquivos XLS"):
    caminho_excel = os.path.join(PASTA_EXCEL, arquivo)

    try:
        planilhas = pd.read_excel(caminho_excel, sheet_name=None, engine="xlrd")
        chunk_count_por_arquivo = 0

        for nome_aba, df in planilhas.items():
            df = df.dropna(how="all").fillna("")
            for _, row in df.iterrows():
                metadata = {col.strip(): str(row[col]).strip() for col in df.columns}
                texto_base = " | ".join(f"{chave}: {valor}" for chave, valor in metadata.items())

                todos_chunks.append({
                    "text": f"<|start_header_id|>\n{texto_base.strip()}\n<|end_header_id|>",
                    "metadata": {
                        "origem": arquivo,
                        "aba": nome_aba,
                        **metadata,
                        "chunk_id": str(uuid.uuid4())
                    }
                })
                chunk_count_por_arquivo += 1

        print(f"✅ {chunk_count_por_arquivo} chunks extraídos de {arquivo}")
        total_chunks += chunk_count_por_arquivo

    except Exception as e:
        print(f"⚠️ Erro ao processar '{arquivo}': {e}")

# Salva o arquivo final
with open(ARQUIVO_JSONL, "w", encoding="utf-8") as f_out:
    for chunk in todos_chunks:
        f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"\n🎉 Processamento concluído.")
print(f"💾 Arquivo salvo: {ARQUIVO_JSONL}")
print(f"📦 Total de arquivos XLS processados: {len(arquivos_excel)}")
print(f"🔹 Total de chunks gerados: {total_chunks}")
