import os

# Caminho da pasta com os arquivos .txt
pasta = '.'  # Exemplo: 'C:/meus_arquivos'

# Nome do arquivo de saída
arquivo_saida = 'analise_ppa.txt'

# Abre o arquivo de saída para escrita
with open(arquivo_saida, 'w', encoding='utf-8') as saida:
    for nome_arquivo in os.listdir(pasta):
        if nome_arquivo.endswith('.txt'):
            caminho_arquivo = os.path.join(pasta, nome_arquivo)
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                saida.write(f'\n--- {nome_arquivo} ---\n')  # Identifica o conteúdo
                saida.write(conteudo + '\n')

print(f'Todos os arquivos .txt foram combinados em "{arquivo_saida}"')
