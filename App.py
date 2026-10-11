from datetime import datetime, date
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
  conn = sqlite3.connect("my_personal_leaves_v5.db")
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
  st.markdown("कैलेंडर और नियम आधारित स्मार्ट लीव डैशबोर्ड")

  # --- साइडबार: ओपनिंग बैलेंस / कोटा सेट करने के लिए ---
  st.sidebar.header("⚙️ लीव कोटा सेटिंग्स")
  total_cpl_allocated = st.sidebar.number_input(
      "इस साल कुल मान्य CPL (Total Applicable CPL)",
      min_value=0,
      max_value=50,
      value=0,
      step=1,
  )

  st.sidebar.markdown("---")
  st.sidebar.header("➕ नई छुट्टी जोड़ें (Apply Leave)")

  # डेटा फेच करना
  conn = sqlite3.connect("my_personal_leaves_v5.db")
  df = pd.read_sql_query("SELECT * FROM my_leaves ORDER BY id DESC", conn)
  conn.close()

  # अब तक ली गई कुल छुट्टियाँ निकालना
  cl_taken = (
      df[df["leave_type"] == "CL"]["days_count"].sum() if not df.empty else 0
  )
  cpl_taken = (
      df[df["leave_type"] == "CPL"]["days_count"].sum() if not df.empty else 0
  )
  el_taken = (
      df[df["leave_type"] == "EL"]["days_count"].sum() if not df.empty else 0
  )

  # RH records check
  rh_df = df[df["leave_type"] == "RH"] if not df.empty else pd.DataFrame()
  rh_taken = rh_df["days_count"].sum() if not rh_df.empty else 0
  already_taken_rh_dates = (
      rh_df["leave_date"].tolist() if not rh_df.empty else []
  )

  # वर्तमान शेष बैलेंस
  cl_remaining = 16 - cl_taken
  cpl_remaining = total_cpl_allocated - cpl_taken
  rh_remaining = 2 - rh_taken

  # आज की तारीख (Current Date)
  today_date = date.today()

  # डायनेमिक RH लिस्ट फ़िल्टर करना:
  # 1. जो तारीखें निकल चुकी हैं या आज से पहले की हैं, उन्हें हटाएँ।
  # 2. जो RH पहले ही ली जा चुकी हैं, उन्हें हटाएँ।
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

    # अगर RH चुना गया है तो सिर्फ आज और उसके बाद की ऑफिशियल लिस्ट दिखेगी
    if leave_category == "RH":
      if rh_remaining <= 0:
        st.warning("⚠️ आपने इस साल की दोनों (2) RH पहले ही पूरी कर ली हैं!")
        selected_rh_key = None
        leave_date = today_date
      elif not available_rh_options:
        st.info(
            "आज या इसके बाद के लिए कोई भी आगामी Restricted Holiday उपलब्ध नहीं"
            " है।"
        )
        selected_rh_key = None
        leave_date = today_date
      else:
        selected_rh_key = st.selectbox(
            "आज या इसके बाद की वैध RH चुनें:",
            list(available_rh_options.keys()),
        )
        leave_date = (
            datetime.strptime(
                available_rh_options[selected_rh_key], "%Y-%m-%d"
            ).date()
            if selected_rh_key
            else today_date
        )
    else:
      leave_date = st.date_input("छुट्टी की तारीख (Date)")

    # दिनों की संख्या (Integers only) - RH के लिए ऑटोमैटिक 1 दिन रहेगा, बिना किसी फालतू मैसेज के
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

      if leave_category == "CL":
        if days_count > cl_remaining:
          error_msg = (
              f"❌ त्रुटि: आपके पास केवल {cl_remaining} CL बची है! इससे ज़्यादा"
              " अनुमति नहीं है।"
          )
      elif leave_category == "CPL":
        if days_count > cpl_remaining:
          error_msg = (
              f"❌ त्रुटि: आपके पास केवल {cpl_remaining} CPL बची है!"
          )
      elif leave_category == "RH":
        if rh_remaining <= 0:
          error_msg = "❌ त्रुटि: आप साल भर में अधिकतम केवल 2 ही RH ले सकते हैं!"
        elif not selected_rh_key:
          error_msg = "❌ कृपया मान्य RH चुनें।"

      if error_msg:
        st.sidebar.error(error_msg)
      else:
        conn = sqlite3.connect("my_personal_leaves_v5.db")
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
        conn.commit()
        conn.close()
        st.sidebar.success("✅ आपकी छुट्टी का रिकॉर्ड सफलतापर्वक दर्ज हो गया!")
        st.rerun()

  # --- डैशबोर्ड और डिटेल्ड समरी ---
  st.subheader("📊 वार्षिक लीव बैलेंस और स्थिति (Leave Quota Summary)")
  col1, col2, col3, col4 = st.columns(4)

  with col1:
    st.metric(
        "CL (Casual Leave)",
        f"खर्च: {cl_taken} दिन",
        f"शेष: {cl_remaining} दिन (मैक्स 16)",
    )
  with col2:
    st.metric(
        "CPL (Compensatory)",
        f"खर्च: {cpl_taken} दिन",
        f"शेष: {cpl_remaining} दिन (कुल: {total_cpl_allocated})",
    )
  with col3:
    el_balance = 33 - el_taken
    st.metric(
        "EL (Earned Leave)",
        f"खर्च: {el_taken} दिन",
        f"बैलेंस/कैरी-फॉरवर्ड: {el_balance} दिन",
    )
  with col4:
    st.metric(
        "RH (Restricted)",
        f"खर्च: {rh_taken} दिन",
        f"शेष: {rh_remaining} दिन (मैक्स 2)",
    )

  # --- फुल डिटेल समरी बॉक्स ---
  st.markdown("---")
  st.info(
      f"📌 **विस्तृत विवरण (Full Detail Summary - 2026):**\n"
      f"- इस कलैंडर वर्ष में अब तक आपने कुल **{cl_taken} दिन** Casual Leave (CL) का उपयोग किया है।\n"
      f"- कुल **{cpl_taken} दिन** Compensatory Leave (CPL) खर्च की गई है।\n"
      f"- कुल **{el_taken} दिन** Earned Leave (EL) ली गई है।\n"
      f"- कुल **{rh_taken} दिन** Restricted Holiday (RH) अवमुक्त की गई है।"
  )

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
        conn = sqlite3.connect("my_personal_leaves_v5.db")
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
