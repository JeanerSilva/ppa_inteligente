import os
from langchain.prompts import PromptTemplate
from settings import PROMPT_FILE


DEFAULT_PROMPT_TEMPLATE = """
Você é um assistente especializado na análise de documentos de planejamento público, com acesso a trechos documentos relativos ao Plano Plurianual (PPA).

Seu trabalho é responder com base **exclusivamente no conteúdo abaixo**, sem usar conhecimento externo ou fazer suposições.

📄 **Trechos do documento (contexto):**
{context}

❓ **Pergunta:**
{question}

📌 **Instruções de resposta**:
- Responda **apenas com informações contidas nos trechos**.
- Seja **claro, objetivo e técnico**, como se estivesse ajudando a revisar e melhorar o plano.
- Se a pergunta for sobre **inconsistências ou sugestões de melhoria**, **analise criticamente os trechos** e aponte pontos contraditórios, lacunas ou possibilidades de aprimoramento.
- Se a pergunta for **aberta ou subjetiva**, busque **respostas diretas** nos trechos, mas também faça **sugestões** de melhorias ou pontos a serem considerados.

📝 **Resposta:**
"""

def get_saved_prompt() -> str:
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return DEFAULT_PROMPT_TEMPLATE

def save_prompt(content: str):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def get_custom_prompt(template: str) -> PromptTemplate:
    return PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )
