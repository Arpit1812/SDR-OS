from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
response = client.get('/providers')
print('status', response.status_code)
print('text', response.text)
print('json', response.json() if response.status_code == 200 else 'no json')
