import streamlit as st
import pandas as pd
from datetime import datetime, time

# 頁面設定
st.set_page_config(page_title="專案審核效率分析", layout="wide")

st.title("📊 專案審核效率分析工具")

# --- 側邊欄：設定與對照表 ---
with st.sidebar:
    st.header("⚙️ 計算設定")
    d = st.date_input("當前判定日期", datetime.now())
    t = st.time_input("當前判定時間", datetime.now().time())
    ref_now = datetime.combine(d, t)
    
    st.divider()
    
    # 這裡整合了您要求的對照表
    st.subheader("📋 判斷等級對照表")
    st.caption("根據專案發起點 (T0) 計算耗時：")
    st.markdown("""
    - **🟢 正常** `H <= 24h` (1天內)  
      *處理速度理想或尚未超時*
    - **🟡 警告** `24h < H <= 48h` (1~2天)  
      *已超過一天，建議提醒*
    - **🟠 延遲** `48h < H <= 72h` (2~3天)  
      *明顯延遲，影響後續時程*
    - **🔴 嚴重延遲** `H > 72h` (超過3天)  
      *嚴重卡關，需介入了解*
    """)
    st.divider()
    st.info("💡 邏輯：已核准者以『實際紀錄』計算；等待中者以『當前判定時間』計算。")

# --- 主要輸入區 ---
st.markdown("請分別輸入以下三類資料：")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("1. 人員名單")
    names_input = st.text_area("貼入所有審核人名單：", height=200)

with col_b:
    st.subheader("2. 核准紀錄")
    approvals_input = st.text_area("貼入已 Approved 的詳細紀錄：", height=200)

with col_c:
    st.subheader("3. 基準起始點")
    base_time_input = st.text_area("貼入 Approval step required 資料：", height=200)

if st.button("開始交叉比對分析", type="primary"):
    if not (names_input and base_time_input):
        st.error("請確認輸入『人員名單』與『基準起始點』")
    else:
        # 1. 解析起始時間 T0
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
            st.error("❌ 無法解析起始時間。格式參考：May 11, 2026 at 12:01 PM")
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

        # 3. 解析名單並分析
        personnel = list(set([l.strip() for l in names_input.split('\n') if l.strip()]))
        blacklist = ["Everyone from", "must approve", "Waiting for", "approvals"]
        personnel = [p for p in personnel if not any(b in p for b in blacklist)]
        
        results = []
        for p in personnel:
            if p in approval_map:
                status = "✅ Approved"
                target_time = approval_map[p]
            else:
                status = "⏳ Waiting"
                target_time = ref_now
            
            diff_hours = round((target_time - start_time).total_seconds() / 3600, 1)
            
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
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("專案發起時間", start_time.strftime('%Y-%m-%d %H:%M'))
            m2.metric("平均處理耗時", f"{round(df['耗時 (H)'].mean(), 1)} H")
            m3.metric("總計分析人數", len(df))

            def highlight_status(row):
                color = ''
                if "🔴" in row["分析結果"]: color = 'background-color: #f8d7da'
                elif "🟡" in row["分析結果"]: color = 'background-color: #fff3cd'
                elif "🟠" in row["分析結果"]: color = 'background-color: #ffeeba'
                return [color] * len(row)

            st.dataframe(df.style.apply(highlight_status, axis=1), use_container_width=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 下載分析報表 (CSV)", csv, "audit_report.csv", "text/csv")
