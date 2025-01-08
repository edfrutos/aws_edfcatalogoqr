import requests

response = requests.post('http://127.0.0.1:5000/enable_pro')
print(response.json())
