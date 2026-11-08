import requests

url = "https://YOUR-URL.onrender.com/student"

response = requests.get(url)

print("Status Code:", response.status_code)
print("Response:", response.text)