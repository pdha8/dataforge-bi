#!/usr/bin/env python
"""
SOTIFibre BI Platform - Script de peuplement des donnees de test
Nomenclature industrielle : SRC_ / DSB_ / ETL_ / KPI_
Usage: python manage.py shell < seed_data.py
"""
import os
import sys
import uuid
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

if not hasattr(cache, 'delete_pattern'):
    cache.delete_pattern = lambda *a, **kw: None

print("\n" + "=" * 60)
print("  SOTIFibre BI Platform - Seeding des donnees de test")
print("=" * 60)

from apps.users.models import User, Team
from apps.data_sources.models import DataSource, DataTable
from apps.data_warehouse.models import (
    DataWarehouseSchema, DataWarehouseTable,
    FactTable, DimensionTable, Measure,
)
from apps.etl_engine.models import ETLPipeline, ExecutionLog
from apps.star_schema.models import DimensionalSchema
from apps.visualizations.models import Dashboard, Widget, KPI, Report, Favorite
from apps.notifications.models import Notification

# ---------------------------------------------------------
# 0. NETTOYAGE - Suppression des donnees existantes
# ---------------------------------------------------------
print("\n[0/14] Nettoyage des donnees existantes...")

Favorite.objects.all().delete()
Notification.objects.all().delete()
Report.objects.all().delete()
Widget.objects.all().delete()
KPI.objects.all().delete()
Dashboard.objects.all().delete()
DimensionalSchema.objects.all().delete()
Measure.objects.all().delete()
ExecutionLog.objects.all().delete()
ETLPipeline.objects.all().delete()
DataWarehouseTable.objects.all().delete()
DataWarehouseSchema.objects.all().delete()
DataTable.objects.all().delete()
DataSource.objects.all().delete()
Team.objects.all().delete()
User.objects.filter(is_superuser=False).delete()
User.objects.exclude(email='admin@admin.com').filter(is_superuser=True).delete()
print("  [OK] Donnees existantes supprimees")

# ---------------------------------------------------------
# 1. UTILISATEURS
# ---------------------------------------------------------
print("\n[1/14] Utilisateurs...")

def make_user(email, username, first, last, role, dept, title, superuser=False):
    u, created = User.objects.get_or_create(email=email, defaults=dict(
        username=username, first_name=first, last_name=last,
        role=role, status='active', department=dept, job_title=title,
        is_verified=True, is_staff=superuser, is_superuser=superuser,
    ))
    if created:
        u.set_password('SOTIFibre@2026!')
        u.save()
        print(f"  [OK] {email}")
    return u

admin_user    = make_user('admin@sotifibre.dz',       'admin_soti',   'Admin',   'SOTIFibre', 'superadmin',   'Direction IT',      'Administrateur BI',      superuser=True)
dev_user      = make_user('dev.bi@sotifibre.dz',      'dev_bi',       'Karim',   'Meziane',   'bi_developer', 'Departement BI',    'Developpeur BI')
analyst_user  = make_user('analyste@sotifibre.dz',    'analyste_bi',  'Nadia',   'Brahim',    'bi_analyst',   'Departement BI',    'Analyste BI')
director_user = make_user('direction@sotifibre.dz',   'direction',    'Mohamed', 'Amrani',    'bi_consumer',  'Direction Generale', 'Directeur General')
tech_user     = make_user('technicien@sotifibre.dz',  'technicien',   'Rachid',  'Hamidi',    'viewer',       'Technique',         'Technicien Reseau')

# ---------------------------------------------------------
# 2. EQUIPES
# ---------------------------------------------------------
print("\n[2/14] Equipes...")

team_bi, c = Team.objects.get_or_create(name='Equipe BI Core', defaults=dict(
    description='Equipe centrale BI - developpement et maintenance des tableaux de bord et KPIs SOTIFibre.',
    team_lead=admin_user,
))
if c:
    team_bi.members.set([admin_user, dev_user, analyst_user])
    print("  [OK] Equipe BI Core")

team_data, c = Team.objects.get_or_create(name='Equipe Data Engineering', defaults=dict(
    description='Equipe Data Engineering - pipelines ETL, Data Warehouse et infrastructure donnees.',
    team_lead=dev_user,
))
if c:
    team_data.members.set([dev_user, analyst_user, tech_user])
    print("  [OK] Equipe Data Engineering")

# ---------------------------------------------------------
# 3. SOURCES DE DONNEES (prefixe SRC_)
# ---------------------------------------------------------
print("\n[3/14] Sources de donnees...")

def make_source(name, **kw):
    s, c = DataSource.objects.get_or_create(name=name, defaults=kw)
    if c: print(f"  [OK] {name}")
    return s

src_pg = make_source(
    'SRC_Production_PostgreSQL',
    description='Base PostgreSQL principale - clients, contrats, equipements reseau et historique incidents SOTIFibre.',
    source_type='postgresql', status='active', database_type='postgresql',
    host='192.168.224.128', port=5432, database_name='sotifibre_db',
    schema_name='public', username='sotifibre_admin',
    use_ssl=False, auth_type='password', sync_frequency='daily',
    auto_refresh_enabled=True, data_quality_score=92,
    row_count=185420, column_count=87, is_validated=True, is_active=True,
    category='Base de donnees', business_domain='Reseau Fibre',
    tags=['production', 'postgresql', 'fibre', 'principal'],
    owner=admin_user, created_by=dev_user,
)

src_iot = make_source(
    'SRC_IoT_Capteurs_Fibre',
    description='API REST exposant les metriques temps reel des capteurs IoT sur les noeuds de distribution fibre : debit, latence, taux erreur.',
    source_type='rest_api', status='active', api_type='rest',
    api_url='http://192.168.224.128:8080', api_endpoint='/api/v1/metrics',
    api_headers={'Content-Type': 'application/json'},
    auth_type='api_key', api_key='STF-IOT-KEY-2026-PROD',
    sync_frequency='realtime', auto_refresh_enabled=True,
    data_quality_score=88, is_validated=True, is_active=True,
    category='API', business_domain='Reseau Fibre',
    tags=['iot', 'capteurs', 'temps-reel', 'fibre'],
    owner=dev_user, created_by=dev_user,
)

src_csv = make_source(
    'SRC_CRM_Clients_CSV',
    description='Fichiers CSV exportes mensuellement depuis le CRM - abonnes fibre, offres et localisation.',
    source_type='csv', status='active', file_type='csv',
    file_path='/data/exports/clients/', file_encoding='utf-8', file_delimiter=';',
    sync_frequency='monthly', data_quality_score=78,
    is_validated=True, is_active=True, category='Fichier', business_domain='Clients',
    tags=['crm', 'clients', 'csv', 'mensuel'],
    owner=analyst_user, created_by=analyst_user,
)

src_kafka = make_source(
    'SRC_Kafka_Alertes_Securite',
    description='Topic Kafka collectant en temps reel les alertes securite reseau et anomalies detectees sur l infrastructure fibre.',
    source_type='kafka', status='active',
    streaming_topic='sotifibre.alertes.securite',
    streaming_broker='192.168.224.128:9092',
    auth_type='none', sync_frequency='realtime', auto_refresh_enabled=True,
    data_quality_score=95, is_validated=True, is_active=True,
    category='Streaming', business_domain='Securite',
    tags=['kafka', 'alertes', 'securite', 'streaming'],
    owner=dev_user, created_by=dev_user,
)

src_meteo = make_source(
    'SRC_API_Meteo_Nationale',
    description='API meteo pour corroler les incidents reseau fibre avec les conditions climatiques dans les zones de deploiement.',
    source_type='rest_api', status='active', api_type='rest',
    api_url='https://api.meteo-algerie.dz', api_endpoint='/v2/conditions/current',
    auth_type='api_key', api_key='METEO-DZ-KEY-2026',
    sync_frequency='hourly', auto_refresh_enabled=True,
    data_quality_score=85, is_validated=True, is_active=True,
    category='API', business_domain='Environnement',
    tags=['meteo', 'correlation', 'incidents', 'api'],
    owner=analyst_user, created_by=analyst_user,
)

# ---------------------------------------------------------
# 4. TABLES DE DONNEES
# ---------------------------------------------------------
print("\n[4/14] Tables de donnees...")

tables_spec = [
    ('clients', 'Abonnes SOTIFibre avec offres fibre actives', 42380, [
        {'name': 'id', 'type': 'integer', 'nullable': False},
        {'name': 'nom', 'type': 'varchar(100)', 'nullable': False},
        {'name': 'prenom', 'type': 'varchar(100)', 'nullable': False},
        {'name': 'email', 'type': 'varchar(200)', 'nullable': True},
        {'name': 'telephone', 'type': 'varchar(20)', 'nullable': True},
        {'name': 'wilaya', 'type': 'varchar(50)', 'nullable': False},
        {'name': 'offre_id', 'type': 'integer', 'nullable': False},
        {'name': 'date_activation', 'type': 'date', 'nullable': False},
        {'name': 'statut', 'type': 'varchar(20)', 'nullable': False},
    ]),
    ('incidents_reseau', 'Journal des incidents reseau fibre optique', 28640, [
        {'name': 'id', 'type': 'integer', 'nullable': False},
        {'name': 'type_incident', 'type': 'varchar(50)', 'nullable': False},
        {'name': 'severite', 'type': 'varchar(20)', 'nullable': False},
        {'name': 'date_signalement', 'type': 'timestamp', 'nullable': False},
        {'name': 'date_resolution', 'type': 'timestamp', 'nullable': True},
        {'name': 'zone_id', 'type': 'integer', 'nullable': False},
        {'name': 'equipement_id', 'type': 'integer', 'nullable': False},
        {'name': 'statut', 'type': 'varchar(20)', 'nullable': False},
        {'name': 'clients_affectes', 'type': 'integer', 'nullable': True},
    ]),
    ('consommation_bande_passante', 'Metriques de consommation bande passante par noeud', 1240000, [
        {'name': 'id', 'type': 'bigint', 'nullable': False},
        {'name': 'noeud_id', 'type': 'integer', 'nullable': False},
        {'name': 'horodatage', 'type': 'timestamp', 'nullable': False},
        {'name': 'debit_montant_mbps', 'type': 'numeric(10,2)', 'nullable': False},
        {'name': 'debit_descendant_mbps', 'type': 'numeric(10,2)', 'nullable': False},
        {'name': 'taux_utilisation_pct', 'type': 'numeric(5,2)', 'nullable': False},
        {'name': 'data_transferee_gb', 'type': 'numeric(12,3)', 'nullable': False},
        {'name': 'latence_ms', 'type': 'integer', 'nullable': True},
    ]),
    ('equipements_reseau', 'Catalogue des equipements reseau fibre deployes', 3840, [
        {'name': 'id', 'type': 'integer', 'nullable': False},
        {'name': 'nom', 'type': 'varchar(200)', 'nullable': False},
        {'name': 'type_equipement', 'type': 'varchar(50)', 'nullable': False},
        {'name': 'fabricant', 'type': 'varchar(100)', 'nullable': True},
        {'name': 'modele', 'type': 'varchar(100)', 'nullable': True},
        {'name': 'localisation', 'type': 'varchar(200)', 'nullable': True},
        {'name': 'date_installation', 'type': 'date', 'nullable': True},
        {'name': 'statut', 'type': 'varchar(20)', 'nullable': False},
    ]),
    ('interventions_techniques', 'Interventions des techniciens terrain', 18720, [
        {'name': 'id', 'type': 'integer', 'nullable': False},
        {'name': 'incident_id', 'type': 'integer', 'nullable': True},
        {'name': 'technicien_id', 'type': 'integer', 'nullable': False},
        {'name': 'date_debut', 'type': 'timestamp', 'nullable': False},
        {'name': 'date_fin', 'type': 'timestamp', 'nullable': True},
        {'name': 'type_intervention', 'type': 'varchar(50)', 'nullable': False},
        {'name': 'cout_da', 'type': 'numeric(10,2)', 'nullable': True},
        {'name': 'resultat', 'type': 'varchar(50)', 'nullable': True},
    ]),
    ('contrats', 'Contrats abonnement fibre actifs et archives', 45920, [
        {'name': 'id', 'type': 'integer', 'nullable': False},
        {'name': 'client_id', 'type': 'integer', 'nullable': False},
        {'name': 'offre_id', 'type': 'integer', 'nullable': False},
        {'name': 'date_debut', 'type': 'date', 'nullable': False},
        {'name': 'date_fin', 'type': 'date', 'nullable': True},
        {'name': 'tarif_mensuel_da', 'type': 'numeric(8,2)', 'nullable': False},
        {'name': 'statut', 'type': 'varchar(20)', 'nullable': False},
    ]),
]

data_tables = {}
for tname, tdesc, trows, tcols in tables_spec:
    dt, c = DataTable.objects.get_or_create(
        data_source=src_pg, name=tname,
        defaults=dict(schema='public', description=tdesc,
                      row_count=trows, columns=tcols, primary_key=['id'],
                      last_analyzed=timezone.now() - timedelta(hours=6)),
    )
    data_tables[tname] = dt
    if c: print(f"  [OK] {tname} ({trows:,} lignes)")

# ---------------------------------------------------------
# 5. DATA WAREHOUSE - SCHEMA
# ---------------------------------------------------------
print("\n[5/14] Schema Data Warehouse...")

dw_schema, c = DataWarehouseSchema.objects.get_or_create(
    name='sotifibre_dw',
    defaults=dict(
        description='Entrepot de donnees centralise SOTIFibre - schema principal alimente par les pipelines ETL.',
        owner=admin_user, is_active=True, default_compression=True,
        tags=['production', 'principal', 'fibre'],
        table_count=8, size_bytes=2_450_000_000,
    )
)
if c: print("  [OK] Schema sotifibre_dw cree")

# ---------------------------------------------------------
# 6. DATA WAREHOUSE - TABLES
# ---------------------------------------------------------
print("\n[6/14] Tables Data Warehouse...")

dw_tables = {}

fact_specs = [
    ('fact_incidents_reseau',   'transaction', 'Incidents reseau fibre - duree, severite, clients impactes', 28640),
    ('fact_consommation_bp',    'daily',       'Consommation bande passante agregee par noeud par jour',     365000),
    ('fact_interventions',      'transaction', 'Interventions terrain - couts, durees, resultats',           18720),
]
for tname, grain, tdesc, trows in fact_specs:
    t, c = DataWarehouseTable.objects.get_or_create(
        schema=dw_schema, name=tname,
        defaults=dict(table_type='fact', granularity=grain, description=tdesc,
                      status='active', row_count=trows, refresh_frequency='daily',
                      last_refresh=timezone.now() - timedelta(hours=2),
                      is_compressed=True, technical_owner=dev_user,
                      columns=[{'name': 'id_sk', 'type': 'bigint'},
                                {'name': 'date_key', 'type': 'integer'}],
                      tags=['fait', 'fibre']),
    )
    dw_tables[tname] = t
    if c: print(f"  [OK] {tname} [FAIT]")

dim_specs = [
    ('dim_temps',        'slowly_changing', 'Dimension temps - hierarchie date et heure',              3653),
    ('dim_client',       'slowly_changing', 'Dimension clients SOTIFibre - attributs abonnes',         42380),
    ('dim_equipement',   'conformed',       'Dimension equipements reseau - OLT, ONT, switches',       3840),
    ('dim_localisation', 'conformed',       'Dimension geographique - wilayas, dairas, communes',      1542),
    ('dim_technicien',   'slowly_changing', 'Dimension techniciens terrain - personnel habilite',       248),
]
for tname, dim_type, tdesc, trows in dim_specs:
    t, c = DataWarehouseTable.objects.get_or_create(
        schema=dw_schema, name=tname,
        defaults=dict(table_type='dimension', dimension_type=dim_type,
                      scd_type='type2' if dim_type == 'slowly_changing' else None,
                      description=tdesc, status='active', row_count=trows,
                      refresh_frequency='daily',
                      last_refresh=timezone.now() - timedelta(hours=2),
                      technical_owner=dev_user,
                      columns=[{'name': 'id_sk', 'type': 'integer'},
                                {'name': 'code_naturel', 'type': 'varchar(50)'},
                                {'name': 'libelle', 'type': 'varchar(200)'},
                                {'name': 'est_courant', 'type': 'boolean'}],
                      tags=['dimension', 'fibre']),
    )
    dw_tables[tname] = t
    if c: print(f"  [OK] {tname} [DIMENSION]")

fact_incidents_tbl     = FactTable.objects.get(pk=dw_tables['fact_incidents_reseau'].pk)
fact_consommation_tbl  = FactTable.objects.get(pk=dw_tables['fact_consommation_bp'].pk)
fact_interventions_tbl = FactTable.objects.get(pk=dw_tables['fact_interventions'].pk)
dim_temps_tbl       = DimensionTable.objects.get(pk=dw_tables['dim_temps'].pk)
dim_client_tbl      = DimensionTable.objects.get(pk=dw_tables['dim_client'].pk)
dim_equip_tbl       = DimensionTable.objects.get(pk=dw_tables['dim_equipement'].pk)
dim_loc_tbl         = DimensionTable.objects.get(pk=dw_tables['dim_localisation'].pk)
dim_tech_tbl        = DimensionTable.objects.get(pk=dw_tables['dim_technicien'].pk)

# ---------------------------------------------------------
# 7. MESURES
# ---------------------------------------------------------
print("\n[7/14] Mesures...")

measures_spec = [
    (fact_incidents_tbl,    'Nombre Incidents',           'nb_incidents',            'count', 'Incidents', ''),
    (fact_incidents_tbl,    'Duree Coupure Totale',       'duree_coupure_h',         'sum',   'Heures',    '#,##0.0'),
    (fact_incidents_tbl,    'Taux Resolution Incidents',  'taux_resolution_pct',     'avg',   '%',         '0.0%'),
    (fact_incidents_tbl,    'Clients Impactes',           'clients_affectes',        'sum',   'Clients',   '#,##0'),
    (fact_consommation_tbl, 'Debit Montant Moyen',        'debit_montant_mbps',      'avg',   'Mbps',      '#,##0.00'),
    (fact_consommation_tbl, 'Debit Descendant Moyen',     'debit_descendant_mbps',   'avg',   'Mbps',      '#,##0.00'),
    (fact_consommation_tbl, 'Taux Utilisation Reseau',    'taux_utilisation_pct',    'avg',   '%',         '0.0%'),
    (fact_consommation_tbl, 'Data Transferee Totale',     'data_transferee_gb',      'sum',   'Go',        '#,##0.000'),
    (fact_interventions_tbl,'Nombre Interventions',       'nb_interventions',        'count', 'Interv.',   '#,##0'),
    (fact_interventions_tbl,'Duree Moyenne Intervention', 'duree_intervention_h',    'avg',   'Heures',    '#,##0.0'),
    (fact_interventions_tbl,'Cout Total Interventions',   'cout_total_da',           'sum',   'DA',        '#,##0'),
    (fact_interventions_tbl,'Taux Resolution Terrain',    'taux_resolution_terrain', 'avg',   '%',         '0.0%'),
]

measures = {}
for ft, mname, mcol, magg, munit, mfmt in measures_spec:
    m, c = Measure.objects.get_or_create(
        fact_table=ft, name=mname,
        defaults=dict(column=mcol, aggregation_type=magg, alias=mname,
                      description=f'Agregation {magg.upper()} sur {mcol}',
                      unit=munit, format_string=mfmt, is_active=True),
    )
    measures[mname] = m
    if c: print(f"  [OK] {mname}")

# ---------------------------------------------------------
# 8. PIPELINES ETL (prefixe ETL_)
# ---------------------------------------------------------
print("\n[8/14] Pipelines ETL...")

pipelines_spec = [
    dict(name='ETL_Incidents_Reseau',
         description='Extrait les incidents depuis SRC_Production_PostgreSQL, normalise et charge dans fact_incidents_reseau.',
         pipeline_type='etl', status='active', source=src_pg,
         schedule_enabled=True, schedule_frequency='daily', schedule_cron='0 2 * * *',
         priority=1, category='Reseau', tags=['incidents', 'reseau', 'critique'],
         execution_count=42, success_count=39, failure_count=3,
         avg_duration_seconds=145.2, total_rows_processed=28640, data_quality_score=91),
    dict(name='ETL_Consommation_Bande_Passante',
         description='Collecte les metriques IoT depuis SRC_IoT_Capteurs_Fibre, agrege par noeud/jour et charge dans fact_consommation_bp.',
         pipeline_type='etl', status='active', source=src_iot,
         schedule_enabled=True, schedule_frequency='hourly', schedule_cron='0 * * * *',
         priority=2, category='Performance', tags=['bande-passante', 'iot', 'metriques'],
         execution_count=1008, success_count=985, failure_count=23,
         avg_duration_seconds=38.7, total_rows_processed=1240000, data_quality_score=87),
    dict(name='ETL_Interventions_Techniques',
         description='Synchronise les interventions terrain depuis SRC_Production_PostgreSQL, calcule MTTR et alimente fact_interventions.',
         pipeline_type='etl', status='active', source=src_pg,
         schedule_enabled=True, schedule_frequency='daily', schedule_cron='30 1 * * *',
         priority=2, category='Terrain', tags=['interventions', 'techniciens', 'terrain'],
         execution_count=42, success_count=42, failure_count=0,
         avg_duration_seconds=89.4, total_rows_processed=18720, data_quality_score=98),
    dict(name='ETL_Alertes_Securite_Kafka',
         description='Consomme SRC_Kafka_Alertes_Securite, detecte les anomalies et charge dans la table de faits securite.',
         pipeline_type='etl', status='active', source=src_kafka,
         schedule_enabled=True, schedule_frequency='realtime', schedule_cron='',
         priority=1, category='Securite', tags=['alertes', 'securite', 'kafka', 'critique'],
         execution_count=8640, success_count=8598, failure_count=42,
         avg_duration_seconds=2.3, total_rows_processed=324580, data_quality_score=94),
    dict(name='ETL_Clients_CSV_Dimension',
         description='Charge les exports SRC_CRM_Clients_CSV dans dim_client avec gestion SCD Type 2 pour historique des changements.',
         pipeline_type='etl', status='active', source=src_csv,
         schedule_enabled=True, schedule_frequency='monthly', schedule_cron='0 3 1 * *',
         priority=3, category='Clients', tags=['clients', 'crm', 'scd2'],
         execution_count=6, success_count=5, failure_count=1,
         avg_duration_seconds=312.8, total_rows_processed=42380, data_quality_score=82),
]

pipelines = {}
for pspec in pipelines_spec:
    name = pspec.pop('name')
    p, c = ETLPipeline.objects.get_or_create(name=name, defaults=dict(
        **pspec,
        last_execution=timezone.now() - timedelta(hours=2),
        next_execution=timezone.now() + timedelta(hours=22),
        owner=dev_user, created_by=dev_user, team=team_data,
        notifications_enabled=True, notify_on_failure=True,
    ))
    pspec['name'] = name
    pipelines[name] = p
    if c: print(f"  [OK] {name}")

# ---------------------------------------------------------
# 9. JOURNAUX D'EXECUTION
# ---------------------------------------------------------
print("\n[9/14] Journaux d'execution...")

etl_inc  = pipelines['ETL_Incidents_Reseau']
etl_cons = pipelines['ETL_Consommation_Bande_Passante']
etl_alrt = pipelines['ETL_Alertes_Securite_Kafka']

exec_count = 0

if not ExecutionLog.objects.filter(pipeline=etl_inc).exists():
    history = [
        (0, 'completed', 'schedule', 28640, 28597, 142.3, ''),
        (1, 'completed', 'schedule', 28512, 28512, 138.7, ''),
        (2, 'failed',    'schedule', 15000,     0,  45.2,
         'ConnectionError: Timeout 30s sur 192.168.224.128:5432 - verifiez la disponibilite du serveur PostgreSQL.'),
        (3, 'completed', 'manual',   28400, 28400, 155.1, ''),
        (4, 'completed', 'schedule', 28380, 28380, 141.9, ''),
        (5, 'completed', 'schedule', 28290, 28290, 139.4, ''),
        (6, 'completed', 'schedule', 28150, 28148, 144.2, ''),
    ]
    for days, status, trig, rr, rw, dur, err in history:
        started   = timezone.now() - timedelta(days=days, hours=2)
        completed = started + timedelta(seconds=dur)
        ExecutionLog.objects.create(
            pipeline=etl_inc,
            execution_id=f'exec-inc-{uuid.uuid4().hex[:8]}',
            status=status, triggered_by=trig,
            triggered_by_user=admin_user if trig == 'manual' else None,
            rows_read=rr, rows_written=rw, rows_errors=max(rr - rw, 0),
            duration_seconds=dur, started_at=started,
            completed_at=completed if status != 'running' else None,
            error_message=err,
            result_summary={'source': 'incidents_reseau', 'target': 'fact_incidents_reseau',
                            'rows_new': rw // 2, 'rows_updated': rw // 2},
            transformation_logs=[
                {'transformation': 'Filtrage doublons',           'status': 'ok', 'timestamp': started.isoformat(), 'details': {'removed': rr - rw}},
                {'transformation': 'Normalisation severite',      'status': 'ok', 'timestamp': (started + timedelta(seconds=10)).isoformat(), 'details': {}},
                {'transformation': 'Enrichissement geographique', 'status': 'ok', 'timestamp': (started + timedelta(seconds=30)).isoformat(), 'details': {}},
            ] if status == 'completed' else [],
        )
        exec_count += 1
    print(f"  [OK] {len(history)} executions pour ETL_Incidents_Reseau")

if not ExecutionLog.objects.filter(pipeline=etl_cons).exists():
    for h in range(0, 25, 6):
        started  = timezone.now() - timedelta(hours=h)
        duration = 36.4 + (h % 5) * 2.1
        ExecutionLog.objects.create(
            pipeline=etl_cons,
            execution_id=f'exec-cons-{uuid.uuid4().hex[:8]}',
            status='completed', triggered_by='schedule',
            rows_read=52000 + h * 100, rows_written=51980 + h * 100, rows_errors=20,
            duration_seconds=duration, started_at=started,
            completed_at=started + timedelta(seconds=duration),
            result_summary={'source': 'api_iot', 'target': 'fact_consommation_bp'},
            transformation_logs=[{'transformation': 'Agregation horaire-journaliere', 'status': 'ok',
                                   'timestamp': started.isoformat(), 'details': {}}],
        )
        exec_count += 1
    ExecutionLog.objects.create(
        pipeline=etl_cons,
        execution_id=f'exec-cons-run-{uuid.uuid4().hex[:8]}',
        status='running', triggered_by='schedule',
        rows_read=12000, rows_written=0, rows_errors=0,
        duration_seconds=0, started_at=timezone.now() - timedelta(minutes=3),
    )
    exec_count += 1
    print(f"  [OK] Executions pour ETL_Consommation_Bande_Passante (dont 1 en cours)")

if not ExecutionLog.objects.filter(pipeline=etl_alrt).exists():
    started_f = timezone.now() - timedelta(hours=5)
    ExecutionLog.objects.create(
        pipeline=etl_alrt,
        execution_id=f'exec-alrt-fail-{uuid.uuid4().hex[:8]}',
        status='failed', triggered_by='schedule',
        rows_read=850, rows_written=0, rows_errors=850, duration_seconds=12.1,
        started_at=started_f, completed_at=started_f + timedelta(seconds=12),
        error_message='KafkaException: Leader Not Available sur topic sotifibre.alertes.securite partition 0.',
        error_traceback='Traceback:\n  File "etl/kafka_consumer.py", line 84\nkafka.errors.KafkaError: LEADER_NOT_AVAILABLE',
    )
    started_r = timezone.now() - timedelta(hours=4, minutes=45)
    ExecutionLog.objects.create(
        pipeline=etl_alrt,
        execution_id=f'exec-alrt-ok-{uuid.uuid4().hex[:8]}',
        status='completed', triggered_by='retry',
        rows_read=1240, rows_written=1238, rows_errors=2, duration_seconds=4.8,
        started_at=started_r, completed_at=started_r + timedelta(seconds=5),
        result_summary={'events_processed': 1238, 'anomalies_detected': 7},
    )
    exec_count += 2
    print(f"  [OK] Executions pour ETL_Alertes_Securite_Kafka (1 echouee, 1 reessai OK)")

print(f"  Total : {exec_count}+ logs crees")

# ---------------------------------------------------------
# 10. SCHEMAS DIMENSIONNELS
# ---------------------------------------------------------
print("\n[10/14] Schemas dimensionnels...")

schema_inc, c = DimensionalSchema.objects.get_or_create(
    name='schema_incidents_reseau',
    defaults=dict(
        description='Schema en etoile - incidents reseau fibre relies aux dimensions temps, localisation, equipement et client.',
        schema_type='star', status='active', version='2.1',
        grain='transaction', default_join_type='left',
        category='Reseau', business_domain='Operations Reseau',
        tags=['incidents', 'reseau', 'star'],
        measure_config=[
            {'name': 'Nombre Incidents',     'column': 'nb_incidents',        'aggregation': 'COUNT'},
            {'name': 'Duree Coupure Totale', 'column': 'duree_coupure_h',     'aggregation': 'SUM'},
            {'name': 'Taux Resolution',      'column': 'taux_resolution_pct', 'aggregation': 'AVG'},
        ],
        owner=analyst_user,
    ),
)
schema_inc.fact_tables.add(fact_incidents_tbl)
schema_inc.dimension_tables.add(dim_temps_tbl, dim_loc_tbl, dim_equip_tbl, dim_client_tbl)
schema_inc.measures.add(
    measures['Nombre Incidents'], measures['Duree Coupure Totale'],
    measures['Taux Resolution Incidents'], measures['Clients Impactes'],
)
if c: print("  [OK] schema_incidents_reseau")

schema_cons, c = DimensionalSchema.objects.get_or_create(
    name='schema_consommation_bp',
    defaults=dict(
        description='Schema en etoile - consommation bande passante par noeud reseau agregee quotidiennement.',
        schema_type='star', status='active', version='1.3',
        grain='daily', default_join_type='left',
        category='Performance', business_domain='Infrastructure Reseau',
        tags=['bande-passante', 'performance', 'star'],
        measure_config=[
            {'name': 'Debit Montant Moyen',    'column': 'debit_montant_mbps',    'aggregation': 'AVG'},
            {'name': 'Debit Descendant Moyen', 'column': 'debit_descendant_mbps', 'aggregation': 'AVG'},
            {'name': 'Taux Utilisation',       'column': 'taux_utilisation_pct',  'aggregation': 'AVG'},
            {'name': 'Data Transferee',        'column': 'data_transferee_gb',     'aggregation': 'SUM'},
        ],
        owner=analyst_user,
    ),
)
schema_cons.fact_tables.add(fact_consommation_tbl)
schema_cons.dimension_tables.add(dim_temps_tbl, dim_equip_tbl, dim_loc_tbl)
schema_cons.measures.add(
    measures['Debit Montant Moyen'], measures['Debit Descendant Moyen'],
    measures['Taux Utilisation Reseau'], measures['Data Transferee Totale'],
)
if c: print("  [OK] schema_consommation_bp")

schema_int, c = DimensionalSchema.objects.get_or_create(
    name='schema_interventions_techniques',
    defaults=dict(
        description='Schema en flocon - interventions terrain enrichies par les dimensions technicien, incident et localisation.',
        schema_type='snowflake', status='active', version='1.0',
        grain='transaction', default_join_type='left',
        category='Terrain', business_domain='Gestion Terrain',
        tags=['interventions', 'techniciens', 'snowflake'],
        measure_config=[
            {'name': 'Nombre Interventions', 'column': 'nb_interventions',     'aggregation': 'COUNT'},
            {'name': 'Duree Moyenne',        'column': 'duree_intervention_h', 'aggregation': 'AVG'},
            {'name': 'Cout Total',           'column': 'cout_total_da',        'aggregation': 'SUM'},
        ],
        owner=analyst_user,
    ),
)
schema_int.fact_tables.add(fact_interventions_tbl)
schema_int.dimension_tables.add(dim_temps_tbl, dim_tech_tbl, dim_loc_tbl)
schema_int.measures.add(
    measures['Nombre Interventions'], measures['Duree Moyenne Intervention'],
    measures['Cout Total Interventions'],
)
if c: print("  [OK] schema_interventions_techniques")

# ---------------------------------------------------------
# 11. TABLEAUX DE BORD (prefixe DSB_)
# ---------------------------------------------------------
print("\n[11/14] Tableaux de bord...")

dashboards_spec = [
    dict(slug='dsb-operationnel-reseau',
         name='DSB_Operationnel_Reseau',
         description='Vue operationnelle temps reel du reseau fibre SOTIFibre : incidents actifs, disponibilite, bande passante et alertes.',
         dashboard_type='operational', theme='dark',
         refresh_frequency='5min', auto_refresh=True,
         category='Reseau', access_level='team', view_count=1284,
         tags=['operationnel', 'reseau', 'temps-reel']),
    dict(slug='dsb-performance-kpis',
         name='DSB_Performance_KPIs_Reseau',
         description='Indicateurs cles de performance reseau fibre : taux de disponibilite, MTTR, satisfaction client et evolution des debits.',
         dashboard_type='executive', theme='light',
         refresh_frequency='daily', auto_refresh=False,
         category='Direction', access_level='public', view_count=892,
         tags=['kpi', 'performance', 'direction']),
    dict(slug='dsb-incidents-fibre',
         name='DSB_Incidents_Fibre_Optique',
         description='Analyse detaillee des incidents reseau fibre : distribution geographique, causes, evolution temporelle et efficacite des equipes.',
         dashboard_type='analytical', theme='light',
         refresh_frequency='hourly', auto_refresh=True,
         category='Qualite', access_level='team', view_count=456,
         tags=['incidents', 'analyse', 'qualite']),
    dict(slug='dsb-consommation-bp',
         name='DSB_Consommation_Bande_Passante',
         description='Cartographie et analyse de la consommation bande passante par zone geographique, noeud et type offre.',
         dashboard_type='analytical', theme='light',
         refresh_frequency='hourly', auto_refresh=True,
         category='Reseau', access_level='team', view_count=321,
         tags=['bande-passante', 'geographie', 'reseau']),
]

dashboards = {}
for dspec in dashboards_spec:
    slug = dspec.pop('slug')
    name = dspec['name']
    db, c = Dashboard.objects.get_or_create(slug=slug, defaults=dict(
        **dspec, status='published',
        layout={'columns': 12, 'row_height': 50},
        owner=analyst_user if dspec['dashboard_type'] == 'analytical' else admin_user,
        team=team_bi,
        allow_export=True, default_export_format='pdf',
        last_viewed=timezone.now() - timedelta(hours=1),
        published_at=timezone.now() - timedelta(days=14),
        published_by=admin_user,
    ))
    dspec['slug'] = slug
    dashboards[slug] = db
    if c:
        db.allowed_users.add(admin_user, dev_user, analyst_user, director_user)
        print(f"  [OK] {name}")

db_op  = dashboards['dsb-operationnel-reseau']
db_kpi = dashboards['dsb-performance-kpis']
db_inc = dashboards['dsb-incidents-fibre']
db_bp  = dashboards['dsb-consommation-bp']

# ---------------------------------------------------------
# 12. WIDGETS
# ---------------------------------------------------------
print("\n[12/14] Widgets...")

widgets_spec = [
    # -- DSB_Operationnel_Reseau --
    (db_op, 'Disponibilite Reseau Temps Reel', 'gauge', schema_inc,
     {'type': 'gauge', 'min': 0, 'max': 100, 'unit': '%',
      'thresholds': [95, 99], 'colors': ['#dc3545', '#fd7e14', '#28a745']},
     {'x': 0, 'y': 0, 'w': 3, 'h': 2}),
    (db_op, 'Incidents Actifs par Severite', 'chart', schema_inc,
     {'type': 'bar', 'axis_x': 'severite', 'axis_y': 'nb_incidents'},
     {'x': 3, 'y': 0, 'w': 4, 'h': 2}),
    (db_op, 'Bande Passante Utilisee 24h', 'chart', schema_cons,
     {'type': 'area', 'axis_x': 'horodatage', 'axis_y': 'taux_utilisation_pct', 'smooth': True},
     {'x': 7, 'y': 0, 'w': 5, 'h': 2}),
    (db_op, 'Alertes Securite en Cours', 'chart', schema_inc,
     {'type': 'table', 'columns': ['type_alerte', 'zone', 'horodatage', 'statut']},
     {'x': 0, 'y': 2, 'w': 6, 'h': 3}),
    (db_op, 'Debit par Noeud - Top 10', 'chart', schema_cons,
     {'type': 'bar', 'orientation': 'horizontal', 'axis_x': 'noeud', 'axis_y': 'debit_descendant_mbps', 'limit': 10},
     {'x': 6, 'y': 2, 'w': 6, 'h': 3}),
    # -- DSB_Performance_KPIs_Reseau --
    (db_kpi, 'Evolution Incidents Mensuels', 'chart', schema_inc,
     {'type': 'line', 'axis_x': 'mois', 'axis_y': 'nb_incidents', 'smooth': True},
     {'x': 0, 'y': 0, 'w': 6, 'h': 3}),
    (db_kpi, 'Repartition par Type Incident', 'chart', schema_inc,
     {'type': 'pie', 'field': 'type_incident', 'value': 'nb_incidents', 'donut': True},
     {'x': 6, 'y': 0, 'w': 6, 'h': 3}),
    (db_kpi, 'Tendance Debit Reseau', 'chart', schema_cons,
     {'type': 'line', 'axis_x': 'date', 'axis_y': ['debit_montant_mbps', 'debit_descendant_mbps']},
     {'x': 0, 'y': 3, 'w': 8, 'h': 3}),
    (db_kpi, 'Heatmap Incidents par Wilaya', 'chart', schema_inc,
     {'type': 'heatmap', 'axis_x': 'wilaya', 'axis_y': 'jour_semaine', 'value': 'nb_incidents'},
     {'x': 8, 'y': 3, 'w': 4, 'h': 3}),
    # -- DSB_Incidents_Fibre_Optique --
    (db_inc, 'Incidents par Wilaya - Carte', 'chart', schema_inc,
     {'type': 'map', 'geography': 'dz', 'value': 'nb_incidents'},
     {'x': 0, 'y': 0, 'w': 8, 'h': 4}),
    (db_inc, 'MTTR par Type Incident', 'chart', schema_int,
     {'type': 'bar', 'axis_x': 'type_incident', 'axis_y': 'duree_intervention_h'},
     {'x': 8, 'y': 0, 'w': 4, 'h': 4}),
    (db_inc, 'Top 10 Zones Incidents', 'chart', schema_inc,
     {'type': 'bar', 'orientation': 'horizontal', 'axis_x': 'zone', 'axis_y': 'nb_incidents', 'limit': 10},
     {'x': 0, 'y': 4, 'w': 6, 'h': 3}),
    (db_inc, 'Evolution Hebdomadaire Incidents', 'chart', schema_inc,
     {'type': 'line', 'axis_x': 'semaine', 'axis_y': 'nb_incidents', 'smooth': True},
     {'x': 6, 'y': 4, 'w': 6, 'h': 3}),
    # -- DSB_Consommation_Bande_Passante --
    (db_bp, 'Consommation par Wilaya', 'chart', schema_cons,
     {'type': 'map', 'geography': 'dz', 'value': 'taux_utilisation_pct'},
     {'x': 0, 'y': 0, 'w': 7, 'h': 4}),
    (db_bp, 'Top 5 Noeuds Saturation', 'chart', schema_cons,
     {'type': 'bar', 'axis_x': 'noeud', 'axis_y': 'taux_utilisation_pct', 'limit': 5},
     {'x': 7, 'y': 0, 'w': 5, 'h': 4}),
    (db_bp, 'Evolution Debit Journalier', 'chart', schema_cons,
     {'type': 'line', 'axis_x': 'date', 'axis_y': 'data_transferee_gb', 'smooth': True},
     {'x': 0, 'y': 4, 'w': 12, 'h': 3}),
]

wcount = 0
for db, wname, wtype, schema, config, pos in widgets_spec:
    if not Widget.objects.filter(dashboard=db, name=wname).exists():
        Widget.objects.create(
            name=wname, widget_type=wtype, dashboard=db,
            dimensional_schema=schema, config=config, position=pos,
            is_enabled=True, cache_enabled=True,
            cache_ttl_seconds=300, refresh_on_load=True,
        )
        wcount += 1

print(f"  [OK] {wcount} widgets crees")

# ---------------------------------------------------------
# 13. KPIs
# ---------------------------------------------------------
print("\n[13/14] KPIs...")

kpis_spec = [
    (db_op,  'KPI_Disponibilite_Reseau',        'percentage', schema_inc,  measures['Taux Resolution Incidents'],
     99.2, 99.0, 99.5, 95.0, '%', 1, 'up',
     'Disponibilite actuelle du reseau fibre SOTIFibre'),
    (db_op,  'KPI_Incidents_Actifs',             'number',     schema_inc,  measures['Nombre Incidents'],
     12.0, None, 20.0, 30.0, 'Incidents', 0, 'down',
     'Nombre incidents reseau en cours de traitement'),
    (db_op,  'KPI_Bande_Passante_Utilisee',      'percentage', schema_cons, measures['Taux Utilisation Reseau'],
     73.4, None, 80.0, 90.0, '%', 1, 'down',
     'Taux moyen utilisation de la bande passante reseau'),
    (db_op,  'KPI_MTTR_Temps_Reparation',        'number',     schema_int,  measures['Duree Moyenne Intervention'],
     4.2, None, 6.0, 8.0, 'Heures', 1, 'down',
     'Duree moyenne de resolution incident reseau'),
    (db_kpi, 'KPI_Clients_Actifs_Fibre',         'number',     schema_int,  None,
     42380.0, 45000.0, None, None, 'Abonnes', 0, 'up',
     'Nombre total abonnes fibre actifs chez SOTIFibre'),
    (db_kpi, 'KPI_Satisfaction_Client',          'percentage', schema_int,  None,
     87.3, 90.0, 85.0, 75.0, '%', 1, 'up',
     'Score de satisfaction client - enquetes mensuelles'),
    (db_kpi, 'KPI_Revenu_Mensuel_Fibre',         'currency',   schema_int,  None,
     18_450_000.0, 20_000_000.0, None, None, 'DA', 0, 'up',
     'Chiffre affaires mensuel des abonnements fibre'),
    (db_kpi, 'KPI_Debit_Moyen_Reseau',           'number',     schema_cons, measures['Debit Descendant Moyen'],
     287.4, None, None, None, 'Mbps', 1, 'up',
     'Debit descendant moyen observe sur ensemble du reseau'),
    (db_inc, 'KPI_Incidents_Resolus_Journee',    'number',     schema_inc,  measures['Nombre Incidents'],
     34.0, None, None, None, 'Incidents', 0, 'up',
     'Nombre incidents clotures dans la journee'),
    (db_inc, 'KPI_Incidents_Critiques_Ouverts',  'number',     schema_inc,  measures['Nombre Incidents'],
     3.0, None, 5.0, 10.0, 'Critiques', 0, 'down',
     'Incidents de severite critique actuellement ouverts'),
    (db_inc, 'KPI_Taux_Resolution_24h',          'percentage', schema_inc,  measures['Taux Resolution Incidents'],
     91.2, 95.0, 85.0, 70.0, '%', 1, 'up',
     'Pourcentage incidents resolus en moins de 24 heures'),
    (db_inc, 'KPI_Temps_Moyen_Detection',        'number',     schema_inc,  None,
     8.4, None, 15.0, 30.0, 'Minutes', 1, 'down',
     'Delai moyen entre apparition et detection incident'),
    (db_bp,  'KPI_Bande_Passante_Totale',        'number',    schema_cons, measures['Data Transferee Totale'],
     1842.7, None, None, None, 'To/mois', 1, 'up',
     'Volume total de donnees transferees sur le reseau ce mois'),
    (db_bp,  'KPI_Noeuds_En_Saturation',         'number',     schema_cons, measures['Taux Utilisation Reseau'],
     7.0, None, 10.0, 20.0, 'Noeuds', 0, 'down',
     'Nombre de noeuds reseau avec taux utilisation superieur a 90%'),
]

kcount = 0
for (db, kname, ktype, schema, measure, cur, target, warn, crit, unit, dec, trend, desc) in kpis_spec:
    if not KPI.objects.filter(dashboard=db, name=kname).exists():
        KPI.objects.create(
            name=kname, description=desc, kpi_type=ktype,
            dimensional_schema=schema, measure=measure,
            config={'type': ktype, 'display_format': 'card'},
            target_value=target, warning_threshold=warn, critical_threshold=crit,
            unit=unit, decimal_places=dec,
            track_trend=True, trend_direction=trend,
            trend_period='previous_period', dashboard=db,
            current_value=cur,
            previous_value=round(cur * (0.95 if trend == 'up' else 1.05), 2),
            trend_percentage=5.0 if trend == 'up' else -5.0,
            last_calculated=timezone.now() - timedelta(minutes=30),
            is_active=True, tags=['sotifibre', ktype],
        )
        kcount += 1

print(f"  [OK] {kcount} KPIs crees")

# ---------------------------------------------------------
# 14. RAPPORTS + NOTIFICATIONS + FAVORIS
# ---------------------------------------------------------
print("\n[14/14] Rapports, notifications, favoris...")

reports_spec = [
    (db_kpi, 'Rapport Mensuel Performances Reseau',
     'pdf', '0 7 1 * *',
     ['direction@sotifibre.dz', 'admin@sotifibre.dz', 'analyste@sotifibre.dz'],
     ['mensuel', 'performance']),
    (db_inc, 'Rapport Hebdomadaire Incidents Reseau',
     'pdf', '0 8 * * 1',
     ['admin@sotifibre.dz', 'analyste@sotifibre.dz'],
     ['hebdomadaire', 'incidents']),
    (db_op, 'Rapport Quotidien Operationnel',
     'pdf', '0 18 * * *',
     ['admin@sotifibre.dz', 'dev.bi@sotifibre.dz'],
     ['quotidien', 'operationnel']),
    (db_kpi, 'Export KPIs Trimestriels Excel',
     'excel', '0 9 1 1,4,7,10 *',
     ['direction@sotifibre.dz'],
     ['trimestriel', 'kpi']),
]

rcount = 0
for db, rname, rfmt, rsched, recips, rtags in reports_spec:
    if not Report.objects.filter(name=rname).exists():
        Report.objects.create(
            name=rname, dashboard=db, format=rfmt, schedule=rsched,
            recipients=recips, is_active=True, owner=admin_user, tags=rtags,
            generation_count=3, last_generated=timezone.now() - timedelta(days=7),
        )
        rcount += 1
print(f"  [OK] {rcount} rapports")

notifs_spec = [
    (admin_user,   'pipeline_complete', 'Pipeline ETL_Incidents_Reseau termine',
     'Le pipeline ETL_Incidents_Reseau a traite 28 597 lignes en 142s. Score qualite : 91/100.',
     'medium', etl_inc, None, None, 'delivered', 1),
    (admin_user,   'pipeline_failed', 'Echec Pipeline - Action requise',
     'Le pipeline ETL_Alertes_Securite_Kafka a echoue. Erreur : Leader Not Available. Verifiez le broker Kafka.',
     'high', etl_alrt, None, None, 'pending', 0),
    (analyst_user, 'kpi_alert', 'KPI_Incidents_Critiques_Ouverts - Seuil approche',
     'Le KPI KPI_Incidents_Critiques_Ouverts atteint 3 incidents (seuil avertissement : 5). Surveillance recommandee.',
     'medium', None, None, None, 'pending', 0),
    (director_user,'report_ready', 'Rapport mensuel disponible',
     'Le rapport Rapport Mensuel Performances Reseau est pret. Telechargez le PDF depuis la plateforme.',
     'low', None, None, None, 'delivered', 1),
    (admin_user,   'data_refresh', 'Rafraichissement donnees termine',
     'La source SRC_Production_PostgreSQL a ete synchronisee - 185 420 lignes indexees.',
     'low', None, None, None, 'delivered', 1),
    (dev_user,     'anomaly_detected', 'Anomalie - Debit Reseau',
     'OLT-ALGER-03 : debit montant 847 Mbps vs moyenne 287 Mbps (+195%). Verification recommandee.',
     'high', None, None, None, 'pending', 0),
    (analyst_user, 'kpi_target_reached', 'Objectif KPI atteint - Disponibilite',
     'Le KPI KPI_Disponibilite_Reseau atteint 99.2%, depassant l objectif de 99.0%. Performance conforme aux SLA.',
     'low', None, None, None, 'read', 1),
    (admin_user,   'system_alert', 'Alerte Disque Data Warehouse',
     'Espace disque sotifibre_dw : 2.45 Go / 3 Go (81.7%). Prevoir une extension de capacite.',
     'high', None, None, None, 'pending', 0),
]

ncount = 0
for i, (recip, ntype, ntitle, nmsg, nprio, pipeline, dash, kpi_obj, nstatus, read_flag) in enumerate(notifs_spec):
    Notification.objects.create(
        recipient=recip, notification_type=ntype, title=ntitle,
        message=nmsg, priority=nprio,
        pipeline=pipeline, dashboard=dash, kpi=kpi_obj,
        status=nstatus,
        sent_at=timezone.now() - timedelta(hours=i * 2),
        read_at=timezone.now() - timedelta(hours=i * 2 - 1) if read_flag else None,
    )
    ncount += 1
print(f"  [OK] {ncount} notifications")

for db in dashboards.values():
    if not Favorite.objects.filter(user=admin_user, dashboard=db, kpi=None, report=None).exists():
        Favorite.objects.create(user=admin_user, dashboard=db)
for db in [db_op, db_kpi]:
    if not Favorite.objects.filter(user=analyst_user, dashboard=db, kpi=None, report=None).exists():
        Favorite.objects.create(user=analyst_user, dashboard=db)
print("  [OK] Favoris")

# ---------------------------------------------------------
# RESUME FINAL
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("  SEEDING TERMINE AVEC SUCCES")
print("=" * 60)
print(f"  Utilisateurs     : {User.objects.count()}")
print(f"  Equipes          : {Team.objects.count()}")
print(f"  Sources donnees  : {DataSource.objects.count()}")
print(f"  Tables donnees   : {DataTable.objects.count()}")
print(f"  Schemas DW       : {DataWarehouseSchema.objects.count()}")
print(f"  Tables DW        : {DataWarehouseTable.objects.count()}")
print(f"  Mesures          : {Measure.objects.count()}")
print(f"  Pipelines ETL    : {ETLPipeline.objects.count()}")
print(f"  Executions ETL   : {ExecutionLog.objects.count()}")
print(f"  Schemas Dim.     : {DimensionalSchema.objects.count()}")
print(f"  Dashboards       : {Dashboard.objects.count()}")
print(f"  Widgets          : {Widget.objects.count()}")
print(f"  KPIs             : {KPI.objects.count()}")
print(f"  Rapports         : {Report.objects.count()}")
print(f"  Notifications    : {Notification.objects.count()}")
print("=" * 60)
print("  Connexion : admin@sotifibre.dz / SOTIFibre@2026!")
print("  Admin Django : admin@admin.com / admin123456")
print("=" * 60 + "\n")
