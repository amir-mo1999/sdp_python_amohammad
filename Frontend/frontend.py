# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# set backend port
backend_port = os.environ.get("BACKEND_PORT")


def set_backend_data():
    # files containing data
    files = {
        "census": [
            (
                "",
                (
                    "acs2017_county_data.csv",
                    open("Data/acs2017_county_data.csv", "rb"),
                    "text/csv",
                ),
            )
        ],
        "state": [
            (
                "",
                (
                    "us_states.txt",
                    open("Data/us_states.txt", "rb"),
                    "text/plain",
                ),
            )
        ],
    }

    # set census data
    requests.request(
        "POST",
        f"http://127.0.0.1:{backend_port}/add-census-data",
        files=files["census"],
    )

    # set state data
    requests.request(
        "POST",
        f"http://127.0.0.1:{backend_port}/add-state-data",
        files=files["state"],
    )


def is_backend_data_set():
    """Checks if the data in the backend is set."""
    data = requests.get(
        f"http://127.0.0.1:{backend_port}/get-state-locations-with-attribute/Walk"
    ).json()["data"]

    if data == "":
        return False

    return True


def get_map_data(attribute):
    data = requests.get(
        f"http://127.0.0.1:{backend_port}/get-state-locations-with-attribute/{attribute}"
    ).json()["data"]
    df = pd.DataFrame.from_dict(data)
    return df


# set backend data if not done already
if not is_backend_data_set():
    set_backend_data()

# get list of attributes in county data
attributes = pd.read_csv(
    "Data/acs2017_county_data.csv", index_col="CountyId", header=0
).columns


app = Dash(__name__)
app.layout = html.Div(
    [
        dcc.Graph(id="us-map"),
        dcc.Dropdown(attributes, "Walk", id="attribute-dropdown"),
    ]
)


@callback(
    Output("us-map", "figure"),
    Input("attribute-dropdown", "value"),
)
def display_us_map(value):
    us_cities = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv"
    )
    print(us_cities)
    fig = px.scatter_mapbox(
        get_map_data(attribute=value),
        lat="state_latitude",
        lon="state_longitude",
        hover_name="State",
        color_discrete_sequence=["fuchsia"],
        zoom=3,
        height=300,
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
