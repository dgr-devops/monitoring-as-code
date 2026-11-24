# Catálogo de alertas

Todas las alertas llevan `severity` (`critical` o `warning`) y las anotaciones `summary`, `description` y `runbook_url`
(enlaza al runbook correspondiente de [runbooks-and-postmortems](https://github.com/dgr-devops/runbooks-and-postmortems)).
Cada una tiene su test unitario en `prometheus/tests/`.

| Alerta | Severidad | Fichero |
|---|---|---|
| InstanceDown | critical | `rules/host.yml` |
| HighCpuUsage | warning | `rules/host.yml` |
| DiskWillFillIn24h | warning | `rules/host.yml` |
| DiskSpaceCritical | critical | `rules/host.yml` |
| MemoryPressure | warning | `rules/host.yml` |
| ContainerRestartingFrequently | warning | `rules/containers.yml` |
| EndpointDown | critical | `rules/endpoints.yml` |
| Watchdog | none | `rules/endpoints.yml` |

## InstanceDown
- **Qué**: `up == 0` durante 1 minuto en cualquier target (node, cAdvisor, Alertmanager, Prometheus…).
- **Por qué ese umbral**: con scrape de 15 s, 1 min son 4 scrapes fallidos seguidos; filtra reinicios cortos sin retrasar el aviso de un caído real.
- **Qué hacer**: `docker compose ps`, mirar `docker compose logs <servicio>`, reiniciar el servicio y comprobar red/DNS entre contenedores. Runbook: *servicio-caido*.

## HighCpuUsage
- **Qué**: CPU media > 85 % durante 10 minutos (`100 - idle`).
- **Por qué**: los picos cortos son normales (compilaciones, backups); 10 min sostenidos indican un proceso descontrolado o falta de capacidad.
- **Qué hacer**: `top`/`pidstat` para identificar el proceso, revisar cron y despliegues recientes, escalar si es carga legítima. Runbook: *alta-carga-cpu*.

## DiskWillFillIn24h
- **Qué**: `predict_linear` sobre las últimas 6 h proyecta espacio libre < 0 dentro de 24 h, y el disco tiene menos del 50 % libre.
- **Por qué**: avisa **antes** de llegar al umbral fijo, con margen para actuar en horario laboral. El filtro del 50 % evita falsos positivos en discos muy vacíos con una escritura puntual grande. `for: 30m` descarta rampas transitorias.
- **Qué hacer**: `du -xh --max-depth=1`, rotar/limpiar logs, revisar imágenes Docker huérfanas (`docker system df`), ampliar volumen. Runbook: *disco-lleno*.

## DiskSpaceCritical
- **Qué**: menos del 10 % libre durante 5 minutos.
- **Por qué**: por debajo del 10 % muchos sistemas de ficheros degradan rendimiento y las aplicaciones empiezan a fallar al escribir.
- **Qué hacer**: igual que la anterior, con urgencia. Runbook: *disco-lleno*.

## MemoryPressure
- **Qué**: `MemAvailable` < 10 % de la RAM total durante 5 minutos.
- **Por qué**: `MemAvailable` (no `MemFree`) cuenta la caché recuperable; por debajo del 10 % el kernel entra en reclaim agresivo/swap y se acerca el OOM killer.
- **Qué hacer**: `ps aux --sort=-%mem`, buscar fugas, revisar `dmesg | grep -i oom`, ajustar límites de memoria de los contenedores. Runbook: *memoria-agotada-oom*.

## ContainerRestartingFrequently
- **Qué**: `container_start_time_seconds` cambia más de 2 veces en 15 minutos (cAdvisor).
- **Por qué**: detecta *crash loops* sin depender de kube-state-metrics; 3+ arranques en 15 min no es un reinicio planificado.
- **Qué hacer**: `docker logs --tail 100 <contenedor>`, `docker inspect` (exit code, OOMKilled), revisar healthcheck y límites. Runbook: *servicio-caido*.

## EndpointDown
- **Qué**: el sondeo HTTP de blackbox_exporter (`probe_success == 0`) falla 2 minutos.
- **Por qué**: mide lo que ve el usuario (respuesta 2xx), no solo que el proceso exista; 2 min tolera un reinicio.
- **Qué hacer**: `curl -v <url>`, comprobar DNS, certificado y el servicio detrás. Runbook: *servicio-caido*.

## Watchdog
- **Qué**: alerta que **siempre** está activa (`vector(1)`), severidad `none`; Alertmanager no la notifica.
- **Por qué**: si deja de llegar a un monitor externo (dead man's switch), la cadena de alertado está rota.

## Enrutado y supresión (Alertmanager)
- `critical` → receptor `webhook-critical` (repetición cada 1 h); `warning` → `webhook-warning` (cada 4 h).
- Una alerta `critical` suprime las `warning` de la misma instancia (`inhibit_rules`) para no duplicar ruido.
