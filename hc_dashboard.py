# import necessary libraries
import streamlit as st
import pyarrow.dataset as ds
import pandas as pd
import os

# read data from S3 curated bucket
@st.cache_data
def load_provider_data():
    dataset = ds.dataset(
        "s3://hc-glue-bucket-curated/provider_info/",
        format = "parquet"
    )
    return dataset.to_table().to_pandas()

@st.cache_data
def load_quality_data():
    dataset = ds.dataset(
        "s3://hc-glue-bucket-curated/quality/",
        format="parquet"
    )
    return dataset.to_table().to_pandas()

@st.cache_data
def load_pbj_data():
    dataset = ds.dataset(
        "s3://hc-glue-bucket-curated/pbj/",
        format="parquet"
    )
    return dataset.to_table().to_pandas()

@st.cache_data
def load_state_averages_data():
    dataset = ds.dataset(
        "s3://hc-glue-bucket-curated/state_averages/",
        format="parquet"
    )
    return dataset.to_table().to_pandas()

provider_df = load_provider_data()

quality_df = load_quality_data()

pbj_df = load_pbj_data()

state_df = load_state_averages_data()

st.sidebar.header("Filters")

state_options = ['All'] + sorted(provider_df["state"].dropna().unique().tolist())

selected_state = st.sidebar.selectbox(
    "State",
    state_options
)
owner_options = ['All'] + sorted(
    provider_df["ownership_type"].dropna().unique().tolist()
    )
selected_owner = st.sidebar.selectbox(
    "Ownership Type",
    owner_options
)
filtered_df = provider_df.copy()

if selected_state != "All":
    filtered_df = filtered_df[
        filtered_df["state"] == selected_state
    ]

if selected_owner != "All":
    filtered_df = filtered_df[
        filtered_df["ownership_type"] == selected_owner
    ]

provider_options = ["All"] + sorted(
    filtered_df["provider_name"]
    .dropna()
    .unique()
    .tolist()
)

selected_provider = st.sidebar.selectbox(
    "Provider",
    provider_options
)

if selected_provider != "All":
    filtered_df = filtered_df[
        filtered_df["provider_name"] == selected_provider
    ]

filtered_ccns = filtered_df[
    "cms_certification_number_ccn"
].unique()

filtered_pbj_df = pbj_df[
    pbj_df["cms_certification_number_ccn"].isin(filtered_ccns)
]

filtered_facility_staffing = (
    filtered_pbj_df
    .groupby(
        [
            "cms_certification_number_ccn",
            "provider_name",
            "state"
        ]
    )["Total_Nurse_Hrs"]
    .mean()
    .reset_index(name="avg_total_nurse_hrs")
)

total_providers = filtered_df["provider_name"].nunique()

average_occupancy = (
    filtered_df["occupancy_rate"].mean()
    if not filtered_df.empty
    else 0
)

average_beds = (
    filtered_df["certified_beds"].mean()
    if not filtered_df.empty
    else 0
)

average_residents =  (
    filtered_df["average_residents_per_day"].mean()
    if not filtered_df.empty
    else 0
)

st.title("HealthCare Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Providers",
    total_providers
)
col2.metric(
    "Avg Occupancy",
    f"{average_occupancy:.1%}"
)
col3.metric(
    "Avg Certified Beds",
    f"{average_beds:.1f}"
)
col4.metric(
    "Avg Residents/Day",
    f"{average_residents:.1f}"
)
with st.expander("Provider Details", expanded=True):

    state_names = {
        "AL": "Alabama",
        "AK": "Alaska",
        "AZ": "Arizona",
        "AR": "Arkansas",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DC": "District of Columbia",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "GU": "Guam",
        "HI": "Hawaii",
        "ID": "Idaho",
        "IL": "Illinois",
        "IN": "Indiana",
        "IA": "Iowa",
        "KS": "Kansas",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "ME": "Maine",
        "MD": "Maryland",
        "MA": "Massachusetts",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MS": "Mississippi",
        "MO": "Missouri",
        "MT": "Montana",
        "NE": "Nebraska",
        "NV": "Nevada",
        "NH": "New Hampshire",
        "NJ": "New Jersey",
        "NM": "New Mexico",
        "NY": "New York",
        "NC": "North Carolina",
        "ND": "North Dakota",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "OR": "Oregon",
        "PA": "Pennsylvania",
        "PR": "Puerto Rico",
        "RI": "Rhode Island",
        "SC": "South Carolina",
        "SD": "South Dakota",
        "TN": "Tennessee",
        "TX": "Texas",
        "UT": "Utah",
        "VT": "Vermont",
        "VA": "Virginia",
        "WA": "Washington",
        "WV": "West Virginia",
        "WI": "Wisconsin",
        "WY": "Wyoming"
    }
    
    if not filtered_df.empty:

        provider = filtered_df.iloc[0]
        # st.write(provider)   # temporary debugging line

        #Overall rating
        if pd.isna(provider["overall_rating"]):
            overall_display = "Not rated"
        else:
            over_rating = int(provider["overall_rating"])
            overall_stars = "★" * over_rating + "☆" * (5 - over_rating)
            overall_display = f"{overall_stars} ({over_rating}/5)"

        #Staffing rating
        if pd.isna(provider["staffing_rating"]):
            staffing_display = "Not rated"
        else:
            staff_rating = int(provider["staffing_rating"])
            staffing_stars = "★" * staff_rating + "☆" * (5 - staff_rating)
            staffing_display = f"{staffing_stars} ({staff_rating}/5)"    

        details = {
            "Provider Name": provider["provider_name"],
            "State": state_names.get(
                provider["state"],
                provider["state"]
            ),
            "Ownership": provider["ownership_type"],
            "Occupancy": f"{provider['occupancy_rate']:.2%}",
            "Overall Rating": overall_display,
            "Staffing Rating": staffing_display
        }
        st.table(details)

    else:
        st.info("No provider is available for the selected filters.")

# Dataframe for correcting charts
chart_df = provider_df.copy()

if selected_state != "All":
    chart_df = chart_df[
        chart_df["state"] == selected_state
    ]

if selected_owner != "All":
    chart_df = chart_df[
        chart_df["ownership_type"] == selected_owner
    ]

if selected_state == "All":
    st.title("Occupancy Rate by State")
elif selected_owner == "All":
    st.title(
        f"{state_names.get(selected_state, selected_state)}"
    )
else:
    st.title(
        f"{selected_owner} Providers in {state_names.get(selected_state, selected_state)}"
    )

occupancy = (
    chart_df.groupby("provider_name") ["occupancy_rate"]
    .mean()
    .sort_values(ascending=False)
)
st.bar_chart(occupancy)

# Beds by ownership type chart
st.title("Certified Beds by Provider")
 
beds = (
    chart_df.groupby("provider_name")["certified_beds"]
    .mean()
    .sort_values(ascending=False)
)
st.bar_chart(beds)

# Providers by state chart
st.title("Providers by State")

providers = (
    chart_df.groupby("state")   
    .size()
    .sort_values(ascending=False)
)
st.bar_chart(providers)

# avg total nurse hrs per facility
filtered_facility_staffing = (
    filtered_pbj_df
    .groupby(
        ["cms_certification_number_ccn", "provider_name", "state"]
    )["Total_Nurse_Hrs"]
    .mean()
    .reset_index(name="avg_total_nurse_hrs")
)

st.subheader("Occupancy vs. Nurse Hours per Resident")

filtered_facility_analysis = (
    filtered_df[
        [
            "cms_certification_number_ccn",
            "provider_name",
            "state",
            "occupancy_rate",
            "average_residents_per_day"
        ]
    ]
    .merge(
        filtered_facility_staffing,
        on=[
            "cms_certification_number_ccn",
            "provider_name"
        ],
        how="inner"
    )
)

filtered_facility_analysis["nurse_hours_per_resident"] = (
    filtered_facility_analysis["avg_total_nurse_hrs"]
    / filtered_facility_analysis["average_residents_per_day"]
)

# chart shown is scattered to
# the left for occupancy rate
st.scatter_chart(
    filtered_facility_analysis,
    x="occupancy_rate",
    y="nurse_hours_per_resident"
)

# extracting month from datetime in order to calculate metrics 
pbj_df["WorkDate"] = pd.to_datetime(
    pbj_df["WorkDate"].astype(str)
)
pbj_df["month"] = pbj_df["WorkDate"].dt.to_period("M").astype(str)

# referred to in nurse_hours_state (below
monthly_nurse_hours = (
    pbj_df
    .groupby(
        [
            "cms_certification_number_ccn",
            "provider_name",
            "state",
            "month"
        ]
    )["Total_Nurse_Hrs"]
    .sum()
    .reset_index()
)

# show a record count of 91 for each cms cert numb (ccn)
pbj_quarters = (
    pbj_df
    .groupby(
        ["cms_certification_number_ccn", "CY_Qtr"]
    )
    .size()
    .reset_index(name="record_count")
)
# nurse hours per state; fewest is AK & PR; most is CA & NY
nurse_hours_state = (
    monthly_nurse_hours
    .groupby("state")["Total_Nurse_Hrs"]
    .sum()
    .reset_index()
    .sort_values("Total_Nurse_Hrs", ascending=True)
)

nurse_hours_provider = (
    monthly_nurse_hours
    .groupby(
        ["provider_name", "state"
    ]
    )["Total_Nurse_Hrs"]
    .sum()
    .reset_index()
    .sort_values("Total_Nurse_Hrs", ascending=False)
)

provider_occupancy = (
    filtered_df[
        ["provider_name", "state", "occupancy_rate"]
    ]
    .sort_values(
        "occupancy_rate",
        ascending=False
    )
)
