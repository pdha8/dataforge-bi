#!/usr/bin/env python
"""
SOTIFibre BI Platform — Enrichissement métier pour PFE
=====================================================

Ajoute des données métier réalistes au-dessus du seed standard :
- Clients réels du secteur télécom algérien (SONATRACH, Algérie Télécom, etc.)
- Requêtes SQL professionnelles (Top clients, marge mensuelle, churn, etc.)
- KPIs cibles + seuils warning/critical alignés sur de vrais objectifs métier
- Pipelines ETL Source → DW avec planification CRON
- Tableaux de bord par domaine (Ventes, Finance, Opérations, RH)

Usage : python manage.py shell < seed_enrichment.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.data_sources.models import DataSource, DataQuery, PowerQuery
from apps.visualizations.models import Dashboard, KPI, Report

User = get_user_model()

# ─── Admin réutilisé ────────────────────────────────────────
admin = User.objects.filter(email='admin@sotifibre.dz').first() or User.objects.filter(is_superuser=True).first()
if not admin:
    print("⚠️  Aucun admin trouvé — exécute d'abord le seed standard.")
    sys.exit(0)

# ─── 1. Sources métier ──────────────────────────────────────
SOURCES = [
    {
        'name': 'SRC_CRM_SONATRACH',
        'source_type': 'postgresql',
        'description': "Base CRM clients grands comptes SONATRACH (5 000+ contrats fibre dédiée)",
    },
    {
        'name': 'SRC_ERP_ALGERIE_TELECOM',
        'source_type': 'oracle',
        'description': "ERP commercial Algérie Télécom — facturation et commandes",
    },
    {
        'name': 'SRC_NETFLOW_BACKBONE',
        'source_type': 'kafka',
        'description': "Flux NetFlow temps réel sur le backbone fibre national",
    },
    {
        'name': 'SRC_API_BANQUE_BNA',
        'source_type': 'rest_api',
        'description': "API Banque Nationale d'Algérie pour rapprochements bancaires",
    },
    {
        'name': 'DSB_CLIENTS_ENRICHIS',
        'source_type': 'csv',
        'description': "Export CSV mensuel — segmentation clients enrichie",
    },
]

for s in SOURCES:
    DataSource.objects.get_or_create(
        name=s['name'],
        defaults={**s, 'status': 'active', 'created_by': admin, 'owner': admin},
    )
print(f"✅ {DataSource.objects.count()} sources de données")

# ─── 2. Requêtes SQL métier réalistes ───────────────────────
src_crm = DataSource.objects.filter(name='SRC_CRM_SONATRACH').first()
QUERIES = [
    {
        'name': 'TOP 10 clients par CA annuel 2025',
        'query_type': 'sql',
        'query_text': """
SELECT c.code_client,
       c.raison_sociale,
       c.secteur_activite,
       SUM(f.montant_ht) AS ca_2025_da,
       COUNT(DISTINCT f.id_facture) AS nb_factures
FROM   crm.clients c
JOIN   crm.factures f ON f.client_id = c.id
WHERE  f.date_emission BETWEEN '2025-01-01' AND '2025-12-31'
  AND  f.statut = 'PAYEE'
GROUP  BY c.code_client, c.raison_sociale, c.secteur_activite
ORDER  BY ca_2025_da DESC
LIMIT  10;""".strip(),
    },
    {
        'name': 'Taux de churn mensuel par segment',
        'query_type': 'sql',
        'query_text': """
WITH contrats_actifs AS (
    SELECT segment_client,
           DATE_TRUNC('month', date_souscription) AS mois,
           COUNT(*) AS souscriptions
    FROM   crm.contrats
    GROUP  BY segment_client, mois
),
contrats_resilies AS (
    SELECT segment_client,
           DATE_TRUNC('month', date_resiliation) AS mois,
           COUNT(*) AS resiliations
    FROM   crm.contrats
    WHERE  date_resiliation IS NOT NULL
    GROUP  BY segment_client, mois
)
SELECT a.segment_client,
       a.mois,
       a.souscriptions,
       COALESCE(r.resiliations, 0) AS resiliations,
       ROUND(100.0 * COALESCE(r.resiliations, 0) / NULLIF(a.souscriptions, 0), 2) AS taux_churn_pct
FROM   contrats_actifs a
LEFT   JOIN contrats_resilies r USING (segment_client, mois)
ORDER  BY a.mois DESC, taux_churn_pct DESC;""".strip(),
    },
    {
        'name': 'Marge brute mensuelle par produit',
        'query_type': 'sql',
        'query_text': """
SELECT p.code_produit,
       p.libelle,
       DATE_TRUNC('month', v.date_vente) AS mois,
       SUM(v.quantite * v.prix_unitaire)                   AS ca_brut,
       SUM(v.quantite * p.cout_unitaire)                   AS cout_revient,
       SUM(v.quantite * (v.prix_unitaire - p.cout_unitaire)) AS marge,
       ROUND(100.0 *
             SUM(v.quantite * (v.prix_unitaire - p.cout_unitaire)) /
             NULLIF(SUM(v.quantite * v.prix_unitaire), 0), 2) AS marge_pct
FROM   ventes v
JOIN   produits p ON p.id = v.produit_id
GROUP  BY p.code_produit, p.libelle, mois
ORDER  BY mois DESC, marge DESC;""".strip(),
    },
    {
        'name': 'Disponibilité réseau par PoP (NetFlow)',
        'query_type': 'sql',
        'query_text': """
SELECT pop_name,
       DATE_TRUNC('day', ts) AS jour,
       ROUND(100.0 * SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END)
                   / COUNT(*), 3) AS uptime_pct,
       AVG(latency_ms)            AS latence_avg_ms,
       MAX(latency_ms)            AS latence_max_ms
FROM   netflow.pop_health
WHERE  ts > NOW() - INTERVAL '30 days'
GROUP  BY pop_name, jour
HAVING ROUND(100.0 * SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END)
                   / COUNT(*), 3) < 99.95
ORDER  BY uptime_pct ASC, jour DESC;""".strip(),
    },
]

for q in QUERIES:
    DataQuery.objects.get_or_create(
        name=q['name'],
        defaults={**q, 'data_source': src_crm, 'created_by': admin, 'is_public': True},
    )
print(f"✅ {DataQuery.objects.count()} requêtes SQL métier")

# ─── 3. KPIs avec cibles et seuils ──────────────────────────
KPIS = [
    ('CA mensuel SOTIFibre',             'currency', 1_000_000_000, 900_000_000, 700_000_000, 'DZD'),
    ('Marge brute',                       'percentage', 35.0, 30.0, 25.0, '%'),
    ('Taux de churn',                     'percentage', 2.0, 3.0, 5.0, '%'),  # cibles inversées
    ('NPS (satisfaction client)',         'number', 65, 50, 30, ''),
    ('Disponibilité réseau backbone',     'percentage', 99.99, 99.95, 99.90, '%'),
    ('Nouveaux contrats / mois',          'number', 200, 150, 100, 'contrats'),
    ('Délai moyen de raccordement',       'number', 7, 14, 21, 'jours'),     # cibles inversées
    ('Coût d\'acquisition client (CAC)',  'currency', 15_000, 20_000, 30_000, 'DZD'),
]

for name, kpi_type, target, warn, crit, unit in KPIS:
    KPI.objects.get_or_create(
        name=name,
        defaults={
            'kpi_type': kpi_type,
            'target_value': target,
            'warning_threshold': warn,
            'critical_threshold': crit,
            'unit': unit,
            'owner': admin,
            'description': f"KPI {name} — objectif PFE Sotifibre 2026.",
        },
    )
print(f"✅ {KPI.objects.count()} KPIs avec cibles & seuils")

# ─── 4. Dashboards par domaine ──────────────────────────────
DASHBOARDS = [
    ('DSB_VENTES_2026',     'Ventes & Commercial — Pilotage mensuel'),
    ('DSB_FINANCE_2026',    'Finance & Trésorerie'),
    ('DSB_OPERATIONS_2026', 'Opérations & Réseau'),
    ('DSB_RH_2026',         'Ressources Humaines & Productivité'),
    ('DSB_CLIENTS_360',     'Vision 360° clients (Acquisition / Rétention / Churn)'),
]

for name, desc in DASHBOARDS:
    Dashboard.objects.get_or_create(
        name=name,
        defaults={
            'description': desc,
            'owner': admin,
            'status': 'active',
            'access_level': 'organization',
            'allow_export': True,
            'default_export_format': 'html',  # aligné sur les 6 formats
        },
    )
print(f"✅ {Dashboard.objects.count()} dashboards métier")

# ─── 5. Rapport HTML hebdomadaire ───────────────────────────
dsb_ventes = Dashboard.objects.filter(name='DSB_VENTES_2026').first()
Report.objects.get_or_create(
    name='Rapport hebdomadaire Ventes — Direction Commerciale',
    defaults={
        'description': "Synthèse hebdomadaire envoyée chaque lundi 8h aux directeurs régionaux.",
        'dashboard': dsb_ventes,
        'format': 'html',
        'schedule': '0 8 * * 1',  # tous les lundis à 8h
        'recipients': ['direction@sotifibre.dz', 'commercial@sotifibre.dz', 'pdg@sotifibre.dz'],
        'include_metadata': True,
        'include_filters': True,
        'owner': admin,
    },
)
print(f"✅ {Report.objects.count()} rapports planifiés")

print("\n🎉 Enrichissement métier terminé.")
