import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from pykrx import stock

# 1. 페이지 설정
st.set_page_config(page_title="Custom Market Dashboard", layout="wide")

# CSS: 가독성 개선 (텍스트 선명도 강화)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* 1. 지수 숫자 - 완전한 흰색으로 선명하게 고정 */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700;
        opacity: 1.0 !important;
    }
    
    /* 2. 지수 이름 - 선명한 민트색 */
    [data-testid="stMetricLabel"] {
        color: #4FD1C5 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        opacity: 1.0 !important;
    }

    /* 3. 등락폭 글자 크기 조정 */
    [data-testid="stMetricDelta"] {
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    /* 카드 디자인 */
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }

    .bottom-right-text {
        position: fixed;
        bottom: 10px;
        right: 15px;
        font-size: 0.75rem;
        color: #FFFFFF;
        background-color: rgba(0, 0, 0, 0.7);
        padding: 6px 12px;
        border-radius: 6px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 맞춤형 실시간 대시보드")

container = st.container()
status_area = st.empty() 

def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

def is_market_open():
    now = get_kst_now()
    if now.weekday() >= 5: return False
    return now.replace(hour=9, minute=0) <= now <= now.replace(hour=15, minute=40)

yahoo_tickers = {
    "해외 지수 및 환율": {
        "나스닥 종합지수": "^IXIC",
        "S&P 500 지수": "^GSPC",
        "나스닥 100 선물": "NQ=F",
        "원/달러 환율": "KRW=X"
    },
    "원자재 및 코인": {
        "WTI 원유 선물": "CL=F",
        "금 (Gold)": "GC=F",
        "비트코인": "BTC-USD"
    }
}

while True:
    with container:
        # --- 1. 국내 주요 지수 ---
        st.subheader("📍 국내 주요 지수")
        cols1 = st.columns(3)
        kr_success = False
        
        if is_market_open():
            try:
                today = get_kst_now().strftime("%Y%m%d")
                df_k = stock.get_index_status_by_date(today, today, "KOSPI")
                df_q = stock.get_index_status_by_date(today, today, "KOSDAQ")
                if not df_k.empty:
                    cols1[0].metric("코스피 (KOSPI)", f"{df_k['종가'].iloc[-1]:,.2f}", f"{df_k['대비'].iloc[-1]:,.2f} ({df_k['등락률'].iloc[-1]:.2f}%)")
                    cols1[1].metric("코스닥 (KOSDAQ)", f"{df_q['종가'].iloc[-1]:,.2f}", f"{df_q['대비'].iloc[-1]:,.2f} ({df_q['등락률'].iloc[-1]:.2f}%)")
                    kr_success = True
            except: pass
            
        if not kr_success:
            try:
                # 안전하게 7일치 데이터를 가져와 마지막 2거래일 비교
                kr_fb = yf.download(["^KS11", "^KQ11"], period="7d", interval="1d", progress=False)['Close']
                for i, sym in enumerate(["^KS11", "^KQ11"]):
                    clean_data = kr_fb[sym].dropna()
                    val = clean_data.iloc[-1]
                    prev_val = clean_data.iloc[-2]
                    diff = val - prev_val
                    rate = (diff / prev_val) * 100
                    name = "코스피 (KOSPI)" if i==0 else "코스닥 (KOSDAQ)"
                    cols1[i].metric(name, f"{val:,.2f}", f"{diff:,.2f} ({rate:.2f}%)")
            except: pass

        # --- 2. 해외 및 원자재 (등락폭 nan 오류 수정) ---
        all_syms = [s for g in yahoo_tickers.values() for s in g.values()]
        # 등락 계산을 위해 7일치 데이터를 미리 확보 (nan 방지)
        y_data = yf.download(all_syms, period="7d", interval="1d", progress=False)['Close']
        # 실시간 가격용 (마지막 1분 데이터)
        y_live = yf.download(all_syms, period="1d", interval="1m", progress=False)['Close']

        # 환율 표시
        try:
            ex_now = y_live['KRW=X'].dropna().iloc[-1]
            ex_prev = y_data['KRW=X'].dropna().iloc[-2]
            ex_diff = ex_now - ex_prev
            cols1[2].metric("원/달러 환율", f"{ex_now:,.2f}", f"{ex_diff:,.2f}")
        except: pass

        for category, items in yahoo_tickers.items():
            st.subheader(f"📍 {category}")
            cols = st.columns(3)
            display_items = {k: v for k, v in items.items() if k != "원/달러 환율"}
            
            for idx, (name, sym) in enumerate(display_items.items()):
                try:
                    current_val = y_live[sym].dropna().iloc[-1]
                    # 어제 종가 데이터 활용 (nan 오류 해결)
                    prev_close = y_data[sym].dropna().iloc[-2]
                    
                    delta_val = current_val - prev_close
                    delta_pct = (delta_val / prev_close) * 100
                    
                    cols[idx % 3].metric(
                        label=name, 
                        value=f"{current_val:,.2f}", 
                        delta=f"{delta_val:,.2f} ({delta_pct:.2f}%)"
                    )
                except:
                    cols[idx % 3].metric(label=name, value="대기 중")

    # --- 하단 갱신 상태 ---
    now_str = get_kst_now().strftime('%H:%M:%S')
    m_status = "🟢 실시간" if is_market_open() else "⚪ 장외"
    status_area.markdown(f"<div class='bottom-right-text'>{m_status} 갱신: {now_str}</div>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
