## Overview
RED metrics, coupled with Grafana visualizations, serve as powerful tools that enhance our system's visibility. They can be seamlessly applied to monitor HTTP traffic, internal service operations, and interactions with external systems. During incidents, we can quickly assess whether a specific component is functioning as expected or if anomalies such as spikes in errors or prolonged latency are occurring. Furthermore, generating dashboards through code adds to the robustness and maintainability of this approach, enabling easier management and updates.

## What you can find here?
- how to setup Prometheus server to gather metrics,

- how to collect RED metrics for HTTP server requests and Redis database calls,

- how to setup Grafana to visualize Prometheus metrics,

- how to automate generating Grafana dashboards.

## Run the service
```bash
$ docker-compose up
```

## Generate Grafana dashboard
```bash
$ cd grafana
$ make dashboard.json
```