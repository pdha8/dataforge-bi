"""
Convertit l'OpenAPI DataForge en code_summary.yaml pour TestSprite.

Pour chaque tag de l'OpenAPI, génère une "feature" TestSprite contenant la liste
des endpoints associés avec leurs schémas request_body extraits.
"""
import yaml
import re
from collections import defaultdict
from pathlib import Path

SRC = Path(r"C:\PFE pour adoume\dataforge-api-v1.yaml")
DST = Path(r"C:\PFE pour adoume\dataforge_backend\testsprite_tests\tmp\code_summary.yaml")


def resolve_ref(ref: str, schemas: dict) -> dict:
    name = ref.split("/")[-1]
    return schemas.get(name, {})


def schema_to_fields(schema: dict, schemas: dict, depth: int = 0) -> dict:
    """Aplatit un schéma en {field: 'type (required/optional, description)'}."""
    if depth > 2:
        return {"...": "nested object truncated"}

    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"], schemas)

    if schema.get("type") == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        result = {}
        for name, prop in props.items():
            if "$ref" in prop:
                resolved = resolve_ref(prop["$ref"], schemas)
                t = resolved.get("type", "object")
            else:
                t = prop.get("type", "any")
            if t == "array":
                items = prop.get("items", {})
                if "$ref" in items:
                    t = f"array<{items['$ref'].split('/')[-1]}>"
                else:
                    t = f"array<{items.get('type', 'any')}>"
            enum = prop.get("enum")
            req = "required" if name in required else "optional"
            extras = []
            if enum:
                extras.append(f"enum: {enum[:5]}")
            if prop.get("readOnly"):
                extras.append("read-only")
            if prop.get("format"):
                extras.append(f"format: {prop['format']}")
            extra = f" ({', '.join(extras)})" if extras else ""
            result[name] = f"{t}, {req}{extra}"
        return result
    return {}


def main() -> None:
    with SRC.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    paths = spec.get("paths", {})
    schemas = spec.get("components", {}).get("schemas", {})

    # Grouper par tag, en gardant seulement les endpoints "principaux"
    # (pas les variants list/{id}/{id} qui dupliquent l'info)
    by_tag: dict[str, list] = defaultdict(list)
    seen_per_tag: dict[str, set] = defaultdict(set)

    for path, methods in paths.items():
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            tags = op.get("tags", ["untagged"])
            tag = tags[0]

            # Skip PUT/PATCH on detail routes — keep POST/PATCH on collection only
            # to avoid 3x duplication of every resource
            is_detail = "{id}" in path or re.search(r"\{[a-z_]+_id\}", path)
            if is_detail and method.lower() == "patch":
                # Skip: PATCH on detail is just an update — covered by POST on collection
                # for schema purposes
                continue
            if is_detail and method.lower() == "put":
                continue
            if is_detail and method.lower() == "delete":
                continue

            # Dedupe variations like /pipelines/{id}/stats/ → just keep stats once
            key = (method.lower(), path)
            if key in seen_per_tag[tag]:
                continue
            seen_per_tag[tag].add(key)

            endpoint = {
                "method": method.upper(),
                "path": path,
                "description": (op.get("description", "").split("\n")[0][:160]
                                or op.get("summary", "")[:160]
                                or op.get("operationId", ""))[:160],
                "auth_required": True,  # nearly everything is auth-protected
            }

            # Extraire le request body pour POST/PUT/PATCH (seulement les essentiels)
            if method.lower() in ("post", "put", "patch"):
                rb = op.get("requestBody", {})
                content = rb.get("content", {})
                json_schema = content.get("application/json", {}).get("schema", {})
                if json_schema:
                    fields = schema_to_fields(json_schema, schemas)
                    # Seulement garder les required + utiles, max 8 champs
                    if fields:
                        required_only = {k: v for k, v in fields.items() if "required" in v}
                        optional = {k: v for k, v in fields.items() if "required" not in v}
                        kept = dict(list(required_only.items())[:6] + list(optional.items())[:2])
                        if kept:
                            endpoint["request_schema"] = {"body": kept}

            by_tag[tag].append(endpoint)

    # Construire le features array dans le format TestSprite v2
    features = []
    TAG_DESCRIPTIONS = {
        "auth":           "JWT authentication — login, refresh, verify",
        "users":          "Users, roles, teams, permissions, activities",
        "data-sources":   "Data source connections, queries, tables, files",
        "etl":            "ETL pipelines, transformations, executions, notifications",
        "data-warehouse": "Warehouse schemas, dimensions, facts, measures, aggregations",
        "star-schema":    "Dimensional schemas, galaxies, hierarchies, calculations",
        "visualizations": "Dashboards, widgets, KPIs, reports, favorites",
        "notifications":  "User notifications and alert rules",
        "ml-analytics":   "ML models, forecasts, anomalies, segmentations",
    }

    for tag in sorted(by_tag.keys()):
        feature = {
            "name": tag.replace("-", " ").title(),
            "description": TAG_DESCRIPTIONS.get(tag, f"{tag} endpoints"),
            "files": [f"apps/{tag.replace('-', '_')}/views.py"],
            "endpoints": by_tag[tag],
        }
        features.append(feature)

    out = {
        "version": "2",
        "type": "backend",
        "tech_stack": [
            "Python 3.13", "Django 5", "Django REST Framework",
            "djangorestframework-simplejwt (JWT)",
            "drf-spectacular + drf-yasg (OpenAPI)",
            "django-filter", "PostgreSQL",
            "Gunicorn (--workers 1 --preload)",
            "Celery", "Pandas, SQLAlchemy",
            "prophet, xgboost, scikit-learn",
        ],
        "features": features,
        "known_limitations": [
            {"issue": "Render free tier cold start (~25-30s)",
             "location": "deployment",
             "impact": "First request after idle is slow — increase timeouts"},
            {"issue": "Response wrapper: success_response renvoie {status, message, data, timestamp}",
             "location": "apps/core/responses.py",
             "impact": "Les @action custom utilisent ce wrapper. Les endpoints CRUD standard (ModelViewSet list/create/retrieve/update/destroy) renvoient le JSON DRF brut, NON wrapped. Pagination: {status, count, results}. Erreurs: {status:false, message, errors, code}."},
            {"issue": "Mock data sources have no real DB behind them",
             "location": "seed_data.py",
             "impact": "POST /queries/{id}/execute/ peut renvoyer 400 avec erreur de connexion — c'est de la data infra, pas un bug API"},
            {"issue": "User creation requires both username AND password_confirm",
             "location": "apps/users/serializers.py UserCreateSerializer",
             "impact": "Payload doit contenir {username, email, password, password_confirm}"},
            {"issue": "Widget creation requires dashboard FK (NOT null)",
             "location": "apps/visualizations/serializers.py",
             "impact": "POST /widgets/ avec dashboard:null → 400"},
            {"issue": "DimensionalSchema creation requires fact_tables non-empty",
             "location": "apps/star_schema/serializers.py",
             "impact": "Liste vide → 400"},
        ],
    }

    DST.parent.mkdir(parents=True, exist_ok=True)
    with DST.open("w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False, width=200)

    total_endpoints = sum(len(f["endpoints"]) for f in features)
    print(f"Generated code_summary.yaml: {len(features)} features, {total_endpoints} endpoints")
    print(f"Size: {DST.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
