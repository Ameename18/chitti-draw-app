import streamlit as st
import random
import time
import base64
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Chitti Draw", layout="centered")

ADMIN_PIN = "1818"

# ================= GOOGLE CONNECTION =================

def connect_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )

    client = gspread.authorize(creds)
    return client.open("The Good Future Project – Chitti Database")

# Handle potential connection errors
try:
    sheet = connect_google_sheets()
    members_sheet = sheet.worksheet("Members")
    winners_sheet = sheet.worksheet("Winners")
    payments_sheet = sheet.worksheet("Payments")
    connection_success = True
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {str(e)}")
    connection_success = False
    members_sheet = None
    winners_sheet = None
    payments_sheet = None

st.title("🎡 The Good Future Project – Chitti Draw")

# ================= LOAD MEMBERS =================

all_members = []
if connection_success and members_sheet:
    try:
        members_data = members_sheet.get_all_records()
        all_members = [
            row["Name"]
            for row in members_data
            if str(row.get("Active", "")).upper() == "TRUE"
        ]
    except Exception as e:
        st.error(f"Error loading members: {str(e)}")
        all_members = []
else:
    all_members = [
        "Aaron Roy", "Aashna Saifudeen", "Abhijith MR", "Ameen O",
        "Dishna D", "DV Kaamya", "Nawal Fathima", "Nishad S",
        "Rinshad TP", "Sreevidya Valsan"
    ]
    st.warning("Using fallback member list (Google Sheets connection failed)")

# ================= LOAD WINNERS =================

def get_previous_winners():
    if connection_success and winners_sheet:
        try:
            winners_data = winners_sheet.get_all_records()
            return [row["Winner"] for row in winners_data]
        except:
            return []
    return []

previous_winners = get_previous_winners()

# ================= LOAD PAYMENTS =================

payments = {}
if connection_success and payments_sheet:
    try:
        payments_data = payments_sheet.get_all_records()
        for row in payments_data:
            month = row["Month"]
            member = row["Member"]
            
            if month not in payments:
                payments[month] = {}
            
            payments[month][member] = {
                "paid": row["Paid"] == "TRUE",
                "date": row.get("Payment Date", ""),
                "amount": float(row.get("Amount", 0))
            }
    except Exception as e:
        st.warning(f"Could not load payments: {str(e)}")

# ================= WIN SOUND =================

def load_audio(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

win_audio = load_audio("win.mp3")

# ================= FIXED AMOUNTS =================

WINNING_AMOUNT = 50000
EMI_AMOUNT = 5000

# ================= ADMIN LOGIN =================

st.subheader("🔒 Admin Access")
entered_pin = st.text_input("Enter Admin PIN", type="password")
is_admin = entered_pin == ADMIN_PIN

# ================= DRAW MONTH SELECTION =================

st.subheader("📅 Draw Month Selection")
draw_date = st.date_input("Select Draw Month", datetime.now(), key="draw_month")
selected_month = draw_date.strftime("%b-%Y")

# Initialize month if not exists in payments dict
if selected_month not in payments and connection_success:
    payments[selected_month] = {}
    for member in all_members:
        payments[selected_month][member] = {
            "paid": False,
            "date": "",
            "amount": 0
        }

# ================= REFRESH WINNERS LIST =================

previous_winners = get_previous_winners()

# ================= PARTICIPATION =================

st.subheader("👥 Select Participating Members")

eligible_members = [m for m in all_members if m not in previous_winners]

if not eligible_members:
    st.warning("⚠️ All members have won already! No eligible participants.")
    participants = []
else:
    participants = st.multiselect(
        "Select members participating this month",
        eligible_members,
        default=eligible_members
    )

st.caption(f"📊 {len(eligible_members)} members eligible (previous winners excluded)")

# ================= DISPLAY FIXED AMOUNTS =================

st.markdown(f"""
<div style='display: flex; justify-content: center; gap: 30px; margin: 20px 0;'>
    <div style='background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%); padding: 15px 30px; border-radius: 15px; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.2);'>
        <h3 style='color: white; margin: 0; font-size: 18px;'>🏆 WINNING PRIZE 🏆</h3>
        <p style='color: white; margin: 5px 0 0 0; font-size: 32px; font-weight: bold;'>₹{WINNING_AMOUNT:,}</p>
    </div>
    <div style='background: linear-gradient(135deg, #4ECDC4 0%, #45B7AF 100%); padding: 15px 30px; border-radius: 15px; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.2);'>
        <h3 style='color: white; margin: 0; font-size: 18px;'>💰 MONTHLY EMI 💰</h3>
        <p style='color: white; margin: 5px 0 0 0; font-size: 32px; font-weight: bold;'>₹{EMI_AMOUNT:,}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= ROULETTE STYLE SPIN =================

if st.button("🎰 SPIN THE ROULETTE", use_container_width=True):
    
    if not is_admin:
        st.error("❌ Admin PIN required")
    elif len(participants) < 2:
        st.warning("⚠️ Please select at least 2 participants")
    else:
        winner = random.choice(participants)
        
        # Create roulette display
        roulette_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        # 30 SECOND TOTAL ANIMATION
        total_fast = 40      # 40 frames × 0.15 = 6 seconds
        total_medium = 40    # 40 frames × 0.3 = 12 seconds  
        total_slow = 40      # 40 frames × 0.3 = 12 seconds
        total_frames = total_fast + total_medium + total_slow  # = 120 frames total = 30 seconds
        
        # FAST SPIN - Quick scrolling
        for i in range(total_fast):
            start_idx = i % len(participants)
            scrolling_names = participants[start_idx:] + participants[:start_idx]
            
            names_html = ""
            for j, name in enumerate(scrolling_names[:5]):
                opacity = 1.0 - (j * 0.2)
                size = 48 - (j * 8)
                if j == 2:  # Center position (highlighted)
                    names_html += f"<div style='background: gold; padding: 15px; margin: 5px; border-radius: 10px; box-shadow: 0 0 15px gold;'><span style='font-size: {size}px; color: #333; font-weight: bold;'>👉 {name} 👈</span></div>"
                else:
                    names_html += f"<div style='background: rgba(255,255,255,{opacity}); padding: 10px; margin: 5px; border-radius: 10px;'><span style='font-size: {size-10}px; color: #666;'>{name}</span></div>"
            
            roulette_placeholder.markdown(f"""
            <div style='text-align: center; background: linear-gradient(135deg, #5433FF 0%, #20BDFF 100%); padding: 30px; border-radius: 30px; margin: 20px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
                <h2 style='color: white; margin-bottom: 20px; font-size: 36px;'>🎰 ROULETTE SPINNING... 🎰</h2>
                <div style='display: inline-block; background: #222; padding: 20px 40px; border-radius: 50px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);'>
                    {names_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar.progress((i + 1) / total_frames)
            time.sleep(0.15)  # 0.15 sec per frame = 6 seconds
        
        # MEDIUM SPIN - Slow down
        for i in range(total_medium):
            start_idx = (total_fast + i) % len(participants)
            scrolling_names = participants[start_idx:] + participants[:start_idx]
            
            names_html = ""
            for j, name in enumerate(scrolling_names[:5]):
                if j == 2:
                    names_html += f"<div style='background: gold; padding: 18px; margin: 5px; border-radius: 12px; box-shadow: 0 0 20px gold;'><span style='font-size: 52px; color: #333; font-weight: bold;'>👉 {name} 👈</span></div>"
                else:
                    names_html += f"<div style='background: rgba(255,255,255,0.4); padding: 12px; margin: 5px; border-radius: 10px;'><span style='font-size: 40px; color: #aaa;'>{name}</span></div>"
            
            roulette_placeholder.markdown(f"""
            <div style='text-align: center; background: linear-gradient(135deg, #5433FF 0%, #20BDFF 100%); padding: 30px; border-radius: 30px; margin: 20px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
                <h2 style='color: white; margin-bottom: 20px; font-size: 36px;'>🎯 SLOWING DOWN... 🎯</h2>
                <div style='display: inline-block; background: #222; padding: 20px 40px; border-radius: 50px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);'>
                    {names_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar.progress((total_fast + i + 1) / total_frames)
            time.sleep(0.3)  # 0.3 sec per frame = 12 seconds
        
        # FINAL SLOW SPIN - Build curiosity (longest phase)
        for i in range(total_slow):
            start_idx = (total_fast + total_medium + i) % len(participants)
            scrolling_names = participants[start_idx:] + participants[:start_idx]
            
            names_html = ""
            for j, name in enumerate(scrolling_names[:5]):
                if j == 2:
                    names_html += f"<div style='background: gold; padding: 22px; margin: 5px; border-radius: 18px; box-shadow: 0 0 40px gold;'><span style='font-size: 60px; color: #333; font-weight: bold;'>👉 {name} 👈</span></div>"
                else:
                    names_html += f"<div style='background: rgba(255,255,255,0.6); padding: 18px; margin: 5px; border-radius: 14px;'><span style='font-size: 48px; color: #ccc;'>{name}</span></div>"
            
            # Change messages to build curiosity
            messages = ["🤔 WHO WILL WIN?", "⏳ ALMOST THERE...", "🎯 GETTING CLOSER...", "💭 THINKING...", "✨ SOON..."]
            message = messages[i % len(messages)]
            
            roulette_placeholder.markdown(f"""
            <div style='text-align: center; background: linear-gradient(135deg, #5433FF 0%, #20BDFF 100%); padding: 30px; border-radius: 30px; margin: 20px 0; animation: pulse 0.5s; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
                <h2 style='color: white; margin-bottom: 20px; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>{message}</h2>
                <div style='display: inline-block; background: #222; padding: 20px 40px; border-radius: 50px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);'>
                    {names_html}
                </div>
            </div>
            <style>
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.03); }}
                }}
            </style>
            """, unsafe_allow_html=True)
            
            progress_bar.progress((total_fast + total_medium + i + 1) / total_frames)
            time.sleep(0.3)  # 0.3 sec per frame = 12 seconds
        
        progress_bar.empty()
        roulette_placeholder.empty()
        
        # Save winner to Google Sheets
        if connection_success and winners_sheet:
            try:
                winners_sheet.append_row([
                    selected_month,
                    winner,
                    WINNING_AMOUNT,
                    datetime.now().strftime("%d-%b-%Y %H:%M")
                ])
                st.success("✅ Winner saved to database")
            except Exception as e:
                st.error(f"❌ Failed to save winner: {str(e)}")
        
        # Play sound
        if win_audio:
            st.components.v1.html(f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{win_audio}" type="audio/mp3">
                </audio>
            """, height=0)
        
        # GRAND WINNER REVEAL
        st.balloons()
        st.markdown(f"""
        <div style='text-align: center; padding: 60px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 40px; margin: 30px 0; animation: winReveal 0.8s; box-shadow: 0 20px 50px rgba(0,0,0,0.4); border: 4px solid white;'>
            <div style='font-size: 100px; margin-bottom: 20px; animation: bounce 1s infinite;'>🏆💰🏆</div>
            <h1 style='color: white; font-size: 90px; margin: 0; text-shadow: 4px 4px 8px rgba(0,0,0,0.4); background: rgba(0,0,0,0.2); padding: 20px 50px; border-radius: 70px; display: inline-block;'>{winner}</h1>
            <div style='margin: 30px 0;'>
                <div style='background: white; padding: 25px 60px; border-radius: 30px; display: inline-block; box-shadow: 0 15px 30px rgba(0,0,0,0.3);'>
                    <p style='color: #333; margin: 0; font-size: 36px;'>WINS</p>
                    <p style='color: #FF6B6B; margin: 15px 0; font-size: 90px; font-weight: bold; text-shadow: 3px 3px 6px rgba(0,0,0,0.2);'>₹{WINNING_AMOUNT:,}</p>
                    <p style='color: #333; margin: 0; font-size: 32px;'>GRAND PRIZE!</p>
                </div>
            </div>
            <p style='color: white; font-size: 48px; margin: 20px 0 0 0; font-weight: bold;'>🎊 CONGRATULATIONS! 🎊</p>
        </div>
        <style>
            @keyframes winReveal {{
                0% {{ transform: scale(0.3) rotate(-10deg); opacity: 0; }}
                60% {{ transform: scale(1.1) rotate(5deg); }}
                100% {{ transform: scale(1) rotate(0); opacity: 1; }}
            }}
            @keyframes bounce {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-30px); }}
            }}
        </style>
        """, unsafe_allow_html=True)
        
        # Force rerun to update winners list
        time.sleep(3)
        st.rerun()

# ================= WINNER TABLE =================

st.subheader("📋 Previous Winners")

if connection_success and winners_sheet:
    try:
        updated_winners = winners_sheet.get_all_records()
        if updated_winners:
            df_winners = pd.DataFrame(updated_winners)
            st.dataframe(df_winners, use_container_width=True)
            st.caption(f"🏆 Total Winners: {len(updated_winners)}")
        else:
            st.info("No winners recorded yet")
    except Exception as e:
        st.error(f"Could not load winners: {str(e)}")
else:
    if previous_winners:
        sample_df = pd.DataFrame({
            "Month": [selected_month] * len(previous_winners[:5]),
            "Winner": previous_winners[:5],
            "Amount": [WINNING_AMOUNT] * len(previous_winners[:5]),
            "Date": [datetime.now().strftime("%d-%b-%Y %H:%M")] * len(previous_winners[:5])
        })
        st.dataframe(sample_df, use_container_width=True)
        st.info("Showing sample data (Google Sheets disconnected)")

# ================= PAYMENT TRACKER =================

st.subheader("💰 Monthly Payment Tracker (EMI: ₹5,000)")

payment_view_date = st.date_input("Select Month to View Payments", datetime.now(), key="payment_view")
payment_view_month = payment_view_date.strftime("%b-%Y")

if connection_success and payments_sheet:
    try:
        payments_data = payments_sheet.get_all_records()
        month_records = [row for row in payments_data if row.get("Month", "") == payment_view_month]
        
        payment_table = []
        total_collected = 0
        
        for member in all_members:
            member_record = next((row for row in month_records if row.get("Member", "") == member), None)
            
            if member_record:
                paid_status = member_record.get("Paid", "") == "TRUE"
                payment_date = member_record.get("Payment Date", "")
            else:
                paid_status = False
                payment_date = ""
            
            if paid_status:
                total_collected += EMI_AMOUNT
            
            payment_table.append({
                "Month": payment_view_month,
                "Member": member,
                "Status": "✅ PAID" if paid_status else "❌ NOT PAID",
                "Payment Date": payment_date if payment_date else "-",
                "Amount": f"₹{EMI_AMOUNT:,}" if paid_status else "₹0"
            })
        
        if payment_table:
            df_payments = pd.DataFrame(payment_table)
            st.dataframe(df_payments, use_container_width=True)
            
            paid_count = sum(1 for row in payment_table if "✅" in row["Status"])
            total_members = len(payment_table)
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; margin-top: 10px;'>
                <div style='display: flex; justify-content: space-around; color: white;'>
                    <div style='text-align: center;'>
                        <p style='margin: 0; font-size: 16px;'>✅ Paid</p>
                        <p style='margin: 5px 0 0 0; font-size: 24px; font-weight: bold;'>{paid_count}/{total_members}</p>
                    </div>
                    <div style='text-align: center;'>
                        <p style='margin: 0; font-size: 16px;'>📊 Rate</p>
                        <p style='margin: 5px 0 0 0; font-size: 24px; font-weight: bold;'>{paid_count/total_members*100:.1f}%</p>
                    </div>
                    <div style='text-align: center;'>
                        <p style='margin: 0; font-size: 16px;'>💰 Total</p>
                        <p style='margin: 5px 0 0 0; font-size: 24px; font-weight: bold;'>₹{total_collected:,}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"No payment records for {payment_view_month}")
            
    except Exception as e:
        st.error(f"Could not load payments: {str(e)}")
else:
    st.info("Payment tracking requires Google Sheets connection")

# ================= ADMIN PAYMENT CONTROLS =================

if is_admin and connection_success:
    
    st.markdown("---")
    st.markdown("### 🔒 Admin Payment Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        admin_month = st.date_input("Payment Month", datetime.now(), key="admin_month")
        admin_month_str = admin_month.strftime("%b-%Y")
    
    with col2:
        selected_member = st.selectbox("Select Member", all_members, key="admin_member")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("✅ Mark as Paid (₹5,000)"):
            try:
                payments_sheet.append_row([
                    admin_month_str,
                    selected_member,
                    "TRUE",
                    datetime.now().strftime("%d-%b-%Y %H:%M"),
                    EMI_AMOUNT
                ])
                st.success(f"✅ {selected_member} marked Paid")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update: {str(e)}")
    
    with col4:
        if st.button("❌ Mark as Unpaid"):
            try:
                payments_sheet.append_row([
                    admin_month_str,
                    selected_member,
                    "FALSE",
                    "",
                    0
                ])
                st.warning(f"❌ {selected_member} marked Unpaid")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update: {str(e)}")
    
    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    
    col5, col6 = st.columns(2)
    
    with col5:
        reset_draw = st.checkbox("Confirm reset draw history")
        if reset_draw and st.button("🗑️ Reset Draw History"):
            try:
                winners_sheet.clear()
                winners_sheet.append_row(["Month", "Winner", "Amount", "Date"])
                st.success("✅ Draw history cleared")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reset: {str(e)}")
    
    with col6:
        reset_payment = st.checkbox("Confirm reset payment records")
        if reset_payment and st.button("💸 Reset Payment Records"):
            try:
                payments_sheet.clear()
                payments_sheet.append_row(["Month", "Member", "Paid", "Payment Date", "Amount"])
                st.success("✅ Payment records cleared")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reset: {str(e)}")

elif is_admin and not connection_success:
    st.warning("⚠️ Admin controls disabled - Google Sheets not connected")