#pip install msal requests
# https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/a38d7b2a-9a74-4c61-9509-25d51a5cae30/isMSAApp~/false
import requests
import msal

# 🔐 DADOS DO REGISTRO DO APLICATIVO NO AZURE (SUBSTITUA)
# Importar os secrets do arquivo .env
import os       
from dotenv import load_dotenv
load_dotenv()
# Carrega as variáveis de ambiente do arquivo .env
CLIENT_ID = os.getenv("CLIENT_ID")  # ID do aplicativo registrado no Azure
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # Segredo do aplicativo registrado no Azure
TENANT_ID = os.getenv("TENANT_ID")  # ID do locatário (tenant) do Azure

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Escopos de permissão para Microsoft Graph API
SCOPE = ["https://graph.microsoft.com/.default"]

# URL da Chat API (versão beta)
CHAT_API_URL = "https://graph.microsoft.com/beta/copilot/chat"

# Mensagem a ser enviada
PROMPT = "Liste meus compromissos para amanhã."

# 🧠 Autenticação via MSAL (Client Credentials Flow)
app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=AUTHORITY
)

# Obtém o token de acesso
result = app.acquire_token_for_client(scopes=SCOPE)

if "access_token" in result:
    token = result["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {
                "role": "user",
                "content": PROMPT
            }
        ]
    }

    print("🔁 Enviando prompt ao Microsoft 365 Copilot...")
    response = requests.post(CHAT_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        resposta = response.json()
        conteudo = resposta.get("choices", [{}])[0].get("message", {}).get("content", "Sem conteúdo.")
        print("\n🟢 Resposta:")
        print(conteudo)
    else:
        print("❌ Erro ao chamar a Chat API:")
        print(f"Status: {response.status_code}")
        print(response.text)
else:
    print("❌ Erro ao obter token:")
    print(result.get("error_description"))
