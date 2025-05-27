import spacy
from rouge_score import rouge_scorer
from tqdm import tqdm

# Carrega modelo spaCy
print("\n Teste de Recall")
print("Carrega modelo spaCy")

nlp = spacy.load("pt_core_news_md")

def comparar_textos(texto_gerado, texto_referencia):
    progresso = tqdm(total=4, desc="Comparando textos", bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt}")

    print("\n 🔠 Normaliza os textos (minúsculas)")
    texto_gerado = texto_gerado.lower()
    texto_referencia = texto_referencia.lower()

    print("\n Etapa 1: Processamento com spaCy")
    progresso.set_description("Processando texto gerado")
    doc_gerado = nlp(texto_gerado)
    progresso.update(1)

    progresso.set_description("Processando texto de referência")
    doc_referencia = nlp(texto_referencia)
    progresso.update(1)

    print("\nEtapa 2: Similaridade vetorial")
    progresso.set_description("Calculando similaridade semântica")
    similaridade = doc_gerado.similarity(doc_referencia)
    progresso.update(1)

    # Etapa 3: ROUGE-L
    progresso.set_description("Calculando ROUGE-L")
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    rouge = scorer.score(texto_referencia, texto_gerado)
    rougeL_f = rouge_l_por_linha(texto_referencia, texto_gerado)

    progresso.update(1)

    progresso.close()

    # Avaliação heurística
    if rougeL_f < 0.5 and similaridade < 0.7:
        avaliacao = "Cobertura baixa (informação possivelmente ausente)"
    elif rougeL_f > 0.9 and similaridade < 0.7:
        avaliacao = "Texto com excesso de informação irrelevante"
    elif similaridade > 0.95 and rougeL_f > 0.95:
        avaliacao = "Textos quase idênticos"
    else:
        avaliacao = "Cobertura aceitável"

    return {
        'similaridade_semantica': round(similaridade, 4),
        'rougeL_fmeasure': round(rougeL_f, 4),
        'avaliacao_conteudo': avaliacao
    }

def rouge_l_por_linha(texto1, texto2):
    linhas1 = [l.strip() for l in texto1.splitlines() if l.strip()]
    linhas2 = [l.strip() for l in texto2.splitlines() if l.strip()]

    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = []

    for l1 in linhas1:
        # Encontra a linha mais semelhante do outro texto
        melhor_score = 0
        for l2 in linhas2:
            score = scorer.score(l2, l1)['rougeL'].fmeasure
            if score > melhor_score:
                melhor_score = score
        scores.append(melhor_score)

    if scores:
        return sum(scores) / len(scores)
    return 0


def ler_arquivo(path):
    print(f"\n Lendo arquivos {path}")
    with open(path, encoding='utf-8') as f:
        return f.read()

def main():
    print("\n Teste de Recall")
    texto_gerado = ler_arquivo('resposta_gerada.txt')
    texto_referencia = ler_arquivo('resposta_referencia.txt')

    resultado = comparar_textos(texto_gerado, texto_referencia)

    print("\n=== RESULTADO DA COMPARAÇÃO ===")
    print(f"Similaridade semântica: {resultado['similaridade_semantica']}")
    print(f"ROUGE-L F1:              {resultado['rougeL_fmeasure']}")
    print(f"Avaliação:               {resultado['avaliacao_conteudo']}")

if __name__ == "__main__":
    main()





#pip install spacy rouge-score
#python -m spacy download pt_core_news_md
#📌 Observações
#Essa solução não depende de torch, não exige admin e roda 100% offline.
#O spaCy faz uma análise semântica baseada em vetores de palavras, o que é eficiente para casos de recall.
#O ROUGE-L complementa a análise verificando cobertura de conteúdo.