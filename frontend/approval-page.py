import streamlit as st
from datetime import datetime

st.markdown("""
<style>
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="RiskLens AI Approvals", layout="wide")

st.markdown("""
<style>
body {
    background: linear-gradient(to right, #f0f4f8, #d9e2ec);
}
.navbar {
    background: linear-gradient(90deg, #0FB5A8, #056D63);
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    color: white;
    margin-bottom: 25px;
}
.card {
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
}
.high-priority {
    background: linear-gradient(135deg, #ffcccc, #ff6666);
}
.pending {
    background: linear-gradient(135deg, #ccf2ff, #66c2ff);
}
.button {
    background-color: #056D63;
    color: white;
    padding: 5px 10px;
    border: none;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="navbar">RiskLens AI - Approvals Dashboard</div>', unsafe_allow_html=True)

# Sorting option
sort_by = st.selectbox("Sort approvals by:", ["Risk Score (high → low)", "Last Submission (recent → old)"])

# Mocked data: to be replaced with API call from backend
approvals = [
    {"case_id": "RL-2025-0045", "vendor": "ABCD Logistics", "risk_score": 72,
     "assigned_to": "alice@company.com", "status": "Awaiting Approval", "last_submission": "2025-11-07 14:20"},
    {"case_id": "RL-2025-0046", "vendor": "Dart Transport", "risk_score": 35,
     "assigned_to": "bob@company.com", "status": "Awaiting Approval", "last_submission": "2025-11-06 09:15"},
    {"case_id": "RL-2025-0047", "vendor": "Gamma Supplies", "risk_score": 18,
     "assigned_to": "charlie@company.com", "status": "Approved", "last_submission": "2025-11-05 11:00"},
     {"case_id": "RL-2025-0048", "vendor": "HackUTD Logistics", "risk_score": 78,
     "assigned_to": "charlie@company.com", "status": "Awaiting Approval", "last_submission": "2025-11-07 11:00"},
     {"case_id": "RL-2025-0049", "vendor": "Hexa Logistics", "risk_score": 62,
     "assigned_to": "charlie@company.com", "status": "Awaiting Approval", "last_submission": "2025-11-05 13:00"}
]

for a in approvals:
    a["last_submission_dt"] = datetime.strptime(a["last_submission"], "%Y-%m-%d %H:%M")

high_priority = [a for a in approvals if a["risk_score"] >= 60]

pending = [a for a in approvals if a not in high_priority]


if sort_by == "Risk Score (high → low)":
    approvals_sorted = sorted(pending, key=lambda x: x["risk_score"], reverse=True)
else:
    approvals_sorted = sorted(pending, key=lambda x: x["last_submission_dt"], reverse=True)



def display_cards(data, high_priority=False):
    cols_per_row = 3
    for i in range(0, len(data), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, approval in enumerate(data[i:i+cols_per_row]):
            col = cols[idx]
            card_class = "high-priority" if high_priority else "pending"
            col.markdown(
                f"""
                <div class="card {card_class}">
                    <h4>{approval['vendor']}</h4>
                    <p><b>Case ID:</b> {approval['case_id']}</p>
                    <p><b>Risk Score:</b> {approval['risk_score']}</p>
                    <p><b>Last Submission:</b> {approval['last_submission']}</p>
                    <p><b>Assigned To:</b> {approval['assigned_to']}</p>
                    <p><b>Status:</b> {approval['status']}</p>
                    <button class="button">View Details</button>
                </div>
                """, unsafe_allow_html=True
            )

if high_priority:
    st.subheader("High Priority Approvals")
    display_cards(high_priority, high_priority=True)

if pending:
    st.subheader("Pending Approvals")
    display_cards(pending, high_priority=False)
