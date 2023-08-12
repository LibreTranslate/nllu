import requests

r = requests.post('http://localhost:4000/commit', json={
    'dataset': "piero", 'batchId': 0, 'phrases': ["abc", "cde", "123"], 'lang': "it"
}, timeout=30)
print(r.json())
