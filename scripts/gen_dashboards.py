#!/usr/bin/env python3
"""Genera los dashboards de Grafana (JSON) de forma reproducible.

Uso: python3 scripts/gen_dashboards.py
El JSON resultante vive en grafana/dashboards/ y se versiona como código.
"""
import json
from pathlib import Path

DS = {"type": "prometheus", "uid": "prometheus"}
OUT = Path(__file__).resolve().parent.parent / "grafana" / "dashboards"


def panel(pid, title, exprs, x, y, w=12, h=8, unit="short", kind="timeseries", mn=None, mx=None):
    fc = {"unit": unit}
    if mn is not None:
        fc["min"] = mn
    if mx is not None:
        fc["max"] = mx
    return {
        "id": pid, "title": title, "type": kind, "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": fc, "overrides": []},
        "targets": [
            {"refId": chr(65 + i), "expr": e, "legendFormat": lf, "datasource": DS}
            for i, (e, lf) in enumerate(exprs)
        ],
    }


def dashboard(uid, title, tags, panels, variables=None):
    return {
        "uid": uid, "title": title, "tags": tags, "schemaVersion": 39, "version": 1,
        "editable": False, "refresh": "30s", "timezone": "browser",
        "time": {"from": "now-1h", "to": "now"},
        "templating": {"list": variables or []},
        "panels": panels,
    }


def var(name, query):
    return {
        "name": name, "label": name, "type": "query", "datasource": DS,
        "query": {"query": query, "refId": "v"}, "refresh": 2,
        "includeAll": False, "multi": False,
    }


node = dashboard("node-overview", "Node overview", ["node", "host"], [
    panel(1, "CPU usage %", [('100 - avg(rate(node_cpu_seconds_total{mode="idle",instance=~"$instance"}[5m])) * 100', "cpu")], 0, 0, unit="percent", mn=0, mx=100),
    panel(2, "Memory used %", [('100 * (1 - node_memory_MemAvailable_bytes{instance=~"$instance"} / node_memory_MemTotal_bytes{instance=~"$instance"})', "memoria")], 12, 0, unit="percent", mn=0, mx=100),
    panel(3, "Load average", [('node_load1{instance=~"$instance"}', "1m"), ('node_load5{instance=~"$instance"}', "5m"), ('node_load15{instance=~"$instance"}', "15m")], 0, 8),
    panel(4, "Disk free %", [('100 * node_filesystem_avail_bytes{instance=~"$instance",fstype!~"tmpfs|overlay|squashfs"} / node_filesystem_size_bytes{instance=~"$instance",fstype!~"tmpfs|overlay|squashfs"}', "{{mountpoint}}")], 12, 8, unit="percent", mn=0, mx=100),
    panel(5, "Network I/O", [('rate(node_network_receive_bytes_total{instance=~"$instance",device!~"lo|veth.*|docker.*|br-.*"}[5m])', "rx {{device}}"), ('-rate(node_network_transmit_bytes_total{instance=~"$instance",device!~"lo|veth.*|docker.*|br-.*"}[5m])', "tx {{device}}")], 0, 16, unit="Bps"),
    panel(6, "Disk I/O", [('rate(node_disk_read_bytes_total{instance=~"$instance"}[5m])', "read {{device}}"), ('-rate(node_disk_written_bytes_total{instance=~"$instance"}[5m])', "write {{device}}")], 12, 16, unit="Bps"),
    panel(7, "Uptime", [('time() - node_boot_time_seconds{instance=~"$instance"}', "uptime")], 0, 24, w=6, h=4, unit="s", kind="stat"),
], [var("instance", "label_values(node_uname_info, instance)")])

containers = dashboard("containers", "Containers (cAdvisor)", ["docker", "containers"], [
    panel(1, "CPU per container", [('sum by (name) (rate(container_cpu_usage_seconds_total{name!=""}[5m])) * 100', "{{name}}")], 0, 0, unit="percent"),
    panel(2, "Memory working set", [('container_memory_working_set_bytes{name!=""}', "{{name}}")], 12, 0, unit="bytes"),
    panel(3, "Network receive", [('sum by (name) (rate(container_network_receive_bytes_total{name!=""}[5m]))', "{{name}}")], 0, 8, unit="Bps"),
    panel(4, "Network transmit", [('sum by (name) (rate(container_network_transmit_bytes_total{name!=""}[5m]))', "{{name}}")], 12, 8, unit="Bps"),
    panel(5, "Container uptime", [('time() - container_start_time_seconds{name!=""}', "{{name}}")], 0, 16, unit="s"),
    panel(6, "Restarts (15 min)", [('changes(container_start_time_seconds{name!=""}[15m])', "{{name}}")], 12, 16),
])

alerts = dashboard("alerts-overview", "Alerts & targets", ["alerts", "prometheus"], [
    panel(1, "Targets up", [('sum(up)', "up")], 0, 0, w=6, h=4, kind="stat"),
    panel(2, "Targets down", [('count(up == 0) or vector(0)', "down")], 6, 0, w=6, h=4, kind="stat"),
    panel(3, "Firing alerts", [('count(ALERTS{alertstate="firing",alertname!="Watchdog"}) or vector(0)', "firing")], 12, 0, w=6, h=4, kind="stat"),
    panel(4, "Endpoint probe success", [('probe_success', "{{instance}}")], 18, 0, w=6, h=4, kind="stat"),
    panel(5, "Alerts by severity", [('count by (alertname, severity) (ALERTS{alertstate="firing",alertname!="Watchdog"})', "{{alertname}} ({{severity}})")], 0, 4, w=24),
    panel(6, "Up by job", [('up', "{{job}} {{instance}}")], 0, 12, w=24),
])

OUT.mkdir(parents=True, exist_ok=True)
for name, d in [("node-overview", node), ("containers", containers), ("alerts-overview", alerts)]:
    (OUT / f"{name}.json").write_text(json.dumps(d, indent=2) + "\n")
    print("generado", name)
