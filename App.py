from datetime import datetime
import pandas as pd
import sqlite3
import streamlit as st


# डेटाबेस सेटअप
def init_db():
  conn = sqlite3.connect("my_personal_leaves_v2.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leave_type TEXT,
            leave_date TEXT,
            days_count REAL,
            reason TEXT,
            timestamp TEXT
        )
    """)
  conn.commit()
  conn.close()


def main():
  init_db()
  st.set_page_config(
      page_title="Personal Leave Manager", page_icon="📅", layout="wide"
  )

  st.title("🏛️ मेरा लीव और अटेंडेंस ट्रैकर (Patna High Court Rules)")
  st.markdown("अपनी छुट्टियों का सटीक और नियम-बद्ध व्यक्तिगत रिकॉर्ड")

  # साइडबार: नई छुट्टी दर्ज करने के लिए फॉर्म
  st.sidebar.header("➕ नई छुट्टी जोड़ें")
  with st.sidebar.form("leave_form"):
    leave_type = st.selectbox(
        "छुट्टी का प्रकार (Leave Type)",
        [
            "CL (Casual Leave - Max 16)",
            "CPL (Compensatory Leave - Valid 1 Year)",
            "EL (Earned Leave - Base 33)",
            "RH (Restricted Holiday - Max 2)",
            "Late Coming",
        ],
    )

    leave_date = st.date_input("छुट्टी की तारीख (Date)")
    days_count = st.number_input(
        "दिनों की संख्या (Days)", min_value=0.5, max_value=30.0, value=1.0, step=0.5
    )
    reason = st.text_area("वजह / टिप्पणी (Optional)")

    submit = st.form_submit_button("रिकॉर्ड सेव करें")

    if submit:
      conn = sqlite3.connect("my_personal_leaves_v2.db")
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO my_leaves (leave_type, leave_date, days_count, reason, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
          (
              leave_type,
              str(leave_date),
              days_count,
              reason,
              str(datetime.now().strftime("%Y-%m-%d %H:%M")),
          ),
      )
      conn.commit()
      conn.close()
      st.sidebar.success("✅ आपकी छुट्टी का रिकॉर्ड सफलतापर्वक दर्ज हो गया!")
      st.rerun()

  # --- पुरानी/अक्टूबर से पहले ली गई छुट्टियाँ सेट करने का सेक्शन (CPL सहित) ---
  st.sidebar.markdown("---")
  st.sidebar.subheader("⚙️ Purani Chhuttiyan (Opening Balance)")
  st.sidebar.markdown(
      "October se pehle ki li gayi purani chhuttiyan yahan enter karein:"
  )

  past_cl = st.sidebar.number_input(
      "Pehle li gayi total CL", min_value=0.0, max_value=16.0, value=0.0, step=0.5
  )
  past_cpl = st.sidebar.number_input(
      "Pehle li gayi total CPL",
      min_value=0.0,
      max_value=30.0,
      value=0.0,
      step=0.5,
  )
  past_el = st.sidebar.number_input(
      "Pehle li gayi total EL",
      min_value=0.0,
      max_value=100.0,
      value=0.0,
      step=0.5,
  )
  past_rh = st.sidebar.number_input(
      "Pehle li gayi total RH", min_value=0.0, max_value=2.0, value=0.0, step=1.0
  )

  # डेटा फेच करना
  conn = sqlite3.connect("my_personal_leaves_v2.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  conn.close()

  # ऐप के अंदर दर्ज की गई छुट्टियाँ + पुरानी छुट्टियाँ जोड़ना
  app_cl = (
      df[df["leave_type"].str.startswith("CL")]["days_count"].sum()
      if not df.empty
      else 0
  )
  app_cpl = (
      df[df["leave_type"].str.startswith("CPL")]["days_count"].sum()
      if not df.empty
      else 0
  )
  app_el = (
      df[df["leave_type"].str.startswith("EL")]["days_count"].sum()
      if not df.empty
      else 0
  )
  app_rh = (
      df[df["leave_type"].str.startswith("RH")]["days_count"].sum()
      if not df.empty
      else 0
  )

  total_cl_taken = app_cl + past_cl
  total_cpl_taken = app_cpl + past_cpl
  total_el_taken = app_el + past_el
  total_rh_taken = app_rh + past_rh

  # मेट्रिक्स और बैलेंस दिखाना
  st.subheader("📊 वार्षिक लीव बैलेंस और स्थिति (Leave Quota Summary)")
  col1, col2, col3, col4 = st.columns(4)

  with col1:
    cl_balance = 16 - total_cl_taken
    st.metric(
        "CL (Casual Leave)",
        f"Kul Kharch: {total_cl_taken}",
        f"Shesh: {cl_balance} (Max 16)",
    )
  with col2:
    st.metric(
        "CPL (Compensatory)",
        f"Kul Kharch: {total_cpl_taken}",
        "1 Saal Validity",
    )
  with col3:
    el_balance = 33 - total_el_taken
    st.metric(
        "EL (Earned Leave)",
        f"Kul Kharch: {total_el_taken}",
        f"Balance: {el_balance}",
    )
  with col4:
    rh_balance = 2 - total_rh_taken
    st.metric(
        "RH (Restricted)",
        f"Kul Kharch: {total_rh_taken}",
        f"Shesh: {rh_balance} (Max 2)",
    )

  st.markdown("---")
  st.subheader("📋 Sabhi App Entries (History)")

  if not df.empty:
    st.dataframe(df, use_container_width=True)

    # रिकॉर्ड हटाने का विकल्प
    st.markdown("### ⚙️ Record Mitayein (Delete)")
    del_id = st.number_input(
        "Hatane ke liye Record ID darj karein", min_value=0, step=1
    )
    if st.button("Chayanit Record Hatayein"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v2.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {del_id} ka record hata diya gaya hai!")
        st.rerun()
  else:
    st.info(
        "Abhi app mein koi entry nahi hai. Sidebar se purani ya nayi entry"
        " set kar sakte hain."
    )


if __name__ == "__main__":
  main()
