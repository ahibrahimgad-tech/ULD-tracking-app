import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# Page configuration
st.set_page_config(page_title="ULD Tracking System", layout="wide", page_icon="✈️")

# Data file (Renamed to start fresh with English columns)
DATA_FILE = "uld_data_en.csv"

# Function to load data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Ensure new columns exist
        if "ULD Status" not in df.columns:
            df["ULD Status"] = "Available"
        if "Check-out Date" not in df.columns:
            df["Check-out Date"] = ""
        return df
    else:
        df = pd.DataFrame(columns=[
            "Date", "ULD No", "Airline", "Flight No", 
             "Employee Name", "Remarks_in", "ULD Status", "Check-out Date", "Remarks_out"
        ])
        df.to_csv(DATA_FILE, index=False)
        return df

# Function to save data
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

st.title("✈️ CACC- ULD Tracking System ")

# Create Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Check-In ULD", 
    "📤 Check-Out ULD", 
    "📊 Reports & Export", 
    "📈 Dashboard"
])

# ----------------- Tab 1: Check-In ULD -----------------
with tab1:
    st.subheader("Add New ULD to Station")
    
    col1, col2 = st.columns(2)
    with col1:
        uld_no = st.text_input("ULD No")
        airline = st.selectbox("Airline", ["RMX", "SVI", "BBN", "MB", "SH", "OTHER"])
        flight_no = st.text_input("Arrival Flight No")
    
    with col2:
        Status = st.selectbox("Status", ["serviceable ", "UNserviceable"])
        employee_name = st.selectbox("Agent", ["Ahmed Ragab ", "Mohamed Fathy","ULD Control ","Dispatch Team","Ramp Team"])
        remarks = st.text_area("Remarks")
        
    if st.button("Save Data (Check-In) 💾"):
        if uld_no and flight_no and employee_name:
            # Check if ULD is already available to prevent duplicates
            if not df[(df["ULD No"] == uld_no) & (df["ULD Status"] == "Available")].empty:
                st.warning("⚠️ This ULD is already registered as (Available) in the station!")
            else:
                new_row = pd.DataFrame({
                    "Date": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "ULD No": [uld_no],
                    "Airline": [airline],
                    "Flight No": [flight_no],
                    "Employee Name": [employee_name],
                    "Remarks": [Remarks_in],
                    "ULD Status": ["Status"],
                    "Check-out Date": [""]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("✅ ULD checked in successfully!")
                st.rerun()
        else:
            st.warning("⚠️ Please fill in mandatory fields (ULD No, Flight No, Employee Name).")

# ----------------- Tab 2: Check-Out ULD -----------------
with tab2:
    st.subheader("Check-Out ULD")
    
    # Fetch only available ULDs
    available_ulds = df[df["ULD Status"] == "Available"]
    
    if not available_ulds.empty:
        col1, col2 = st.columns(2)
        with col1:
            checkout_uld = st.selectbox("Select ULD No to Check-Out", available_ulds["ULD No"].tolist())
            checkout_flight = st.text_input("Departure Flight No")
        with col2:
            checkout_emp = st.text_input("Handing Over Employee Name")
            checkout_remarks = st.text_area("Check-out Remarks (Optional)")
            
        if st.button("Check-Out 📤"):
            if checkout_flight and checkout_emp:
                # Update ULD status
                idx = df[(df["ULD No"] == checkout_uld) & (df["ULD Status"] == "Available")].index
                df.loc[idx, "ULD Status"] = "Checked Out"
                df.loc[idx, "Check-out Date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Append checkout notes to old remarks
                old_remarks = df.loc[idx, "Remarks_out"].values[0]
                new_note = f"{old_remarks} | Checked out on flight {checkout_flight} by {checkout_emp}. {checkout_remarks}"
                df.loc[idx, "Remarks"] = new_note
                
                save_data(df)
                st.success(f"✅ ULD {checkout_uld} checked out successfully!")
                st.rerun()
            else:
                st.warning("⚠️ Please enter Departure Flight No and Employee Name.")
    else:
        st.info("💡 No available ULDs in the station to check out.")

# ----------------- Tab 3: Reports & Export -----------------
with tab3:
    st.subheader("ULD Movement Report")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        airlines = ["All"] + list(df["Airline"].dropna().unique())
        selected_airline = st.selectbox("🔍 Filter by Airline", airlines)
    with col2:
        status_filter = st.radio("🔍 Filter by Status", ["All", "Available", "Checked Out"], horizontal=True)
    
    # Apply Filters
    filtered_df = df.copy()
    if selected_airline != "All":
        filtered_df = filtered_df[filtered_df["Airline"] == selected_airline]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["ULD Status"] == status_filter]
        
    # Display Dataframe
    st.dataframe(filtered_df, use_container_width=True)
    
    # Export Button
    @st.cache_data
    def convert_df(df_to_export):
        return df_to_export.to_csv(index=False).encode('utf-8')

    if not filtered_df.empty:
        csv = convert_df(filtered_df)
        st.download_button(
            label=f"📥 Export Report ( {selected_airline} - {status_filter} ) to CSV",
            data=csv,
            file_name=f'uld_reports_{selected_airline}.csv',
            mime='text/csv',
        )

# ----------------- Tab 4: Dashboard -----------------
with tab4:
    st.subheader("ULD Statistics")
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Chart: Available ULDs by Airline
            available_df = df[df["ULD Status"] == "Available"]
            if not available_df.empty:
                airline_counts = available_df["Airline"].value_counts().reset_index()
                airline_counts.columns = ["Airline", "Count"]
                fig1 = px.pie(airline_counts, names="Airline", values="Count", title="Currently Available ULDs by Airline")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No available ULDs to show statistics.")
                
        with col2:
            # Chart: Total Movement
            status_counts = df["ULD Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig2 = px.bar(status_counts, x="Status", y="Count", title="Total ULD Movement", color="Status")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough data to display statistics yet.")
        # ----------------- Footer (حقوق الملكية) -----------------
footer = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: transparent;
    color: #6c757d;
    text-align: center;
    padding: 10px;
    font-size: 14px;
    border-top: 1px solid #eaeaea;
}
</style>
<div class="footer">
    <p>Designed by <b>Ahmed Gad</b> ©</p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)

