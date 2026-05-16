import re

path = '/home/adoum/Integrated_BI/sotifibre_backend_django/seed_data.py'
with open(path) as f:
    content = f.read()

# Fix import: replace Connection with DataSourceConnection
content = content.replace(
    'from apps.data_sources.models import DataSource, DataTable, Connection',
    'from apps.data_sources.models import DataSource, DataTable, DataSourceConnection',
    1
)

# Fix Connection.objects.all().delete() in cleanup
content = content.replace(
    '    Connection.objects.all().delete()',
    '    DataSourceConnection.objects.all().delete()',
    1
)

# Fix Connection usage in seeding block — replace the entire Connection seeding section
# Find and replace the conn_specs block
old_conn_block = '''    conn_specs = [
        dict(name='CONN_Production_PostgreSQL',
             description='Connexion directe a la base PostgreSQL de production SOTIFibre.',
             connection_type='postgresql',
             host='192.168.224.128', port=5432, database='sotifibre_db',
             username='sotifibre_readonly', password='readonly_2026!',
             is_active=True, last_tested=None,
             owner=dev_user, tags=['production', 'postgresql']),
        dict(name='CONN_DW_PostgreSQL',
             description='Connexion a l entrepot de donnees - schema sotifibre_dw.',
             connection_type='postgresql',
             host='192.168.224.128', port=5432, database='supervisionolt_db',
             username='supervisionolt_admin', password='dw_2026!',
             is_active=True, last_tested=None,
             owner=dev_user, tags=['production', 'postgresql']),
    ]
    conn_count = 0
    for cspec in conn_specs:
        name = cspec['name']
        import django.utils.timezone as tz
        cspec['last_tested'] = tz.now()
        c_obj, c = Connection.objects.get_or_create(name=name, defaults=cspec)
        if c:
            print(f"  [OK] {name}")
            conn_count += 1
    print(f"  Total connexions: {conn_count}")'''

new_conn_block = '''    conn_count = 0
    import django.utils.timezone as tz
    conn_specs = [
        (src_pg,    '192.168.224.128', 5432, 'sotifibre_db',      'public', 'sotifibre_readonly'),
        (src_kafka, '192.168.224.128', 9092, 'kafka',             '',       'kafka_user'),
    ]
    for src, host, port, dbname, schema, user in conn_specs:
        c_obj, c = DataSourceConnection.objects.get_or_create(
            data_source=src,
            defaults=dict(
                host=host, port=port, database_name=dbname, schema_name=schema,
                username=user, password='', use_ssl=False,
                is_connected=True, last_connected=tz.now(),
                latency_ms=8,
                connection_test_result={'status': 'ok', 'message': 'Connexion etablie'},
            )
        )
        if c:
            print(f"  [OK] Connexion {src.name}")
            conn_count += 1
    print(f"  Total connexions: {conn_count}")'''

if old_conn_block in content:
    content = content.replace(old_conn_block, new_conn_block, 1)
    print('Fixed Connection seeding block')
else:
    print('Connection seeding block not found — searching...')
    # Try to find Connection.objects.get_or_create
    idx = content.find('Connection.objects.get_or_create')
    if idx >= 0:
        print(f'  Found at char {idx}: {content[idx-50:idx+100]}')

with open(path, 'w') as f:
    f.write(content)
print('seed_data.py fixed')
