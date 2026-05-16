#!/usr/bin/env python3
import subprocess, sys, json

# Run via Django shell
script = '''
import requests

base = 'http://127.0.0.1:8000/api'

# Try to login
creds_list = [
    {'email': 'admin@sotifibre.com', 'password': 'admin123'},
    {'email': 'admin@sotifibre.com', 'password': 'admin'},
    {'email': 'admin@admin.com', 'password': 'admin'},
]
token = None
for creds in creds_list:
    try:
        r = requests.post(f'{base}/users/auth/login/', json=creds, timeout=5)
        if r.status_code == 200:
            token = r.json().get('access', '')
            print(f"Login OK with {creds['email']}")
            break
    except Exception as e:
        print(f"Login error: {e}")

if not token:
    print("Could not get token, trying without auth...")

headers = {'Authorization': f'Bearer {token}'} if token else {}

endpoints = [
    ('GET', '/star-schema/fact-relationships/'),
    ('GET', '/visualizations/activities/'),
    ('GET', '/visualizations/widgets/'),
    ('GET', '/data-sources/tables/'),
    ('GET', '/data-sources/files/'),
    ('GET', '/data-sources/connections/'),
    ('GET', '/visualizations/favorites/'),
    ('GET', '/etl/pipelines/'),
    ('GET', '/data-sources/sources/'),
    ('GET', '/data-warehouse/tables/'),
    ('GET', '/star-schema/schemas/'),
    ('GET', '/ml-analytics/models/'),
    ('GET', '/visualizations/visualizations/'),
    ('GET', '/visualizations/dashboards/'),
    ('GET', '/visualizations/kpis/'),
    ('GET', '/visualizations/reports/'),
    ('GET', '/notifications/notifications/'),
]

for method, ep in endpoints:
    try:
        resp = requests.request(method, f'{base}{ep}', headers=headers, timeout=5)
        print(f'{resp.status_code} {method} {ep}')
        if resp.status_code >= 400:
            print(f'  -> {resp.text[:150]}')
    except Exception as e:
        print(f'ERR {method} {ep}: {e}')
'''

with open('/tmp/test_api_script.py', 'w') as f:
    f.write(script)
print("Script written to /tmp/test_api_script.py")
