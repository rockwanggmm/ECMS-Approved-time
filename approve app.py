import streamlit as st
import pandas as pd
from datetime import datetime, time

# 頁面設定
st.set_page_config(page_title="專案審核效率分析", layout="wide")

st.title("📊 專案審核效率分析工具")

# --- 側邊欄：設定與對照表 ---
with st.sidebar:
    st.header("⚙️ 計算設定")
    
    # 修正時間跳動問題：使用 session_state 鎖定使用者選定的時間
    if 'set_date' not in st.session_state:
        st.session_state.set_date = datetime.now().date()
    if 'set_time' not in st.session_state:
        st.session_state.set_time = datetime.now().time()

    # 綁定輸入元件
    d = st.date_input("當前判定日期", value=st.session_state.set_date)
    t = st.time_input("當前判定時間", value=st.session_state.set_time)
    
    # 更新 session_state
    st.session_state.set_date = d
    st.session_state.set_time = t
    
    ref_now = datetime.combine(d, t)
    
    st.divider()
    
    # 整合等級對照表
    st.subheader("📋 判斷等級對照表")
    st.caption("根據專案發起點 (T0) 計算耗時：")
    st.markdown("""
    | 標記 | 耗時條件 (H) | 狀態含義 |
    | :--- | :--- | :--- |
    | **🟢 正常** | `H <= 24` | 處理速度理想 |
    | **🟡 警告** | `24 < H <= 48` | 已超過 1 天 |
    | **🟠 延遲** | `48 < H <= 72` | 已超過 2 天 |
    | **🔴 嚴重延遲** | `H > 72` | 已超過 3 天 |
    """)
    st.divider()
    st.info("💡 邏輯：\n- 已核准：紀錄時間 - 起始時間\n- 等待中：判定時間 - 起始時間")

# --- 主要輸入區 ---
st.markdown("請分別輸入以下三類資料，系統將自動比對並計算耗時。")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("1. 人員名單")
    names_input = st.text_area("貼入所有審核人名單：", height=250, placeholder="")

with col_b:
    st.subheader("2. 核准紀錄")
    approvals_input = st.text_area("貼入已 Approved 的詳細紀錄：", height=250, placeholder="")

with col_c:
    st.subheader("3. 基準起始點")
    base_time_input = st.text_area("貼入 Approval step required 資料：", height=250, placeholder="")

if st.button("開始交叉比對分析", type="primary"):
    if not (names_input and base_time_input):
        st.error("請確認輸入『人員名單』與『基準起始點』")
    else:
        # --- 1. 解析基準時間 T0 (強化版) ---
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

        # --- 2. 解析核准紀錄 ---
        approval_map = {}
        app_lines = [l.strip() for l in approvals_input.split('\n') if l.strip()]
        for i, line in enumerate(app_lines):
            if line == "Approved":
                if i > 0:
                    name = app_lines[i-1]
                    # 往下搜尋最近的時間格式
                    for j in range(i + 1, min(i + 5, len(app_lines))):
                        try:
                            time_val = pd.to_datetime(app_lines[j].replace('at ', '').strip())
                            approval_map[name] = time_val
                            break
                        except: continue

        # --- 3. 解析名單並分析 ---
        raw_personnel = [l.strip() for l in names_input.split('\n') if l.strip()]
        # 過濾雜訊
        blacklist = ["Everyone from", "must approve", "Waiting for", "approvals"]
        personnel = []
        for p in raw_personnel:
            if not any(b in p for b in blacklist):
                personnel.append(p)
        
        # 去除重複
        personnel = list(dict.fromkeys(personnel))
        
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

        # --- 4. 呈現結果 ---
        df = pd.DataFrame(results)
        if not df.empty:
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("專案發起時間", start_time.strftime('%Y-%m-%d %H:%M'))
            m2.metric("平均處理耗時", f"{round(df['耗時 (H)'].mean(), 1)} H")
            m3.metric("分析總人數", len(df))

            # Modified 著色邏輯 for better visibility on dark backgrounds
            def highlight_analysis_results(val):
                # 僅將文字顏色應用於 '分析結果' 欄位
                # 使用適合深色背景的淺色調
                if "🔴" in val:
                    return "color: #ffcccc;" # 淺紅
                elif "🟠" in val:
                    return "color: #ffe0b3;" # 淺橘
                elif "🟡" in val:
                    return "color: #ffffcc;" # 淺黃
                return ""

            # 使用 applymap 將著色僅應用於 '分析結果' 欄位，且僅影響文字顏色
            st.dataframe(df.style.applymap(highlight_analysis_results, subset=['分析結果']), use_container_width=True)
            
            # 檔案下載
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 下載分析報表 (CSV)", csv, f"audit_report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
