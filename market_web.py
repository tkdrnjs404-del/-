import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from pykrx import stock

# 1. 페이지 설정
st.set_page_config(page_title="Custom Market Dashboard", layout="wide")

# CSS: 등락폭 표시 및 가격 변동 애니메이션 효과
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* 지수 이름 색상 (민트/청록) */
    [data-testid="stMetricLabel"] {
        color: #4FD1C5 !important;
        font-weight: 600 !important;
    }
    
    /* 카드 디자인 */
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
        transition: background-color 0.5s ease;
    }

    /* 우측 하단 고정 텍스트 */
    .bottom-right-text {
        position: fixed;
        bottom: 10px;
        right: 15px;
        font-size: 0.75rem;
        color: #888888;
        background-color: rgba(14, 17, 23, 0.7);
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

# 티커 구성 (나스닥 종합지수 최상단)
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
                kr_fb = yf.download(["^KS11", "^KQ11"], period="2d", progress=False)['Close']
                for i, sym in enumerate(["^KS11", "^KQ11"]):
                    val = kr_fb[sym].iloc[-1]
                    diff = val - kr_fb[sym].iloc[-2]
                    rate = (diff / kr_fb[sym].iloc[-2]) * 100
                    name = "코스피 (KOSPI)" if i==0 else "코스닥 (KOSDAQ)"
                    cols1[i].metric(name, f"{val:,.2f}", f"{diff:,.2f} ({rate:.2f}%)")
            except: pass

        # --- 2. 해외 및 원자재 (등락폭 계산 추가) ---
        all_syms = [s for g in yahoo_tickers.values() for s in g.values()]
        # 전일 대비 등락 계산을 위해 period를 2d로 설정
        y_data = yf.download(all_syms, period="2d", interval="1m", progress=False)['Close']

        # 환율 표시
        try:
            ex_now = y_data['KRW=X'].dropna().iloc[-1]
            ex_prev = y_data['KRW=X'].dropna().iloc[0] # 전일 종가 혹은 첫 데이터
            ex_diff = ex_now - ex_prev
            cols1[2].metric("원/달러 환율", f"{ex_now:,.2f}", f"{ex_diff:,.2f}")
        except: pass

        for category, items in yahoo_tickers.items():
            st.subheader(f"📍 {category}")
            cols = st.columns(3)
            display_items = {k: v for k, v in items.items() if k != "원/달러 환율"}
            
            for idx, (name, sym) in enumerate(display_items.items()):
                try:
                    series = y_data[sym].dropna()
                    current_val = series.iloc[-1]
                    # 야후 파이낸스에서 전일 종가 기준 등락 계산
                    prev_val = y_data[sym].iloc[0] 
                    delta_val = current_val - prev_val
                    delta_pct = (delta_val / prev_val) * 100
                    
                    cols[idx % 3].metric(
                        label=name, 
                        value=f"{current_val:,.2f}", 
                        delta=f"{delta_val:,.2f} ({delta_pct:.2f}%)"
                    )
                except:
                    cols[idx % 3].metric(label=name, value="대기 중")

    # --- 하단 갱신 상태 ---
    now_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
    m_status = "🟢 장중 실시간" if is_market_open() else "⚪ 장외 고정 데이터"
    status_area.markdown(f"<div class='bottom-right-text'>{m_status} (갱신: {now_str} KST)</div>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
