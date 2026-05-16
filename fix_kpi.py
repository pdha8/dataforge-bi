path = '/home/adoum/Integrated_BI/sotifibre_backend_django/apps/visualizations/views.py'
with open(path) as f:
    content = f.read()

old = "    queryset = KPI.objects.all().select_related('dimensional_schema', 'measure', 'dashboard', 'owner')"
new = "    queryset = KPI.objects.all().select_related('dimensional_schema', 'measure', 'dashboard')"

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print('OK visualizations/views.py — removed invalid owner from select_related')
else:
    print('Pattern not found, searching...')
    for i, line in enumerate(content.split('\n'), 1):
        if 'select_related' in line and 'KPI' in content.split('\n')[max(0,i-10):i+1][-1] or ('select_related' in line and 'owner' in line):
            print(f'  line {i}: {repr(line)}')
