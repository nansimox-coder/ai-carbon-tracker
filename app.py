import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
import plotly.express as px

st.set_page_config(
    page_title="Carbonly | AI Carbon Tracker",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# DEMO EMISSION FACTORS
# These are illustrative starter values for a classroom prototype.
# Replace with properly sourced, Thailand-appropriate factors before
# presenting results as factual or using the app for real reporting.
# -------------------------------------------------------------------
DEFAULT_FACTORS = {
    "ไฟฟ้า (kg CO₂e/kWh)": 0.50,
    "รถยนต์ (kg CO₂e/km)": 0.18,
    "มอเตอร์ไซค์ (kg CO₂e/km)": 0.07,
    "รถโดยสาร (kg CO₂e/km)": 0.08,
    "รถไฟ/รถไฟฟ้า (kg CO₂e/km)": 0.04,
    "เนื้อวัว (kg CO₂e/มื้อ)": 5.00,
    "เนื้อหมู (kg CO₂e/มื้อ)": 2.00,
    "ไก่ (kg CO₂e/มื้อ)": 1.50,
    "อาหารทะเล (kg CO₂e/มื้อ)": 2.00,
    "อาหารจากพืช (kg CO₂e/มื้อ)": 0.70,
}
DATA_FILE = Path("carbon_activity_log.csv")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'Prompt','Inter',sans-serif;}
.stApp {background:linear-gradient(180deg,#f5faf6 0%,#f8fafc 45%,#f8fafc 100%);}
.block-container {max-width:1240px;padding-top:2rem;padding-bottom:3rem;}
[data-testid="stSidebar"] {background:#102d24;}
[data-testid="stSidebar"] * {color:#f3faf5 !important;}
[data-testid="stMetric"] {background:white;border:1px solid #e7eee9;padding:16px 18px;border-radius:16px;box-shadow:0 4px 16px rgba(16,45,36,.04);}
[data-testid="stMetricLabel"] {color:#64756b;}
[data-testid="stMetricValue"] {color:#163d2d;}
div.stButton > button[kind="primary"], div.stFormSubmitButton > button {background:#16784b;color:white;border:0;border-radius:12px;font-weight:600;min-height:2.8rem;}
div.stButton > button {border-radius:12px;}
.hero {background:linear-gradient(115deg,#103d2d,#1d7950);padding:30px 32px;border-radius:22px;color:white;margin-bottom:22px;box-shadow:0 12px 30px rgba(16,61,45,.13);}
.hero h1 {font-size:2.25rem;font-weight:700;margin:0 0 8px 0;color:white;}
.hero p {font-size:1rem;color:#d7f3e2;margin:0;}
.eyebrow {font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:#a9e7bf;font-weight:600;margin-bottom:10px;}
.section-title {font-size:1.25rem;font-weight:600;color:#183b2c;margin:10px 0 4px;}
.muted {color:#6b7d72;font-size:.9rem;}
.tip-card {background:white;border:1px solid #e5eee8;border-radius:16px;padding:18px 20px;height:100%;}
.tip-tag {display:inline-block;background:#e7f6ed;color:#16784b;padding:4px 10px;border-radius:99px;font-size:.75rem;font-weight:600;margin-bottom:9px;}
div[data-testid="stAlert"] {border-radius:14px;}
</style>
""", unsafe_allow_html=True)

def load_data():
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                for c in ["travel_kg", "electricity_kg", "food_kg", "total_kg"]:
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
                return df.dropna(subset=["date"])
        except Exception:
            pass
    return pd.DataFrame(columns=[
        "date","transport","distance_km","travel_kg","electricity_kwh",
        "electricity_kg","food","meals","food_kg","total_kg","note"
    ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False, date_format="%Y-%m-%d")

def fmt(v):
    return f"{v:,.2f}"

if "records" not in st.session_state:
    st.session_state.records = load_data()

# Sidebar settings
with st.sidebar:
    st.markdown("## 🌿 Carbonly")
    st.caption("PERSONAL CARBON COMPANION")
    st.markdown("---")
    page = st.radio(
        "เมนูหลัก",
        ["ภาพรวม", "บันทึกกิจกรรม", "วิเคราะห์ & คำแนะนำ", "ประวัติข้อมูล"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### ⚙️ ตั้งค่าเป้าหมาย")
    weekly_goal = st.number_input("เป้าหมายต่อสัปดาห์ (kg CO₂e)", min_value=1.0, max_value=10000.0, value=50.0, step=5.0)
    st.markdown("---")
    st.caption("เวอร์ชันต้นแบบเพื่อการศึกษา")
    with st.expander("ดูค่าปัจจัยตัวอย่าง"):
        st.write("ค่าต่อไปนี้เป็นค่าเริ่มต้นสมมติสำหรับทดลอง สามารถแก้ไขได้ในโค้ด")
        for k, v in DEFAULT_FACTORS.items():
            st.write(f"**{k}** — {v}")

df = st.session_state.records.copy()
today = pd.Timestamp(date.today())
week_start = today - pd.Timedelta(days=today.weekday())
week_df = df[df["date"] >= week_start] if not df.empty else df
week_total = float(week_df["total_kg"].sum()) if not week_df.empty else 0.0
all_total = float(df["total_kg"].sum()) if not df.empty else 0.0
avg_day = float(df.groupby(df["date"].dt.date)["total_kg"].sum().mean()) if not df.empty else 0.0
goal_pct = min(week_total / weekly_goal * 100, 100) if weekly_goal else 0

# Header
st.markdown("""
<div class="hero">
  <div class="eyebrow">SUSTAINABLE LIVING, MADE SIMPLE</div>
  <h1>รู้จักคาร์บอนของเรา<br>เริ่มเปลี่ยนโลกได้ทุกวัน 🌱</h1>
  <p>บันทึกกิจกรรม • เข้าใจผลกระทบ • ค้นหาวิธีลด Carbon Footprint ในชีวิตประจำวัน</p>
</div>
""", unsafe_allow_html=True)

if page == "ภาพรวม":
    st.markdown('<div class="section-title">ภาพรวมของคุณ</div><div class="muted">สรุปจากกิจกรรมที่คุณบันทึกไว้</div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    a.metric("คาร์บอนสัปดาห์นี้", f"{fmt(week_total)} kg", help="รวมจากรายการที่บันทึกตั้งแต่วันจันทร์ของสัปดาห์นี้")
    b.metric("สะสมทั้งหมด", f"{fmt(all_total)} kg")
    c.metric("เฉลี่ยต่อวันบันทึก", f"{fmt(avg_day)} kg")
    d.metric("จำนวนรายการ", f"{len(df):,}")
    st.write("")
    left,right = st.columns([1.25,1])
    with left:
        st.markdown("#### 📈 แนวโน้มการปล่อยคาร์บอน")
        if not df.empty:
            daily = df.groupby(df["date"].dt.date)["total_kg"].sum().reset_index()
            daily.columns = ["วันที่","kg CO₂e"]
            fig = px.area(daily, x="วันที่", y="kg CO₂e", markers=True)
            fig.update_traces(line_color="#168653", fillcolor="rgba(22,134,83,.12)")
            fig.update_layout(height=310,margin=dict(l=5,r=5,t=20,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_family="Prompt")
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูล เริ่มจากเมนู “บันทึกกิจกรรม” เพื่อดูกราฟของคุณ")
    with right:
        st.markdown("#### 🎯 เป้าหมายรายสัปดาห์")
        st.metric("ใช้ไปแล้ว", f"{fmt(week_total)} / {fmt(weekly_goal)} kg")
        st.progress(int(goal_pct))
        if week_total <= weekly_goal:
            st.success(f"ยังอยู่ในเป้าหมาย เหลือพื้นที่อีก {fmt(max(weekly_goal-week_total,0))} kg CO₂e")
        else:
            st.warning("ยอดรวมสัปดาห์นี้สูงกว่าเป้าหมายที่ตั้งไว้ ลองดูคำแนะนำเพื่อหาจุดที่ปรับได้")
        st.markdown('<div class="tip-card"><span class="tip-tag">SMALL STEPS MATTER</span><br><b>เริ่มจากสิ่งที่ทำได้วันนี้</b><p class="muted">การบันทึกอย่างสม่ำเสมอช่วยให้เห็นรูปแบบการใช้ชีวิต และเลือกเปลี่ยนพฤติกรรมได้ตรงจุด</p></div>',unsafe_allow_html=True)
    st.markdown("#### 🧭 สัดส่วนการปล่อยตามหมวด")
    if not df.empty:
        cats = pd.DataFrame({"หมวด":["การเดินทาง","ไฟฟ้า","อาหาร"],"kg CO₂e":[df["travel_kg"].sum(),df["electricity_kg"].sum(),df["food_kg"].sum()]})
        fig2 = px.pie(cats, names="หมวด", values="kg CO₂e", hole=.62, color_discrete_sequence=["#16784b","#8ac9a5","#c5e7d2"])
        fig2.update_layout(height=300,margin=dict(l=5,r=5,t=5,b=5),paper_bgcolor="rgba(0,0,0,0)",font_family="Prompt",legend_title="")
        st.plotly_chart(fig2,use_container_width=True)
    else:
        st.caption("กราฟจะแสดงเมื่อมีการบันทึกกิจกรรม")

elif page == "บันทึกกิจกรรม":
    st.markdown("### ✍️ บันทึกกิจกรรมประจำวัน")
    st.markdown('<div class="muted">กรอกข้อมูลเท่าที่ทราบ ระบบจะคำนวณค่าประมาณให้โดยอัตโนมัติ</div>',unsafe_allow_html=True)
    with st.form("entry", clear_on_submit=True):
        activity_date = st.date_input("วันที่", value=date.today())
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### 🚗 การเดินทาง")
            transport = st.selectbox("วิธีเดินทาง",["รถยนต์","มอเตอร์ไซค์","รถโดยสาร","รถไฟ/รถไฟฟ้า","เดิน/จักรยาน","ไม่ได้เดินทาง"])
            distance = st.number_input("ระยะทาง (กิโลเมตร)",min_value=0.0,max_value=1000.0,value=0.0,step=1.0)
            st.markdown("#### ⚡ พลังงาน")
            electricity = st.number_input("ไฟฟ้าที่ใช้ (kWh)",min_value=0.0,max_value=10000.0,value=0.0,step=0.5,help="ดูหน่วย kWh จากมิเตอร์หรือบิลค่าไฟ หากไม่มีข้อมูลสามารถใส่ 0")
        with col2:
            st.markdown("#### 🍽️ อาหาร")
            food = st.selectbox("ประเภทอาหาร",["ไม่ระบุ","เนื้อวัว","เนื้อหมู","ไก่","อาหารทะเล","อาหารจากพืช"])
            meals = st.number_input("จำนวนมื้อ",min_value=0,max_value=20,value=0,step=1)
            st.markdown("#### 📝 บันทึกเพิ่มเติม")
            note = st.text_input("หมายเหตุ (ไม่บังคับ)",placeholder="เช่น เดินทางไปโรงเรียน")
        submit = st.form_submit_button("คำนวณและบันทึกกิจกรรม  →",type="primary",use_container_width=True)
    if submit:
        tf = {"รถยนต์":.18,"มอเตอร์ไซค์":.07,"รถโดยสาร":.08,"รถไฟ/รถไฟฟ้า":.04,"เดิน/จักรยาน":0,"ไม่ได้เดินทาง":0}
        ff = {"ไม่ระบุ":0,"เนื้อวัว":5.0,"เนื้อหมู":2.0,"ไก่":1.5,"อาหารทะเล":2.0,"อาหารจากพืช":.7}
        travel = distance*tf[transport]
        power = electricity*.50
        meal = meals*ff[food]
        total = travel+power+meal
        row = {"date":pd.Timestamp(activity_date),"transport":transport,"distance_km":distance,"travel_kg":travel,"electricity_kwh":electricity,"electricity_kg":power,"food":food,"meals":meals,"food_kg":meal,"total_kg":total,"note":note}
        st.session_state.records = pd.concat([st.session_state.records,pd.DataFrame([row])],ignore_index=True)
        save_data(st.session_state.records)
        st.success(f"บันทึกเรียบร้อย! ค่าประมาณของกิจกรรมนี้คือ {fmt(total)} kg CO₂e")
        x,y,z = st.columns(3)
        x.metric("การเดินทาง",f"{fmt(travel)} kg")
        y.metric("ไฟฟ้า",f"{fmt(power)} kg")
        z.metric("อาหาร",f"{fmt(meal)} kg")
    st.info("เคล็ดลับ: ถ้าไม่ทราบค่าไฟฟ้ารายวัน ให้เริ่มบันทึกหมวดเดินทางและอาหารก่อน แล้วค่อยเพิ่มข้อมูลไฟฟ้าเมื่อมีบิลหรือข้อมูลมิเตอร์")

elif page == "วิเคราะห์ & คำแนะนำ":
    st.markdown("### 💡 วิเคราะห์และคำแนะนำ")
    if df.empty:
        st.info("ยังไม่มีข้อมูล กรุณาบันทึกกิจกรรมก่อน")
    else:
        sums = {"การเดินทาง":float(df["travel_kg"].sum()),"ไฟฟ้า":float(df["electricity_kg"].sum()),"อาหาร":float(df["food_kg"].sum())}
        highest = max(sums,key=sums.get)
        advice = {
            "การเดินทาง":("🚲 ลองปรับการเดินทาง","รวมธุระให้อยู่ในเส้นทางเดียวกัน ใช้ขนส่งสาธารณะเมื่อสะดวก หรือเดิน/ปั่นจักรยานในระยะใกล้"),
            "ไฟฟ้า":("⚡ ใช้พลังงานอย่างรู้คุณค่า","ปิดไฟและอุปกรณ์เมื่อไม่ใช้งาน ตั้งเครื่องปรับอากาศในระดับที่เหมาะสม และติดตามหน่วยไฟจากบิล"),
            "อาหาร":("🥬 ลองเพิ่มมื้ออาหารจากพืช","วางแผนมื้ออาหาร ลดอาหารเหลือทิ้ง และลองเลือกเมนูจากพืชเพิ่มขึ้นตามความเหมาะสม")
        }
        st.markdown(f"จากข้อมูลที่บันทึก หมวดที่มีค่าประมาณสะสมสูงสุดคือ **{highest}** ({fmt(sums[highest])} kg CO₂e)")
        title,desc = advice[highest]
        st.markdown(f'<div class="tip-card"><span class="tip-tag">PERSONALIZED INSIGHT</span><h3>{title}</h3><p>{desc}</p><p class="muted">คำแนะนำนี้เลือกจากหมวดที่มีค่ารวมสูงสุดในข้อมูลของคุณ ไม่ใช่คำแนะนำจากโมเดลภาษา (LLM)</p></div>',unsafe_allow_html=True)
        st.markdown("#### รายละเอียดแต่ละหมวด")
        for k,v in sums.items():
            st.write(f"**{k}** — {fmt(v)} kg CO₂e")
            st.progress(int(v/max(sum(sums.values()),0.0001)*100))
        st.caption("คำแนะนำเป็นแนวทางทั่วไป ควรพิจารณาความเหมาะสมกับบริบทของแต่ละคน")

else:
    st.markdown("### 🗂️ ประวัติการบันทึก")
    if df.empty:
        st.info("ยังไม่มีรายการบันทึก")
    else:
        view = df.sort_values("date",ascending=False).copy()
        view["date"] = view["date"].dt.strftime("%d/%m/%Y")
        st.dataframe(view[["date","transport","distance_km","electricity_kwh","food","meals","total_kg","note"]],use_container_width=True,hide_index=True)
        csv = st.session_state.records.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ ดาวน์โหลดข้อมูล CSV",csv,"carbon_activity_log.csv","text/csv")
        if st.button("ล้างข้อมูลทั้งหมด",type="secondary"):
            st.session_state.records = pd.DataFrame(columns=df.columns)
            if DATA_FILE.exists():
                DATA_FILE.unlink()
            st.rerun()

st.markdown("---")
st.caption("Carbonly · AI Carbon Tracker Prototype | ผลลัพธ์เป็นค่าประมาณเพื่อการศึกษา ไม่ใช่บัญชีคาร์บอนที่ผ่านการรับรอง")
st.caption("ความโปร่งใส: เวอร์ชันนี้ใช้สูตรคำนวณและกฎแนะนำ (rule-based) ไม่ได้เชื่อม LLM หรือ Predictive AI จริง ค่าปัจจัยการปล่อยเป็นตัวอย่าง ต้องตรวจสอบและแทนที่ด้วยแหล่งอ้างอิงที่เหมาะสมกับประเทศไทยก่อนนำไปอ้างเป็นผลจริง")
