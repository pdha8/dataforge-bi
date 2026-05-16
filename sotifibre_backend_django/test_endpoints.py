"""
Test automatique de tous les endpoints API Django
Usage: python test_endpoints.py
"""
import urllib.request
import urllib.error
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"

# --- 1. Authentification ---
def get_token():
    data = json.dumps({"email": "admin@sotifibre.dz", "password": "SOTIFibre@2026!"}).encode()
    req = urllib.request.Request(f"{BASE}/api/auth/jwt/token/", data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["access"]

# --- 2. Liste des endpoints à tester ---
ENDPOINTS = [
    # Users
    ("Users",                   "GET", "/api/users/users/"),
    ("Teams",                   "GET", "/api/users/teams/"),
    ("Roles",                   "GET", "/api/users/roles/"),
    ("Permissions",             "GET", "/api/users/permissions/"),
    ("User Activities",         "GET", "/api/users/activities/"),
    # Data Sources
    ("Sources",                 "GET", "/api/data-sources/sources/"),
    ("Tables",                  "GET", "/api/data-sources/tables/"),
    ("DS Queries",              "GET", "/api/data-sources/queries/"),
    ("DS Star-schemas",         "GET", "/api/data-sources/star-schemas/"),
    ("DS Logs",                 "GET", "/api/data-sources/logs/"),
    ("DS Metrics",              "GET", "/api/data-sources/metrics/"),
    ("Files",                   "GET", "/api/data-sources/files/"),
    ("Power Queries",           "GET", "/api/data-sources/power-queries/"),
    ("Connections",             "GET", "/api/data-sources/connections/"),
    # ETL
    ("Pipelines",               "GET", "/api/etl/pipelines/"),
    ("Transformations",         "GET", "/api/etl/transformations/"),
    ("Executions",              "GET", "/api/etl/executions/"),
    ("Target Schemas ETL",      "GET", "/api/etl/target-schemas/"),
    ("Source Schemas ETL",      "GET", "/api/etl/source-schemas/"),
    ("Pipeline Notifications",  "GET", "/api/etl/notifications/"),
    # Data Warehouse
    ("DW Schemas",              "GET", "/api/data-warehouse/schemas/"),
    ("DW Tables",               "GET", "/api/data-warehouse/tables/"),
    ("DW Fact Tables",          "GET", "/api/data-warehouse/fact-tables/"),
    ("DW Dimension Tables",     "GET", "/api/data-warehouse/dimension-tables/"),
    ("DW Star Schemas",         "GET", "/api/data-warehouse/star-schemas/"),
    ("DW Measures",             "GET", "/api/data-warehouse/measures/"),
    ("DW Attributes",           "GET", "/api/data-warehouse/attributes/"),
    ("DW Aggregations",         "GET", "/api/data-warehouse/aggregations/"),
    ("DW Logs",                 "GET", "/api/data-warehouse/logs/"),
    ("DW Metrics",              "GET", "/api/data-warehouse/metrics/"),
    # Star Schema
    ("Dimensional Schemas",     "GET", "/api/star-schema/dimensional-schemas/"),
    ("Fact Relationships",      "GET", "/api/star-schema/fact-relationships/"),
    ("Dim Hierarchies",         "GET", "/api/star-schema/dimension-hierarchies/"),
    ("Calculations",            "GET", "/api/star-schema/calculations/"),
    ("Galaxies",                "GET", "/api/star-schema/galaxies/"),
    # Visualizations
    ("Dashboards",              "GET", "/api/visualizations/dashboards/"),
    ("Widgets",                 "GET", "/api/visualizations/widgets/"),
    ("KPIs",                    "GET", "/api/visualizations/kpis/"),
    ("Reports",                 "GET", "/api/visualizations/reports/"),
    ("Favorites",               "GET", "/api/visualizations/favorites/"),
    ("Viz Activities",          "GET", "/api/visualizations/activities/"),
    # Notifications
    ("Notifications",           "GET", "/api/notifications/notifications/"),
    ("Notif Channels",          "GET", "/api/notifications/channels/"),
    ("Subscriptions",           "GET", "/api/notifications/subscriptions/"),
    ("Alert Rules",             "GET", "/api/notifications/alerts/"),
    # ML Analytics
    ("ML Models",               "GET", "/api/ml-analytics/models/"),
    ("Forecasts",               "GET", "/api/ml-analytics/forecasts/"),
    ("Anomalies",               "GET", "/api/ml-analytics/anomalies/"),
    ("Segmentations",           "GET", "/api/ml-analytics/segmentations/"),
    ("Recommendations",         "GET", "/api/ml-analytics/recommendations/"),
    ("Training Logs",           "GET", "/api/ml-analytics/training-logs/"),
]

def test_endpoint(name, method, path, token):
    url = BASE + path
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            code = r.getcode()
            body = r.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
                if isinstance(parsed, list):
                    count = f"{len(parsed)} items"
                elif isinstance(parsed, dict) and "count" in parsed:
                    count = f"{parsed['count']} items"
                elif isinstance(parsed, dict) and "results" in parsed:
                    count = f"{len(parsed['results'])} resultats"
                else:
                    count = "JSON OK"
                return ("[OK]    ", code, count, None)
            except json.JSONDecodeError as e:
                return ("[WARN]  ", code, "JSON INVALIDE", str(e)[:100])
    except urllib.error.HTTPError as e:
        code = e.code
        try:
            body = e.read().decode("utf-8", errors="replace")
            err_detail = body[:200]
        except:
            err_detail = str(e)
        if code == 500:
            return ("[ERR500]", code, "ERREUR 500", err_detail)
        elif code == 404:
            return ("[404]   ", code, "NOT FOUND", err_detail[:100])
        elif code == 403:
            return ("[403]   ", code, "FORBIDDEN", err_detail[:100])
        elif code == 401:
            return ("[401]   ", code, "UNAUTHORIZED", err_detail[:100])
        else:
            return (f"[{code}]   ", code, f"HTTP {code}", err_detail[:100])
    except Exception as e:
        return ("[EXC]   ", 0, "EXCEPTION", str(e)[:100])

def main():
    print("=== AUDIT ENDPOINTS API ===\n")
    try:
        token = get_token()
        print("[OK] Token JWT obtenu\n")
    except Exception as e:
        print(f"[ERREUR AUTH] {e}")
        sys.exit(1)

    errors = []
    ok_count = 0

    print(f"{'Statut':<10} {'Code':<5} {'Nom':<28} {'Resultat':<22} Detail erreur")
    print("-" * 100)

    for name, method, path in ENDPOINTS:
        icon, code, result, detail = test_endpoint(name, method, path, token)
        detail_str = f"-> {detail}" if detail else ""
        print(f"{icon} {code:<5} {name:<28} {result:<22} {detail_str}")
        if icon == "[OK]    ":
            ok_count += 1
        else:
            errors.append((icon, code, name, path, detail))

    print(f"\n{'='*100}")
    print(f"[OK]     : {ok_count} / {len(ENDPOINTS)}")
    print(f"[ERREURS]: {len(errors)}")
    if errors:
        print("\n=== DETAIL DES ERREURS ===")
        for icon, code, name, path, detail in errors:
            print(f"\n{icon} [{code}] {name} ({path})")
            if detail:
                print(f"   {detail}")

if __name__ == "__main__":
    main()
