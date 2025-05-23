# qa_chain.py

import logging
from langchain.chains import RetrievalQA
from rag.prompt import get_custom_prompt
from settings import RETRIEVER_TOP_K

def build_qa_chain(vectorstore, llm, prompt_template):
    from rag.prompt import get_custom_prompt
    from settings import RETRIEVER_TOP_K

    if not vectorstore or not llm:
        logging.error("Vectorstore ou LLM nulo ao tentar construir a QA Chain.")
        return None

    logging.info("Construindo cadeia de pergunta e resposta com o modelo selecionado.")
    retriever = vectorstore.as_retriever(search_type="mmr", k=RETRIEVER_TOP_K, fetch_k=30)
    prompt = get_custom_prompt(prompt_template)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    logging.info("QA Chain construída com sucesso.")
    return chain