import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta, timezone

# 頁面設定
st.set_page_config(page_title="專案審核效率分析", layout="wide")

st.title("📊 專案審核效率分析工具")

# --- 側邊欄：設定與時區修正 ---
with st.sidebar:
    st.header("⚙️ 計算設定")
    tz_taiwan = timezone(timedelta(hours=8))
    now_taiwan = datetime.now(tz_taiwan)

    if 'set_date' not in st.session_state:
        st.session_state.set_date = now_taiwan.date()
    if 'set_time' not in st.session_state:
        st.session_state.set_time = now_taiwan.time()

    d = st.date_input("當前判定日期", value=st.session_state.set_date)
    t = st.time_input("當前判定時間", value=st.session_state.set_time)
    
    st.session_state.set_date = d
    st.session_state.set_time = t
    ref_now = datetime.combine(d, t)
    
    st.divider()
    st.subheader("📋 判斷等級對照表")
    st.markdown("""
    | 標記 | 耗時條件 (H) | 狀態含義 |
    | :--- | :--- | :--- |
    | **🟢 正常** | `H <= 24` | 處理速度理想 |
    | **🟡 警告** | `24 < H <= 48` | 已超過 1 天 |
    | **🟠 延遲** | `48 < H <= 72` | 已超過 2 天 |
    | **🔴 嚴重延遲** | `H > 72` | 已超過 3 天 |
    """)

# --- 主要輸入區 ---
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("1. 人員名單")
    names_input = st.text_area("貼入所有審核人名單：", height=250)

with col_b:
    st.subheader("2. 核准紀錄")
    approvals_input = st.text_area("貼入已 Approved 的詳細紀錄：", height=250)

with col_c:
    st.subheader("3. 基準起始點")
    base_time_input = st.text_area("貼入 Approval step required 資料：", height=250)

if st.button("開始交叉比對分析", type="primary"):
    if not (names_input and base_time_input):
        st.error("請確認輸入『人員名單』與『基準起始點』")
    else:
        # 1. 解析起始時間
        start_time = None
        base_lines = [l.strip() for l in base_time_input.split('\n') if l.strip()]
        for line in base_lines:
            try:
                clean_line = line.replace('at ', '').strip()
                potential_time = pd.to_datetime(clean_line)
                if potential_time.year > 2000:
                    start_time = potential_time
                    break
            except: continue
        
        if not start_time:
            st.error("❌ 無法解析起始時間。")
            st.stop()

        # 2. 解析核准紀錄
        approval_map = {}
        app_lines = [l.strip() for l in approvals_input.split('\n') if l.strip()]
        for i, line in enumerate(app_lines):
            if line == "Approved":
                if i > 0:
                    name = app_lines[i-1]
                    for j in range(i + 1, min(i + 5, len(app_lines))):
                        try:
                            time_val = pd.to_datetime(app_lines[j].replace('at ', '').strip())
                            approval_map[name] = time_val
                            break
                        except: continue

        # 3. 解析名單並過濾系統字串
        raw_personnel = [l.strip() for l in names_input.split('\n') if l.strip()]
        blacklist = [
            "Everyone from", "must approve", "Waiting for", 
            "approvals", "Approved", "Waiting for approval"
        ]
        
        personnel = []
        for p in raw_personnel:
            if p not in blacklist and not any(b in p for b in ["Everyone from", "must approve"]):
                personnel.append(p)
        
        personnel = list(dict.fromkeys(personnel))
        
        results = []
        for p in personnel:
            status = "✅ Approved" if p in approval_map else "⏳ Waiting"
            target_time = approval_map[p] if p in approval_map else ref_now
            
            # 計算耗時
            diff_hours = (target_time - start_time).total_seconds() / 3600

            if diff_hours > 72: level = "🔴 嚴重延遲 (>3天)"
            elif diff_hours > 48: level = "🟠 延遲 (>2天)"
            elif diff_hours > 24: level = "🟡 警告 (>1天)"
            else: level = "🟢 正常"

            results.append({
                "人員名稱": p, 
                "當前狀態": status, 
                "紀錄/判定時間": target_time.strftime('%Y-%m-%d %H:%M'), 
                "耗時 (H)": diff_hours, 
                "分析結果": level
            })

        # 4. 呈現結果
        df = pd.DataFrame(results)
        if not df.empty:
            # --- 關鍵修正：將索引加 1，使顯示編號從 1 開始 ---
            df.index = df.index + 1
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("專案發起時間 (T0)", start_time.strftime('%Y-%m-%d %H:%M'))
            m2.metric("平均處理效率", f"{df['耗時 (H)'].mean():.2f} H")
            m3.metric("分析總人數", len(df))

            def highlight_text(val):
                if "🔴" in val: return "color: #FF6B6B; font-weight: bold;"
                elif "🟠" in val: return "color: #FFAD60; font-weight: bold;"
                elif "🟡" in val: return "color: #FFEEAD; font-weight: bold;"
                elif "🟢" in val: return "color: #96CEB4;"
                return ""

            # 顯示表格並設定顯示格式
            st.dataframe(
                df.style.map(highlight_text, subset=['分析結果']),
                use_container_width=True,
                column_config={
                    "耗時 (H)": st.column_config.NumberColumn(
                        "耗時 (H)",
                        format="%.2f"
                    )
                }
            )
            
            csv = df.to_csv(index=True, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 下載分析報表 (CSV)", csv, f"audit_report.csv", "text/csv")
