import pyarrow.dataset as ds
import pyarrow.fs as fs
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

# Create single S3 filesystem connection using Streamlit secrets
s3 = fs.S3FileSystem(
    access_key=st.secrets["AWS_ACCESS_KEY_ID"],
    secret_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region=st.secrets.get("AWS_DEFAULT_REGION", "us-east-1")
)

@st.cache_data
def load_provider_data():
    dataset = ds.dataset(
        "hc-glue-bucket-curated/provider_info/",
        format="parquet",
        filesystem=s3
    )
    return dataset.to_table().to_pandas()

@st.cache_data
def load_pbj_data():
    dataset = ds.dataset(
        "hc-glue-bucket-curated/pbj/",
        format="parquet",
        filesystem=s3
    )
    return dataset.to_table().to_pandas()

# Load DataFrames
provider_df = load_provider_data()
pbj_df = load_pbj_data()

st.write("DEBUG: Data loaded successfully")

st.title("Nurse Staffing Analysis")

st.write(
    "This page examines nursing staffing levels in relation to "
    "facility occupancy and resident population."
)

filtered_provider_df = provider_df.copy()

st.sidebar.header("Filters")

state_options = ['All'] + sorted(
    provider_df["state"].dropna().unique().tolist()
)
selected_state = st.sidebar.selectbox(
    "State",
    state_options
)

if selected_state != "All":
    filtered_provider_df = filtered_provider_df[
        filtered_provider_df["state"] == selected_state
    ]

owner_options = ["All"] + sorted(
    filtered_provider_df["ownership_type"]
   .dropna()
   .unique()
   .tolist()
   )
selected_owner = st.sidebar.selectbox(
    "Ownership Type",
    owner_options
)

if selected_owner != "All":
    filtered_provider_df = filtered_provider_df[
        filtered_provider_df["ownership_type"] == selected_owner
    ]

provider_options = ['All'] + sorted(
    filtered_provider_df["provider_name"].dropna().unique().tolist()
)
selected_provider = st.sidebar.selectbox(
    "Provider",
    provider_options
)

if selected_provider != "All":
    filtered_provider_df = filtered_provider_df[
        filtered_provider_df["provider_name"] == selected_provider
    ]
st.write("1. Staffing page started")

filtered_ccns = filtered_provider_df[
    "cms_certification_number_ccn"
].unique()

st.write("2. CCNs identified:", len(filtered_ccns))

filtered_pbj_df = pbj_df[
    pbj_df["cms_certification_number_ccn"].isin(filtered_ccns)
]
st.write(
    "3. PBJ filtering completed:",
    len(filtered_pbj_df)
)

st.write(
    "DEBUG - selected state:",
    selected_state
)

st.write(
    "DEBUG - CCNs:",
    len(filtered_ccns)
)

st.write(
    "DEBUG - PBJ records:",
    len(filtered_pbj_df)
)

st.write("3. PBJ filtering completed:", len(filtered_pbj_df))

facility_staffing = (
    filtered_pbj_df
    .groupby(
        ["cms_certification_number_ccn", "provider_name"]
    )["Total_Nurse_Hrs"]
    .mean()
    .reset_index(name="avg_total_nurse_hrs")
)
st.write(
    "4. Facility staffing calculation completed:",
    len(facility_staffing)
)
st.write("Selected state:", selected_state)
st.write("Selected ownership:", selected_owner)
st.write("Selected provider:", selected_provider)

# st.write("5. Starting metrics calculation")

# st.write(
#     "5a. Filtered provider records:",
#     len(filtered_provider_df)
)

# st.write(
#     "5b. Filtered PBJ records:",
#     len(filtered_pbj_df)
# )

# st.write("5c. Starting facility merge")

# # subset of facility_analysis currently selected by the dashboard user
# filtered_facility_analysis = (
#     filtered_provider_df[
#         [
#             "cms_certification_number_ccn",
#             "provider_name",
#             "state",
#             "ownership_type",
#             "occupancy_rate",
#             "average_residents_per_day"
#         ]
#     ]
#     .merge(
#         facility_staffing,
#         on=["cms_certification_number_ccn", "provider_name"],
#         how="inner"
#     )
# )

# st.write(
#     "5d. Facility merge completed:",
#     len(filtered_facility_analysis)
# )

# st.write("5e. Starting nurse-hours-per-resident calculation")

# filtered_facility_analysis["nurse_hours_per_resident"] = (
#     filtered_facility_analysis["avg_total_nurse_hrs"]
#     / filtered_facility_analysis["average_residents_per_day"]
# )

# filtered_facility_analysis["nurse_hours_per_resident"] = (
#     filtered_facility_analysis["nurse_hours_per_resident"]
#     .replace([float("inf"), -float("inf")], pd.NA)
# )

# st.write("5f. Nurse-hours-per-resident calculation completed")

# st.write("Starting metrics calculation")
# total_providers = filtered_provider_df["provider_name"].nunique()
# st.write("5. Provider count calculated")
# avg_nurse_hours = (
#     filtered_facility_analysis["avg_total_nurse_hrs"].mean()
# )
# st.write("6. Average nurse hours calculated")

# avg_nurse_hours_per_resident = (
#     filtered_facility_analysis["nurse_hours_per_resident"].mean()
# )

# st.write("6a. Average nurse hours per resident calculated")

# avg_occupancy = (
#     filtered_facility_analysis["occupancy_rate"].mean()
# )
# st.write("7. Average occupancy calculated")

# avg_nurse_hours = 0 if pd.isna(avg_nurse_hours) else avg_nurse_hours
# avg_nurse_hours_per_resident = (
#     0 if pd.isna(avg_nurse_hours_per_resident)
#     else avg_nurse_hours_per_resident
# )
# avg_occupancy = 0 if pd.isna(avg_occupancy) else avg_occupancy

# st.write("7a. NaN handling completed")

# total_employee_hrs = filtered_pbj_df["employee_hrs"].sum()
# total_contractor_hrs = filtered_pbj_df["contractor_hrs"].sum()

# st.write("8. Employee and contractor hours summed")

# # Contractor percentage
# if total_employee_hrs == 0 and total_contractor_hrs == 0:
#     contractor_hours_pct = None
# else:
#     contractor_hours_pct = (
#         total_contractor_hrs /
#         (total_employee_hrs + total_contractor_hrs)
#     )

# contractor_pct_display = (
#     "N/A"
#     if contractor_hours_pct is None
#     else f"{contractor_hours_pct:.1%}"
# )

# # Permanent / Contractor hours ratio
# if total_contractor_hrs > 0:
#     employee_contractor_ratio = (
#         total_employee_hrs / total_contractor_hrs
#     )
# else:
#     employee_contractor_ratio = None

# employee_contractor_ratio_display = (
#     "N/A"
#     if employee_contractor_ratio is None
#     else f"{employee_contractor_ratio:.2f}:1"
# )
# st.write("9. Employee/contractor calculations completed")
# total_nursing_hrs = (
#     total_employee_hrs + total_contractor_hrs
# )

# if total_nursing_hrs > 0:
#     employee_pct = total_employee_hrs / total_nursing_hrs
#     contractor_pct = total_contractor_hrs / total_nursing_hrs
# else:
#     employee_pct = 0
#     contractor_pct = 0

# staffing_mix = pd.DataFrame({
#     "Staff Type": ["Employee", "Contractor"],
#     "Hours": [total_employee_hrs, total_contractor_hrs]
# })

# # First row
# col1, col2, col3, col4 = st.columns(4)

# col1.metric(
#     "Providers",
#     total_providers
# )

# col2.metric(
#     "Avg Nurse Hours",
#     f"{avg_nurse_hours:,.1f}"
# )

# col3.metric(
#     "Avg Nurse Hours / Resident",
#     f"{avg_nurse_hours_per_resident:,.2f}"
# )

# col4.metric(
#     "Avg Occupancy",
#     f"{avg_occupancy:.1%}"
# )


# # Second row
# col5, col6, col7, col8 = st.columns(4)

# col5.metric(
#     "Employee Nursing Hours",
#     f"{total_employee_hrs:,.0f}"
# )

# col6.metric(
#     "Contractor Nursing Hours",
#     f"{total_contractor_hrs:,.0f}"
# )

# col7.metric(
#     "Permanent / Contractor Hours Ratio",
#     employee_contractor_ratio_display
# )

# col8.metric(
#     "Contractor Hours %",
#     contractor_pct_display
# )

# state_names = {
#         "AL": "Alabama",
#         "AK": "Alaska",
#         "AZ": "Arizona",
#         "AR": "Arkansas",
#         "CA": "California",
#         "CO": "Colorado",
#         "CT": "Connecticut",
#         "DC": "District of Columbia",
#         "DE": "Delaware",
#         "FL": "Florida",
#         "GA": "Georgia",
#         "GU": "Guam",
#         "HI": "Hawaii",
#         "ID": "Idaho",
#         "IL": "Illinois",
#         "IN": "Indiana",
#         "IA": "Iowa",
#         "KS": "Kansas",
#         "KY": "Kentucky",
#         "LA": "Louisiana",
#         "ME": "Maine",
#         "MD": "Maryland",
#         "MA": "Massachusetts",
#         "MI": "Michigan",
#         "MN": "Minnesota",
#         "MS": "Mississippi",
#         "MO": "Missouri",
#         "MT": "Montana",
#         "NE": "Nebraska",
#         "NV": "Nevada",
#         "NH": "New Hampshire",
#         "NJ": "New Jersey",
#         "NM": "New Mexico",
#         "NY": "New York",
#         "NC": "North Carolina",
#         "ND": "North Dakota",
#         "OH": "Ohio",
#         "OK": "Oklahoma",
#         "OR": "Oregon",
#         "PA": "Pennsylvania",
#         "PR": "Puerto Rico",
#         "RI": "Rhode Island",
#         "SC": "South Carolina",
#         "SD": "South Dakota",
#         "TN": "Tennessee",
#         "TX": "Texas",
#         "UT": "Utah",
#         "VT": "Vermont",
#         "VA": "Virginia",
#         "WA": "Washington",
#         "WV": "West Virginia",
#         "WI": "Wisconsin",
#         "WY": "Wyoming"
# }
# st.write("Permanent / Contractor H... represents Permanent / Contractor " \
# "Hours Ratio; It's calculated using employee nursing hours and contractor nursing " \
# "hours; this is an hours-based ratio, not a staff headcount ratio.")

# with st.expander("Provider Details", expanded=True):

#     if not filtered_facility_analysis.empty:

#         provider =  filtered_facility_analysis.iloc[0]
            
#         details = {
#             "Provider Name": provider["provider_name"],
#             "State": state_names.get(
#                 provider["state"],
#                 provider["state"]
#             ),
#             "Ownership": provider["ownership_type"],
#             "Average Nurse Hours": f"{avg_nurse_hours:,.1f}",
#             "Average Nurse Hours to each Resident":
#                 f"{avg_nurse_hours_per_resident:,.2f}",
#             "Average Occupancy": f"{avg_occupancy:.1%}"
#         }

#         st.table(details)

#     else:
#         st.info("No staffing data is available for the selected provider")

# st.write("6. Metrics calculation completed")

# st.write("10. Starting charts")

# st.subheader(
#     "Occupancy Rate vs. Nurse Hours per Resident"
# )
# st.scatter_chart(
#     filtered_facility_analysis,
#     x="occupancy_rate",
#     y="nurse_hours_per_resident"
# )
# state_staffing = (
#     filtered_facility_analysis
#     .groupby("state")["nurse_hours_per_resident"]
#     .mean()
#     .sort_values(ascending=False)
# )
# st.subheader("Average Nurse Hours per Resident by State")

# st.write("10a. Starting state staffing chart")

# st.bar_chart(state_staffing)

# st.write("11. State staffing chart completed")

# # pbj_df["WorkDate"] = pd.to_datetime(
# #     pbj_df["WorkDate"].astype(str)
# # )
# # pbj_df["month"] = (
# #     pbj_df["WorkDate"]
# #     .dt.to_period("M")
# #     .astype(str)
# # )

# # monthly_nurse_hours = (
# #     pbj_df
# #     .groupby(
# #         [
# #             "cms_certification_number_ccn",
# #             "provider_name",
# #             "state",
# #             "month"
# #         ]
# #     )["Total_Nurse_Hrs"]
# #     .sum()
# #     .reset_index()
# # )
# # monthly_totals = (
# #     monthly_nurse_hours
# #     .groupby("month")["Total_Nurse_Hrs"]
# #     .sum()
# # )
# # st.subheader("Total Nurse Hours by Month")

# # # st.write(monthly_nurse_hours)
# # # st.write(monthly_totals)

# # st.line_chart(monthly_totals)

# # ---------------------------------------------------------
# # Employee vs. Contractor Nursing Hours
# # ---------------------------------------------------------

# st.subheader("Employee vs. Contractor Nursing Hours")

# # -------------------------
# # Matplotlib pie chart
# # -------------------------

# st.write("Pie chart below courtesy of Matplotlib")

# fig, ax = plt.subplots()

# ax.pie(
#     [total_employee_hrs, total_contractor_hrs],
#     labels=["Employees", "Contractors"],
#     autopct="%1.1f%%"
# )

# st.pyplot(fig)

# # -------------------------
# # Altair pie chart
# # -------------------------

# st.write("Pie chart below courtesy of Altair")

# pie_chart = (
#     alt.Chart(staffing_mix)
#     .mark_arc()
#     .encode(
#         theta="Hours",
#         color="Staff Type",
#         tooltip=[
#             "Staff Type",
#             "Hours"
#         ]
#     )
# )

# st.altair_chart(pie_chart, width="stretch")

# st.caption(
#     "Percentage of total nursing hours worked by employees versus contractors."
# )

