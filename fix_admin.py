#!/usr/bin/env python3
import sys

# Fix 1: data_sources/admin.py — cast success_rate to float so {:.0f} works
path1 = '/home/adoum/Integrated_BI/sotifibre_backend_django/apps/data_sources/admin.py'
with open(path1) as f:
    content = f.read()
old1 = '            color, success_rate, obj.total_queries'
new1 = '            color, float(success_rate), obj.total_queries'
if old1 in content:
    content = content.replace(old1, new1, 1)
    with open(path1, 'w') as f:
        f.write(content)
    print('OK data_sources/admin.py')
else:
    print('SKIP data_sources/admin.py — pattern not found')

# Fix 2: users/admin.py — format_html with no args -> mark_safe
path2 = '/home/adoum/Integrated_BI/sotifibre_backend_django/apps/users/admin.py'
with open(path2) as f:
    content = f.read()
old2 = "        return format_html('<span class=\"badge bg-secondary\">✗</span>')"
new2 = "        return mark_safe('<span class=\"badge bg-secondary\">✗</span>')"
if old2 in content:
    content = content.replace(old2, new2, 1)
    with open(path2, 'w') as f:
        f.write(content)
    print('OK users/admin.py')
else:
    print('SKIP users/admin.py — pattern not found, searching...')
    for i, line in enumerate(content.split('\n'), 1):
        if 'format_html' in line and 'bg-secondary' in line:
            print(f'  line {i}: {repr(line)}')

# Fix 3: visualizations/admin.py — format_html with no args -> mark_safe + import
path3 = '/home/adoum/Integrated_BI/sotifibre_backend_django/apps/visualizations/admin.py'
with open(path3) as f:
    content = f.read()

# Add mark_safe import if missing
if 'from django.utils.safestring import mark_safe' not in content:
    content = content.replace(
        'from django.utils.html import format_html',
        'from django.utils.html import format_html\nfrom django.utils.safestring import mark_safe',
        1
    )
    print('Added mark_safe import to visualizations/admin.py')

old3 = "        return format_html('<span class=\"badge bg-secondary\">N/A</span>')"
new3 = "        return mark_safe('<span class=\"badge bg-secondary\">N/A</span>')"
if old3 in content:
    content = content.replace(old3, new3, 1)
    with open(path3, 'w') as f:
        f.write(content)
    print('OK visualizations/admin.py')
else:
    print('SKIP visualizations/admin.py — pattern not found, searching...')
    for i, line in enumerate(content.split('\n'), 1):
        if 'format_html' in line and 'N/A' in line:
            print(f'  line {i}: {repr(line)}')
