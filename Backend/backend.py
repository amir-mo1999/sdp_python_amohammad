from flask import Flask
from flask import request
import pandas as pd
import json

app = Flask(__name__)

# global variables
census_data: pd.DataFrame = None
state_data: pd.DataFrame = None
census_and_state_data: pd.DataFrame = None


def join_census_and_state_data():
    """
    Merges the two DataFrames census_data and state_data into
    the census_and_state_data DataFrame by adding state coordinates to census_data.
    States for which no coordinate data is given in state_data are printed to the console and
    their coordinates in the final merged DataFrame are set to NaN.
    """
    # retrieve global variables
    global census_data, state_data, census_and_state_data

    # join census and state data if both are set
    if census_data is not None and state_data is not None:
        census_and_state_data = census_data.merge(
            state_data, how="left", on="State"
        )

        # infer object dtypes
        census_and_state_data = census_and_state_data.infer_objects()

        # print out states from census data that do not exist in state data
        nan_coordinates = (
            census_and_state_data[["state_latitude", "state_longitude"]]
            .isna()
            .any(axis=1)
        )
        print("No coordinates for the following states:")
        print(census_and_state_data.loc[nan_coordinates, "State"].unique())


@app.route("/add-census-data", methods=["POST"])
def add_census_data():
    # response to return for bad requests
    bad_response = app.response_class(
        response=json.dumps(
            {
                "message": (
                    "Request body must contain a single .csv"
                    " file holding the comma separated USA census"
                    " data and may not contain any form data."
                )
            }
        ),
        status=400,
        mimetype="application/json",
    )

    # request may not contain any form data
    if len(request.form) != 0:
        return bad_response

    # file data may only have one key
    if len(request.files.keys()) != 1:
        return bad_response

    # retrieve file data key
    key = list(request.files.keys())[0]

    # retrieve file data
    request_files = request.files.getlist(key)

    # file data may only contain one file
    if len(request_files) != 1:
        return bad_response

    # retrieve file
    request_file = request_files[0]

    # file must have .csv extension
    if not request_file.filename.endswith(".csv"):
        return bad_response

    # the .csv file must contain the following columns
    required_columns = [
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

    # read csv file into pandas DataFrame
    global census_data
    census_data = pd.read_csv(request_file, encoding="utf-8")

    # check if required columns are present
    if not all(column in census_data.columns for column in required_columns):
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
                    "Request body must contain a single .txt file"
                    " holding coordinates of US states and may not"
                    " contain any form data."
                )
            }
        ),
        status=400,
        mimetype="application/json",
    )

    # request may not contain any form data
    if len(request.form) != 0:
        return bad_response

    # file data may only have one key
    if len(request.files.keys()) != 1:
        return bad_response

    # retrieve file data key
    key = list(request.files.keys())[0]

    # retrieve file data
    request_files = request.files.getlist(key)

    # file data should only contain one file
    if len(request_files) != 1:
        return bad_response

    # retrieve file
    request_file = request_files[0]

    # file must have a .txt extension
    if not request_file.filename.endswith(".txt"):
        return bad_response

    # retrieve data for each state iteratively since file does not
    # have a consistent separator
    states = []
    latitudes = []
    longitudes = []
    for line in request_file.stream.read().decode("utf-8").split("\n"):
        # split line on comma + space
        line_split = line.split(", ")

        # retrieve state
        states.append(line_split[0])

        # strip second part of the line and replace commas with dots to make
        # decimal separators consistent
        line_split[1] = line_split[1].strip().replace(",", ".")

        # retrieve latitude and longitude by splitting on tab stops
        lat, lng = line_split[1].split("\t")[1:]
        latitudes.append(lat)
        longitudes.append(lng)

    # save state data as DataFrame
    global state_data
    state_data = pd.DataFrame.from_dict(
        {
            "State": states,
            "state_latitude": lat,
            "state_longitude": lng,
        },
    )

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
