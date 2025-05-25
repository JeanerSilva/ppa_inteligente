import subprocess
import sys
import json
import os
from collections import defaultdict

# Executa os scripts
python_exec = sys.executable

print("🚀 Executando A3_conversor_finalistico_gpt.py...")
subprocess.run([python_exec, "A3_conversor_finalistico_gpt.py"], check=True)

print("🚀 Executando A3_objetivos_especificos.py...")
subprocess.run([python_exec, "A3_objetivos_especificos.py"], check=True)

# Caminhos
arquivo1 = "chunks/chunks_programas_finalisticos.jsonl"
arquivo2 = "chunks/objetivos_especificos.jsonl"
saida = "chunks/anexo_iii-programas_finalisticos.jsonl"

# Carrega os dados em memória
def carregar_jsonl(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return [json.loads(linha) for linha in f]

chunks1 = carregar_jsonl(arquivo1)
chunks2 = carregar_jsonl(arquivo2)
todos_chunks = chunks1 + chunks2

# Agrupa por programa_id
programas = defaultdict(list)
for chunk in todos_chunks:
    pid = chunk["metadata"].get("programa_id", "desconhecido")
    programas[pid].append(chunk)

# Ordem das categorias
ordem_categorias = [
    "objetivo_geral",
    "objetivos_estrategicos",
    "publico_alvo",
    "orgao_responsavel",
    "objetivos_especificos"
]

# Ordena os chunks por programa e categoria
with open(saida, "w", encoding="utf-8") as fout:
    for pid in sorted(programas.keys()):
        chunks_programa = programas[pid]
        # Ordena por ordem predefinida de categorias
        chunks_ordenados = sorted(
            chunks_programa,
            key=lambda c: ordem_categorias.index(c["metadata"]["categoria"])
        )
        for chunk in chunks_ordenados:
            fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✅ Arquivo final salvo como: {saida}")

# Remove intermediários
for arquivo in [arquivo1, arquivo2]:
    try:
        os.remove(arquivo)
        print(f"🗑️ Arquivo removido: {arquivo}")
    except FileNotFoundError:
        print(f"⚠️ Arquivo não encontrado para remoção: {arquivo}")
