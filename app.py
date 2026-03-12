import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread
import time

# Page configuration
st.set_page_config(page_title="CACC - ULD Tracking System", layout="wide", page_icon="✈️")

# --- Google Sheets Connection ---
@st.cache_resource
def init_connection():
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
    return gc

try:
    gc = init_connection()
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
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""
        else:
            df = pd.DataFrame(columns=expected_columns)
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
        df = df.fillna("")
        sh.update(range_name='A1', values=[df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Error saving data: {e}")

df = load_data()

st.title("✈️ CACC - ULD Tracking System ")

# --- نظام إشعارات النجاح ---
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None

# القائمة المحدثة لأسماء الموظفين (Agents)
agent_list = sorted([
    "Islam salah", "Sherif Talal", "Ahmed Raouf", "Saleh Elsayed", "Mostafa Atta", 
    "Mohsen Metwaly", "Yousry Awad", "Ismail Elsayed", "Ahmed Melegy", "Mahmoud Ismail", 
    "Hussien Hefny", "Hatem Sayed", "Abdel Aleem Attia", "Osama Rizk", "Mohamed Ashraf", 
    "Farid Fawzy", "Islam Ali", "Ibrahim salah", "Karim Ahmed", "Samir Ahmed", 
    "Ahmed Said", "Islam karam", "Mohamed khalil", "Mohamed Abdel Razik", "Fahd Fathy", 
    "Ibrahim Bayoumy", "Mouhand Yousry", "Ahmed Ali", "Mostafa Azoz", "Mohamed Fatin", 
    "Mahmoud Gamal", "Mohamed khaled", "Ahmed Morgan", "Karim Helmy", "Mahmoud sabry", 
    "Mohamed Abu ElDahab", "Kirollos Tharwat", "Mostafa Mohsen", "Mostafa Abu zied", 
    "Mostafa Sief", "Omar Mostafa", "Omar Amgad", "Omar Khaled", "Mostafa Azazy", 
    "Hossam Abdel salam", "Ibrahim Mohamed", "Mostafa Mohmoud", "Ahmed salamah",
    "Ahmed Ragab", "Mohamed Fathy"
])

# Create Tabs (Added Tab 6 for Handover)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Check-In ULD", 
    "📤 Check-Out ULD", 
    "📊 Reports & Export", 
    "📈 Dashboard",
    "🕒 ULD History",
    "🖨️ Handover Sheet"
])

# ----------------- Tab 1: Check-In ULD -----------------
with tab1:
    st.subheader("Add New ULD to Station")
    
    col1, col2 = st.columns(2)
    with col1:
        uld_no = st.text_input("ULD No")
        airline = st.selectbox("Airline", ["RMX", "SVI", "BBT", "MNG", "SH","Avairy","National Air","MAS Air","Air Challenge"])
        flight_no = st.text_input("Arrival Flight No")
    
    with col2:
        Status = st.selectbox("Status", ["Serviceable", "Unserviceable"])
        employee_name = st.selectbox("Agent", agent_list)
        remarks = st.text_area("Remarks")
        
    if st.button("Save Data (Check-In) 💾"):
        if uld_no and flight_no and employee_name:
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
                
                st.session_state.success_msg = f"✅ ULD {uld_no} Checked-In successfully!"
                st.rerun()
        else:
            st.warning("⚠️ Please fill in mandatory fields.")


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
            checkout_emp = st.selectbox("Handing Over Employee Name", agent_list)
            checkout_remarks = st.text_area("Check-out Remarks (Optional)")
            
        if st.button("Check-Out 📤"):
            if checkout_flight and checkout_emp:
                idx = df[(df["ULD No"] == checkout_uld) & (df["ULD Status"].isin(["Serviceable", "Unserviceable"]))].index
                df.loc[idx, "ULD Status"] = "Checked Out"
                df.loc[idx, "Check-out Date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                old_remarks = str(df.loc[idx, "Remarks_out"].values[0])
                if old_remarks == "nan" or old_remarks == "": old_remarks = ""
                else: old_remarks += " | "
                new_note = f"{old_remarks}Checked out on flight {checkout_flight} by {checkout_emp}. {checkout_remarks}"
                df.loc[idx, "Remarks_out"] = new_note
                save_data(df)
                
                st.session_state.success_msg = f"✅ ULD {checkout_uld} Checked-Out successfully!"
                st.rerun()
            else:
                st.warning("⚠️ Please enter Departure Flight No and Employee Name.")
    else:
        st.info("💡 No ULDs currently available in the station.")

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
                label=f"📥 Export Report to CSV",
                data=csv,
                file_name=f'uld_reports.csv',
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
    search_uld = st.text_input("Enter ULD No to search:")
    if search_uld and not df.empty:
        uld_history = df[df["ULD No"].astype(str).str.contains(search_uld, case=False, na=False)]
        if not uld_history.empty:
            st.dataframe(uld_history, use_container_width=True)
        else:
            st.warning(f"⚠️ No history found for ULD: {search_uld}")

# ----------------- Tab 6: Handover Sheet (NEW) -----------------
with tab6:
    st.subheader("🖨️ Generate Handover Sheet")
    st.write("قم بتحديد اليوم وشركة الطيران لإنشاء نموذج التسليم مطابق للملف الورقي.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ho_date = st.date_input("Select Date", datetime.date.today())
    with col2:
        ho_airline = st.selectbox("Select Airline for Handover", ["All", "RMX", "SVI", "BBT", "MNG", "SH","Avairy","National Air","MAS Air","Air Challenge"])
    with col3:
        ho_type = st.selectbox("Movement Type", ["Check-In (Received)", "Check-Out (Delivered)"])

    if st.button("Generate Handover Sheet 📄"):
        if not df.empty:
            # فلترة البيانات بناءً على التاريخ ونوع الحركة
            date_str = ho_date.strftime("%Y-%m-%d")
            filtered_ho = df.copy()
            
            if ho_airline != "All":
                filtered_ho = filtered_ho[filtered_ho["Airline"] == ho_airline]
                
            if ho_type == "Check-In (Received)":
                filtered_ho = filtered_ho[filtered_ho["Date"].astype(str).str.startswith(date_str)]
                uld_list = filtered_ho[["ULD No", "Remarks_in"]].values.tolist()
            else:
                filtered_ho = filtered_ho[filtered_ho["Check-out Date"].astype(str).str.startswith(date_str)]
                uld_list = filtered_ho[["ULD No", "Remarks_out"]].values.tolist()
            
            if len(uld_list) == 0:
                st.warning("⚠️ No ULDs found for the selected criteria.")
            else:
                # تجهيز البيانات بحد أقصى 40 صف ليطابق النموذج
                ulds_data = [{"uld": item[0], "comment": item[1]} for item in uld_list]
                while len(ulds_data) < 40:
                    ulds_data.append({"uld": "", "comment": ""})
                ulds_data = ulds_data[:40] # في حال تجاوز ال 40 يتم اقتطاعه
                
                # بناء هيكل الـ HTML
                rows_html = ""
                for i in range(20):
                    sn1, uld1, com1 = i + 1, ulds_data[i]["uld"], ulds_data[i]["comment"]
                    sn2, uld2, com2 = i + 21, ulds_data[20+i]["uld"], ulds_data[20+i]["comment"]
                    
                    rows_html += f"""
                    <tr>
                        <td>{com2}</td>
                        <td class="bold-text">{uld2}</td>
                        <td>{sn2}</td>
                        <td>{com1}</td>
                        <td class="bold-text">{uld1}</td>
                        <td>{sn1}</td>
                    </tr>
                    """
                
                html_template = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>Handover Sheet</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; font-size: 11px; margin: 20px; }}
                        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ed1c24; padding-bottom: 10px; margin-bottom: 20px; }}
                        .logo {{ color: #ed1c24; font-size: 20px; font-weight: bold; display: flex; align-items: center; }}
                        .logo span {{ margin-left: 5px; color: black; font-size: 14px; font-weight: normal; }}
                        .title {{ color: #ed1c24; font-size: 16px; font-weight: bold; }}
                        .sub-info {{ display: flex; justify-content: space-between; margin-bottom: 5px; font-weight: bold; }}
                        .red-text {{ color: #ed1c24; font-size: 10px; margin-bottom: 15px; }}
                        .arabic-text {{ direction: rtl; text-align: right; margin-bottom: 5px; font-weight: bold; }}
                        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; text-align: center; }}
                        th, td {{ border: 1px solid black; padding: 6px; }}
                        th {{ background-color: #f9f9f9; font-size: 10px; }}
                        .bold-text {{ font-weight: bold; }}
                        .signatures {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                        .signatures th, .signatures td {{ border: 1px solid black; padding: 10px; text-align: left; height: 30px; }}
                        .signatures th {{ text-align: center; background-color: #f9f9f9; }}
                        .text-right {{ text-align: right; }}
                        @media print {{
                            @page {{ size: A4 portrait; margin: 10mm; }}
                            body {{ margin: 0; }}
                            .no-print {{ display: none; }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="logo">CACC <span>CARGOLINX</span></div>
                        <div class="title">Empty ULDs Handover Sheet</div>
                    </div>
                    
                    <div class="sub-info">
                        <div>We hereby declare that we received below</div>
                        <div style="font-size: 14px;">ULD {ho_airline if ho_airline != 'All' else ''}</div>
                        <div>{date_str}</div>
                    </div>
                    
                    <div class="red-text">*In case of any deviation, please insert comments in below table</div>
                    
                    <div class="arabic-text">
                        تم استلام المعدات المذكورة ادناه ULD {ho_airline if ho_airline != 'All' else ''} {date_str} وهي في حالة ظاهرية سليمة.
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Comment<br><span dir="rtl">ملاحظات ان وجدت</span></th>
                                <th>ULD ID<br><span dir="rtl">أرقام المعدات</span></th>
                                <th>SN<br><span dir="rtl">م</span></th>
                                <th>Comment<br><span dir="rtl">ملاحظات ان وجدت</span></th>
                                <th>ULD ID<br><span dir="rtl">أرقام المعدات</span></th>
                                <th>SN<br><span dir="rtl">م</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                    
                    <table class="signatures">
                        <thead>
                            <tr>
                                <th></th>
                                <th>Ramp Handler Rep</th>
                                <th>CACC Operation</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="text-right">Name -- الاسم</td>
                                <td></td>
                                <td></td>
                            </tr>
                            <tr>
                                <td class="text-right">Signature -- التوقيع</td>
                                <td></td>
                                <td></td>
                            </tr>
                            <tr>
                                <td class="text-right">Permit no. -- تصريح رقم</td>
                                <td></td>
                                <td></td>
                            </tr>
                            <tr>
                                <td class="text-right">Date / Time of handover 1st ULD --<br>وقت تسليم اول معدة // التاريخ</td>
                                <td style="text-align: center;">{date_str}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td class="text-right">Date / Time of handover last ULD --<br>وقت تسليم اخر معدة // التاريخ</td>
                                <td style="text-align: center;">{date_str}</td>
                                <td></td>
                            </tr>
                        </tbody>
                    </table>
                    <div style="text-align: right; font-size: 9px; margin-top: 10px;">CL/CSA/EUHS-V1.0/AUG23</div>
                </body>
                </html>
                """
                
                st.success("✅ Sheet generated successfully! Click below to download.")
                st.download_button(
                    label="📥 Download Handover Sheet (HTML)",
                    data=html_template.encode('utf-8'),
                    file_name=f"Handover_Sheet_{ho_airline}_{date_str}.html",
                    mime="text/html"
                )
                st.info("💡 **نصيحة للطباعة:** قم بفتح الملف المحمل في متصفحك (مثل Chrome) واضغط على `Ctrl + P` لطباعته أو حفظه بصيغة PDF. التصميم معد ليناسب مقاس ورقة A4 مباشرةً.")
        else:
            st.error("No data available in the database.")

# ----------------- Footer -----------------
footer = """<div style="position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; color: #6c757d; padding: 10px; border-top: 1px solid #eaeaea; background-color: white; z-index: 100;">Designed by <b>Ahmed Ragab</b> ©</div>"""
st.markdown(footer, unsafe_allow_html=True)
