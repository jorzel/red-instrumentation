import json
import os

from grafanalib.prometheus import PromGraph
from grafanalib.core import (
    Dashboard, Row, Graph, Target, Histogram, OPS_FORMAT, single_y_axis, YAxes,
    YAxis, MILLISECONDS_FORMAT, SHORT_FORMAT,
)
from grafanalib._gen import DashboardEncoder


def duration_panel(metric, title='Response times', y_axes_format=MILLISECONDS_FORMAT):
    return PromGraph(
        title=title,
        data_source='prometheus',
        expressions=[
            ('p99', f'histogram_quantile(0.99, sum(rate({metric}_bucket[1m])) by (le))'),
            ('p90', f'histogram_quantile(0.90, sum(rate({metric}_bucket[1m])) by (le))'),
            ('p50', f'histogram_quantile(0.5, sum(rate({metric}_bucket[1m])) by (le))'),
        ],
        yAxes=single_y_axis(format=y_axes_format),
    )


def requests_panel(metric, title="Requests", y_axes_format=OPS_FORMAT, legend_format="{{path}} {{method}} {{code}}"):
    return Graph(
        title=title,
        dataSource='prometheus',
        targets=[
            Target(
                expr=f'rate({metric}_count[1m])',
                legendFormat=legend_format,
                refId='A',
            ),
        ],
        yAxes=single_y_axis(format=y_axes_format),
    )


http_requests_duration = duration_panel("http_request_duration", "HTTP Requests Response Times") 
http_requests = requests_panel("http_request_duration", "HTTP Requests")


# Create a dashboard containing the RED panel
dashboard = Dashboard(
    title='Service instrumenation',
    rows=[
        Row(title="RED - HTTP", panels=[http_requests, http_requests_duration]),
    ],
    refresh='10s',
).auto_panel_ids()


# Convert the dashboard object to JSON
def get_dashboard_json(dashboard, overwrite=False, message="Updated by grafanlib"):
    '''
    get_dashboard_json generates JSON from grafanalib Dashboard object

    :param dashboard - Dashboard() created via grafanalib
    '''

    # grafanalib generates json which need to pack to "dashboard" root element
    return json.dumps(
        dashboard.to_json_data(),
        sort_keys=True,
        indent=2,
        cls=DashboardEncoder,
    )


def save_dashboard(dashboard):
    current_dir = os.path.dirname(__file__)
    output_path = os.path.join(current_dir, "dashboards/dashboard.json")
    dashboard_json = get_dashboard_json(dashboard)
    with open(output_path, "w") as outfile:
        outfile.write(dashboard_json)


save_dashboard(dashboard)
