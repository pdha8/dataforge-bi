"""
apps/ml_analytics/ml/grok.py

Service d'intégration avec l'API Grok AI (xAI).
Fournit : insights, prévisions, détection d'anomalies, recommandations d'actions.

Améliorations vs version initiale :
- Session HTTP réutilisable avec retry automatique + backoff exponentiel
- Exception typée GrokAPIError avec status_code
- Validation de la clé API avant tout appel
- Logging structuré avec durée de réponse
- Type hints complets
- Méthodes train/evaluate/save/load pour compatibilité MLService
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ─── Constantes réseau ───────────────────────────────────────────────────────

_MAX_RETRIES = 3
_BACKOFF_FACTOR = 0.5
_RETRY_STATUS_CODES = (429, 500, 502, 503, 504)
_DEFAULT_ENDPOINT = "https://api.x.ai/v1/chat/completions"
_DEFAULT_MODEL = "grok-3"
_DEFAULT_TIMEOUT = 30


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class GrokAPIError(Exception):
    """Erreur d'appel à l'API Grok AI."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# ─────────────────────────────────────────────────────────────────────────────
# Session HTTP
# ─────────────────────────────────────────────────────────────────────────────

def _build_session(max_retries: int = _MAX_RETRIES) -> requests.Session:
    """
    Construit une session requests avec retry automatique
    et backoff exponentiel sur les codes d'erreur transitoires.
    """
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=_BACKOFF_FACTOR,
        status_forcelist=_RETRY_STATUS_CODES,
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class GrokService:
    """
    Service pour interagir avec l'API Grok AI (xAI).
    Compatible avec l'interface MLService (train/evaluate/save/load no-ops).
    """

    def __init__(self, model_instance) -> None:
        self.model = model_instance
        self.config: dict = model_instance.config
        self.params: dict = model_instance.parameters

        self._api_key: str = getattr(settings, "GROK_API_KEY", "")
        self._endpoint: str = getattr(settings, "GROK_API_ENDPOINT", _DEFAULT_ENDPOINT)
        self._model_name: str = getattr(settings, "GROK_MODEL", _DEFAULT_MODEL)
        self._timeout: int = int(getattr(settings, "GROK_TIMEOUT", _DEFAULT_TIMEOUT))
        self._session: requests.Session = _build_session()

    # ────────────────────────────────────────────────────────────────────────
    # Appel API central
    # ────────────────────────────────────────────────────────────────────────

    def _call(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Appelle l'API Grok et retourne le dict JSON brut.
        Lève GrokAPIError sur tout échec (réseau, auth, rate-limit, serveur).
        """
        if not self._api_key:
            raise GrokAPIError(
                "GROK_API_KEY manquant dans les settings. "
                "Ajoutez GROK_API_KEY=... dans votre fichier .env."
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.params.get("max_tokens", 1000),
        }

        start = time.perf_counter()
        try:
            response = self._session.post(
                self._endpoint,
                headers=headers,
                json=payload,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout:
            raise GrokAPIError(f"Timeout Grok API après {self._timeout}s.")
        except requests.exceptions.ConnectionError as exc:
            raise GrokAPIError(f"Erreur de connexion Grok API : {exc}")
        except requests.exceptions.RequestException as exc:
            raise GrokAPIError(f"Erreur HTTP inattendue : {exc}")

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Grok API: status=%s, duration=%.0fms, model=%s",
            response.status_code, elapsed_ms, self._model_name,
        )

        if response.status_code == 401:
            raise GrokAPIError("Clé API Grok invalide ou expirée.", status_code=401)
        if response.status_code == 429:
            raise GrokAPIError(
                "Limite de taux Grok atteinte. Réessayez dans quelques secondes.",
                status_code=429,
            )
        if response.status_code >= 400:
            raise GrokAPIError(
                f"Erreur Grok API {response.status_code} : {response.text[:300]}",
                status_code=response.status_code,
            )

        return response.json()

    @staticmethod
    def _extract_text(result: dict) -> str:
        """Extrait le texte généré de la réponse JSON Grok de façon défensive."""
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            logger.warning("Impossible d'extraire le texte de la réponse Grok : %s", result)
            return ""

    # ────────────────────────────────────────────────────────────────────────
    # API publique
    # ────────────────────────────────────────────────────────────────────────

    def generate_insight(
        self,
        data: list[dict],
        context: Optional[dict] = None,
    ) -> str:
        """
        Génère des insights business actionnables à partir des données.

        Returns:
            Texte d'insight en français, ou message d'erreur.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un analyste BI expert. "
                    "Fournis des insights concis, structurés et actionnables en français."
                ),
            },
            {"role": "user", "content": self._prompt_insight(data, context)},
        ]
        try:
            result = self._call(messages, temperature=0.5)
            return self._extract_text(result) or "Aucun insight généré."
        except GrokAPIError as exc:
            logger.error("generate_insight failed: %s", exc)
            return f"Erreur Grok : {exc}"

    def forecast(self, data: list[dict], horizon: int = 30) -> dict:
        """
        Prédit les `horizon` prochaines valeurs d'une série temporelle.

        Returns:
            Dict avec 'forecast_values' (list[float]) si le JSON est parseable,
            sinon 'forecast_text' (str brut).
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un expert en prévision de séries temporelles. "
                    f"Préds les {horizon} prochaines valeurs. "
                    "Réponds UNIQUEMENT avec un tableau JSON de nombres, sans texte autour."
                ),
            },
            {"role": "user", "content": self._prompt_forecast(data, horizon)},
        ]
        try:
            result = self._call(messages, temperature=0.2)
            text = self._extract_text(result)
            try:
                values = json.loads(text)
                if isinstance(values, list) and all(isinstance(v, (int, float)) for v in values):
                    return {"forecast_values": values, "horizon": horizon}
            except json.JSONDecodeError:
                pass
            return {"forecast_text": text, "horizon": horizon}
        except GrokAPIError as exc:
            logger.error("forecast failed: %s", exc)
            return {"error": str(exc)}

    def detect_anomalies(self, data: list[dict]) -> dict:
        """
        Identifie les anomalies dans les données avec leur indice et raison.

        Returns:
            Dict avec 'anomalies_text' (description textuelle) ou 'error'.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un expert en détection d'anomalies. "
                    "Pour chaque anomalie, indique : indice, valeur, raison. "
                    "Si aucune anomalie, réponds 'Aucune anomalie détectée.'"
                ),
            },
            {"role": "user", "content": self._prompt_anomaly(data)},
        ]
        try:
            result = self._call(messages, temperature=0.2)
            return {"anomalies_text": self._extract_text(result)}
        except GrokAPIError as exc:
            logger.error("detect_anomalies failed: %s", exc)
            return {"error": str(exc)}

    def recommend_actions(
        self,
        data: list[dict],
        context: Optional[dict] = None,
    ) -> str:
        """
        Propose des actions concrètes et mesurables pour améliorer la performance.

        Returns:
            Texte de recommandations en français, ou message d'erreur.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un consultant business expert. "
                    "Propose des actions concrètes, mesurables et priorisées en français."
                ),
            },
            {"role": "user", "content": self._prompt_recommendation(data, context)},
        ]
        try:
            result = self._call(messages, temperature=0.6)
            return self._extract_text(result) or "Aucune recommandation générée."
        except GrokAPIError as exc:
            logger.error("recommend_actions failed: %s", exc)
            return f"Erreur Grok : {exc}"

    # ────────────────────────────────────────────────────────────────────────
    # Compatibilité MLService (no-ops)
    # ────────────────────────────────────────────────────────────────────────

    def train(self, data: Any = None) -> None:
        """Grok est un service cloud — aucun entraînement local requis."""

    def evaluate(self, test_data: Any = None) -> dict:
        """Grok n'a pas de métriques d'évaluation classiques."""
        return {}

    def save(self, path: str) -> None:
        """Grok est un service cloud — aucun fichier à sauvegarder."""

    def load(self, path: str) -> None:
        """Grok est un service cloud — aucun fichier à charger."""

    # ────────────────────────────────────────────────────────────────────────
    # Constructeurs de prompts
    # ────────────────────────────────────────────────────────────────────────

    def _prompt_insight(self, data: list[dict], context: Optional[dict]) -> str:
        sample = data[:100]
        ctx = f"Contexte métier : {json.dumps(context, ensure_ascii=False)}\n\n" if context else ""
        return (
            f"{ctx}"
            f"Analyse les données suivantes ({len(sample)}/{len(data)} points) "
            f"et fournis :\n"
            f"1. La tendance générale (hausse, baisse, stable)\n"
            f"2. Les anomalies ou valeurs inhabituelles\n"
            f"3. Les patterns ou facteurs clés\n"
            f"4. Des recommandations actionnables\n\n"
            f"Données :\n{json.dumps(sample, ensure_ascii=False, indent=2)}"
        )

    def _prompt_forecast(self, data: list[dict], horizon: int) -> str:
        # On envoie les données les plus récentes (plus pertinentes pour la prévision)
        sample = data[-200:]
        return (
            f"Série temporelle ({len(data)} points au total, {len(sample)} montrés) :\n"
            f"{json.dumps(sample, ensure_ascii=False, indent=2)}\n\n"
            f"Préds les {horizon} prochaines valeurs. "
            f"Réponds UNIQUEMENT avec un tableau JSON de {horizon} nombres."
        )

    def _prompt_anomaly(self, data: list[dict]) -> str:
        sample = data[:200]
        return (
            f"Identifie les anomalies dans ces {len(sample)} points de données :\n"
            f"{json.dumps(sample, ensure_ascii=False, indent=2)}\n\n"
            f"Pour chaque anomalie trouvée, indique : indice, valeur, raison."
        )

    def _prompt_recommendation(
        self, data: list[dict], context: Optional[dict]
    ) -> str:
        sample = data[:100]
        ctx = f"Contexte : {json.dumps(context, ensure_ascii=False)}\n\n" if context else ""
        return (
            f"{ctx}"
            f"Basé sur ces données ({len(sample)}/{len(data)} points), "
            f"propose des actions concrètes pour améliorer la performance :\n"
            f"{json.dumps(sample, ensure_ascii=False, indent=2)}"
        )
