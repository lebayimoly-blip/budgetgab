import requests

url = "http://127.0.0.1:8000/users/register"

data = {
    "username": "agent_test",
    "password": "Agent123.",   # mot de passe brut
    "role": "agent"
}

response = requests.post(url, data=data)

print("Status:", response.status_code)
print("Réponse:", response.json())
