#!/usr/bin/env bash
# Valida configuración, reglas, tests de reglas, Alertmanager y dashboards.
# Usa las imágenes oficiales para no instalar nada en el host.
set -euo pipefail
cd "$(dirname "$0")/.."

PROM_IMG=prom/prometheus:v3.5.0
AM_IMG=prom/alertmanager:v0.28.1
BB_IMG=prom/blackbox-exporter:v0.27.0

run_prom() { docker run --rm --entrypoint "$1" -v "$PWD:/w:ro" -w /w "$PROM_IMG" "${@:2}"; }

echo "== promtool check config =="
# prometheus.yml referencia /etc/prometheus/rules; se monta igual que en el compose
docker run --rm --entrypoint promtool \
  -v "$PWD/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  -v "$PWD/prometheus/rules:/etc/prometheus/rules:ro" "$PROM_IMG" \
  check config /etc/prometheus/prometheus.yml

echo "== promtool check rules =="
run_prom promtool check rules prometheus/rules/*.yml

echo "== promtool test rules =="
run_prom promtool test rules prometheus/tests/*.yml

echo "== amtool check-config =="
docker run --rm --entrypoint amtool -v "$PWD/alertmanager:/c:ro" "$AM_IMG" check-config /c/alertmanager.yml

echo "== blackbox config =="
docker run --rm --entrypoint blackbox_exporter -v "$PWD/blackbox:/c:ro" "$BB_IMG" --config.check --config.file=/c/blackbox.yml

echo "== docker compose config =="
docker compose config --quiet

echo "== dashboards JSON =="
python3 - <<'PY'
import json, pathlib, sys
ok = True
for p in sorted(pathlib.Path("grafana/dashboards").glob("*.json")):
    d = json.loads(p.read_text())
    for k in ("uid", "title", "panels"):
        if k not in d:
            print(f"FAIL {p}: falta '{k}'"); ok = False
    uids = [x["datasource"]["uid"] for x in d["panels"]]
    if set(uids) != {"prometheus"}:
        print(f"FAIL {p}: datasource inesperado {set(uids)}"); ok = False
    print(f"OK   {p} ({len(d['panels'])} paneles)")
sys.exit(0 if ok else 1)
PY
echo "== TODO OK =="
