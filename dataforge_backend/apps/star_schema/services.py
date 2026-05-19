# apps/star_schema/services.py
"""
Services pour l'application star_schema
"""
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.utils import timezone

from apps.core.utils import Timer
from apps.data_warehouse.services import DataWarehouseService

from .models import DimensionalSchema, CustomCalculation  # ← Changé de StarSchema à DimensionalSchema


class DimensionalSchemaService:
    """Service pour la gestion des schémas dimensionnels"""
    
    def __init__(self, dimensional_schema: DimensionalSchema):  # ← Renommé
        self.dimensional_schema = dimensional_schema
        self.dw_service = None
    
    def execute(self, filters: Dict = None, limit: int = None, offset: int = None) -> Dict[str, Any]:
        """
        Exécute le schéma dimensionnel
        """
        timer = Timer().start()
        
        # Vérifier le cache
        cache_key = f"dimensional_schema_{self.dimensional_schema.id}_{hash(str(filters))}"
        if self.dimensional_schema.is_cached:
            cached_result = cache.get(cache_key)
            if cached_result:
                return {
                    'success': True,
                    'data': cached_result,
                    'from_cache': True,
                    'execution_time_ms': 0
                }
        
        try:
            # Générer la requête SQL
            sql = self.dimensional_schema.generate_query(filters, limit, offset)
            
            # Exécuter la requête sur la première table de faits
            fact_table = self.dimensional_schema.fact_tables.first()
            if not fact_table:
                return {'success': False, 'error': 'Aucune table de faits définie'}
            
            # Service Data Warehouse
            self.dw_service = DataWarehouseService()
            result = self.dw_service.execute_query(fact_table.schema.name, sql)
            
            timer.stop()
            
            # Mettre à jour les statistiques
            self.dimensional_schema.query_count += 1
            self.dimensional_schema.last_queried_at = timezone.now()
            self.dimensional_schema.avg_query_time_ms = (
                (self.dimensional_schema.avg_query_time_ms * (self.dimensional_schema.query_count - 1) +
                 timer.duration_ms()) / self.dimensional_schema.query_count
            )
            self.dimensional_schema.save(update_fields=['query_count', 'last_queried_at', 'avg_query_time_ms'])
            
            # Appliquer les calculs personnalisés
            if result.get('success') and result.get('data'):
                result['data'] = self._apply_calculations(result['data'])
            
            # Mettre en cache
            if self.dimensional_schema.is_cached:
                cache.set(cache_key, result.get('data'), self.dimensional_schema.cache_ttl_seconds)
            
            return {
                'success': True,
                'data': result.get('data'),
                'columns': result.get('columns', []),
                'row_count': len(result.get('data', [])),
                'execution_time_ms': timer.duration_ms(),
                'sql': sql
            }
            
        except Exception as e:
            timer.stop()
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': timer.duration_ms()
            }
    
    def _apply_calculations(self, data: List[Dict]) -> List[Dict]:
        """
        Applique les calculs personnalisés aux données
        """
        if not data or not self.dimensional_schema.calculations:
            return data
        
        calculations = CustomCalculation.objects.filter(
            dimensional_schema=self.dimensional_schema,  # ← Changé de star_schema à dimensional_schema
            is_active=True
        )
        
        for row in data:
            for calc in calculations:
                try:
                    value = calc.evaluate(row)
                    if value is not None:
                        row[calc.result_column] = value
                except Exception:
                    pass
        
        return data
    
    def generate_sql(self, filters: Dict = None, limit: int = None) -> str:
        """Génère la requête SQL sans l'exécuter"""
        return self.dimensional_schema.generate_query(filters, limit)
    
    def export(self, format: str = 'csv', filters: Dict = None) -> Any:
        """Exporte les données du schéma"""
        result = self.execute(filters)
        
        if not result['success']:
            return result
        
        df = pd.DataFrame(result['data'])
        
        if format == 'csv':
            return df.to_csv(index=False)
        elif format == 'excel':
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=self.dimensional_schema.name, index=False)
            output.seek(0)
            return output.getvalue()
        elif format == 'json':
            return df.to_json(orient='records', indent=2)
        
        return result['data']
    
    def validate(self) -> Dict[str, Any]:
        """Valide la configuration du schéma"""
        errors = []
        warnings = []
        
        # Vérifier les tables de faits
        if not self.dimensional_schema.fact_tables.exists():
            errors.append("Aucune table de faits définie")
        
        # Vérifier les mesures
        if not self.dimensional_schema.measures.exists():
            warnings.append("Aucune mesure définie")
        
        # Vérifier les dimensions
        if not self.dimensional_schema.dimension_mapping:
            warnings.append("Aucune dimension définie")
        
        # Vérifier les relations
        for relation in self.dimensional_schema.relationships:
            if not all(k in relation for k in ['from_table', 'to_table', 'from_column', 'to_column']):
                errors.append(f"Relation invalide: {relation}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


class GalaxySchemaService:
    """Service pour les schémas galaxie"""
    
    def __init__(self, galaxy_schema):
        self.galaxy_schema = galaxy_schema
    
    def execute_unified(self, filters: Dict = None) -> Dict[str, Any]:
        """Exécute tous les schémas de la galaxie"""
        results = []
        
        for dimensional_schema in self.galaxy_schema.dimensional_schemas.all():  # ← Changé de star_schemas à dimensional_schemas
            service = DimensionalSchemaService(dimensional_schema)
            result = service.execute(filters)
            results.append({
                'dimensional_schema': dimensional_schema.name,  # ← Renommé
                'result': result
            })
        
        return {
            'success': True,
            'galaxy': self.galaxy_schema.name,
            'results': results
        }
    
    def generate_unified_query(self) -> str:
        """Génère la requête unifiée pour toute la galaxie"""
        return self.galaxy_schema.generate_unified_query()