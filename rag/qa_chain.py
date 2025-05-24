# rag/qa_chain.py

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from rag.prompt import get_prompt
import streamlit as st

from rag.reranker_local import LocalReranker

def rerank_documents(query, docs):
    reranker = LocalReranker()
    return reranker.rerank(query, docs, top_k=st.session_state["retriever_k"])


def build_qa_chain(vectorstore, llm, prompt_template_name="teste"):
    """Constrói a QA chain com o prompt nomeado no prompt_templates.json."""

    prompt_text = get_prompt(prompt_template_name)

    if not prompt_text:
        raise ValueError(f"❌ Prompt '{prompt_template_name}' não encontrado.")

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_text
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    return chain
