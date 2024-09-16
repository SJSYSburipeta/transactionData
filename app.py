import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import networkx as nx
import plotly.graph_objects as go

# Create a directed graph (DiGraph)
G = nx.DiGraph()

# Add nodes with labels and costs
nodes = [
    ("SELECT", {"label": "SELECT", "cost": 0}),
    ("Hash Match 1", {"label": "Hash Match\n(Right Outer Join)", "cost": 18}),
    ("Index Scan 1", {"label": "Index Scan\nNonClustered", "cost": 3}),
    ("Hash Match 2", {"label": "Hash Match\n(Right Outer Join)", "cost": 13}),
    ("Index Scan 2", {"label": "Index Scan\nNonClustered", "cost": 2}),
    ("Compute Scalar", {"label": "Compute Scalar", "cost": 0}),
    ("Hash Match 3", {"label": "Hash Match\n(Inner Join)", "cost": 1}),
]

# Add edges with details (hover information for each edge)
edges = [
    ("SELECT", "Hash Match 1", {"detail": "Joins SELECT with Hash Match 1", "cost": "Cost: 18"}),
    ("Hash Match 1", "Index Scan 1", {"detail": "Joins Hash Match 1 with Index Scan 1", "cost": "Cost: 3"}),
    ("Hash Match 1", "Hash Match 2", {"detail": "Joins Hash Match 1 with Hash Match 2", "cost": "Cost: 13"}),
    ("Hash Match 2", "Index Scan 2", {"detail": "Joins Hash Match 2 with Index Scan 2", "cost": "Cost: 2"}),
    ("Hash Match 2", "Compute Scalar", {"detail": "Joins Hash Match 2 with Compute Scalar", "cost": "Cost: 0"}),
    ("Compute Scalar", "Hash Match 3", {"detail": "Joins Compute Scalar with Hash Match 3", "cost": "Cost: 1"}),
    ("Hash Match 3", "Index Scan 2", {"detail": "Joins Hash Match 3 with Index Scan 2", "cost": "Cost: 2"}),
]

# Add nodes and edges to the graph
G.add_nodes_from(nodes)
G.add_edges_from([(edge[0], edge[1]) for edge in edges])

# Custom positions for an organizational chart (organized left to right)
pos = {
    "SELECT": (0, 3),
    "Hash Match 1": (2, 3),
    "Index Scan 1": (4, 2),
    "Hash Match 2": (4, 3),
    "Index Scan 2": (6, 2),
    "Compute Scalar": (6, 3),
    "Hash Match 3": (6, 1),
}

# Create a function to generate the figure based on filtered data
def create_figure(selected_label=None, cost_range=[0, 20]):
    # Filter the nodes based on cost range
    filtered_nodes = {k: v for k, v in nodes if cost_range[0] <= v["cost"] <= cost_range[1]}

    # Create node traces (rectangular markers)
    node_x = []
    node_y = []
    node_labels = []
    node_costs = []

    for node, position in pos.items():
        if node in filtered_nodes:
            x, y = position
            node_x.append(x)
            node_y.append(y)
            node_labels.append(G.nodes[node]['label'])
            node_costs.append(G.nodes[node]['cost'])

    # Create L-shaped edges (lines connecting the blocks with 90-degree bends)
    edge_x = []
    edge_y = []
    edge_text = []  # To store hover text for each edge
    arrow_x = []
    arrow_y = []
    arrow_text = []

    for edge in edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        # Create L-shaped bend: first go horizontally, then vertically
        edge_x.append(x0)
        edge_x.append(x1)  # Horizontal move to align x-axis
        edge_x.append(x1)
        edge_x.append(None)  # Break between edges
        edge_y.append(y0)
        edge_y.append(y0)  # Stay at the same y (horizontal edge)
        edge_y.append(y1)  # Vertical move
        edge_y.append(None)  # Break between edges

        # Add hover text for each edge
        edge_text.append(f"{edge[2]['detail']}<br>{edge[2]['cost']}")

        # Calculate midpoint for the arrow and store hover info
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        arrow_x.append(mid_x)
        arrow_y.append(mid_y)
        arrow_text.append(f"{edge[2]['detail']}<br>{edge[2]['cost']}")

    # Create the rectangular node blocks (using squares as a substitute for rectangles)
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_labels,
        textposition="middle center",
        marker=dict(
            size=60,  # Square size
            color=node_costs,
            colorscale='Bluered',
            colorbar=dict(
                title='Cost'
            ),
            symbol="square",  # Set marker shape to square
            line_width=2,
            line_color="darkblue" if selected_label is None else "red",
        ),
        hoverinfo="text"
    )

    # Create the L-shaped edge trace (lines with 90-degree bends connecting the blocks)
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=2, color='gray'),
        mode='lines',
        hoverinfo='none',  # Disable hover on the edge itself
    )

    # Add directional arrows on the edges for hover effect
    arrow_trace = go.Scatter(
        x=arrow_x,
        y=arrow_y,
        mode='markers',
        marker=dict(
            size=10,
            color='red',
            symbol='triangle-right',  # Arrow shape pointing to the right
            line=dict(width=1, color='darkred')
        ),
        text=arrow_text,  # Hover text for arrows
        hoverinfo='text'  # Show hover text on hover
    )

    # Create the figure for the organizational chart
    fig = go.Figure(data=[edge_trace, arrow_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=0),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False),
                        title="Query Execution Plan"
                    ))

    return fig

# Initialize the Dash app
app = dash.Dash(__name__)

# App Layout
app.layout = html.Div([
    html.H1("Bank Transactional Data Visualization Chart- Example"),

    # Filter by cost range slider
    html.Div([
        html.Label("Filter by Cost Range:"),
        dcc.RangeSlider(
            id='cost-range-slider',
            min=0,
            max=20,
            step=1,
            marks={i: str(i) for i in range(0, 21)},
            value=[0, 20]  # Default range
        )
    ], style={'width': '50%', 'margin': '20px'}),

    # Filter by node label
    html.Div([
        html.Label("Highlight Node by Label:"),
        dcc.Dropdown(
            id='label-dropdown',
            options=[{'label': G.nodes[node]['label'], 'value': node} for node in G.nodes],
            value=None,
            placeholder="Select a node to highlight"
        )
    ], style={'width': '50%', 'margin': '20px'}),

    # Graph output
    dcc.Graph(id='graph-output'),

])

# Callback to update the graph based on filters
@app.callback(
    Output('graph-output', 'figure'),
    [Input('cost-range-slider', 'value'),
     Input('label-dropdown', 'value')]
)
def update_graph(cost_range, selected_label):
    return create_figure(selected_label, cost_range)


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
