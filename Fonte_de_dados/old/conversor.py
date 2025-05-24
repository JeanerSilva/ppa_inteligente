import pandas as pd
import os
import unicodedata
import re

# === 1. Carrega os arquivos .xls ===
df_programa = pd.read_excel("tabelas/Programa.xls")
df_objetivo_geral = pd.read_excel("tabelas/ObjetivoGeral.xls")
df_objetivo = pd.read_excel("tabelas/Objetivo.xls")
df_objetivo_especifico = pd.read_excel("tabelas/ObjetivoEspecifico.xls")
df_indicador_entrega = pd.read_excel("tabelas/Indicador Entrega.xls")
df_indicador_obj_espec = pd.read_excel("tabelas/Indicador Objetivo Especifico.xls")

# === 2. Padroniza nomes das colunas para evitar erros por variações ===
for df in [df_programa, df_objetivo_geral, df_objetivo, df_objetivo_especifico, df_indicador_entrega, df_indicador_obj_espec]:
    df.columns = df.columns.str.strip().str.upper()

# === 3. Cria diretório de saída ===
output_dir = "docs"
os.makedirs(output_dir, exist_ok=True)

# === 4. Gera os textos estruturados com base no nome do programa ===
def gerar_passages(df_programa, df_objetivo_geral, df_objetivo, df_objetivo_especifico, df_ind_entrega, df_ind_obj_esp):
    passages = []

    for _, prog in df_programa.iterrows():
        PROG_ID = prog["PROGRAMA"]
        prog_nome = prog["TÍTULO"].strip()
        

        texto = f"Programa: {prog_nome}\n\n"

        # Campos descritivos adicionais do programa
        campos_adicionais = [
            ("PÚBLICO ALVO", "Público Alvo"),
            ("DESCRIÇÃO DO PROBLEMA", "Descrição do Problema"),
            ("CAUSA DO PROBLEMA", "Causa do Problema"),
            ("EVIDÊNCIAS DO PROBLEMA", "Evidências do Problema"),
            ("JUSTIFICATIVA PARA A INTERVENÇÃO", "Justificativa para a Intervenção"),
            ("EVOLUÇÃO HISTÓRICA", "Evolução Histórica"),
            ("COMPARAÇÕES INTERNACIONAIS", "Comparações Internacionais"),
            ("RELAÇÃO COM OS ODS", "Relação com os ODS"),
            ("AGENTES ENVOLVIDOS", "Agentes Envolvidos"),
            ("ARTICULAÇÃO FEDERATIVA", "Articulação Federativa"),
            ("ENFOQUE TRANSVERSAL", "Enfoque Transversal"),
            ("MARCO LEGAL", "Marco Legal"),
            ("PLANOS NACIONAIS, SETORIAIS E REGIONAIS", "Planos Nacionais, Setoriais e Regionais"),
        ]

        for col_key, col_label in campos_adicionais:
            valor = prog.get(col_key)
            if pd.notna(valor):
                texto += f"{col_label}:\n{valor}\n\n"

        # Filtra conteúdos relacionados ao programa
        objetivos_gerais = df_objetivo_geral[df_objetivo_geral["PROGRAMA"] == PROG_ID]
        objetivos = df_objetivo[df_objetivo["PROGRAMA"] == PROG_ID]
        objetivos_esp = df_objetivo_especifico[df_objetivo_especifico["PROGRAMA"] == PROG_ID]
        ind_entrega = df_ind_entrega[df_ind_entrega["PROGRAMA"] == PROG_ID]
        ind_obj = df_ind_obj_esp[df_ind_obj_esp["PROGRAMA"] == PROG_ID]

        # Objetivo Geral
        if not objetivos_gerais.empty:
            texto += "Objetivo Geral:\n"
            for _, row in objetivos_gerais.iterrows():
                texto += f"- {row['ENUNCIADO']}\n"
            texto += "\n"

        # Objetivos
        if not objetivos.empty:
            texto += "Objetivos:\n"
            for _, row in objetivos.iterrows():
                texto += f"- {row['ENUNCIADO']}\n"
            texto += "\n"

        # Objetivos Específicos
        if not objetivos_esp.empty:
            texto += "Objetivos Específicos:\n"
            for _, row in objetivos_esp.iterrows():
                texto += f"- {row['ENUNCIADO']}\n"
            texto += "\n"

        # Indicadores de Entrega
        if not ind_entrega.empty:
            texto += "Indicadores de Entrega:\n"
            for _, ind in ind_entrega.iterrows():
                nome = ind.get("DENOMINAÇÃO", "Indicador sem nome")
                desc = ind.get("DESCRIÇÃO", "meta não informada")
                #ano = ind.get("ANO_FINAL", "")
                texto += f"- {nome}: {desc} \n"
            texto += "\n"

        # Indicadores de Objetivos Específicos
        if not ind_obj.empty:
            texto += "Indicadores de Objetivos Específicos:\n"
            for _, ind in ind_obj.iterrows():
                nome = ind.get("DENOMINAÇÃO", "Indicador sem nome")
                desc = ind.get("DESCRIÇÃO", "meta não informada")
                #ano = ind.get("ANO_FINAL", "")
                texto += f"- {nome}: {desc} \n"
            texto += "\n"

        # Adiciona prefixo para uso com embeddings do modelo E5
        passage = f"passage: {texto.strip()}"
        passages.append((prog_nome, passage))

    return passages

# === 5. Executa a geração e salva os arquivos ===
passagens = gerar_passages(
    df_programa,
    df_objetivo_geral,
    df_objetivo,
    df_objetivo_especifico,
    df_indicador_entrega,
    df_indicador_obj_espec
)
def normalizar_nome_arquivo(nome):
    # Remove acentos e caracteres especiais
    nome_normalizado = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
    # Substitui espaços por _
    nome_normalizado = nome_normalizado.replace(' ', '_')
    # Remove qualquer outro caractere indesejado (opcional)
    nome_normalizado = re.sub(r'[^a-zA-Z0-9_\-]', '', nome_normalizado)
    return nome_normalizado + ".txt"

for nome_prog, passage in passagens:
    nome_arquivo = normalizar_nome_arquivo(nome_prog)
    with open(os.path.join(output_dir, nome_arquivo), "w", encoding="utf-8") as f:
        f.write(passage)

print(f"✅ {len(passagens)} arquivos salvos em '{output_dir}'")
