from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import os
import requests
from flask_caching import Cache
from dotenv import load_dotenv

load_dotenv()

# backend port and base url
backend_port = os.environ.get("BACKEND_PORT")
backend_url = f"http://127.0.0.1:{backend_port}/"


def set_backend_data():
    """Sets data within the backend by sending the needed files to the respective endpoints."""
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
        backend_url + "add-census-data",
        files=files["census"],
    )

    # set state data
    requests.request(
        "POST",
        backend_url + "add-state-data",
        files=files["state"],
    )


def is_backend_data_set():
    """Checks if the data in the backend is set."""
    data = requests.get(
        backend_url + "get-state-locations-with-attribute/Walk"
    ).json()["data"]

    if data == "":
        return False

    return True


def get_map_data(attribute):
    """Retrieves DataFrame from backend for given attribute."""
    data = requests.get(
        backend_url + f"get-state-locations-with-attribute/{attribute}"
    ).json()["data"]
    df = pd.DataFrame.from_dict(data)
    return df


# set backend data if not done already
if not is_backend_data_set():
    set_backend_data()

# get list of attributes in county data
attributes = pd.read_csv(
    "Data/acs2017_county_data.csv", index_col="CountyId", header=0
).columns.remove("State")
print(attributes)

# set up app
app = Dash(__name__)
app.layout = html.Div(
    [
        dcc.Graph(id="us-map"),
        dcc.Dropdown(attributes, "Drive", id="attribute-dropdown"),
    ]
)


@callback(
    Output("us-map", "figure"),
    Input("attribute-dropdown", "value"),
)
def display_us_map(attribute_value):
    # get data
    df = get_map_data(attribute=attribute_value)

    # normalize values for attributes to determine point size
    attribute_series = df[attribute_value]
    attribute_max = attribute_series.max()
    attribute_min = attribute_series.min()
    attribute_series = (attribute_series - attribute_min) / (
        attribute_max - attribute_min
    )
    attribute_series *= 10
    attribute_series = attribute_series.clip(1, 10)
    # add point size to DataFrame
    df["size"] = attribute_series

    # create mapbox
    fig = px.scatter_mapbox(
        df,
        lat="state_latitude",
        lon="state_longitude",
        hover_name="State",
        hover_data={attribute_value: True, "size": False},
        size="size",
        color_discrete_sequence=["fuchsia"],
        zoom=3.5,
        height=300,
        labels={"state_latitude": "Lat", "state_longitude": "Lon"},
    )
    # add tiles
    fig.update_layout(mapbox_style="open-street-map")
    # set margins and height
    # fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=100)
    # make sure map does not reload
    # fig.update_layout(uirevision=True)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
