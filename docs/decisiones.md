# Decisiones de diseño

1. **Todo como fichero, nada en la UI.** Datasource y dashboards se provisionan (`allowUiUpdates: false`); reglas y rutas viven en Git. El stack es reproducible con `docker compose up`.
2. **Dashboards generados por script** (`scripts/gen_dashboards.py`). El JSON de Grafana es verboso; el script mantiene los paneles consistentes y el diff revisable. El JSON generado también se versiona para que Grafana lo cargue sin pasos extra.
3. **Alertas por síntoma + una predictiva.** Se alerta de CPU, memoria, disco, contenedores y endpoints; `predict_linear` para disco da margen antes del umbral fijo.
4. **Tests de reglas con `promtool test rules`.** Cada alerta tiene un caso que dispara y otro que no (o que se resuelve), incluidas las anotaciones. Una regresión de umbral rompe el CI (ver `docs/evidencias/04-*`).
5. **Validación con las imágenes oficiales** (`scripts/validate.sh`): no hay que instalar promtool/amtool y local y CI ejecutan lo mismo.
6. **Versiones fijadas** en las imágenes, nunca `latest`.
7. **cAdvisor v0.61.1 desde `ghcr.io/google/cadvisor`.** La v0.52.1 no identificaba los contenedores en un Docker reciente con el snapshotter de containerd (`failed to identify the read-write layer ID`, sin etiqueta `name`). La v0.61.1 los etiqueta bien. Se usa `cgroup: host` para ver los cgroups del anfitrión.
8. **Receptor webhook local** (Python estándar, sin dependencias) en vez de un servicio real: demuestra el enrutado sin tokens ni cuentas. Sustituir por Slack/email/PagerDuty es cambiar un `receiver` (los secretos irían en `*_file`, nunca en el repo).
9. **Puertos solo en `127.0.0.1`** y contraseña de Grafana por variable de entorno (`admin/admin` solo como valor por defecto de laboratorio).
10. **runbook_url hacia otro repositorio del portfolio**, para cerrar el ciclo alerta → procedimiento.
11. **Alcance**: un solo host. La futura versión en AWS reutilizará reglas y dashboards cambiando los `static_configs` por service discovery (EC2/ECS).
