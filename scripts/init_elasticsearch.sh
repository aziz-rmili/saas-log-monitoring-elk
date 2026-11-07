#!/usr/bin/env bash
# Crée le template d'index "logs-*" dans Elasticsearch (à lancer une fois, après le démarrage de la stack).
set -euo pipefail

ES_URL="${ES_URL:-http://localhost:9200}"
cd "$(dirname "$0")/.."

curl -fsS -X PUT "$ES_URL/_index_template/logs-template" \
  -H 'Content-Type: application/json' \
  --data-binary @elasticsearch/logs-template.json
echo
echo "Template logs-template créé."
