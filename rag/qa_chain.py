# rag/qa_chain.py

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from rag.prompt import get_prompt
import streamlit as st
from rag.reranker_local import LocalReranker
import logging

def rerank_documents(query, docs):
    reranker = LocalReranker()
    logging.info(f"Ranqueando documentos com query {query}, docs {docs}")
    return reranker.rerank(query, docs, top_k=st.session_state["retriever_k"])

def build_qa_chain(retriever, llm, prompt_template_name):
    logging.info(f"Construindo cadeia qa com retriever {retriever}, llm {llm} e prompt {prompt_template_name}.")
    prompt_text = get_prompt(prompt_template_name)
    if not prompt_text:
        raise ValueError(f"❌ Prompt '{prompt_template_name}' não encontrado.")

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_text
    )
    logging.info(f"Prompt enviado para qa_chain {prompt}")
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    return chain
