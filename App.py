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
  conn = sqlite3.connect("my_personal_leaves_v7.db")
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
  st.markdown("कैलेंडर और सख्त नियम आधारित स्मार्ट लीव डैशबोर्ड")

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
  conn = sqlite3.connect("my_personal_leaves_v7.db")
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

  # डायनेमिक RH लिस्ट फ़िल्टर करना
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
        st.warning("⚠️ Aapne is saal ki dono (2) RH pehle hi poori kar li hain!")
        selected_rh_key = None
        leave_date = today_date
      elif not available_rh_options:
        st.info("Aaj ya iske baad ke liye koi bhi RH uplabdh nahi hai.")
        selected_rh_key = None
        leave_date = today_date
      else:
        selected_rh_key = st.selectbox(
            "Aaj ya iske baad ki vaidya RH chunein:",
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
      leave_date = st.date_input("Chhutti ki tarikh (Date)")

    if leave_category == "RH":
      days_count = 1
    else:
      days_count = st.number_input(
          "Dino ki sankhya (Full Days)",
          min_value=1,
          max_value=30,
          value=1,
          step=1,
      )

    reason = st.text_area("Vajah / Tippani (Optional)")
    submit = st.form_submit_button("Record Save Karein")

    if submit:
      error_msg = None

      # Strict Balance Validation Checks
      if leave_category == "CL":
        if days_count > cl_remaining:
          error_msg = f"❌ Error: Aapke paas kewal {cl_remaining} CL bachi hai! Isse zyada ki entry nahi ho sakti."
      elif leave_category == "CPL":
        if days_count > cpl_remaining:
          error_msg = f"❌ Error: Aapke paas kewal {cpl_remaining} CPL bachi hai! Kripya sahi sankhya darj karein."
      elif leave_category == "RH":
        if rh_remaining <= 0:
          error_msg = "❌ Error: Aap saal bhar me adhiktam kewal 2 hi RH le sakte hain!"
        elif not selected_rh_key:
          error_msg = "❌ Kripya manya RH chunein."

      if error_msg:
        st.sidebar.error(error_msg)
      else:
        conn = sqlite3.connect("my_personal_leaves_v7.db")
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
        st.sidebar.success(
            "✅ Aapki chhutti ka record safaltapoorvak darj ho gaya!"
        )
        st.rerun()

  # --- मुख्य होम पेज पर हमेशा दिखने वाला लाइव बैलेंस (Always Visible Summary Header) ---
  st.markdown("### 🟢 Aapka Vartaman Leave Balance (Live Status)")
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

  # --- डैशबोर्ड और डिटेल्ड समरी मेट्रिक्स ---
  st.subheader("📊 Varshik Leave Balance aur Sthiti (Leave Quota Summary)")
  col1, col2, col3, col4 = st.columns(4)

  with col1:
    st.metric(
        "CL (Casual Leave)",
        f"Kharch: {cl_taken} din",
        f"Shesh: {cl_remaining} din (Max 16)",
    )
  with col2:
    st.metric(
        "CPL (Compensatory)",
        f"Kharch: {cpl_taken} din",
        f"Shesh: {cpl_remaining} din (Kul: {total_cpl_allocated})",
    )
  with col3:
    st.metric(
        "EL (Earned Leave)",
        f"Kharch: {el_taken} din",
        f"Balance/Carry-forward: {el_balance} din",
    )
  with col4:
    st.metric(
        "RH (Restricted)",
        f"Kharch: {rh_taken} din",
        f"Shesh: {rh_remaining} din (Max 2)",
    )

  # --- फुल डिटेल समरी बॉक्स ---
  st.markdown("---")
  st.info(
      f"📌 **Vistrit Vivaran (Full Detail Summary - 2026):**\n"
      f"- Is calendar varsh me ab tak aapne kul **{cl_taken} din** Casual Leave (CL) ka upyog kiya hai.\n"
      f"- Kul **{cpl_taken} din** Compensatory Leave (CPL) kharch ki gayi hai.\n"
      f"- Kul **{el_taken} din** Earned Leave (EL) li gayi hai.\n"
      f"- Kul **{rh_taken} din** Restricted Holiday (RH) avmukt ki gayi hai."
  )

  st.subheader("📋 Sabhi Leave Records (History)")

  if not df.empty:
    st.dataframe(df, use_container_width=True)

    # रिकॉर्ड हटाने का विकल्प
    st.markdown("### ⚙️ Record Prabandhit Karein (Delete Record)")
    del_id = st.number_input(
        "Hatane ke liye Record ID darj karein", min_value=0, step=1
    )
    if st.button("Chayanit Record Hatayein"):
      if del_id > 0:
        conn = sqlite3.connect("my_personal_leaves_v7.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM my_leaves WHERE id = ?", (del_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {del_id} ka record hata diya gaya hai!")
        st.rerun()
  else:
    st.info("Abhi tak koi record darj nahi kiya gaya hai.")


if __name__ == "__main__":
  main()
