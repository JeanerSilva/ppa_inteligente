import json
from collections import defaultdict

# Caminho de entrada e saída
CAMINHO_ENTRADA = "anexo_iii-programas_finalisticos.jsonl"
CAMINHO_SAIDA = "programas_agrupados.jsonl"

def carregar_dados(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return [json.loads(linha) for linha in f]

def salvar_dados(dados, caminho):
    with open(caminho, 'w', encoding='utf-8') as f:
        for item in dados:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def agregar_por_categoria(dados):
    agrupado = defaultdict(lambda: defaultdict(list))

    for item in dados:
        programa_id = item["metadata"]["programa_id"]
        categoria = item["metadata"]["categoria"]
        texto = item["text"].strip()

        # Remove prefixo redundante
        if '\n\n' in texto:
            texto = texto.split('\n\n', 1)[-1]

        agrupado[programa_id][categoria].append(texto)

    resultado = []
    for programa_id, categorias in agrupado.items():
        for categoria, textos in categorias.items():
            texto_agrupado = '\n'.join(textos)
            texto_final = f"PROGRAMA: {programa_id}\n\n{categoria.replace('_', ' ').title()}:\n{texto_agrupado}"
            resultado.append({
                "text": texto_final,
                "metadata": {
                    "programa_id": programa_id,
                    "categoria": categoria
                }
            })

    return resultado

def main():
    dados = carregar_dados(CAMINHO_ENTRADA)
    dados_agrupados = agregar_por_categoria(dados)
    salvar_dados(dados_agrupados, CAMINHO_SAIDA)
    print(f"Arquivo salvo em: {CAMINHO_SAIDA}")

if __name__ == "__main__":
    main()
