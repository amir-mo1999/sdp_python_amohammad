from flask import Flask
from flask import request
import pandas as pd
import json
from typing import List

app = Flask(__name__)

# global variables
census_data: pd.DataFrame = None
state_data: pd.DataFrame = None
census_and_state_data: pd.DataFrame = None
census_data_req_columns: List = [
    "CountyId",
    "State",
    "County",
    "TotalPop",
    "Men",
    "Women",
    "Hispanic",
    "White",
    "Black",
    "Native",
    "Asian",
    "Pacific",
    "VotingAgeCitizen",
    "Income",
    "IncomeErr",
    "IncomePerCap",
    "IncomePerCapErr",
    "Poverty",
    "ChildPoverty",
    "Professional",
    "Service",
    "Office",
    "Construction",
    "Production",
    "Drive",
    "Carpool",
    "Transit",
    "Walk",
    "OtherTransp",
    "WorkAtHome",
    "MeanCommute",
    "Employed",
    "PrivateWork",
    "PublicWork",
    "SelfEmployed",
    "FamilyWork",
    "Unemployment",
]


def get_file_from_request(request):
    """
    Retrieves file from request and performs validation:
    - request only contains one file
    - file has a .csv or .txt extension

    Returns file if validation is successful and False otherwise.
    """

    # file data may only have one key
    if len(request.files.keys()) != 1:
        return None

    # retrieve file data key
    key = list(request.files.keys())[0]

    # retrieve file data
    request_files = request.files.getlist(key)

    # file data may only contain one file
    if len(request_files) != 1:
        return None

    # retrieve file
    request_file = request_files[0]

    # file must have .csv extension
    if not (
        request_file.filename.endswith(".csv")
        or request_file.filename.endswith(".txt")
    ):
        return None

    return request_file


def join_census_and_state_data():
    # retrieve global variables
    global census_data, state_data, census_and_state_data

    # join census and state data if both are set
    if census_data is not None and state_data is not None:
        # add coordinates for Puerto Rico if its not in state Data
        if "Puerto Rico" not in state_data["State"].tolist():
            state_data.loc[len(state_data)] = {
                "State": "Puerto Rico",
                "state_latitude": 18.46633000,
                "state_longitude": -66.10572000,
            }

        # merge state and census data
        census_and_state_data = census_data.merge(
            state_data, how="left", on="State"
        )

        # infer object dtypes
        census_and_state_data = census_and_state_data.infer_objects()


@app.route("/add-census-data", methods=["POST"])
def add_census_data():
    # response to return for bad requests
    bad_response = app.response_class(
        response=json.dumps(
            {
                "message": (
                    "Request body must contain a single .csv or .txt file"
                    " file holding the comma separated USA census data."
                )
            }
        ),
        status=400,
        mimetype="application/json",
    )

    request_file = get_file_from_request(request)

    # if request does not contain a valid file, return a bad response
    if request_file is None:
        return bad_response

    # read csv file into pandas DataFrame
    global census_data
    census_data = pd.read_csv(request_file, encoding="utf-8")

    # check if required columns are present
    global census_data_req_columns
    if not all(
        column in census_data.columns for column in census_data_req_columns
    ):
        return bad_response

    # call function to join census and state data
    join_census_and_state_data()

    # return success
    return app.response_class(
        response=json.dumps({"message": "Success"}),
        status=200,
        mimetype="application/json",
    )


@app.route("/add-state-data", methods=["POST"])
def add_state_data():
    # response to return for bad requests
    bad_response = app.response_class(
        response=json.dumps(
            {
                "message": (
                    "Request body must contain a single .txt or .csv file"
                    " holding coordinates of US states and may not."
                )
            }
        ),
        status=400,
        mimetype="application/json",
    )

    request_file = get_file_from_request(request)

    # if request does not contain a valid file, return a bad response
    if request_file is None:
        return bad_response

    # save state data as DataFrame
    global state_data
    state_data = pd.read_csv(
        request_file,
        delimiter="\t",
        encoding="utf-8",
        names=["State", "state_latitude", "state_longitude"],
    )

    state_data.loc[:, ["state_latitude", "state_longitude"]] = state_data.loc[
        :, ["state_latitude", "state_longitude"]
    ].apply(lambda x: x.str.replace(",", "."))

    state_data["State"] = state_data["State"].str.split(",", expand=True)[0]

    # cast latitude and longitude columns to float type and State column to object type
    state_data = state_data.astype(
        {
            "State": str,
            "state_latitude": float,
            "state_longitude": float,
        }
    )

    # call function to join census and state data
    join_census_and_state_data()

    # return success
    return app.response_class(
        response=json.dumps({"message": "Success"}),
        status=200,
        mimetype="application/json",
    )


@app.route("/get-state-locations-with-attribute/<attribute>", methods=["GET"])
def get_state_locations_with_attribute(attribute):
    global census_and_state_data

    # wrapper function that returns response for successful requests
    def get_200_response(data):
        return app.response_class(
            response=json.dumps({"data": data}),
            status=200,
            mimetype="application/json",
        )

    # if census and state data is not set return an empty string as data
    if census_and_state_data is None:
        return get_200_response("")

    # return DataFrame view as dict if attribute is in DataFrame
    if attribute in census_and_state_data.columns:
        # view of the DataFrame containing the given attribute, State, latitude and longitude
        return_df = census_and_state_data.loc[
            :,
            [
                attribute,
                "State",
                "state_latitude",
                "state_longitude",
            ],
        ]

        # return view as dictionary
        return get_200_response(return_df.to_dict())

    # if attribute not found return 404 response
    else:
        return app.response_class(
            response=json.dumps({"message": "Attribute not found."}),
            status=404,
            mimetype="application/json",
        )


@app.route("/")
def hello():
    return "<div>Hello World!</div>"
