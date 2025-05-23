# app/handlers/prompt_handler.py
import streamlit as st
from rag.prompt import get_prompt, get_saved_prompts, save_prompt

def prompt_editor_ui():
    st.subheader("🛠️ Prompts personalizados")

    prompts = get_saved_prompts()
    prompt_names = list(prompts.keys()) or ["default"]
    prompt_selecionado = st.selectbox("Escolha um prompt para editar ou criar:", prompt_names + ["<novo>"], key="prompt_selector")

    if prompt_selecionado == "<novo>":
        novo_nome = st.text_input("Nome do novo prompt:", key="novo_nome_prompt")
        prompt_conteudo = ""
    else:
        novo_nome = prompt_selecionado
        prompt_conteudo = prompts.get(prompt_selecionado, "")

    edited_prompt = st.text_area(
        "Conteúdo do prompt (use {context} e {question}):",
        value=prompt_conteudo,
        height=400,
        key="prompt_editor"
    )

    if st.button("💾 Salvar prompt"):
        if novo_nome.strip() == "":
            st.warning("Nome do prompt não pode estar vazio.")
        else:
            save_prompt(novo_nome.strip(), edited_prompt)
            st.session_state["prompt_template"] = edited_prompt
            st.session_state["prompt_name"] = novo_nome
            st.success(f"Prompt '{novo_nome}' salvo com sucesso!")
            st.rerun()

    st.session_state["prompt_template"] = edited_prompt
