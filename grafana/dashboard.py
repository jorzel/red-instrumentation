import json
import os

from grafanalib.prometheus import PromGraph
from grafanalib.core import Dashboard, Row, Graph, Target, OPS_FORMAT, single_y_axis
from grafanalib._gen import DashboardEncoder

prom_panel = PromGraph(
    title="Prom HTTP Requests",
    data_source='prometheus',
    expressions=[
        ('requests', 'rate(http_request_duration_count[5m])'),
        ('server errors (5xx)', 'rate(http_request_duration_count{code=~"5.."}[5m])'),
        ('user errors (4xx)', 'rate(http_request_duration_count{code=~"4.."}[5m])'),

    ],
    yAxes=single_y_axis(format=OPS_FORMAT),
)

red_panel = Graph(
    title="HTTP Requests",
    dataSource='prometheus',
    targets=[
        Target(
            expr='rate(http_request_duration_count[5m])',
            legendFormat="{{path}} {{method}} {{code}}",
            refId='A',
        ),
    ],
    yAxes=single_y_axis(format=OPS_FORMAT),
)

# # Define queries for each RED metric
# rate_query = TimeSeries(
#     title="Requests",
#     dataSource='prometheus',
#     targets=[
#         Target(
#             expr='rate(http_request_duration_count[5m])',
#             legendFormat="Rate",
#             refId='A',
#         ),
#     ],
#     unit=OPS_FORMAT,
#     gridPos=GridPos(h=8, w=16, x=0, y=10),
# ),


# # Create a RED panel
# red_panel = Graph(
#     title='RED Panel',
#     dataSource='Prometheus',
#     targets=[rate_query],
#     yAxes=[
#         YAxis(format=OPS_FORMAT),
#         YAxis(format=SHORT_FORMAT),
#     ],
#     gridPos=GridPos(h=8, w=24, x=0, y=0)
# )

# Create a dashboard containing the RED panel
dashboard = Dashboard(
    title='RED service instrumenation',
    rows=[Row(panels=[red_panel]), Row(panels=[prom_panel])],
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
