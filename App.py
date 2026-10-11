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
  conn = sqlite3.connect("my_personal_leaves_v41.db")
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
  st.markdown("इंटरैक्टिव क्लिकेबल कैलेंडर, सारांश और अटेंडेंस रजिस्टर")

  today_date = date.today()
  today_str = str(today_date)
  is_today_sunday = today_date.weekday() == 6

  conn_h = sqlite3.connect("my_personal_leaves_v41.db")
  ch = conn_h.cursor()
  ch.execute(
      "SELECT occasion FROM custom_holidays WHERE holiday_date = ?",
      (today_str,),
  )
  cust_today = ch.fetchone()
  conn_h.close()

  is_today_gazetted = (
      today_date.year == 2026 and today_str in OFFICIAL_GAZETTED_2026
  ) or (cust_today is not None)

  # --- HOLIDAY NOTIFICATION BANNER ---
  if is_today_sunday:
    st.info(
        f"🎉 **आज रविवार (Sunday) है — ऑफिस बंद है!** (Date: {today_date})"
    )
  elif is_today_gazetted:
    occ_name = (
        cust_today[0]
        if cust_today
        else OFFICIAL_GAZETTED_2026.get(today_str, "Gazetted Holiday")
    )
    st.info(
        f"🎉 **आज सार्वजनिक अवकाश है!** अवसर: **{occ_name}** (Date:"
        f" {today_date})"
    )

  # --- 1. PROMINENT ATTENDANCE & ROSTER REGISTER ---
  with st.sidebar.expander(
      "🟢 🟢 अटेंडेंस और रोस्टर रजिस्टर (Attendance & Roster)", expanded=False
  ):
    st.markdown("### **उपस्थिति या रोस्टर ड्यूटी दर्ज करें**")
    att_selected_date = st.date_input(
        "तारीख चुनें (Select Date)", value=today_date, key="att_date_input"
    )

    d_str_sel = str(att_selected_date)
    is_sunday_selected = att_selected_date.weekday() == 6

    conn_val = sqlite3.connect("my_personal_leaves_v41.db")
    c_val = conn_val.cursor()
    c_val.execute(
        "SELECT leave_type, reason FROM my_leaves WHERE leave_date = ?",
        (d_str_sel,),
    )
    leave_check = c_val.fetchone()

    c_val.execute(
        "SELECT occasion FROM custom_holidays WHERE holiday_date = ?",
        (d_str_sel,),
    )
    cust_hol_check = c_val.fetchone()

    c_val.execute(
        "SELECT status, remarks FROM my_attendance WHERE att_date = ?",
        (d_str_sel,),
    )
    existing_att = c_val.fetchone()
    conn_val.close()

    is_gaz_sel = (
        att_selected_date.year == 2026 and d_str_sel in OFFICIAL_GAZETTED_2026
    ) or (cust_hol_check is not None)

    if leave_check:
      st.error(
          f"⚠️ **Alert:** Is tareekh par pehle se **Leave ({leave_check[0]})**"
          f" darj hai!"
      )
    elif is_sunday_selected:
      st.warning("📌 **Info:** Yeh din **Sunday (Off)** hai.")
    elif is_gaz_sel:
      occ_lbl = (
          cust_hol_check[0]
          if cust_hol_check
          else OFFICIAL_GAZETTED_2026.get(d_str_sel, "Gazetted Holiday")
      )
      st.warning(f"📌 **Info:** Yeh din **Gazetted Holiday ({occ_lbl})** hai.")

    current_remarks = (
        existing_att[1] if existing_att and len(existing_att) > 1 else ""
    )

    if is_sunday_selected:
      sunday_emergency = st.checkbox(
          "⚠️ Sunday Emergency / Roster Working (छुट्टी के दिन ऑफिस आए थे?)"
      )
      if sunday_emergency:
        attendance_status = "Office Present"
        remarks_input = st.text_input(
            "रोस्टर वजह (Remarks - Mandatory):",
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
          "टिप्पणी / Remarks (Optional / Mandatory for Holidays):",
          value=current_remarks,
          key="normal_rem",
      )

    if st.button(
        "💾 उपस्थिति सुरक्षित करें (Save Attendance)", use_container_width=True
    ):
      if leave_check:
        st.error(
            f"❌ Error: Is tareekh par Leave ({leave_check[0]}) hai, attendance"
            " save nahi ho sakti!"
        )
      elif (is_sunday_selected or is_gaz_sel) and attendance_status in [
          "Office Present",
          "Roster Duty (Holiday Working)",
      ] and not remarks_input.strip():
        st.error(
            "❌ Error: Chhutti ke din office aane par remarks likhna anivarya"
            " hai!"
        )
      else:
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

        conn = sqlite3.connect("my_personal_leaves_v41.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT OR REPLACE INTO my_attendance (att_date, status, remarks)
                    VALUES (?, ?, ?)
                """,
            (d_str_sel, status_db, remarks_input),
        )
        conn.commit()
        conn.close()
        st.success("✅ Attendance successfully save ho gayi!")
        st.rerun()

  # --- 2. EDIT / DELETE ATTENDANCE REGISTER ---
  with st.sidebar.expander("✏️ पुरानी अटेंडेंस एडिट या सुधार करें"):
    conn = sqlite3.connect("my_personal_leaves_v41.db")
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
          conn = sqlite3.connect("my_personal_leaves_v41.db")
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
          conn = sqlite3.connect("my_personal_leaves_v41.db")
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
    conn = sqlite3.connect("my_personal_leaves_v41.db")
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
          error_msg = f"❌ त्रुटि: अधिकतम 2 ही RH ले सकते हैं!"

        if error_msg:
          st.error(error_msg)
        else:
          conn = sqlite3.connect("my_personal_leaves_v41.db")
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
          st.success("✅ छुट्टी दर्ज हो गई और अटेंडेंस में स्वतः अपडेट हो गई!")
          st.rerun()

  # --- 4. QUICK ADD MISSING HOLIDAY ---
  with st.sidebar.expander("📌 छूट गई छुट्टी यहाँ जोड़ें (Add Missing Holiday)"):
    missing_date = st.date_input(
        "छुट्टी की तारीख (Date)", value=today_date, key="miss_date"
    )
    missing_occasion = st.text_input(
        "अवसर/वजह (जैसे Gazetted Holiday)", value="Gazetted Holiday"
    )
    if st.button("छुट्टी सेव करें", use_container_width=True):
      conn = sqlite3.connect("my_personal_leaves_v41.db")
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
    conn = sqlite3.connect("my_personal_leaves_v41.db")
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
      conn = sqlite3.connect("my_personal_leaves_v41.db")
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
  conn = sqlite3.connect("my_personal_leaves_v41.db")
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

  # --- MONTHLY & YEARLY SUMMARY ANALYTICS ---
  st.subheader("📊 मासिक और वार्षिक सारांश (Attendance Summary Analytics)")
  sum_col1, sum_col2 = st.columns(2)
  with sum_col1:
    sum_year = st.selectbox(
        "Summary Year:", [2026, 2027], index=0, key="sum_yr"
    )
  with sum_col2:
    sum_month = st.selectbox(
        "Summary Month:",
        list(range(1, 13)),
        format_func=lambda x: calendar.month_name[x],
        index=today_date.month - 1,
        key="sum_mo",
    )

  days_in_mo = calendar.monthrange(sum_year, sum_month)[1]
  mo_working_days = 0
  mo_regular_present = 0
  mo_roster_working = 0
  mo_leaves_count = 0

  for d_num in range(1, days_in_mo + 1):
    dt_obj = date(sum_year, sum_month, d_num)
    dt_str = str(dt_obj)
    w_day = dt_obj.weekday()
    is_sun = w_day == 6
    is_gaz = (sum_year == 2026 and dt_str in OFFICIAL_GAZETTED_2026) or (
        dt_str in custom_hol_dict
    )

    if not is_sun and not is_gaz:
      mo_working_days += 1

    att_row = (
        att_df[att_df["att_date"] == dt_str] if not att_df.empty else pd.DataFrame()
    )
    leave_row = (
        df[df["leave_date"] == dt_str] if not df.empty else pd.DataFrame()
    )

    if not leave_row.empty:
      mo_leaves_count += 1
    elif not att_row.empty:
      st_val = att_row.iloc[0]["status"]
      if st_val == "Present":
        if is_sun or is_gaz:
          mo_roster_working += 1
        else:
          mo_regular_present += 1

  col_m1, col_m2, col_m3, col_m4 = st.columns(4)
  with col_m1:
    st.metric(
        label="Total Working Days",
        value=mo_working_days,
        help="Normal working days in this month",
    )
  with col_m2:
    st.metric(
        label="Regular Present",
        value=mo_regular_present,
        help="Days you came to office on normal working days",
    )
  with col_m3:
    st.metric(
        label="Roster / Holiday Duty",
        value=mo_roster_working,
        help="Days you came to office on Sunday or Gazetted Holiday",
    )
  with col_m4:
    st.metric(
        label="Total Leave Days",
        value=mo_leaves_count,
        help="Total leaves taken in this month",
    )

  st.markdown("---")

  # --- INTERACTIVE CLICKABLE BUTTON CALENDAR ---
  st.subheader(
      "📅 इंटरैक्टिव कैलेंडर व्यू (किसी भी तारीख के बटन पर क्लिक करें)"
  )

  c_col1, c_col2 = st.columns(2)
  with c_col1:
    selected_year = st.selectbox("वर्ष चुनें", [2026, 2027], index=0, key="cal_yr")
  with c_col2:
    selected_month = st.selectbox(
        "महीना चुनें",
        list(range(1, 13)),
        format_func=lambda x: calendar.month_name[x],
        index=today_date.month - 1,
        key="cal_mo",
    )

  att_dict = {}
  if not att_df.empty:
    for _, row in att_df.iterrows():
      att_dict[row["att_date"]] = (row["status"], row["remarks"])

  leave_dict = {}
  if not df.empty:
    for _, row in df.iterrows():
      leave_dict[row["leave_date"]] = (row["leave_type"], row["reason"])

  # Color Legend Display
  st.markdown(
      """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; font-size: 13px; font-weight: bold;">
        <span style="color: #2e7d32; background: #e8f5e9; padding: 3px 6px; border-radius: 4px;">🟢 Present / Roster</span>
        <span style="color: #c62828; background: #ffebee; padding: 3px 6px; border-radius: 4px;">🔴 Leave</span>
        <span style="color: #1565c0; background: #e3f2fd; padding: 3px 6px; border-radius: 4px;">🔵 Sunday / Gazetted Off</span>
        <span style="color: #616161; background: #f5f5f5; padding: 3px 6px; border-radius: 4px;">⚪ Normal</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # Initialize Session State for Selected Date Inspection
  if "clicked_date_info" not in st.session_state:
    st.session_state.clicked_date_info = None

  cal_matrix = calendar.monthcalendar(selected_year, selected_month)
  days_header = [
      "Mon",
      "Tue",
      "Wed",
      "Thu",
      "Fri",
      "Sat",
      "Sun",
  ]

  # Render Days Header using Columns
  head_cols = st.columns(7)
  for idx, dh in enumerate(days_header):
    head_cols[idx].markdown(
        f"<p style='text-align: center; font-weight: bold; color: #555;'>{dh}</p>",
        unsafe_allow_html=True,
    )

  # Render Calendar Matrix with Clickable Buttons
  for week in cal_matrix:
    row_cols = st.columns(7)
    for i, day in enumerate(week):
      if day == 0:
        row_cols[i].markdown("")
      else:
        d_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
        is_sunday = i == 6
        is_gazetted = (
            selected_year == 2026 and d_str in OFFICIAL_GAZETTED_2026
        ) or (d_str in custom_hol_dict)
        
        att_info = att_dict.get(d_str, None)
        leave_info = leave_dict.get(d_str, None)

        # Button Label & Emoji indicators
        btn_label = f"{day}"
        if leave_info:
          btn_label = f"🔴 {day} ({leave_info[0]})"
        elif att_info:
          st_val = att_info[0]
          if st_val == "Present":
            if is_sunday or is_gazetted:
              btn_label = f"🟢 {day} (Roster)"
            else:
              btn_label = f"🟢 {day} (Pres)"
          elif st_val == "Half-Day":
            btn_label = f"🟡 {day} (Half)"
          elif st_val == "Absent":
            btn_label = f"❌ {day} (Abst)"
          elif st_val == "Sunday Off":
            btn_label = f"🔵 {day} (Off)"
        elif is_sunday or is_gazetted:
          btn_label = f"🔵 {day} (Off)"

        if row_cols[i].button(btn_label, key=f"btn_{d_str}", use_container_width=True):
          # Save clicked date info to show status box
          occ_name = custom_hol_dict.get(d_str, OFFICIAL_GAZETTED_2026.get(d_str, "Sunday Off" if is_sunday else "Working Day"))
          st.session_state.clicked_date_info = {
              "date": d_str,
              "is_sunday": is_sunday,
              "is_gazetted": is_gazetted,
              "occasion": occ_name,
              "attendance": att_info,
              "leave": leave_info
          }

  # Display Clicked Date Details Popup Box below calendar
  if st.session_state.clicked_date_info:
    info = st.session_state.clicked_date_info
    st.markdown("---")
    st.markdown(f"### 🔍 Selected Date Details: `{info['date']}`")
    
    # Base day type description
    if info['is_sunday']:
      day_desc = "Sunday Off"
    elif info['is_gazetted']:
      day_desc = f"Gazetted Holiday ({info['occasion']})"
    else:
      day_desc = "Normal Working Day"

    # Action / Status description
    if info['leave']:
      action_desc = f"On Leave ({info['leave'][0]}) | Reason: {info['leave'][1]}"
    elif info['attendance']:
      db_st = info['attendance'][0]
      rem = info['attendance'][1]
      if db_st == "Present":
        if info['is_sunday'] or info['is_gazetted']:
          action_desc = f"Present in Roster (Holiday Working) | Remarks: {rem}"
        else:
          action_desc = f"Regular Present | Remarks: {rem}"
      else:
        action_desc = f"{db_st} | Remarks: {rem}"
    else:
      if info['is_sunday'] or info['is_gazetted']:
        action_desc = "Off Day (No entry made)"
      else:
        action_desc = "No attendance entry made yet"

    st.info(f"**Base Day Type:** {day_desc}\n\n**Status:** {action_desc}")
    if st.button("Close Details"):
      st.session_state.clicked_date_info = None
      st.rerun()

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
        conn = sqlite3.connect("my_personal_leaves_v41.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {del_id} ka record hata diya gaya hai!")
        st.rerun()
  else:
    st.info("Abhi तक कोई लीव रिकॉर्ड दर्ज नहीं है।")


if __name__ == "__main__":
  main()
