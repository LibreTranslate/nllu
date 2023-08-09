import requests

r = requests.post('http://localhost:3000/commit', json={
    'dataset': "test-ds", 'batchId': 0, 'phrases': ["abc", "cde"], 'lang': "it"
}, timeout=30)
print(r.json())
