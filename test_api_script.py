import requests
import time

base = 'http://127.0.0.1:8000/api'

# JWT login
r = requests.post(base + '/auth/jwt/token/', json={'email': 'admin@admin.com', 'password': 'admin123'}, timeout=5)
if r.status_code == 200:
    token = r.json().get('access', '')
    print('Login OK')
else:
    print('Login failed: ' + str(r.status_code) + ' ' + r.text[:200])
    exit(1)

headers = {'Authorization': 'Bearer ' + token}

# These are the ACTUAL frontend URLs
endpoints = [
    '/star-schema/fact-relationships/',
    '/star-schema/dimensional-schemas/',
    '/star-schema/galaxies/',
    '/star-schema/calculations/',
    '/star-schema/dimension-hierarchies/',
    '/visualizations/activities/',
    '/visualizations/widgets/',
    '/visualizations/kpis/',
    '/visualizations/dashboards/',
    '/visualizations/reports/',
    '/data-sources/tables/',
    '/data-sources/files/',
    '/data-sources/connections/',
    '/data-sources/sources/',
    '/visualizations/favorites/',
    '/etl/pipelines/',
    '/data-warehouse/tables/',
    '/ml-analytics/models/',
    '/ml-analytics/training-logs/',
    '/ml-analytics/forecasts/',
    '/ml-analytics/anomalies/',
    '/ml-analytics/segmentations/',
    '/ml-analytics/recommendations/',
    '/notifications/notifications/',
    '/users/users/',
    '/etl/transformations/',
]

ok = 0
errors = []
for ep in endpoints:
    try:
        resp = requests.get(base + ep, headers=headers, timeout=5)
        if resp.status_code == 200:
            ok += 1
            print('OK  ' + ep)
        else:
            errors.append(ep)
            print('ERR ' + str(resp.status_code) + ' ' + ep)
            print('    ' + resp.text[:150])
    except Exception as e:
        errors.append(ep)
        print('EXC ' + ep + ': ' + str(e))

print('\n--- SUMMARY ---')
print(str(ok) + '/' + str(len(endpoints)) + ' endpoints OK')
if errors:
    print('FAILED: ' + ', '.join(errors))
