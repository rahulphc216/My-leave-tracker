from datetime import datetime, date
import calendar
import pandas as pd
import sqlite3
import streamlit as st

# Patna High Court 2026 Official Restricted Holidays (RH) List
OFFICIAL_RH_2026 = {
    "Jan 16 - Guru Gobind Singh Ji's Birthday": "2026-01-16",
    "Jan 26 - Shab-e-Barat": "2026-01-26",
    "Feb 15 - Maha Shivaratri": "2026-02-15",
    "Mar 04 - Holika Dahan": "2026-03-04",
    "Apr 03 - Good Friday": "2026-04-03",
    "Apr 14 - Mahavir Jayanti": "2026-04-14",
    "May 15 - Buddha Purnima": "2026-05-15",
    "Aug 28 - Muharram": "2026-08-28",
    "Oct 20 - Karwa Chauth": "2026-10-20",
}


# डेटाबेस सेटअप
def init_db():
  conn = sqlite3.connect("my_personal_leaves_v9.db")
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
            status TEXT
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
  st.markdown("दैनिक उपस्थिति और स्मार्ट लीव डैशबोर्ड (बैकडेट एंट्री सहित)")

  # --- साइडबार: कोटा सेटिंग्स ---
  st.sidebar.header("⚙️ लीव कोटा सेटिंग्स")
  total_cpl_allocated = st.sidebar.number_input(
      "इस साल कुल मान्य CPL (Total Applicable CPL)",
      min_value=0,
      max_value=50,
      value=0,
      step=1,
  )

  st.sidebar.markdown("---")
  st.sidebar.header("🟢 उपस्थिति दर्ज करें (Backdate / Daily Attendance)")

  # किसी भी पुरानी या आज की तारीख चुनने का विकल्प
  att_selected_date = st.sidebar.date_input(
      "उपस्थिति की तारीख चुनें (Select Date)", value=date.today()
  )

  # चुनी गई तारीख की पुरानी अटेंडेंस चेक करना
  conn = sqlite3.connect("my_personal_leaves_v9.db")
  c = conn.cursor()
  c.execute(
      "SELECT status FROM my_attendance WHERE att_date = ?",
      (str(att_selected_date),),
  )
  existing_att = c.fetchone()
  conn.close()

  default_att = (
      True
      if existing_att
      and (
          existing_att[0] == "Present"
          or "Leave" in existing_att[0]
          or existing_att[0] == "Office"
      )
      else False
  )
  mark_present = st.sidebar.checkbox(
      f"तारीख {att_selected_date} को कार्यालय में उपस्थित रहे?",
      value=default_att,
  )

  if st.sidebar.button("उपस्थिति सेव/सुधार करें"):
    status_val = "Present" if mark_present else "Absent"
    conn = sqlite3.connect("my_personal_leaves_v9.db")
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT OR REPLACE INTO my_attendance (att_date, status)
            VALUES (?, ?)
        """,
        (str(att_selected_date), status_val),
    )
    conn.commit()
    conn.close()
    st.sidebar.success(
        f"✅ {att_selected_date} की उपस्थिति '{status_val}' के रूप में दर्ज हो"
        " गई!"
    )
    st.rerun()

  st.sidebar.markdown("---")
  st.sidebar.header("➕ नई छुट्टी जोड़ें (Apply Leave)")

  # डेटा फेच करना
  conn = sqlite3.connect("my_personal_leaves_v9.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  att_df = pd.read_sql_query("SELECT * FROM my_attendance", conn)
  conn.close()

  # छुट्टियाँ निकालना
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
  cpl_remaining = total_cpl_allocated - cpl_taken
  rh_remaining = 2 - rh_taken

  today_date = date.today()
  available_rh_options = {}
  for rh_name, rh_date_str in OFFICIAL_RH_2026.items():
    rh_dt = datetime.strptime(rh_date_str, "%Y-%m-%d").date()
    if rh_dt >= today_date and rh_date_str not in already_taken_rh_dates:
      available_rh_options[rh_name] = rh_date_str

  with st.sidebar.form("leave_form"):
    leave_category = st.selectbox(
        "छुट्टी का प्रकार (Leave Type)",
        ["CL", "CPL", "EL", "RH", "Late Coming"],
    )

    if leave_category == "RH":
      if rh_remaining <= 0:
        st.warning("⚠️ आपने इस साल की दोनों (2) RH पूरी कर ली हैं!")
        selected_rh_key = None
        leave_date = today_date
      elif not available_rh_options:
        st.info("आगामी कोई RH उपलब्ध नहीं है।")
        selected_rh_key = None
        leave_date = today_date
      else:
        selected_rh_key = st.selectbox(
            "वैध RH चुनें:", list(available_rh_options.keys())
        )
        leave_date = (
            datetime.strptime(
                available_rh_options[selected_rh_key], "%Y-%m-%d"
            ).date()
            if selected_rh_key
            else today_date
        )
    else:
      leave_date = st.date_input("छुट्टी की तारीख (Date - पीछे की तारीख भी चुन सकते हैं)")

    if leave_category == "RH":
      days_count = 1
    else:
      days_count = st.number_input(
          "दिनों की संख्या (Full Days)",
          min_value=1,
          max_value=30,
          value=1,
          step=1,
      )

    reason = st.text_area("वजह / टिप्पणी (Optional)")
    submit = st.form_submit_button("रिकॉर्ड सेव करें")

    if submit:
      error_msg = None
      if leave_category == "CL" and days_count > cl_remaining:
        error_msg = (
            f"❌ त्रुटि: आपके पास केवल {cl_remaining} CL बची है!"
        )
      elif leave_category == "CPL" and days_count > cpl_remaining:
        error_msg = (
            f"❌ त्रुटि: आपके पास केवल {cpl_remaining} CPL बची है!"
        )
      elif leave_category == "RH" and rh_remaining <= 0:
        error_msg = "❌ त्रुटि: अधिकतम 2 ही RH ले सकते हैं!"

      if error_msg:
        st.sidebar.error(error_msg)
      else:
        conn = sqlite3.connect("my_personal_leaves_v9.db")
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
                    INSERT OR REPLACE INTO my_attendance (att_date, status)
                    VALUES (?, ?)
                """,
            (str(leave_date), f"Leave ({leave_category})"),
        )
        conn.commit()
        conn.close()
        st.sidebar.success("✅ छुट्टी का रिकॉर्ड सफलतापर्वक दर्ज हो गया!")
        st.rerun()

  # --- होम पेज लाइव बैलेंस ---
  st.markdown("### 🟢 आपका वर्तमान लीव बैलेंस (Live Status)")
  bal_col1, bal_col2, bal_col3, bal_col4 = st.columns(4)
  with bal_col1:
    st.success(f"**CL बची हुई:** {cl_remaining} दिन")
  with bal_col2:
    st.info(f"**CPL बची हुई:** {cpl_remaining} दिन")
  with bal_col3:
    el_balance = 33 - el_taken
    st.warning(f"**EL बैलेंस:** {el_balance} दिन")
  with bal_col4:
    st.error(f"**RH बची हुई:** {rh_remaining} दिन")

  st.markdown("---")

  # --- कैलेंडर व्यू ---
  st.subheader("📅 उपस्थिति और लीव कैलेंडर व्यू (Calendar View)")

  c_col1, c_col2 = st.columns(2)
  with c_col1:
    selected_year = st.selectbox("वर्ष चुनें (Year)", [2026, 2027], index=0)
  with c_col2:
    selected_month = st.selectbox(
        "महीना चुनें (Month)",
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

  st.markdown(
      "🟢 **हरा (Present)** | 🔴 **लाल (Leave/Absent)** | ⚪ **सामान्य**"
  )

  cal_matrix = calendar.monthcalendar(selected_year, selected_month)
  days_header = ["सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि", "रवि"]

  cal_data = []
  for week in cal_matrix:
    week_row = {}
    for i, day in enumerate(week):
      if day == 0:
        week_row[days_header[i]] = ""
      else:
        d_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
        status = att_dict.get(d_str, "")
        if d_str in leave_dates_set or "Leave" in status:
          week_row[days_header[i]] = f"🔴 {day} (Leave)"
        elif status == "Present":
          week_row[days_header[i]] = f"🟢 {day} (Office)"
        else:
          week_row[days_header[i]] = f"{day}"
    cal_data.append(week_row)

  cal_df = pd.DataFrame(cal_data)
  st.table(cal_df)

  # --- मेट्रिक्स और हिस्ट्री ---
  st.markdown("---")
  st.subheader("📊 वार्षिक लीव कोटा समरी")
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("CL", f"खर्च: {cl_taken}", f"शेष: {cl_remaining}")
  with col2:
    st.metric("CPL", f"खर्च: {cpl_taken}", f"शेष: {cpl_remaining}")
  with col3:
    st.metric("EL", f"खर्च: {el_taken}", f"बैलेंस: {el_balance}")
  with col4:
    st.metric("RH", f"खर्च: {rh_taken}", f"शेष: {rh_remaining}")

  st.markdown("---")
  st.subheader("📋 सभी लीव रिकॉर्ड्स (History)")
  if not df.empty:
    st.dataframe(df, use_container_width=True)

    del_id = st.number_input(
        "हटाने के लिए रिकॉर्ड ID दर्ज करें", min_value=0, step=1
    )
    if st.button("चयनित रिकॉर्ड हटाएं"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v9.db")
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
