import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread

# Page configuration
st.set_page_config(page_title="CACC - ULD Tracking System", layout="wide", page_icon="✈️")

# --- Google Sheets Connection ---
@st.cache_resource
def init_connection():
    # استدعاء المفاتيح السرية من إعدادات Streamlit
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
    return gc

try:
    gc = init_connection()
    # اسم ملف جدول جوجل (تأكد أنك سميته بنفس هذا الاسم في Google Sheets)
    SHEET_NAME = "ULD_Database"
except Exception as e:
    st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من إعدادات Streamlit Secrets.")
    st.stop()

# Function to load data from Google Sheets
def load_data():
    try:
        sh = gc.open(SHEET_NAME).sheet1
        records = sh.get_all_records()
        expected_columns = [
            "Date", "ULD No", "Airline", "Flight No", 
            "Employee Name", "Remarks_in", "ULD Status", "Check-out Date", "Remarks_out"
        ]
        
        if records:
            df = pd.DataFrame(records)
            # Ensure all columns exist
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""
        else:
            df = pd.DataFrame(columns=expected_columns)
            # تحديث الجدول بالأعمدة إذا كان فارغاً
            sh.update(range_name='A1', values=[df.columns.values.tolist()])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Function to save data to Google Sheets
def save_data(df):
    try:
        sh = gc.open(SHEET_NAME).sheet1
        sh.clear()
        # ملء الفراغات (NaN) بنصوص فارغة لتجنب أخطاء الرفع
        df = df.fillna("")
        # تحويل البيانات إلى قائمة ورفعها لجدول جوجل
        sh.update(range_name='A1', values=[df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Error saving data: {e}")

df = load_data()

st.title("✈️ CACC - ULD Tracking System ")

# Create Tabs 
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Check-In ULD", 
    "📤 Check-Out ULD", 
    "📊 Reports & Export", 
    "📈 Dashboard",
    "🕒 ULD History"
])

# ----------------- Tab 1: Check-In ULD -----------------
with tab1:
    st.subheader("Add New ULD to Station")
    
    col1, col2 = st.columns(2)
    with col1:
        uld_no = st.text_input("ULD No")
        airline = st.selectbox("Airline", ["RMX", "SVI", "BBT", "MNG", "SH","Avairy", "Air Challenge"])
        flight_no = st.text_input("Arrival Flight No")
    
    with col2:
        Status = st.selectbox("Status", ["Serviceable", "Unserviceable"])
        employee_name = st.selectbox("Agent", ["Ahmed Ragab", "Mohamed Fathy","ULD Control","Dispatch Team","Ramp Team"])
        remarks = st.text_area("Remarks")
        
    if st.button("Save Data (Check-In) 💾"):
        if uld_no and flight_no and employee_name:
            # التأكد من أن المعدة ليست موجودة بالفعل في المحطة
            in_station_check = df[(df["ULD No"] == uld_no) & (df["ULD Status"].isin(["Serviceable", "Unserviceable"]))]
            
            if not in_station_check.empty:
                st.warning("⚠️ This ULD is already registered in the station!")
            else:
                new_row = pd.DataFrame({
                    "Date": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "ULD No": [uld_no],
                    "Airline": [airline],
                    "Flight No": [flight_no],
                    "Employee Name": [employee_name],
                    "Remarks_in": [remarks],
                    "ULD Status": [Status], 
                    "Check-out Date": [""],
                    "Remarks_out": [""] 
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("✅ ULD checked in successfully! Saved to Google Sheets.")
                st.rerun()
        else:
            st.warning("⚠️ Please fill in mandatory fields (ULD No, Flight No, Employee Name).")

# ----------------- Tab 2: Check-Out ULD -----------------
with tab2:
    st.subheader("Check-Out ULD")
    
    if not df.empty and "ULD Status" in df.columns:
        available_ulds = df[df["ULD Status"].isin(["Serviceable", "Unserviceable"])]
    else:
        available_ulds = pd.DataFrame()
    
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
                idx = df[(df["ULD No"] == checkout_uld) & (df["ULD Status"].isin(["Serviceable", "Unserviceable"]))].index
                
                df.loc[idx, "ULD Status"] = "Checked Out"
                df.loc[idx, "Check-out Date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                
                old_remarks = str(df.loc[idx, "Remarks_out"].values[0])
                if old_remarks == "nan" or old_remarks == "": 
                    old_remarks = ""
                else:
                    old_remarks += " | "
                    
                new_note = f"{old_remarks}Checked out on flight {checkout_flight} by {checkout_emp}. {checkout_remarks}"
                df.loc[idx, "Remarks_out"] = new_note
                
                save_data(df)
                st.success(f"✅ ULD {checkout_uld} checked out successfully!")
                st.rerun()
            else:
                st.warning("⚠️ Please enter Departure Flight No and Employee Name.")
    else:
        st.info("💡 No ULDs currently available in the station to check out.")

# ----------------- Tab 3: Reports & Export -----------------
with tab3:
    st.subheader("ULD Movement Report")
    
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            airlines = ["All"] + list(df["Airline"].dropna().unique())
            selected_airline = st.selectbox("🔍 Filter by Airline", airlines)
        with col2:
            status_filter = st.radio("🔍 Filter by Status", ["All","Serviceable", "Unserviceable", "Checked Out"], horizontal=True)
        
        filtered_df = df.copy()
        if selected_airline != "All":
            filtered_df = filtered_df[filtered_df["Airline"] == selected_airline]
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["ULD Status"] == status_filter]
            
        st.dataframe(filtered_df, use_container_width=True)
        
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
    else:
        st.info("No data available yet.")

# ----------------- Tab 4: Dashboard -----------------
with tab4:
    st.subheader("ULD Statistics")
    
    if not df.empty and "ULD Status" in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # تم التعديل لتشمل الحالات المتاحة (Serviceable/Unserviceable)
            available_df = df[df["ULD Status"].isin(["Serviceable", "Unserviceable"])]
            if not available_df.empty:
                airline_counts = available_df["Airline"].value_counts().reset_index()
                airline_counts.columns = ["Airline", "Count"]
                fig1 = px.pie(airline_counts, names="Airline", values="Count", title="Currently Available ULDs by Airline")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No available ULDs to show statistics.")
                
        with col2:
            status_counts = df["ULD Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig2 = px.bar(status_counts, x="Status", y="Count", title="Total ULD Movement", color="Status")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough data to display statistics yet.")

# ----------------- Tab 5: ULD History -----------------
with tab5:
    st.subheader("🔍 ULD Full History")
    st.write("ابحث عن رقم المعدة لمعرفة كل حركاتها منذ تسجيلها.")
    
    search_uld = st.text_input("Enter ULD No to search:")
    
    if search_uld and not df.empty:
        uld_history = df[df["ULD No"].astype(str).str.contains(search_uld, case=False, na=False)]
        
        if not uld_history.empty:
            st.success(f"✅ Found {len(uld_history)} record(s) for ULD: **{search_uld.upper()}**")
            
            st.dataframe(uld_history, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📅 Timeline / السجل الزمني")
            
            for index, row in uld_history.iterrows():
                # تم التعديل لتتوافق الأيقونات مع حالة المعدة الحالية
                status_icon = "🟢" if row['ULD Status'] in ["Serviceable", "Unserviceable"] else "🔴"
                
                with st.expander(f"{status_icon} Date In: {row['Date']} | Status: {row['ULD Status']}"):
                    st.write(f"**Airline:** {row['Airline']}")
                    st.write(f"**Arrival Flight No:** {row['Flight No']}")
                    st.write(f"**Handled By (In):** {row['Employee Name']}")
                    st.write(f"**Check-In Remarks:** {row['Remarks_in']}")
                    
                    if pd.notna(row['Check-out Date']) and str(row['Check-out Date']).strip() != "":
                        st.markdown("---")
                        st.write(f"**Check-Out Date:** {row['Check-out Date']}")
                        st.write(f"**Check-Out Details:** {row['Remarks_out']}")
        else:
            st.warning(f"⚠️ No history found for ULD: {search_uld}")

# ----------------- Footer -----------------
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



