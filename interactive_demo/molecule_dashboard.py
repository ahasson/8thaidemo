import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw
import base64
import io


feature_data = pd.read_csv("figure_2_demo_data.csv")
feature_data.columns = ["feature", "x_coord", "y_coord", "cov", "top_smiles"]
# Convert str list to list
feature_to_smiles = feature_data["top_smiles"].apply(lambda x: eval(x))
feature_data["feature_name"] = feature_data["feature"].values.astype(str)
# Convert list to dict
feature_to_mols = dict(zip(feature_data["feature"], feature_to_smiles))

feature_data["num_molecules"] = feature_data.apply(
    lambda x: len(feature_to_smiles[x["feature"]]), axis=1
)

df = pd.DataFrame(feature_data)

# Function to generate molecule image as base64 string
def mol_to_img_base64(smiles, img_size=(200, 200)):
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        img = Draw.MolToImage(mol, size=img_size)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Error generating image for SMILES {smiles}: {e}")
        return None


# Function to create a horizontal row of molecule images
def create_molecule_grid(smiles_list, max_cols=None):
    """Create a horizontal row layout of molecule structures for widescreen displays"""
    if not smiles_list:
        return html.Div(
            "No molecules available", style={"textAlign": "center", "color": "#7f8c8d"}
        )

    # Calculate width based on number of molecules for horizontal display
    num_molecules = len(smiles_list)
    molecule_width = min(250, max(180, 1200 // num_molecules))  # Responsive width

    grid_items = []
    for i, smiles in enumerate(smiles_list):
        mol_img = mol_to_img_base64(
            smiles, img_size=(molecule_width - 20, molecule_width - 20)
        )
        if mol_img:
            grid_items.append(
                html.Div(
                    [
                        html.Img(
                            src=mol_img,
                            style={
                                "width": "100%",
                                "height": "auto",
                                "border": "2px solid #ddd",
                                "borderRadius": "8px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                "backgroundColor": "white",
                            },
                        ),
                        html.P(
                            f"Molecule {i+1}",
                            style={
                                "textAlign": "center",
                                "fontSize": "12px",
                                "fontWeight": "500",
                                "margin": "8px 0 0 0",
                                "color": "#2c3e50",
                            },
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "width": f"{molecule_width}px",
                        "verticalAlign": "top",
                        "margin": "10px",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e9ecef",
                        "transition": "transform 0.2s ease",
                    },
                    className="molecule-card",  # For potential CSS hover effects
                )
            )
        else:
            grid_items.append(
                html.Div(
                    [
                        html.Div(
                            "Invalid SMILES",
                            style={
                                "border": "2px dashed #ccc",
                                "padding": "40px 20px",
                                "textAlign": "center",
                                "color": "#999",
                                "fontSize": "14px",
                                "borderRadius": "8px",
                                "backgroundColor": "#f8f9fa",
                            },
                        ),
                        html.P(
                            f"Molecule {i+1}",
                            style={
                                "textAlign": "center",
                                "fontSize": "12px",
                                "fontWeight": "500",
                                "margin": "8px 0 0 0",
                                "color": "#2c3e50",
                            },
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "width": f"{molecule_width}px",
                        "verticalAlign": "top",
                        "margin": "10px",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e9ecef",
                    },
                )
            )

    return html.Div(
        grid_items,
        style={
            "textAlign": "center",
            "overflowX": "auto",  # Allow horizontal scrolling if needed
            "whiteSpace": "nowrap",  # Prevent wrapping
            "padding": "10px 0",
        },
    )


# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div(
    [
        html.H1(
            "Feature Space Visualization - Top Molecules per Feature",
            style={"textAlign": "center", "marginBottom": 30, "color": "#2c3e50"},
        ),
        # Scatterplot section
        html.Div(
            [
                dcc.Graph(
                    id="molecule-scatter",
                    style={"height": "600px"},
                    config={"displayModeBar": True},
                )
            ],
            style={"width": "100%", "marginBottom": "20px"},
        ),
        # Info panel section - full width below the plot
        html.Div(
            [
                html.H3(
                    "Feature Molecules",
                    style={
                        "textAlign": "center",
                        "color": "#34495e",
                        "marginBottom": "15px",
                    },
                ),
                html.Div(id="molecule-info", style={"padding": "20px"}),
            ],
            style={
                "width": "100%",
                "border": "1px solid #bdc3c7",
                "borderRadius": "5px",
                "backgroundColor": "#f8f9fa",
            },
        ),
    ],
    style={
        "fontFamily": "Arial, sans-serif",
        "margin": "20px",
        "maxWidth": "1400px",
        "marginLeft": "auto",
        "marginRight": "auto",
    },
)


# Create the scatter plot
@app.callback(
    Output("molecule-scatter", "figure"),
    Input("molecule-scatter", "id"),  # Dummy input to trigger callback on load
)
def update_scatter(graph_id):
    fig = go.Figure()

    # Add scatter plot
    fig.add_trace(
        go.Scatter(
            x=df["x_coord"],
            y=df["y_coord"],
            mode="markers",
            marker=dict(
                size=10,
                color=df["cov"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Coefficient of Variation"),
                line=dict(width=2, color="DarkSlateGrey"),
            ),
            text=df["feature_name"],
            hovertemplate="<b>%{text}</b><br>"
            + "X: %{x}<br>"
            + "Y: %{y}<br>"
            + "Coefficient of Variation: %{marker.color:.2f}<br>"
            + "<extra></extra>",
            customdata=df.index,
        )
    )
    fig.update_xaxes(type="log")

    fig.update_layout(
        title="Feature Space Visualization",
        xaxis_title="Activation frequency [log scale]",
        yaxis_title="Mean normalised activation",
        hovermode="closest",
        plot_bgcolor="rgba(240,240,240,0.8)",
        paper_bgcolor="white",
        font=dict(size=12),
    )

    return fig


# Update molecule info panel when hovering over points
@app.callback(
    Output("molecule-info", "children"), Input("molecule-scatter", "hoverData")
)
def update_molecule_info(hoverData):
    if hoverData is None:
        return html.Div(
            [
                html.P(
                    "Hover over a feature point to see the top molecules for that feature!",
                    style={
                        "textAlign": "center",
                        "color": "#7f8c8d",
                        "fontStyle": "italic",
                    },
                )
            ]
        )

    # Get the point index - try multiple methods for robustness
    point_data = hoverData["points"][0]

    # Try to get point index from pointIndex, pointNumber, or by matching text
    if "pointIndex" in point_data:
        point_index = point_data["pointIndex"]
    elif "pointNumber" in point_data:
        point_index = point_data["pointNumber"]
    elif "customdata" in point_data:
        point_index = point_data["customdata"]
    else:
        # Fallback: match by feature name from text field
        feature_name = point_data.get("text", "")
        point_index = (
            df[df["feature_name"] == feature_name].index[0]
            if feature_name in df["feature_name"].values
            else 0
        )

    feature = df.iloc[point_index]
    feature_id = feature["feature"]

    # Get molecules for this feature
    molecules_smiles = feature_to_mols.get(feature_id, [])

    # Create the info panel content
    info_content = [
        html.H4(
            f"Feature {feature_id}: {feature['feature_name']}",
            style={"color": "#2c3e50", "marginBottom": "10px"},
        ),
        html.Hr(),
    ]

    # Add molecule grid
    if molecules_smiles:
        molecule_grid = create_molecule_grid(molecules_smiles)
        info_content.append(molecule_grid)
    else:
        info_content.append(
            html.P(
                "No molecules available for this feature",
                style={
                    "color": "#e74c3c",
                    "fontStyle": "italic",
                    "textAlign": "center",
                },
            )
        )

    return info_content


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
