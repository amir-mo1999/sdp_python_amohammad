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


def init_dashboard(server):
    # set backend data if not done already
    if not is_backend_data_set():
        set_backend_data()

    # get list of attributes in county data
    attributes = pd.read_csv(
        "Data/acs2017_county_data.csv", index_col="CountyId", header=0
    ).columns.tolist()  # .remove("State")
    attributes.remove("State")
    # set up app
    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname="/",
    )
    dash_app.layout = html.Div(
        [
            dcc.Graph(id="us-map"),
            dcc.Dropdown(attributes, "Drive", id="attribute-dropdown"),
        ]
    )

    # set up cache
    cache = Cache(
        dash_app.server,
        config={
            # try 'filesystem' if you don't want to setup redis
            "CACHE_TYPE": "filesystem",
            "CACHE_DIR": "cache-directory",
        },
    )
    timeout = 50

    @cache.memoize(timeout=timeout)
    def query_map_data(attribute):
        """Retrieves DataFrame from backend for given attribute."""
        data = requests.get(
            backend_url + f"get-state-locations-with-attribute/{attribute}"
        ).json()["data"]
        df = pd.DataFrame.from_dict(data)
        return df

    # Initialize callbacks after dash app is loaded
    @callback(
        Output("us-map", "figure"),
        Input("attribute-dropdown", "value"),
    )
    def display_us_map(attribute_value):
        # get data
        df = query_map_data(attribute=attribute_value)

        if attribute_value != "County":
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
        else:
            # no matter what value i put here the markers always default to the max size, idk what the problem is
            df["size"] = 1

        # create mapbox
        fig = px.scatter_mapbox(
            df,
            lat="state_latitude",
            lon="state_longitude",
            hover_name="State",
            hover_data={attribute_value: True, "size": False},
            size=df["size"],
            size_max=15,
            color_discrete_sequence=["fuchsia"],
            zoom=3.5,
            height=300,
            labels={"state_latitude": "Lat", "state_longitude": "Lon"},
        )
        # add tiles
        fig.update_layout(mapbox_style="open-street-map")
        # set margins and height
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=450)
        # make sure map does not reload
        fig.update_layout(uirevision=True)

        return fig

    return dash_app.server
