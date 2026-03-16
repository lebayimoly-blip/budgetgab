import requests

url = "http://127.0.0.1:8000/users/register"

data = {
    "username": "lebayi moly",
    "password": "Google99.",
    "role": "admin"
}

response = requests.post(url, data=data)

print("Status:", response.status_code)
print("Réponse:", response.json())
