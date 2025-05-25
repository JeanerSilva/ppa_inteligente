import json

arquivo1 = "chunks/chunks_programas_finalisticos.jsonl"
arquivo2 = "chunks/objetivos_especificos.jsonl"
saida = "chunks/chunks_unificados.jsonl"

with open(saida, "w", encoding="utf-8") as fout:
    for arquivo in [arquivo1, arquivo2]:
        with open(arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                fout.write(linha)

print(f"✅ Arquivo final salvo como: {saida}")
