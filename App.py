from datetime import datetime, date
import calendar
import pandas as pd
import sqlite3
import streamlit as st

# Patna High Court Official Restricted Holidays (RH) List
OFFICIAL_RH = {
    2026: {
        "Jan 16 - Guru Gobind Singh Ji's Birthday": "2026-01-16",
        "Jan 26 - Shab-e-Barat": "2026-01-26",
        "Feb 15 - Maha Shivaratri": "2026-02-15",
        "Mar 04 - Holika Dahan": "2026-03-04",
        "Apr 03 - Good Friday": "2026-04-03",
        "Apr 14 - Mahavir Jayanti": "2026-04-14",
        "May 15 - Buddha Purnima": "2026-05-15",
        "Aug 28 - Muharram": "2026-08-28",
        "Oct 20 - Karwa Chauth": "2026-10-20",
    },
    2027: {"Jan 15 - Example 2027 RH": "2027-01-15"},
}


def init_db():
  conn = sqlite3.connect("my_personal_leaves_v19.db")
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leave_type TEXT,
            leave_date TEXT,
            days_count INTEGER,
            reason TEXT,
            timestamp TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            att_date TEXT UNIQUE,
            status TEXT,
            remarks TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_cpl_setting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_cpl INTEGER
        )
    """)

  conn.commit()
  conn.close()


def main():
  init_db()
  st.set_page_config(
      page_title="Leave & Attendance Tracker", page_icon="📅", layout="wide"
  )

  st.title("🏛️ मेरा लीव और अटेंडेंस ट्रैकर (Patna High Court Rules)")
  st.markdown("दैनिक उपस्थिति और स्मार्ट कलर-कोडेड डैशबोर्ड")

  # --- 1. PROMINENT & LARGE ATTENDANCE REGISTER (Sidebar Top) ---
  with st.sidebar.expander(
      "🟢 🟢 अटेंडेंस रजिस्टर (Daily Attendance)", expanded=False
  ):
    st.markdown("### **रोज़ की उपस्थिति दर्ज करें**")
    today_date = date.today()
    att_selected_date = st.date_input(
        "तारीख चुनें (Select Date)", value=today_date, key="att_date_input"
    )

    is_sunday_selected = att_selected_date.weekday() == 6

    conn = sqlite3.connect("my_personal_leaves_v19.db")
    c = conn.cursor()
    c.execute(
        "SELECT status, remarks FROM my_attendance WHERE att_date = ?",
        (str(att_selected_date),),
    )
    existing_att = c.fetchone()
    conn.close()

    current_status_val = existing_att[0] if existing_att else "Present"
    current_remarks = (
        existing_att[1] if existing_att and len(existing_att) > 1 else ""
    )

    if is_sunday_selected:
      st.info("📌 यह रविवार (Sunday) है। सामान्यतः इस दिन अवकाश रहता है।")
      sunday_emergency = st.checkbox(
          "⚠️ Sunday Emergency Working (विशेष स्थिति में ऑफिस आए थे?)"
      )
      if sunday_emergency:
        attendance_status = "Office Present"
        remarks_input = st.text_input(
            "इमरजेंसी की वजह (Remarks):",
            value=current_remarks,
            key="sun_rem",
        )
      else:
        attendance_status = "Sunday Off"
        remarks_input = ""
    else:
      attendance_status = st.selectbox(
          "स्थिति चुनें (Status):",
          ["Office Present", "Half-Day Office", "Absent / Leave"],
          index=(
              0
              if current_status_val == "Present"
              else (1 if current_status_val == "Half-Day" else 2)
          ),
          key="att_status_box",
      )
      remarks_input = st.text_area(
          "टिप्पणी / Remarks (Optional):",
          value=current_remarks,
          key="normal_rem",
      )

    if st.button(
        "💾 उपस्थिति सुरक्षित करें (Save Attendance)", use_container_width=True
    ):
      if attendance_status == "Office Present":
        status_db = "Present"
      elif attendance_status == "Half-Day Office":
        status_db = "Half-Day"
      elif attendance_status == "Sunday Off":
        status_db = "Sunday Off"
      else:
        status_db = "Absent"

      conn = sqlite3.connect("my_personal_leaves_v19.db")
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT OR REPLACE INTO my_attendance (att_date, status, remarks)
                VALUES (?, ?, ?)
            """,
          (str(att_selected_date), status_db, remarks_input),
      )
      conn.commit()
      conn.close()
      st.success("✅ उपस्थिति सफलतापूर्वक दर्ज हो गई!")
      st.rerun()

  # --- 2. Other Small Expander Settings (Hidden below) ---
  with st.sidebar.expander("➕ नई छुट्टी जोड़ें (Apply Leave)", expanded=False):
    conn = sqlite3.connect("my_personal_leaves_v19.db")
    df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
    c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
    saved_cpl = c.fetchone()
    active_cpl_quota = saved_cpl[0] if saved_cpl else 0
    conn.close()

    cl_taken = (
        df[df["leave_type"] == "CL"]["days_count"].sum() if not df.empty else 0
    )
    cpl_taken = (
        df[df["leave_type"] == "CPL"]["days_count"].sum() if not df.empty else 0
    )
    el_taken = (
        df[df["leave_type"] == "EL"]["days_count"].sum() if not df.empty else 0
    )
    rh_df = df[df["leave_type"] == "RH"] if not df.empty else pd.DataFrame()
    rh_taken = rh_df["days_count"].sum() if not rh_df.empty else 0
    already_taken_rh_dates = (
        rh_df["leave_date"].tolist() if not rh_df.empty else []
    )

    cl_remaining = 16 - cl_taken
    cpl_remaining = active_cpl_quota - cpl_taken
    rh_remaining = 2 - rh_taken

    target_year = date.today().year
    year_rh_dict = OFFICIAL_RH.get(target_year, OFFICIAL_RH[2026])

    available_rh_options = {}
    for rh_name, rh_date_str in year_rh_dict.items():
      rh_dt = datetime.strptime(rh_date_str, "%Y-%m-%d").date()
      if rh_dt >= date.today() and rh_date_str not in already_taken_rh_dates:
        available_rh_options[rh_name] = rh_date_str

    with st.form("leave_form"):
      leave_category = st.selectbox(
          "छुट्टी का प्रकार", ["CL", "CPL", "EL", "RH", "Late Coming"]
      )

      if leave_category == "RH":
        if rh_remaining <= 0:
          st.warning("⚠️ दोनों RH पूरी हो चुकी हैं!")
          selected_rh_key = None
          leave_date = date.today()
        elif not available_rh_options:
          st.info("इस साल के लिए कोई और RH उपलब्ध नहीं है।")
          selected_rh_key = None
          leave_date = date.today()
        else:
          selected_rh_key = st.selectbox(
              "वैध RH चुनें:", list(available_rh_options.keys())
          )
          leave_date = (
              datetime.strptime(
                  year_rh_dict[selected_rh_key], "%Y-%m-%d"
              ).date()
              if selected_rh_key
              else date.today()
          )
      else:
        leave_date = st.date_input("छुट्टी की तारीख")

      if leave_category == "RH":
        days_count = 1
      else:
        days_count = st.number_input(
            "दिनों की संख्या", min_value=1, max_value=30, value=1, step=1
        )

      reason = st.text_area("वजह / टिप्पणी (Reason)")
      submit = st.form_submit_button("रिकॉर्ड सेव करें")

      if submit:
        error_msg = None
        if leave_category == "CL" and days_count > cl_remaining:
          error_msg = f"❌ त्रुटि: केवल {cl_remaining} CL बची है!"
        elif leave_category == "CPL" and days_count > cpl_remaining:
          error_msg = f"❌ त्रुटि: केवल {cpl_remaining} CPL बची है!"
        elif leave_category == "RH" and rh_remaining <= 0:
          error_msg = "❌ त्रुटि: अधिकतम 2 ही RH ले सकते हैं!"

        if error_msg:
          st.error(error_msg)
        else:
          conn = sqlite3.connect("my_personal_leaves_v19.db")
          cursor = conn.cursor()
          cursor.execute(
              """
                      INSERT INTO my_leaves (leave_type, leave_date, days_count, reason, timestamp)
                      VALUES (?, ?, ?, ?, ?)
                  """,
              (
                  leave_category,
                  str(leave_date),
                  days_count,
                  reason,
                  str(datetime.now().strftime("%Y-%m-%d %H:%M")),
              ),
          )
          cursor.execute(
              """
                      INSERT OR REPLACE INTO my_attendance (att_date, status, remarks)
                      VALUES (?, ?, ?)
                  """,
              (str(leave_date), f"Leave ({leave_category})", reason),
          )
          conn.commit()
          conn.close()
          st.success("✅ छुट्टी दर्ज हो गई और कैलेंडर अपडेट हो गया!")
          st.rerun()

  with st.sidebar.expander("⚙️ CPL कोटा सेटिंग्स"):
    conn = sqlite3.connect("my_personal_leaves_v19.db")
    c = conn.cursor()
    c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
    saved_cpl = c.fetchone()
    default_cpl = saved_cpl[0] if saved_cpl else 0
    conn.close()

    total_cpl_allocated = st.number_input(
        "कुल मान्य CPL", min_value=0, max_value=50, value=default_cpl, step=1
    )
    if st.button("CPL सेव करें"):
      conn = sqlite3.connect("my_personal_leaves_v19.db")
      cursor = conn.cursor()
      cursor.execute("DELETE FROM my_cpl_setting")
      cursor.execute(
          "INSERT INTO my_cpl_setting (total_cpl) VALUES (?)",
          (total_cpl_allocated,),
      )
      conn.commit()
      conn.close()
      st.success("✅ CPL सेव हो गया!")
      st.rerun()

  with st.sidebar.expander("📤 कैलेंडर / RH अपलोड (2027+)"):
    st.file_uploader("कैलेंडर इमेज/PDF अपलोड करें", type=["png", "jpg", "pdf"])

  # Refresh data for main view
  conn = sqlite3.connect("my_personal_leaves_v19.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  att_df = pd.read_sql_query("SELECT * FROM my_attendance", conn)
  c = conn.cursor()
  c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
  saved_cpl = c.fetchone()
  active_cpl_quota = saved_cpl[0] if saved_cpl else 0
  conn.close()

  cl_taken = (
      df[df["leave_type"] == "CL"]["days_count"].sum() if not df.empty else 0
  )
  cpl_taken = (
      df[df["leave_type"] == "CPL"]["days_count"].sum() if not df.empty else 0
  )
  el_taken = (
      df[df["leave_type"] == "EL"]["days_count"].sum() if not df.empty else 0
  )
  rh_df = df[df["leave_type"] == "RH"] if not df.empty else pd.DataFrame()
  rh_taken = rh_df["days_count"].sum() if not rh_df.empty else 0

  cl_remaining = 16 - cl_taken
  cpl_remaining = active_cpl_quota - cpl_taken
  rh_remaining = 2 - rh_taken
  el_balance = 33 - el_taken

  # --- Home Page Live Balance ---
  st.markdown("### 🟢 आपका वर्तमान लीव बैलेंस")
  bal_col1, bal_col2, bal_col3, bal_col4 = st.columns(4)
  with bal_col1:
    st.success(f"**CL बची हुई:** {cl_remaining} दिन")
  with bal_col2:
    st.info(f"**CPL बची हुई:** {cpl_remaining} दिन")
  with bal_col3:
    st.warning(f"**EL बैलेंस:** {el_balance} दिन")
  with bal_col4:
    st.error(f"**RH बची हुई:** {rh_remaining} दिन")

  st.markdown("---")

  # --- Advanced HTML Color-Coded Calendar View ---
  st.subheader("📅 कैलेंडर व्यू")

  c_col1, c_col2 = st.columns(2)
  with c_col1:
    selected_year = st.selectbox("वर्ष चुनें", [2026, 2027], index=0)
  with c_col2:
    selected_month = st.selectbox(
        "महीना चुनें",
        list(range(1, 13)),
        format_func=lambda x: calendar.month_name[x],
        index=date.today().month - 1,
    )

  att_dict = {}
  if not att_df.empty:
    for _, row in att_df.iterrows():
      att_dict[row["att_date"]] = row["status"]

  leave_dates_set = set()
  if not df.empty:
    for _, row in df.iterrows():
      leave_dates_set.add(row["leave_date"])

  # Color Legend Display
  st.markdown(
      """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; font-size: 13px; font-weight: bold;">
        <span style="color: #2e7d32; background: #e8f5e9; padding: 3px 6px; border-radius: 4px;">🟢 Present</span>
        <span style="color: #f57f17; background: #fffde7; padding: 3px 6px; border-radius: 4px;">🟡 Half-Day</span>
        <span style="color: #c62828; background: #ffebee; padding: 3px 6px; border-radius: 4px;">🔴 Leave</span>
        <span style="color: #1565c0; background: #e3f2fd; padding: 3px 6px; border-radius: 4px;">🔵 Sunday</span>
        <span style="color: #616161; background: #f5f5f5; padding: 3px 6px; border-radius: 4px;">⚪ Normal</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

  cal_matrix = calendar.monthcalendar(selected_year, selected_month)
  days_header = [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
      "Sunday",
  ]

  html_table = (
      "<table style='width:100%; border-collapse: collapse; text-align: center;"
      " font-family: sans-serif; font-size: 14px;'>"
  )
  html_table += "<tr>"
  for dh in days_header:
    html_table += f"<th style='border: 1px solid #ddd; padding: 8px 4px; background-color: #f8f9fa; color: #333; font-size: 12px;'>{dh}</th>"
  html_table += "</tr>"

  for week in cal_matrix:
    html_table += "<tr>"
    for i, day in enumerate(week):
      if day == 0:
        html_table += (
            "<td style='border: 1px solid #ddd; padding: 10px;"
            " background-color: #fafafa;'></td>"
        )
      else:
        d_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
        status = att_dict.get(d_str, "")
        is_sunday = i == 6

        bg_color = "#ffffff"
        text_color = "#333333"
        border_color = "#ddd"

        if d_str in leave_dates_set or "Leave" in status:
          bg_color = "#ffebee"  # Light Red
          text_color = "#c62828"
        elif is_sunday and status != "Present":
          bg_color = "#e3f2fd"  # Light Blue
          text_color = "#1565c0"
        elif status == "Present" or status == "Sunday Emergency":
          bg_color = "#e8f5e9"  # Light Green
          text_color = "#2e7d32"
        elif status == "Half-Day":
          bg_color = "#fffde7"  # Light Yellow
          text_color = "#f57f17"

        html_table += f"<td style='border: 1px solid {border_color}; padding: 10px 4px; background-color: {bg_color}; color: {text_color}; font-weight: bold; font-size: 15px;'>{day}</td>"
    html_table += "</tr>"
  html_table += "</table>"

  st.markdown(html_table, unsafe_allow_html=True)

  # --- History & Delete ---
  st.markdown("---")
  st.subheader("📋 सभी लीव रिकॉर्ड्स (History)")
  if not df.empty:
    st.dataframe(df, use_container_width=True)

    del_id = st.number_input(
        "हटाने के लिए रिकॉर्ड ID दर्ज करें", min_value=0, step=1
    )
    if st.button("चयनित रिकॉर्ड हटाएं"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v19.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {del_id} का रिकॉर्ड हटा दिया गया है!")
        st.rerun()
  else:
    st.info("अभी तक कोई लीव रिकॉर्ड दर्ज नहीं है।")


if __name__ == "__main__":
  main()
