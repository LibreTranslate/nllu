import requests

r = requests.get('http://localhost:3000/checkout?dataset=test-ds&timeout=60', timeout=30)
print(r.json())
