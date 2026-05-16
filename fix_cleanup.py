path = '/home/adoum/Integrated_BI/sotifibre_backend_django/seed_data.py'
with open(path) as f:
    content = f.read()

# Add missing imports for DW models
old_import = 'from apps.data_warehouse.models import (\n    DataWarehouseSchema, DataWarehouseTable,\n    FactTable, DimensionTable, Measure,\n)'
new_import = 'from apps.data_warehouse.models import (\n    DataWarehouseSchema, DataWarehouseTable,\n    FactTable, DimensionTable, Measure,\n    DimensionAttribute, AggregationTable, DataWarehouseLog, DataWarehouseMetric,\n)'
if 'DataWarehouseLog' not in content:
    content = content.replace(old_import, new_import, 1)
    print('Added DW model imports')

# Add missing deletions before DataWarehouseTable.objects.all().delete()
old_cleanup = 'DataWarehouseTable.objects.all().delete()'
new_cleanup = ('DataWarehouseLog.objects.all().delete()\n'
               'DataWarehouseMetric.objects.all().delete()\n'
               'DimensionAttribute.objects.all().delete()\n'
               'AggregationTable.objects.all().delete()\n'
               'DataWarehouseTable.objects.all().delete()')
if 'DataWarehouseLog.objects.all().delete()' not in content:
    content = content.replace(old_cleanup, new_cleanup, 1)
    print('Added DW cleanup deletions')

# Also add ml_analytics cleanup if not there
from apps_check = 'from apps.ml_analytics.models import MLModel, ModelTrainingLog'
if 'ModelTrainingLog.objects.all().delete()' not in content:
    pass  # already handled

with open(path, 'w') as f:
    f.write(content)
print('Done')
