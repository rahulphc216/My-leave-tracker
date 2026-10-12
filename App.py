from datetime import datetime, date, timezone, timedelta
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
    # Durga Puja & October Vacation 2026
    "2026-10-16": "Durga Puja Vacation",
    "2026-10-17": "Durga Puja Vacation",
    "2026-10-18": "Durga Puja (Saptami)",
    "2026-10-19": "Durga Puja (Ashtami)",
    "2026-10-20": "Durga Puja (Navami)",
    "2026-10-21": "Durga Puja (Dashami)",
    "2026-10-22": "Durga Puja Vacation",
    "2026-10-23": "Durga Puja Vacation",
    "2026-10-24": "Durga Puja Vacation",
    "2026-10-25": "Durga Puja Vacation",
    # Diwali & Chhath Puja Continuous Long Vacation
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
  conn = sqlite3.connect("my_personal_leaves_v47.db")
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
            occasion TEXT,
            override_type TEXT
        )
    """)

  conn.commit()
  conn.close()


def main():
  init_db()
  st.set_page_config(
      page_title="Leave & Attendance Tracker", page_icon="📅", layout="wide"
  )

  IST = timezone(timedelta(hours=5, minutes=30))
  today_date = datetime.now(IST).date()
  today_str = str(today_date)
  is_today_sunday = today_date.weekday() == 6

  st.title("🏛️ मेरा लीव और अटेंडेंस ट्रैकर (Patna High Court Rules)")
  st.markdown(
      f"**आज की तारीख (Live):** `{today_date.strftime('%d %B %Y')}` |"
      " मासिक/वार्षिक सारांश और अटेंडेंस रजिस्टर"
  )

  # Fetch overrides from DB
  conn_chk = sqlite3.connect("my_personal_leaves_v47.db")
  ch_df = pd.read_sql_query("SELECT * FROM custom_holidays", conn_chk)
  conn_chk.close()

  holiday_override_dict = {}
  forced_working_set = set()
  if not ch_df.empty:
    for _, row in ch_df.iterrows():
      h_date = row["holiday_date"]
      o_type = row["override_type"]
      if o_type == "Holiday":
        holiday_override_dict[h_date] = row["occasion"]
      elif o_type == "Working":
        forced_working_set.add(h_date)

  is_today_gazetted = (
      today_date.year == 2026 and today_str in OFFICIAL_GAZETTED_2026
  ) or (today_str in holiday_override_dict)
  if today_str in forced_working_set:
    is_today_gazetted = False

  # --- HOLIDAY NOTIFICATION BANNER ---
  if is_today_sunday and today_str not in forced_working_set:
    st.info(
        f"🎉 **आज रविवार (Sunday) है — ऑफिस बंद है!** (Date: {today_date})"
    )
  elif is_today_gazetted:
    occ_name = holiday_override_dict.get(
        today_str, OFFICIAL_GAZETTED_2026.get(today_str, "Gazetted Holiday")
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

    conn_val = sqlite3.connect("my_personal_leaves_v47.db")
    c_val = conn_val.cursor()
    c_val.execute(
        "SELECT leave_type, reason FROM my_leaves WHERE leave_date = ?",
        (d_str_sel,),
    )
    leave_check = c_val.fetchone()

    c_val.execute(
        "SELECT status, remarks FROM my_attendance WHERE att_date = ?",
        (d_str_sel,),
    )
    existing_att = c_val.fetchone()
    conn_val.close()

    is_gaz_sel = (
        (att_selected_date.year == 2026 and d_str_sel in OFFICIAL_GAZETTED_2026)
        or (d_str_sel in holiday_override_dict)
    ) and (d_str_sel not in forced_working_set)

    if leave_check:
      st.error(
          f"⚠️ **Alert:** Is tareekh par pehle se **Leave ({leave_check[0]})**"
          f" darj hai!"
      )
    elif is_sunday_selected and d_str_sel not in forced_working_set:
      st.warning("📌 **Info:** Yeh din **Sunday (Off)** hai.")
    elif is_gaz_sel:
      occ_lbl = holiday_override_dict.get(
          d_str_sel, OFFICIAL_GAZETTED_2026.get(d_str_sel, "Gazetted Holiday")
      )
      st.warning(f"📌 **Info:** Yeh din **Gazetted Holiday ({occ_lbl})** hai.")

    current_remarks = (
        existing_att[1] if existing_att and len(existing_att) > 1 else ""
    )

    if is_sunday_selected and d_str_sel not in forced_working_set:
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
        st.toast(
            f"❌ Error: Is tareekh par Leave ({leave_check[0]}) hai!", icon="❌"
        )
      elif ((is_sunday_selected and d_str_sel not in forced_working_set) or is_gaz_sel) and attendance_status in [
          "Office Present",
          "Roster Duty (Holiday Working)",
      ] and not remarks_input.strip():
        st.toast("❌ Error: Chhutti ke din remarks likhna anivarya hai!", icon="❌")
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

        conn = sqlite3.connect("my_personal_leaves_v47.db")
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
        st.toast("✅ Attendance successfully saved!", icon="🎉")
        st.rerun()

  # --- 2. ADVANCED DATE STATUS & DETAILS CHECKER ---
  with st.sidebar.expander(
      "🔍 Date Status & Details Checker", expanded=False
  ):
    check_date = st.date_input(
        "Tarik chunein:", value=today_date, key="check_dt"
    )
    d_str_chk = str(check_date)
    chk_weekday = check_date.weekday()

    conn = sqlite3.connect("my_personal_leaves_v47.db")
    c = conn.cursor()
    c.execute(
        "SELECT status, remarks FROM my_attendance WHERE att_date = ?",
        (d_str_chk,),
    )
    att_res = c.fetchone()

    c.execute(
        "SELECT leave_type, reason FROM my_leaves WHERE leave_date = ?",
        (d_str_chk,),
    )
    leave_res = c.fetchone()
    conn.close()

    is_sun = chk_weekday == 6
    is_gaz = (
        (check_date.year == 2026 and d_str_chk in OFFICIAL_GAZETTED_2026)
        or (d_str_chk in holiday_override_dict)
    ) and (d_str_chk not in forced_working_set)
    is_half = check_date.year == 2026 and d_str_chk in OFFICIAL_HALFDAY_2026

    if is_sun and d_str_chk not in forced_working_set:
      day_type_str = "Sunday Off"
    elif is_gaz:
      occ_lbl = holiday_override_dict.get(
          d_str_chk, OFFICIAL_GAZETTED_2026.get(d_str_chk, "Gazetted Holiday")
      )
      day_type_str = f"Gazetted Holiday ({occ_lbl})"
    elif is_half:
      day_type_str = "Half-Day Office Day"
    else:
      day_type_str = "Normal Working Day"

    if leave_res:
      action_str = f"On Leave ({leave_res[0]}) - Reason: {leave_res[1]}"
    elif att_res:
      db_st = att_res[0]
      if db_st == "Present":
        if (is_sun and d_str_chk not in forced_working_set) or is_gaz:
          action_str = f"Present in Roster (Holiday Working) | Remarks: {att_res[1]}"
        else:
          action_str = f"Regular Present | Remarks: {att_res[1]}"
      elif db_st == "Half-Day":
        action_str = f"Half-Day Present | Remarks: {att_res[1]}"
      elif db_st == "Absent":
        action_str = f"Absent | Remarks: {att_res[1]}"
      elif db_st == "Sunday Off":
        action_str = "Sunday Off (No Office)"
      else:
        action_str = f"{db_st} | Remarks: {att_res[1]}"
    else:
      if (is_sun and d_str_chk not in forced_working_set) or is_gaz:
        action_str = "Off Day (No entry made)"
      else:
        action_str = "No attendance entry made yet"

    st.markdown(f"### **📅 {d_str_chk} Report:**")
    st.info(f"**Base Day Type:** {day_type_str}\n\n**Status:** {action_str}")

  # --- 3. EDIT / DELETE ATTENDANCE REGISTER ---
  with st.sidebar.expander("✏️ पुरानी अटेंडेंस एडिट या सुधार करें"):
    conn = sqlite3.connect("my_personal_leaves_v47.db")
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
          conn = sqlite3.connect("my_personal_leaves_v47.db")
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE my_attendance SET status = ?, remarks = ? WHERE att_date"
              " = ?",
              (edit_status, edit_remarks, selected_att_id),
          )
          conn.commit()
          conn.close()
          st.toast("✅ Attendance updated successfully!", icon="🎉")
          st.rerun()
      with col_e2:
        if st.button("Record Hatayein"):
          conn = sqlite3.connect("my_personal_leaves_v47.db")
          cursor = conn.cursor()
          cursor.execute(
              "DELETE FROM my_attendance WHERE att_date = ?",
              (selected_att_id,),
          )
          conn.commit()
          conn.close()
          st.toast("✅ Record removed!", icon="🗑️")
          st.rerun()
    else:
      st.info("Abhi koi attendance record nahi hai.")

  # --- 4. ADVANCE / REGULAR LEAVE APPLY ---
  with st.sidebar.expander(
      "➕ एडवांस / नई छुट्टी जोड़ें (Apply / Advance Leave)", expanded=False
  ):
    conn = sqlite3.connect("my_personal_leaves_v47.db")
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
          st.toast(error_msg, icon="❌")
        else:
          conn = sqlite3.connect("my_personal_leaves_v47.db")
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
                  str(datetime.now(IST).strftime("%Y-%m-%d %H:%M")),
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
          st.toast("✅ Leave successfully applied & synced!", icon="🎉")
          st.rerun()

  # --- 5. HOLIDAY OVERRIDE MANAGER ---
  with st.sidebar.expander(
      "🛠️ कैलेंडर सुधार / छुट्टी सेटिंग्स (Holiday Override)"
  ):
    st.markdown(
        "### **तारीख को छुट्टी या वर्किंग डे बनाएं (Permanent Save)**"
    )
    ov_date = st.date_input(
        "तारीख चुनें", value=today_date, key="ov_date_input"
    )
    ov_action = st.selectbox(
        "क्या करना चाहते हैं?",
        [
            "इसे Gazetted Holiday (छुट्टी) बनाएं",
            "इसे Normal Working Day (खुला दिन) बनाएं",
        ],
    )
    ov_reason = st.text_input(
        "वजह / अवसर (जैसे Durga Puja Vacation)", value="Vacation / Working Day"
    )

    if st.button("बदलाव सुरक्षित करें (Save Override)", use_container_width=True):
      conn = sqlite3.connect("my_personal_leaves_v47.db")
      cursor = conn.cursor()
      d_str = str(ov_date)
      if "Holiday" in ov_action:
        cursor.execute(
            """
                    INSERT OR REPLACE INTO custom_holidays (holiday_date, occasion, override_type)
                    VALUES (?, ?, ?)
                """,
            (d_str, ov_reason, "Holiday"),
        )
        st.toast(f"✅ {d_str} saved as Holiday!", icon="🎉")
      else:
        cursor.execute(
            """
                    INSERT OR REPLACE INTO custom_holidays (holiday_date, occasion, override_type)
                    VALUES (?, ?, ?)
                """,
            (d_str, ov_reason, "Working"),
        )
        st.toast(f"✅ {d_str} set as Working Day!", icon="🎉")
      conn.commit()
      conn.close()
      st.rerun()

    st.markdown("---")
    st.markdown("### **सहेजे गए ओवरराइड्स हटाएं (Reset)**")
    conn_r = sqlite3.connect("my_personal_leaves_v47.db")
    saved_ov = pd.read_sql_query("SELECT * FROM custom_holidays", conn_r)
    conn_r.close()

    if not saved_ov.empty:
      del_target = st.selectbox(
          "रीसेट के लिए तारीख चुनें:", saved_ov["holiday_date"].tolist()
      )
      if st.button("ओवरराइड हटाएं (Reset to Default)", use_container_width=True):
        conn_d = sqlite3.connect("my_personal_leaves_v47.db")
        cursor_d = conn_d.cursor()
        cursor_d.execute(
            "DELETE FROM custom_holidays WHERE holiday_date = ?", (del_target,)
        )
        conn_d.commit()
        conn_d.close()
        st.toast("✅ Reset to default rule!", icon="🔄")
        st.rerun()
    else:
      st.info("Abhi koi custom override save nahi hai.")

  # --- 6. MANUAL CPL SETTINGS ---
  with st.sidebar.expander("⚙️ मैनुअल CPL कोटा सेटिंग्स"):
    conn = sqlite3.connect("my_personal_leaves_v47.db")
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
      conn = sqlite3.connect("my_personal_leaves_v47.db")
      cursor = conn.cursor()
      cursor.execute("DELETE FROM my_cpl_setting")
      cursor.execute(
          "INSERT INTO my_cpl_setting (total_cpl) VALUES (?)",
          (total_cpl_allocated,),
      )
      conn.commit()
      conn.close()
      st.toast("✅ CPL quota updated!", icon="🎉")
      st.rerun()

  # Refresh data for main view
  conn = sqlite3.connect("my_personal_leaves_v47.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  att_df = pd.read_sql_query("SELECT * FROM my_attendance", conn)
  custom_hol_df = pd.read_sql_query("SELECT * FROM custom_holidays", conn)
  c = conn.cursor()
  c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
  saved_cpl = c.fetchone()
  active_cpl_quota = saved_cpl[0] if saved_cpl else 0
  conn.close()

  holiday_override_dict = {}
  forced_working_set = set()
  if not custom_hol_df.empty:
    for _, row in custom_hol_df.iterrows():
      h_date = row["holiday_date"]
      o_type = row["override_type"]
      if o_type == "Holiday":
        holiday_override_dict[h_date] = row["occasion"]
      elif o_type == "Working":
        forced_working_set.add(h_date)

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
    
    is_gaz = (
        (sum_year == 2026 and dt_str in OFFICIAL_GAZETTED_2026)
        or (dt_str in holiday_override_dict)
    ) and (dt_str not in forced_working_set)

    is_off_day = (is_sun and dt_str not in forced_working_set) or is_gaz

    if not is_off_day:
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
        if is_off_day:
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

  # --- Advanced HTML Calendar View with Clear Badge System ---
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

  # Clear Legend with Badge Indicators
  st.markdown(
      """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; font-size: 13px; font-weight: bold;">
        <span style="background: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 4px; border: 1px solid #c8e6c9;">🟢 Present / Roster</span>
        <span style="background: #fffde7; color: #f57f17; padding: 4px 8px; border-radius: 4px; border: 1px solid #fff9c4;">🟡 Half-Day</span>
        <span style="background: #ffebee; color: #c62828; padding: 4px 8px; border-radius: 4px; border: 1px solid #ffcdd2;">🔴 Leave</span>
        <span style="background: #e3f2fd; color: #1565c0; padding: 4px 8px; border-radius: 4px; border: 1px solid #bbdefb;">🔵 Sunday / Holiday</span>
        <span style="background: #ffffff; color: #333333; padding: 4px 8px; border-radius: 4px; border: 1px solid #ddd;">⚪ Normal</span>
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
            "<td style='border: 1px solid #ddd; padding: 12px;"
            " background-color: #fafafa;'></td>"
        )
      else:
        d_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
        status = att_dict.get(d_str, "")
        is_sunday = i == 6
        
        is_gazetted = (
            (selected_year == 2026 and d_str in OFFICIAL_GAZETTED_2026)
            or (d_str in holiday_override_dict)
        ) and (d_str not in forced_working_set)
        
        is_halfday = selected_year == 2026 and d_str in OFFICIAL_HALFDAY_2026

        tooltip = ""
        badge_html = ""
        is_off_day = (is_sunday and d_str not in forced_working_set) or is_gazetted

        # Logic for status badges (Keeping digit color perfectly black & clear)
        if "Leave" in status or d_str in leave_dates_set:
          badge_html = "<br><span style='font-size:10px; background:#ffebee; color:#c62828; padding:2px 4px; border-radius:3px; font-weight:bold;'>Leave</span>"
        elif status == "Present" or status == "Sunday Emergency":
          if is_off_day:
            badge_html = "<br><span style='font-size:10px; background:#c8e6c9; color:#1b5e20; padding:2px 4px; border-radius:3px; font-weight:bold;'>Roster</span>"
          else:
            badge_html = "<br><span style='font-size:10px; background:#e8f5e9; color:#2e7d32; padding:2px 4px; border-radius:3px; font-weight:bold;'>Present</span>"
        elif is_off_day:
          badge_html = "<br><span style='font-size:10px; background:#e3f2fd; color:#1565c0; padding:2px 4px; border-radius:3px; font-weight:bold;'>Off</span>"
          if d_str in holiday_override_dict:
            tooltip = f" title='{holiday_override_dict[d_str]}'"
          elif d_str in OFFICIAL_GAZETTED_2026:
            tooltip = f" title='{OFFICIAL_GAZETTED_2026[d_str]}'"
        elif is_halfday or status == "Half-Day":
          badge_html = "<br><span style='font-size:10px; background:#fffde7; color:#f57f17; padding:2px 4px; border-radius:3px; font-weight:bold;'>Half</span>"
          if is_halfday:
            tooltip = f" title='{OFFICIAL_HALFDAY_2026[d_str]}'"

        # Cell background remains clean white, digit remains clear dark (#222)
        html_table += f"<td{tooltip} style='border: 1px solid #e0e0e0; padding: 8px 2px; background-color: #ffffff; color: #222222; font-weight: bold; font-size: 16px; vertical-align: middle;'>{day}{badge_html}</td>"
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
        conn = sqlite3.connect("my_personal_leaves_v47.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.toast(f"✅ Leave record ID {del_id} deleted!", icon="🗑️")
        st.rerun()
  else:
    st.info("Abhi तक कोई लीव रिकॉर्ड दर्ज नहीं है।")


if __name__ == "__main__":
  main()
