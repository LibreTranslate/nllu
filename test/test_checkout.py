import requests

r = requests.get('http://localhost:4000/checkout?dataset=test-ds&lang=it&timeout=60', timeout=30)
print(r.json())
