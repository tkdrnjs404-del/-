import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from pykrx import stock

# 1. 페이지 설정
st.set_page_config(page_title="Real-time Market Dashboard", layout="wide")

# 2. CSS 및 애니메이션 (박스 깜빡임 효과 추가)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* 기본 카드 디자인 */
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
        transition: background-color 1s ease-out; /* 색상이 서서히 돌아오는 효과 */
    }

    /* 텍스트 선명도 고정 */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 2.2rem !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #4FD1C5 !important; font-weight: 600 !important; }

    /* 상승/하락 깜빡이 애니메이션 정의 */
    @keyframes flash-red {
        0% { background-color: rgba(255, 0, 0, 0.3); }
        100% { background-color: #1c1f26; }
    }
    @keyframes flash-blue {
        0% { background-color: rgba(0, 0, 255, 0.3); }
        100% { background-color: #1c1f26; }
    }

    .flash-up { animation: flash-red 1.5s ease-out; }
    .flash-down { animation: flash-blue 1.5s ease-out; }

    .bottom-right-text {
        position: fixed; bottom: 10px; right: 15px; font-size: 0.75rem;
        color: #FFFFFF; background-color: rgba(0, 0, 0, 0.7);
        padding: 6px 12px; border-radius: 6px; z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 맞춤형 실시간 대시보드")

# 이전 값을 저장하기 위한 세션 상태 초기화
if 'prev_values' not in st.session_state:
    st.session_state.prev_values = {}

container = st.container()
status_area = st.empty() 

def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

def is_market_open():
    now = get_kst_now()
    if now.weekday() >= 5: return False
    return now.replace(hour=9, minute=0) <= now <= now.replace(hour=15, minute=40)

yahoo_tickers = {
    "해외 지수 및 환율": {"나스닥 종합": "^IXIC", "S&P 500": "^GSPC", "나스닥 100 선물": "NQ=F", "원/달러 환율": "KRW=X"},
    "원자재 및 코인": {"WTI 원유": "CL=F", "금 (Gold)": "GC=F", "비트코인": "BTC-USD"}
}

while True:
    with container:
        # --- 데이터 동시 다운로드 (비트코인 포함 실시간) ---
        all_syms = [s for g in yahoo_tickers.values() for s in g.values()]
        # 비트코인 등 실시간 데이터 갱신을 위해 period 1d, interval 1m 강제
        y_live = yf.download(all_syms, period="1d", interval="1m", progress=False)['Close']
        y_daily = yf.download(all_syms, period="5d", interval="1d", progress=False)['Close']

        # 1. 국내 지수 (생략 가능하나 구조 유지)
        st.subheader("📍 국내 주요 지수")
        cols1 = st.columns(3)
        # ... (기존 국내 지수 로직 동일)

        # 2. 해외 및 코인 섹션
        for category, items in yahoo_tickers.items():
            st.subheader(f"📍 {category}")
            cols = st.columns(3)
            
            for idx, (name, sym) in enumerate(items.items()):
                try:
                    current_val = y_live[sym].dropna().iloc[-1]
                    prev_close = y_daily[sym].dropna().iloc[-2]
                    delta = current_val - prev_close
                    delta_pct = (delta / prev_close) * 100
                    
                    # --- 깜빡이 로직 처리 ---
                    flash_class = ""
                    if sym in st.session_state.prev_values:
                        if current_val > st.session_state.prev_values[sym]:
                            flash_class = "flash-up"
                        elif current_val < st.session_state.prev_values[sym]:
                            flash_class = "flash-down"
                    
                    st.session_state.prev_values[sym] = current_val
                    
                    # HTML을 사용하여 애니메이션 클래스 주입
                    with cols[idx % 3]:
                        st.markdown(f'<div class="{flash_class}">', unsafe_allow_html=True)
                        st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{delta:,.2f} ({delta_pct:.2f}%)")
                        st.markdown('</div>', unsafe_allow_html=True)
                except:
                    cols[idx % 3].metric(label=name, value="연결 중...")

    now_str = get_kst_now().strftime('%H:%M:%S')
    status_area.markdown(f"<div class='bottom-right-text'>갱신: {now_str} KST (5초 간격)</div>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
