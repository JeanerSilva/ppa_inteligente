import msal
import requests
import webbrowser


# 🔐 DADOS DO REGISTRO DO APLICATIVO NO AZURE (SUBSTITUA)
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost"  # Precisa estar registrado no Azure

SCOPE = ["User.Read"]

# Inicializa o app MSAL
app = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority=AUTHORITY
)

# Solicita o token com login interativo
flow = app.initiate_device_flow(scopes=SCOPE)
if "user_code" not in flow:
    raise Exception("Falha ao iniciar o fluxo interativo.")

print("👉 Vá para o site a seguir e entre com sua conta:")
print(flow["verification_uri"])
print("Digite este código quando solicitado:", flow["user_code"])
webbrowser.open(flow["verification_uri"])

# Aguarda o login do usuário e obtém o token
result = app.acquire_token_by_device_flow(flow)

if "access_token" in result:
    token = result["access_token"]
    print("✅ Login bem-sucedido!")

    # Faz a chamada à API Graph /me
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        print("👤 Informações do usuário:")
        print(f"Nome:  {user_info['displayName']}")
        print(f"E-mail: {user_info['mail'] or user_info['userPrincipalName']}")
        print(f"ID:    {user_info['id']}")
    else:
        print("❌ Erro ao acessar o endpoint /me")
        print(response.text)
else:
    print("❌ Não foi possível obter o token.")
    print(result.get("error_description"))
