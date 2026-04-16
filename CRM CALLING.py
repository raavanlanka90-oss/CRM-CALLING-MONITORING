import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -------------------------
# CONFIG
# -------------------------
SHEET_ID = "1jwfAPG4e59_mIwDIpxoaXQ_blgxCsdEUsA9oW7yeJFQ"
DS_SHEET = "DS"
STORE_SHEET = "STORE"

st.set_page_config(layout="wide")

# -------------------------
# GOOGLE CONNECTION
# -------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID)
ds = sheet.worksheet(DS_SHEET)
store = sheet.worksheet(STORE_SHEET)

# -------------------------
# LOAD DATA
# -------------------------
data = ds.get_all_records()
df = pd.DataFrame(data)

# -------------------------
# FILTER (REMOVE BLANKS)
# -------------------------
df = df[
    (df["DUE DATE"] != "") &
    (df["BILL NUMBER"] != "")
]

# -------------------------
# DATE CONVERSION
# -------------------------
df["CALLING AFTER +10 DAYS"] = pd.to_datetime(df["CALLING AFTER +10 DAYS"], errors='coerce')
df["CALLING AFTER +20 DAYS"] = pd.to_datetime(df["CALLING AFTER +20 DAYS"], errors='coerce')

today = pd.to_datetime("today").normalize()

# -------------------------
# FILTER UI
# -------------------------
st.title("📞 CALL TRACKING SYSTEM")

st.subheader("🔍 Filters")

colf1, colf2, colf3 = st.columns(3)

with colf1:
    party_filter = st.selectbox(
        "PARTY NAME",
        [""] + sorted(df["PARTY NAME"].dropna().unique())
    )

with colf2:
    agent_filter = st.selectbox(
        "AGENT NAME",
        [""] + sorted(df["AGENT NAME"].dropna().unique())
    )

with colf3:
    bill_filter = st.selectbox(
        "BILL NUMBER",
        [""] + sorted(df["BILL NUMBER"].dropna().unique())
    )

# Apply filters
if party_filter:
    df = df[df["PARTY NAME"] == party_filter]

if agent_filter:
    df = df[df["AGENT NAME"] == agent_filter]

if bill_filter:
    df = df[df["BILL NUMBER"] == bill_filter]

# -------------------------
# SESSION STATE
# -------------------------
if "done_rows" not in st.session_state:
    st.session_state.done_rows = set()

# -------------------------
# GET EXISTING STORE DATA (FOR DUPLICATE CHECK)
# -------------------------
existing_data = store.get_all_values()
existing_bills = [row[4] for row in existing_data if len(row) > 4]

# -------------------------
# DISPLAY TABLE
# -------------------------
for i, row in df.iterrows():

    # -------------------------
    # CONDITIONAL COLOR
    # -------------------------
    color = ""

    if pd.notna(row["CALLING AFTER +10 DAYS"]) and row["CALLING AFTER +10 DAYS"] >= today:
        color = "#f4c2c2"

    if pd.notna(row["CALLING AFTER +20 DAYS"]) and row["CALLING AFTER +20 DAYS"] >= today:
        color = "#f4c2c2"

    st.markdown(
        f'<div style="background-color:{color}; padding:10px; border-radius:10px;">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([5, 3, 2])

    # -------------------------
    # DATA DISPLAY
    # -------------------------
    with col1:
        st.write(f"**PARTY:** {row['PARTY NAME']}")
        st.write(f"**AGENT:** {row['AGENT NAME']}")
        st.write(f"**AMOUNT:** {row['OUTSTANDING AMOUNT']}")
        st.write(f"**DUE DATE:** {row['DUE DATE']}")
        st.write(f"**BILL NO:** {row['BILL NUMBER']}")

    # -------------------------
    # REMARK INPUT
    # -------------------------
    with col2:
        remark = st.text_input(
            "REMARK",
            key=f"remark_{i}"
        )

    # -------------------------
    # BUTTON
    # -------------------------
    with col3:

        if row["BILL NUMBER"] in existing_bills or i in st.session_state.done_rows:
            st.success("✔ DONE")
        else:
            if st.button("CALL DONE", key=f"btn_{i}"):

                if row["BILL NUMBER"] in existing_bills:
                    st.warning("Already stored!")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    new_row = [
                        row["PARTY NAME"],          # A
                        row["AGENT NAME"],          # B
                        row["OUTSTANDING AMOUNT"],  # C
                        row["DUE DATE"],            # D
                        row["BILL NUMBER"],         # E
                        row["CALLING AFTER +10 DAYS"], # F
                        row["CALLING AFTER +20 DAYS"], # G
                        timestamp,                  # H
                        remark                      # I
                    ]

                    store.append_row(new_row)

                    st.session_state.done_rows.add(i)
                    st.success("Stored Successfully ✅")

    st.markdown("</div>", unsafe_allow_html=True)