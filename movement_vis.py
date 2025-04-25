import streamlit as st
import pandas as pd
import glob
import plotly.graph_objs as go

# Set page config
st.set_page_config(page_title="Measurement Viewer", layout="wide")

st.title("📊 Interactive Measurement Data Viewer")

# Find all CSV files matching pattern
csv_files = sorted(glob.glob("measurement_*.csv"))

if not csv_files:
    st.warning("No measurement_*.csv files found in the current directory.")
    st.stop()

# Select CSV file
selected_file = st.selectbox("Select a CSV file", csv_files)

# Load data
df = pd.read_csv(selected_file)

# Ensure 'Time' is datetime
df['Time'] = pd.to_datetime(df['Time'])

# Select value normalization mode
normalization_mode = st.radio(
    "Choose how to display the data:",
    ("Absolute", "Relative to Start", "Relative to Selected Time")
)

# Handle normalization
if normalization_mode == "Relative to Selected Time":
    selected_time = st.select_slider(
        "Pick a reference time", options=df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    )
    base_index = df[df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S') == selected_time].index[0]
    base_row = df.loc[base_index]
elif normalization_mode == "Relative to Start":
    base_row = df.iloc[0]
else:
    base_row = None  # Absolute

# Prepare data for plotting
columns_to_plot = df.columns[1:]  # Exclude 'Time'

if normalization_mode != "Absolute":
    df_plot = df.copy()
    for col in columns_to_plot:
        df_plot[col] = df[col] - base_row[col]
else:
    df_plot = df

# Create Plotly figure
fig = go.Figure()
for col in columns_to_plot:
    fig.add_trace(go.Scatter(
        x=df_plot['Time'],
        y=df_plot[col],
        mode='lines',
        name=col
    ))

fig.update_layout(
    title="Interactive Measurement Data Over Time",
    xaxis_title="Time",
    yaxis_title="Value" + (" (Relative)" if normalization_mode != "Absolute" else ""),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=60, b=40)
)

st.plotly_chart(fig, use_container_width=True)
