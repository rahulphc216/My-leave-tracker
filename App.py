from datetime import datetime, date
import calendar
import pandas as pd
import sqlite3
import streamlit as st

# Patna High Court 2026 Comprehensive Gazetted Holidays List
OFFICIAL_GAZETTED_2026 = {
    "2026-01-14": "Makar Sankranti",
    "2026-01-26": "Republic Day",
    "2026-02-15": "Maha Shivaratri",
    "2026-03-03": "Holi / Dolapurnima",
    "2026-03-04": "Holi",
    "2026-03-31": "Id-ul-Fitr",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Babasaheb Ambedkar Birthday / Mahavir Jayanti",
    "2026-05-01": "May Day / Buddha Purnima",
    "2026-05-30": "Bakrid / Eid al-Adha",
    "2026-06-29": "Muharram",
    "2026-08-15": "Independence Day",
    "2026-08-28": "Chehlum",
    "2026-09-04": "Janmashtami",
    "2026-09-17": "Vishwakarma Puja",
    "2026-10-02": "Mahatma Gandhi Birthday",
    # Durga Puja & October Long Vacation 2026
    "2026-10-18": "Durga Puja (Saptami)",
    "2026-10-19": "Durga Puja (Ashtami)",
    "2026-10-20": "Durga Puja (Navami)",
    "2026-10-21": "Durga Puja (Dashami)",
    "2026-10-22": "Durga Puja Vacation",
    "2026-10-23": "Durga Puja Vacation",
    "2026-10-24": "Durga Puja Vacation",
    "2026-10-26": "Lakhshmi Puja",
    # Diwali & Chhath Puja Continuous Long Vacation (November 8 to November 17)
    "2026-11-08": "Diwali",
    "2026-11-09": "Govardhan Puja / Chitragupta Puja",
    "2026-11-10": "Chhath Puja",
    "2026-11-11": "Chhath Puja",
    "2026-11-12": "Vacation Holiday",
    "2026-11-13": "Vacation Holiday",
    "2026-11-14": "Vacation Holiday",
    "2026-11-15": "Vacation Holiday",
    "2026-11-16": "Vacation Holiday",
    "2026-11-17": "Vacation Holiday",
    # December Holidays
    "2026-12-12": "Gazetted Holiday",
    "2026-12-25": "Christmas Day",
    "2026-12-26": "Winter Vacation",
    "2026-12-27": "Winter Vacation",
    "2026-12-28": "Winter Vacation",
    "2026-12-29": "Winter Vacation",
    "2026-12-30": "Winter Vacation",
    "2026-12-31": "Winter Vacation",
}

OFFICIAL_HALFDAY_2026 = {
    "2026-08-04": "Half-Day Office",
    "2026-09-25": "Half-Day Office",
}


def init_db():
  conn = sqlite3.connect("my_personal_leaves_v33.db")
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

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date TEXT UNIQUE,
            occasion TEXT
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
  st.markdown("रोस्टर ड्यूटी, एडिट फीचर्स और स्मार्ट डैशबोर्ड")

  # --- 1. PROMINENT ATTENDANCE & ROSTER REGISTER ---
  with st.sidebar.expander(
      "🟢 🟢 अटेंडेंस और रोस्टर रजिस्टर (Attendance & Roster)", expanded=False
  ):
    st.markdown("### **उपस्थिति या रोस्टर ड्यूटी दर्ज करें**")
    today_date = date.today()
    att_selected_date = st.date_input(
        "तारीख चुनें (Select Date)", value=today_date, key="att_date_input"
    )

    is_sunday_selected = att_selected_date.weekday() == 6

    conn = sqlite3.connect("my_personal_leaves_v33.db")
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
      st.info("📌 यह रविवार (Sunday) है।")
      sunday_emergency = st.checkbox(
          "⚠️ Sunday Emergency / Roster Working (छुट्टी के दिन ऑफिस आए थे?)"
      )
      if sunday_emergency:
        attendance_status = "Office Present"
        remarks_input = st.text_input(
            "रोस्टर/इमरजेंसी वजह (Remarks):",
            value=current_remarks,
            key="sun_rem",
        )
      else:
        attendance_status = "Sunday Off"
        remarks_input = ""
    else:
      attendance_status = st.selectbox(
          "स्थिति चुनें (Status):",
          [
              "Office Present",
              "Half-Day Office",
              "Roster Duty (Holiday Working)",
              "Absent / Leave",
          ],
          index=0,
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
      if (
          attendance_status == "Office Present"
          or attendance_status == "Roster Duty (Holiday Working)"
      ):
        status_db = "Present"
      elif attendance_status == "Half-Day Office":
        status_db = "Half-Day"
      elif attendance_status == "Sunday Off":
        status_db = "Sunday Off"
      else:
        status_db = "Absent"

      conn = sqlite3.connect("my_personal_leaves_v33.db")
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
      st.success("✅ उपस्थिति/रोस्टर रिकॉर्ड सुरक्षित हो गया!")
      st.rerun()

  # --- 2. EDIT / DELETE ATTENDANCE REGISTER ---
  with st.sidebar.expander("✏️ पुरानी अटेंडेंस एडिट या सुधार करें"):
    conn = sqlite3.connect("my_personal_leaves_v33.db")
    att_df_all = pd.read_sql_query(
        "SELECT * FROM my_attendance ORDER BY att_date DESC", conn
    )
    conn.close()

    if not att_df_all.empty:
      selected_att_id = st.selectbox(
          "सुधार के लिए तारीख और रिकॉर्ड चुनें:",
          att_df_all["att_date"].tolist(),
      )
      row_to_edit = att_df_all[
          att_df_all["att_date"] == selected_att_id
      ].iloc[0]

      edit_status = st.selectbox(
          "नया Status चुनें:",
          ["Present", "Half-Day", "Absent", "Sunday Off"],
          index=(
              0
              if row_to_edit["status"] == "Present"
              else (
                  1
                  if row_to_edit["status"] == "Half-Day"
                  else (2 if row_to_edit["status"] == "Absent" else 3)
              )
          ),
      )
      edit_remarks = st.text_input(
          "Remarks update karein:", value=str(row_to_edit["remarks"])
      )

      col_e1, col_e2 = st.columns(2)
      with col_e1:
        if st.button("Update Karein"):
          conn = sqlite3.connect("my_personal_leaves_v33.db")
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE my_attendance SET status = ?, remarks = ? WHERE att_date"
              " = ?",
              (edit_status, edit_remarks, selected_att_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ Attendance update ho gayi!")
          st.rerun()
      with col_e2:
        if st.button("Record Hatayein"):
          conn = sqlite3.connect("my_personal_leaves_v33.db")
          cursor = conn.cursor()
          cursor.execute(
              "DELETE FROM my_attendance WHERE att_date = ?",
              (selected_att_id,),
          )
          conn.commit()
          conn.close()
          st.success("✅ Record hata diya gaya!")
          st.rerun()
    else:
      st.info("Abhi koi attendance record nahi hai.")

  # --- 3. ADVANCE / REGULAR LEAVE APPLY ---
  with st.sidebar.expander(
      "➕ एडवांस / नई छुट्टी जोड़ें (Apply / Advance Leave)", expanded=False
  ):
    conn = sqlite3.connect("my_personal_leaves_v33.db")
    df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
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

    with st.form("leave_form"):
      leave_category = st.selectbox(
          "छुट्टी का प्रकार", ["CL", "CPL", "EL", "RH", "Late Coming"]
      )
      leave_date = st.date_input(
          "छुट्टी की तारीख (वर्तमान या एडवांस तारीख चुनें)"
      )

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
          conn = sqlite3.connect("my_personal_leaves_v33.db")
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
          st.success("✅ एडवांस/नियमित छुट्टी दर्ज हो गई!")
          st.rerun()

  # --- 4. QUICK ADD MISSING HOLIDAY ---
  with st.sidebar.expander("📌 छूट गई छुट्टी यहाँ जोड़ें (Add Missing Holiday)"):
    missing_date = st.date_input(
        "छुट्टी की तारीख (Date)", value=today_date, key="miss_date"
    )
    missing_occasion = st.text_input(
        "अवसर/वजह (যেমন Gazetted Holiday)", value="Gazetted Holiday"
    )
    if st.button("छुट्टी सेव करें", use_container_width=True):
      conn = sqlite3.connect("my_personal_leaves_v33.db")
      cursor = conn.cursor()
      try:
        cursor.execute(
            """
                    INSERT OR REPLACE INTO custom_holidays (holiday_date, occasion)
                    VALUES (?, ?)
                """,
            (str(missing_date), missing_occasion),
        )
        conn.commit()
        st.success(f"✅ {missing_date} ko chhutti ke roop me jod diya gaya!")
      except Exception as e:
        st.error(f"Error: {e}")
      finally:
        conn.close()
      st.rerun()

  # --- 5. MANUAL CPL SETTINGS ---
  with st.sidebar.expander("⚙️ मैनुअल CPL कोटा सेटिंग्स"):
    conn = sqlite3.connect("my_personal_leaves_v33.db")
    c = conn.cursor()
    c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
    saved_cpl = c.fetchone()
    default_cpl = saved_cpl[0] if saved_cpl else 0
    conn.close()

    total_cpl_allocated = st.number_input(
        "कुल मान्य CPL (रोस्टर आदि जोड़कर)",
        min_value=0,
        max_value=50,
        value=default_cpl,
        step=1,
    )
    if st.button("CPL सेव करें"):
      conn = sqlite3.connect("my_personal_leaves_v33.db")
      cursor = conn.cursor()
      cursor.execute("DELETE FROM my_cpl_setting")
      cursor.execute(
          "INSERT INTO my_cpl_setting (total_cpl) VALUES (?)",
          (total_cpl_allocated,),
      )
      conn.commit()
      conn.close()
      st.success("✅ CPL update ho gaya!")
      st.rerun()

  # Refresh data for main view
  conn = sqlite3.connect("my_personal_leaves_v33.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  att_df = pd.read_sql_query("SELECT * FROM my_attendance", conn)
  custom_hol_df = pd.read_sql_query("SELECT * FROM custom_holidays", conn)
  c = conn.cursor()
  c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
  saved_cpl = c.fetchone()
  active_cpl_quota = saved_cpl[0] if saved_cpl else 0
  conn.close()

  custom_hol_dict = {}
  if not custom_hol_df.empty:
    for _, row in custom_hol_df.iterrows():
      custom_hol_dict[row["holiday_date"]] = row["occasion"]

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
        index=today_date.month - 1,
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
        <span style="color: #2e7d32; background: #e8f5e9; padding: 3px 6px; border-radius: 4px;">🟢 Present / Roster</span>
        <span style="color: #f57f17; background: #fffde7; padding: 3px 6px; border-radius: 4px;">🟡 Half-Day</span>
        <span style="color: #c62828; background: #ffebee; padding: 3px 6px; border-radius: 4px;">🔴 Leave</span>
        <span style="color: #1565c0; background: #e3f2fd; padding: 3px 6px; border-radius: 4px;">🔵 Sunday / Gazetted Off</span>
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
        is_gazetted = (
            selected_year == 2026 and d_str in OFFICIAL_GAZETTED_2026
        ) or (d_str in custom_hol_dict)
        is_halfday = selected_year == 2026 and d_str in OFFICIAL_HALFDAY_2026

        bg_color = "#ffffff"
        text_color = "#333333"
        border_color = "#ddd"
        tooltip = ""
        extra_badge = ""

        # Priority rules & Clear Roster Highlighting
        if status == "Present" or status == "Sunday Emergency":
          if is_sunday or is_gazetted:
            bg_color = "#c8e6c9"  # Stronger Green for Holiday Working/Roster
            text_color = "#1b5e20"
            border_color = "#2e7d32"
            extra_badge = (
                "<br><span style='font-size:10px; background:#2e7d32; color:white;"
                " padding:1px 3px; border-radius:3px;'>Roster</span>"
            )
          else:
            bg_color = "#e8f5e9"  # Normal Present Green
            text_color = "#2e7d32"
        elif d_str in leave_dates_set or "Leave" in status:
          bg_color = "#ffebee"  # Light Red
          text_color = "#c62828"
        elif is_sunday or is_gazetted:
          bg_color = "#e3f2fd"  # Light Blue (Off / Holiday)
          text_color = "#1565c0"
          if d_str in custom_hol_dict:
            tooltip = f" title='{custom_hol_dict[d_str]}'"
          elif is_gazetted:
            tooltip = f" title='{OFFICIAL_GAZETTED_2026[d_str]}'"
        elif is_halfday or status == "Half-Day":
          bg_color = "#fffde7"  # Light Yellow (Half-Day Office)
          text_color = "#f57f17"
          if is_halfday:
            tooltip = f" title='{OFFICIAL_HALFDAY_2026[d_str]}'"

        html_table += f"<td{tooltip} style='border: 2px solid {border_color}; padding: 8px 2px; background-color: {bg_color}; color: {text_color}; font-weight: bold; font-size: 15px;'>{day}{extra_badge}</td>"
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
        conn = sqlite3.connect("my_personal_leaves_v33.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {del_id} ka record hata diya gaya hai!")
        st.rerun()
  else:
    st.info("Abhi tak koi leave record darj nahi hai.")


if __name__ == "__main__":
  main()
