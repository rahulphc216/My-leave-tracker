from datetime import datetime
import pandas as pd
import sqlite3
import streamlit as st


# डेटाबेस सेटअप
def init_db():
  conn = sqlite3.connect("my_personal_leaves_v3.db")
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
  conn.commit()
  conn.close()


def main():
  init_db()
  st.set_page_config(
      page_title="Personal Leave Manager", page_icon="📅", layout="wide"
  )

  st.title("🏛️ मेरा लीव और अटेंडेंस ट्रैकर (Patna High Court Rules)")
  st.markdown("नियम-बद्ध व्यक्तिगत लीव डैशबोर्ड")

  # --- साइडबार: ओपनिंग बैलेंस / कोटा सेट करने के लिए ---
  st.sidebar.header("⚙️ लीव कोटा और ओपनिंग सेटिंग्स")

  # CPL का साल भर का कुल कोटा मैन्युअल रूप से सेट करने के लिए
  total_cpl_allocated = st.sidebar.number_input(
      "इस साल कुल मान्य CPL (Total Applicable CPL)",
      min_value=0,
      max_value=50,
      value=0,
      step=1,
  )

  st.sidebar.markdown("---")
  st.sidebar.header("➕ नई छुट्टी जोड़ें (Apply Leave)")

  # डेटा फेच करना ताकि तुरंत कैलकुलेशन हो सके
  conn = sqlite3.connect("my_personal_leaves_v3.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  conn.close()

  # अब तक ली गई कुल छुट्टियाँ निकालना (Only Integers)
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

  # वर्तमान शेष बैलेंस
  cl_remaining = 16 - cl_taken
  cpl_remaining = total_cpl_allocated - cpl_taken
  rh_remaining = 2 - rh_taken

  with st.sidebar.form("leave_form"):
    leave_type = st.selectbox(
        "छुट्टी का प्रकार (Leave Type)",
        [
            f"CL (Casual Leave - शेष: {cl_remaining})",
            f"CPL (Compensatory Leave - शेष: {cpl_remaining})",
            "EL (Earned Leave - Base 33)",
            f"RH (Restricted Holiday - शेष: {rh_remaining})",
            "Late Coming",
        ],
    )

    leave_date = st.date_input("छुट्टी की तारीख (Date)")

    # सिर्फ पूरे अंकों (Integers) में दिनों की संख्या
    days_count = st.number_input(
        "दिनों की संख्या (Days - Full Numbers Only)",
        min_value=1,
        max_value=30,
        value=1,
        step=1,
    )

    reason = st.text_area("वजह / टिप्पणी (Optional)")
    submit = st.form_submit_button("रिकॉर्ड सेव करें")

    if submit:
      # Validation Checks
      error_msg = None
      clean_leave_type = leave_type.split(" ")[
          0
      ]  # सिर्फ CL, CPL, EL, RH निकालना

      if clean_leave_type == "CL":
        if days_count > cl_remaining:
          error_msg = (
              f"❌ त्रुटि: आपके पास केवल {cl_remaining} CL बची है! आप इससे"
              " ज़्यादा आवेदन नहीं कर सकते।"
          )
      elif clean_leave_type == "CPL":
        if days_count > cpl_remaining:
          error_msg = (
              f"❌ त्रुटि: आपके पास केवल {cpl_remaining} CPL बची है! कृपया"
              " सही संख्या दर्ज करें।"
          )
      elif clean_leave_type == "RH":
        if rh_taken + days_count > 2:
          error_msg = (
              "❌ त्रुटि: आप साल भर में अधिकतम केवल 2 ही RH ले सकते हैं!"
          )

      if error_msg:
        st.sidebar.error(error_msg)
      else:
        conn = sqlite3.connect("my_personal_leaves_v3.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO my_leaves (leave_type, leave_date, days_count, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """,
            (
                clean_leave_type,
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

  # --- डैशबोर्ड और मेट्रिक्स ---
  st.subheader("📊 वार्षिक लीव बैलेंस और स्थिति (Leave Quota Summary)")
  col1, col2, col3, col4 = st.columns(4)

  with col1:
    st.metric(
        "CL (Casual Leave)",
        f"खर्च: {cl_taken}",
        f"शेष: {cl_remaining} (मैक्स 16)",
    )
  with col2:
    st.metric(
        "CPL (Compensatory)",
        f"खर्च: {cpl_taken}",
        f"शेष: {cpl_remaining} (कुल: {total_cpl_allocated})",
    )
  with col3:
    el_balance = 33 - el_taken
    st.metric(
        "EL (Earned Leave)", f"खर्च: {el_taken}", f"बैलेंस/कैरी-फॉरवर्ड: {el_balance}"
    )
  with col4:
    st.metric(
        "RH (Restricted)", f"खर्च: {rh_taken}", f"शेष: {rh_remaining} (मैक्स 2)"
    )

  st.markdown("---")
  st.subheader("📋 सभी लीव रिकॉर्ड्स (History)")

  if not df.empty:
    st.dataframe(df, use_container_width=True)

    # रिकॉर्ड हटाने का विकल्प
    st.markdown("### ⚙️ रिकॉर्ड प्रबंधित करें (Delete Record)")
    del_id = st.number_input(
        "हटाने के लिए रिकॉर्ड ID दर्ज करें", min_value=0, step=1
    )
    if st.button("चयनित रिकॉर्ड हटाएं"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v3.db")
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
