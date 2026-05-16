#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_tests.sh  –  Lance tous les tests BI (Newman API + Playwright E2E)
#
# Usage :
#   ./run_tests.sh              → serveur remote 192.168.224.128:8000 (défaut)
#   ./run_tests.sh local        → serveur local 127.0.0.1:8000
#   ./run_tests.sh remote       → serveur remote (explicite)
#   ./run_tests.sh api-only     → Newman seulement
#   ./run_tests.sh e2e-only     → Playwright seulement
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$SCRIPT_DIR/tests"
RESULTS_DIR="$SCRIPT_DIR/test-results"
COLLECTION="$TESTS_DIR/newman/bi-collection.postman_collection.json"

TARGET="${1:-remote}"

case "$TARGET" in
  local)
    ENV_FILE="$TESTS_DIR/newman/env.local.postman_environment.json"
    FRONTEND_URL="http://localhost:5173"
    ;;
  remote|*)
    ENV_FILE="$TESTS_DIR/newman/env.remote.postman_environment.json"
    # Le frontend Vue tourne toujours en local (npm run dev sur Windows)
    FRONTEND_URL="http://localhost:5173"
    ;;
esac

mkdir -p "$RESULTS_DIR"

PASS=0; FAIL=0

# ─── Couleurs ────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

header() { echo -e "\n${YELLOW}══════════════════════════════════════════${NC}"; echo -e "${YELLOW}  $1${NC}"; echo -e "${YELLOW}══════════════════════════════════════════${NC}"; }

# ─── 1. Vérifier les dépendances ─────────────────────────────────────────────
check_dep() {
  if ! command -v "$1" &>/dev/null; then
    echo -e "${RED}✗ '$1' n'est pas installé.${NC} Lance : $2"
    return 1
  fi
}

header "Vérification des dépendances"
DEPS_OK=true
check_dep npx "npm install (dans le dossier tests/)" || DEPS_OK=false

if [ "$DEPS_OK" = false ]; then
  echo -e "${RED}Installe Node.js / npm puis relance ce script.${NC}"
  exit 1
fi

# S'assurer que les dépendances du dossier tests/ sont installées
if [ ! -d "$TESTS_DIR/node_modules" ]; then
  echo "Installation des dépendances de test..."
  (cd "$TESTS_DIR" && npm install --silent)
fi
echo -e "${GREEN}✓ Dépendances OK${NC}"

# ─── 2. Newman – Tests API ────────────────────────────────────────────────────
run_newman() {
  header "Tests API Newman ($TARGET)"
  echo "Collection : $COLLECTION"
  echo "Env        : $ENV_FILE"
  echo ""

  REPORT="$RESULTS_DIR/newman-report.html"

  if (cd "$TESTS_DIR" && npx newman run "$COLLECTION" \
      --environment "$ENV_FILE" \
      --reporters cli,htmlextra \
      --reporter-htmlextra-export "$REPORT" \
      --color on); then
    echo -e "\n${GREEN}✓ Tous les tests API ont réussi${NC}"
    echo "  Rapport HTML : $REPORT"
    PASS=$((PASS+1))
  else
    echo -e "\n${RED}✗ Des tests API ont échoué – voir rapport : $REPORT${NC}"
    FAIL=$((FAIL+1))
  fi
}

# ─── 3. Playwright – Tests E2E ───────────────────────────────────────────────
run_playwright() {
  header "Tests E2E Playwright ($TARGET)"
  echo "Frontend URL : $FRONTEND_URL"
  echo ""

  cd "$TESTS_DIR"
  if FRONTEND_URL="$FRONTEND_URL" \
     TEST_USER_EMAIL="admin@sotifibre.dz" \
     TEST_USER_PASSWORD="SOTIFibre@2026!" \
     npx playwright test --config=playwright.config.ts; then
    echo -e "\n${GREEN}✓ Tous les tests E2E ont réussi${NC}"
    PASS=$((PASS+1))
  else
    echo -e "\n${RED}✗ Des tests E2E ont échoué – voir test-results/playwright-report/index.html${NC}"
    FAIL=$((FAIL+1))
  fi
  cd "$SCRIPT_DIR"
}

# ─── Sélection du mode ───────────────────────────────────────────────────────
case "${1:-remote}" in
  api-only)   run_newman ;;
  e2e-only)   run_playwright ;;
  local|remote|*)
    run_newman
    run_playwright
    ;;
esac

# ─── Résumé final ────────────────────────────────────────────────────────────
header "Résumé"
echo -e "  ${GREEN}Suites réussies : $PASS${NC}"
echo -e "  ${RED}Suites échouées : $FAIL${NC}"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
