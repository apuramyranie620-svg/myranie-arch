import requests

url = "https://myranie-arch.onrender.com"

response = requests.get(url)

print("Status Code:", response.status_code)
print("Response:", response.text)