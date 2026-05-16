path = '/home/adoum/Integrated_BI/sotifibre_backend_django/seed_data.py'
with open(path) as f:
    lines = f.readlines()

# Find the line with Connection.objects.get_or_create and replace the whole block
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'Connection.objects.get_or_create' in line:
        # Replace lines from conn_specs start to end of this block
        # Find the start of conn_specs going backwards
        start = i
        while start > 0 and 'conn_specs' not in lines[start]:
            start -= 1
        # Now replace from start to i+3 (if c: print / conn_count += 1)
        replacement = [
            '    import django.utils.timezone as tz2\n',
            '    conn_count = 0\n',
            '    for src, h, p, dbn, sch, usr in [\n',
            "        (src_pg,    '192.168.224.128', 5432, 'sotifibre_db', 'public', 'sotifibre_readonly'),\n",
            "    ]:\n",
            '        c_obj, c = DataSourceConnection.objects.get_or_create(\n',
            '            data_source=src,\n',
            "            defaults=dict(host=h, port=p, database_name=dbn, schema_name=sch,\n",
            "                          username=usr, password='', use_ssl=False,\n",
            '                          is_connected=True, last_connected=tz2.now(), latency_ms=8,\n',
            "                          connection_test_result={'status': 'ok', 'message': 'Connexion etablie'}),\n",
            '        )\n',
            '        if c:\n',
            "            print(f'  [OK] Connexion {src.name}')\n",
            '            conn_count += 1\n',
            "    print(f'  Total connexions: {conn_count}')\n",
        ]
        # Skip old lines from start to end of block (find end: next empty try/except or print)
        # Just keep everything up to start, add replacement, then skip up to "    print(f"
        new_lines = new_lines[:len(new_lines) - (i - start)] + replacement
        # Skip old lines
        while i < len(lines) and 'Total connexions' not in lines[i]:
            i += 1
        i += 1  # skip the print line too
        continue
    new_lines.append(line)
    i += 1

with open(path, 'w') as f:
    f.writelines(new_lines)

# Verify fix
with open(path) as f:
    content = f.read()
remaining = content.count('Connection.objects.get_or_create')
print(f'Remaining Connection.objects.get_or_create: {remaining}')
print('Done')
