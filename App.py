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
  conn = sqlite3.connect("my_personal_leaves_v16.db")
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
  st.markdown("ऑटोमैटिक लीव सिंक और स्मार्ट डैशबोर्ड")

  # --- CPL Setting Expander ---
  with st.sidebar.expander("⚙️ Advanced Settings (CPL Quota Setup)"):
    conn = sqlite3.connect("my_personal_leaves_v16.db")
    c = conn.cursor()
    c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
    saved_cpl = c.fetchone()
    default_cpl = saved_cpl[0] if saved_cpl else 0
    conn.close()

    total_cpl_allocated = st.number_input(
        "Is saal ke liye Kul Applicable CPL",
        min_value=0,
        max_value=50,
        value=default_cpl,
        step=1,
    )

    if st.button("CPL Quota Save Karein"):
      conn = sqlite3.connect("my_personal_leaves_v16.db")
      cursor = conn.cursor()
      cursor.execute("DELETE FROM my_cpl_setting")
      cursor.execute(
          "INSERT INTO my_cpl_setting (total_cpl) VALUES (?)",
          (total_cpl_allocated,),
      )
      conn.commit()
      conn.close()
      st.success("✅ CPL quota save ho gaya!")
      st.rerun()

  conn = sqlite3.connect("my_personal_leaves_v16.db")
  c = conn.cursor()
  c.execute("SELECT total_cpl FROM my_cpl_setting ORDER BY id DESC LIMIT 1")
  saved_cpl = c.fetchone()
  active_cpl_quota = saved_cpl[0] if saved_cpl else 0
  conn.close()

  # --- Upload Calendar / RH List ---
  with st.sidebar.expander("📤 Upload Calendar / RH List (For 2027+)"):
    uploaded_file = st.file_uploader(
        "High Court Calendar Image/PDF upload karein", type=["png", "jpg", "pdf"]
    )
    if uploaded_file is not None:
      st.success("📁 File upload ho gayi! Calendar data sync ke liye taiyar hai.")

  # --- Attendance Manager (Default Hide / Collapsed) ---
  with st.sidebar.expander(
      "🟢 Manual Attendance / Sunday Emergency Manager"
  ):
    today_date = date.today()
    att_selected_date = st.date_input(
        "Tarikh chunein (Auto Today)", value=today_date, key="att_date_input"
    )

    is_sunday_selected = att_selected_date.weekday() == 6

    conn = sqlite3.connect("my_personal_leaves_v16.db")
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
      st.info("📌 Yeh din Sunday hai. Sunday ko aam taur par off rehta hai.")
      sunday_emergency = st.checkbox(
          "⚠️ Sunday Emergency Working (Khas sthiti me office aaye the?)"
      )
      if sunday_emergency:
        attendance_status = "Office Present"
        remarks_input = st.text_input(
            "Sunday Emergency Remarks (Vajah likhein):",
            value=current_remarks,
            key="sun_rem",
        )
      else:
        attendance_status = "Sunday Off"
        remarks_input = ""
    else:
      attendance_status = st.selectbox(
          "Stithi Chunein:",
          ["Office Present", "Half-Day Office", "Absent / Leave"],
          index=(
              0
              if current_status_val == "Present"
              else (1 if current_status_val == "Half-Day" else 2)
          ),
          key="att_status_box",
      )
      remarks_input = st.text_area(
          "Remarks / Tippani (Optional):",
          value=current_remarks,
          key="normal_rem",
      )

    if st.button("Upasthiti Save Karein"):
      if attendance_status == "Office Present":
        status_db = "Present"
      elif attendance_status == "Half-Day Office":
        status_db = "Half-Day"
      elif attendance_status == "Sunday Off":
        status_db = "Sunday Off"
      else:
        status_db = "Absent"

      conn = sqlite3.connect("my_personal_leaves_v16.db")
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
      st.success(
          f"✅ {att_selected_date} ki upasthiti safaltapoorvak save ho gayi!"
      )
      st.rerun()

  st.sidebar.markdown("---")
  st.sidebar.header("➕ Nayi Chhutti Jodein (Apply Leave)")

  # Data Fetch
  conn = sqlite3.connect("my_personal_leaves_v16.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  att_df = pd.read_sql_query("SELECT * FROM my_attendance", conn)
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

  with st.sidebar.form("leave_form"):
    leave_category = st.selectbox(
        "Chhutti ka prakar", ["CL", "CPL", "EL", "RH", "Late Coming"]
    )

    if leave_category == "RH":
      if rh_remaining <= 0:
        st.warning("⚠️ Dono RH poori ho chuki hain!")
        selected_rh_key = None
        leave_date = date.today()
      elif not available_rh_options:
        st.info("Is saal ke liye koi aur RH uplabdh nahi hai.")
        selected_rh_key = None
        leave_date = date.today()
      else:
        selected_rh_key = st.selectbox(
            "Vaidya RH chunein:", list(available_rh_options.keys())
        )
        leave_date = (
            datetime.strptime(
                year_rh_dict[selected_rh_key], "%Y-%m-%d"
            ).date()
            if selected_rh_key
            else date.today()
        )
    else:
      leave_date = st.date_input("Chhutti ki tarikh")

    if leave_category == "RH":
      days_count = 1
    else:
      days_count = st.number_input(
          "Dino ki sankhya", min_value=1, max_value=30, value=1, step=1
      )

    reason = st.text_area("Vajah / Tippani (Reason)")
    submit = st.form_submit_button("Record Save Karein")

    if submit:
      error_msg = None
      if leave_category == "CL" and days_count > cl_remaining:
        error_msg = f"❌ Error: Kewal {cl_remaining} CL bachi hai!"
      elif leave_category == "CPL" and days_count > cpl_remaining:
        error_msg = f"❌ Error: Kewal {cpl_remaining} CPL bachi hai!"
      elif leave_category == "RH" and rh_remaining <= 0:
        error_msg = f"❌ Error: Max 2 RH hi le sakte hain!"

      if error_msg:
        st.sidebar.error(error_msg)
      else:
        conn = sqlite3.connect("my_personal_leaves_v16.db")
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
        st.sidebar.success("✅ Chhutti darj ho gayi aur calendar me update ho gayi!")
        st.rerun()

  # --- Home Page Live Balance ---
  st.markdown("### 🟢 Aapka Vartaman Leave Balance")
  bal_col1, bal_col2, bal_col3, bal_col4 = st.columns(4)
  with bal_col1:
    st.success(f"**CL Bacha Hua:** {cl_remaining} din")
  with bal_col2:
    st.info(f"**CPL Bacha Hua:** {cpl_remaining} din")
  with bal_col3:
    el_balance = 33 - el_taken
    st.warning(f"**EL Balance:** {el_balance} din")
  with bal_col4:
    st.error(f"**RH Bacha Hua:** {rh_remaining} din")

  st.markdown("---")

  # --- Calendar View ---
  st.subheader("📅 Calendar View")

  c_col1, c_col2 = st.columns(2)
  with c_col1:
    selected_year = st.selectbox("Varsh chunein", [2026, 2027], index=0)
  with c_col2:
    selected_month = st.selectbox(
        "Mahina chunein",
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

  st.markdown(
      "🟢 **Office Present** | 🟡 **Half-Day Office** | 🔴 **Leave** | 🔵 **Sunday"
      " (Off)** | ⚪ **Samanya**"
  )

  cal_matrix = calendar.monthcalendar(selected_year, selected_month)
  days_header = ["Som", "Mangal", "Budh", "Guru", "Shukra", "Shani", "Ravi"]

  cal_data = []
  for week in cal_matrix:
    week_row = {}
    for i, day in enumerate(week):
      if day == 0:
        week_row[days_header[i]] = ""
      else:
        d_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
        status = att_dict.get(d_str, "")
        is_sunday = i == 6

        if d_str in leave_dates_set or "Leave" in status:
          week_row[days_header[i]] = f"🔴 {day}"
        elif is_sunday and status != "Present":
          week_row[days_header[i]] = f"🔵 {day}"
        elif status == "Present" or status == "Sunday Emergency":
          week_row[days_header[i]] = f"🟢 {day}"
        elif status == "Half-Day":
          week_row[days_header[i]] = f"🟡 {day}"
        else:
          week_row[days_header[i]] = f"{day}"
    cal_data.append(week_row)

  cal_df = pd.DataFrame(cal_data)
  st.table(cal_df)

  # --- History & Delete ---
  st.markdown("---")
  st.subheader("📋 Sabhi Leave Records (History)")
  if not df.empty:
    st.dataframe(df, use_container_width=True)

    del_id = st.number_input(
        "Hatane ke liye Record ID darj karein", min_value=0, step=1
    )
    if st.button("Chayanit Record Hatayein"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v16.db")
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
