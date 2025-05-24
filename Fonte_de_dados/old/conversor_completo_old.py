import pandas as pd
import os
import unicodedata
import re

# === CONFIGURAÇÕES ===
PASTA_PLANILHAS = "Fonte_de_dados"  # onde estão seus .xls
COLUNA_PROGRAMA = "PROGRAMA"   # coluna identificadora do programa
PASTA_SAIDA = "passages_txt" # onde salvar os .txt

# === FUNÇÃO: normaliza nomes de arquivos ===
def normalizar_nome_arquivo(nome):
    nome = unicodedata.normalize('NFKD', str(nome)).encode('ASCII', 'ignore').decode('ASCII')
    nome = nome.replace(' ', '_')
    return re.sub(r'[^a-zA-Z0-9_\-]', '', nome)

# === FUNÇÃO: converte linha em texto ===
def linha_para_texto(linha):
    return "\n".join(f"{col.strip().title()}: {str(valor).strip()}" for col, valor in linha.items() if pd.notna(valor))

# === FUNÇÃO PRINCIPAL ===
def processar_planilhas(pasta, coluna_programa, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".xls")]
    total_chunks = {}

    for arq in arquivos:
        caminho = os.path.join(pasta, arq)
        print(f"🔍 Lendo: {arq}")
        try:
            df = pd.read_excel(caminho)
            df.columns = df.columns.str.strip().str.upper()
            col_prog = coluna_programa.upper()

            if col_prog not in df.columns:
                print(f"⚠️ Coluna '{COLUNA_PROGRAMA}' não encontrada em {arq}. Pulando.")
                continue

            for prog_num, grupo in df.groupby(col_prog):
                partes = [linha_para_texto(linha) for _, linha in grupo.iterrows()]
                texto = f"passage: Programa Número {prog_num}\n\n" + "\n\n".join(partes)

                if prog_num not in total_chunks:
                    total_chunks[prog_num] = []
                total_chunks[prog_num].append(texto)

        except Exception as e:
            print(f"❌ Erro ao processar {arq}: {e}")

    # === SALVA OS ARQUIVOS ===
    for prog_num, blocos in total_chunks.items():
        nome_arquivo = normalizar_nome_arquivo(f"programa_{prog_num}.txt")
        caminho_saida = os.path.join(pasta_saida, nome_arquivo)
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write("\n\n".join(blocos))
        print(f"✅ Salvo: {nome_arquivo}")

# === EXECUÇÃO ===
if __name__ == "__main__":
    processar_planilhas(PASTA_PLANILHAS, COLUNA_PROGRAMA, PASTA_SAIDA)
