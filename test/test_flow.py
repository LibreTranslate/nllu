import requests

url = "http://localhost:4000"
dataset = "piero"
lang = "fr"

batch = {'done': False}
while not batch['done']:
    r = requests.get(f'{url}/checkout?dataset={dataset}&lang={lang}&timeout=60', timeout=30)
    batch = r.json()
    if batch['done']: 
        break

    print(batch)
    r = requests.post(f'{url}/commit', json={
        'dataset': dataset, 'batchId': batch['batchId'], 'phrases': [f"{p} - translated" for p in batch['phrases']], 'lang': lang
    }, timeout=30)
    print(r.json())


r = requests.get(f'{url}/download?dataset={dataset}&lang={lang}', timeout=30)
print(r.content)
    