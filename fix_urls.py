path = '/home/adoum/Integrated_BI/sotifibre_backend_django/config/urls.py'
with open(path) as f:
    content = f.read()

# Add ml-analytics URL after notifications
old = "    path('api/notifications/', include('apps.notifications.urls')),"
new = ("    path('api/notifications/', include('apps.notifications.urls')),\n"
       "\n"
       "    # ML Analytics App - Analyse et modeles ML\n"
       "    path('api/ml-analytics/', include('apps.ml_analytics.urls')),")

if 'ml-analytics' not in content:
    if old in content:
        content = content.replace(old, new, 1)
        with open(path, 'w') as f:
            f.write(content)
        print('OK config/urls.py — added ml-analytics')
    else:
        print('Pattern not found in urls.py')
        for i, line in enumerate(content.split('\n'), 1):
            if 'notifications' in line and 'include' in line:
                print(f'  line {i}: {repr(line)}')
else:
    print('ml-analytics already present')
