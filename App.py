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
          ),
      )
      conn.commit()
      conn.close()
      st.sidebar.success("✅ आपकी छुट्टी का रिकॉर्ड सफलतापर्वक दर्ज हो गया!")
      st.rerun()

  # डेटा फेच करना
  conn = sqlite3.connect("my_personal_leaves_v2.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  conn.close()

  # अलग-अलग छुट्टियों का कुल योग निकालना
  cl_taken = (
      df[df["leave_type"].str.startswith("CL")]["days_count"].sum()
      if not df.empty
      else 0
  )
  cpl_taken = (
      df[df["leave_type"].str.startswith("CPL")]["days_count"].sum()
      if not df.empty
      else 0
  )
  el_taken = (
      df[df["leave_type"].str.startswith("EL")]["days_count"].sum()
      if not df.empty
      else 0
  )
  rh_taken = (
      df[df["leave_type"].str.startswith("RH")]["days_count"].sum()
      if not df.empty
      else 0
  )

  # मेट्रिक्स और बैलेंस दिखाना
  st.subheader("📊 वार्षिक लीव बैलेंस और स्थिति (Leave Quota Summary)")
  col1, col2, col3, col4 = st.columns(4)

  with col1:
    cl_balance = 16 - cl_taken
    st.metric(
        "CL (Casual Leave)",
        f"खर्च: {cl_taken}",
        f"शेष: {cl_balance} (मैक्स 16)",
    )
  with col2:
    st.metric(
        "CPL (Compensatory)", f"कुल ली गई: {cpl_taken}", "1 साल की वैधता"
    )
  with col3:
    el_balance = 33 - el_taken
    st.metric("EL (Earned Leave)", f"खर्च: {el_taken}", f"बचत/बैलेंस: {el_balance}")
  with col4:
    rh_balance = 2 - rh_taken
    st.metric("RH (Restricted)", f"खर्च: {rh_taken}", f"शेष: {rh_balance} (मैक्स 2)")

  st.markdown("---")
  st.subheader("📋 सभी लीव रिकॉर्ड्स (History)")

  if not df.empty:
    st.dataframe(df, use_container_width=True)

    # रिकॉर्ड हटाने का विकल्प
    st.markdown("### ⚙️ रिकॉर्ड प्रबंधित करें")
    del_id = st.number_input(
        "हटाने के लिए रिकॉर्ड ID दर्ज करें", min_value=0, step=1
    )
    if st.button("चयनित रिकॉर्ड हटाएं"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v2.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {del_id} का रिकॉर्ड हटा दिया गया है!")
        st.rerun()
  else:
    st.info("अभी तक कोई रिकॉर्ड दर्ज नहीं किया गया है।")


if __name__ == "__main__":
  main()
