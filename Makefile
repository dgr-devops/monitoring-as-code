.DEFAULT_GOAL := help
.PHONY: help up down validate test dashboards logs status clean

help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

up: ## Levanta el stack (Prometheus, Alertmanager, Grafana, exporters)
	docker compose up -d

down: ## Para el stack (conserva volúmenes)
	docker compose down

clean: ## Para el stack y borra los volúmenes
	docker compose down -v

validate: ## promtool/amtool/JSON + tests de reglas
	./scripts/validate.sh

test: ## Solo los tests unitarios de reglas
	docker run --rm --entrypoint promtool -v "$(CURDIR):/w:ro" -w /w prom/prometheus:v3.5.0 test rules prometheus/tests/*.yml

dashboards: ## Regenera los dashboards JSON desde el script
	python3 scripts/gen_dashboards.py

status: ## Estado de targets y alertas activas
	@curl -s localhost:9090/api/v1/targets | python3 -c "import json,sys;[print(t['labels']['job'],t['labels']['instance'],t['health']) for t in json.load(sys.stdin)['data']['activeTargets']]"
	@curl -s localhost:9093/api/v2/alerts | python3 -c "import json,sys;[print('ALERT',a['labels']['alertname'],a['status']['state']) for a in json.load(sys.stdin)]"

logs: ## Notificaciones recibidas por el webhook local
	docker compose logs -f webhook
