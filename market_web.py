import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정 및 다크 테마 디자인
st.set_page_config(page_title="Real-time Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #AAAAAA !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ 실시간 시장 대시보드")

container = st.container()
st.divider()
status_area = st.empty() 

# 티커 설정: 코스닥 150 심볼을 ^KQ150으로 변경하여 호환성 높임
tickers = {
    "국내 지수 (대표 200/150)": {
        "코스피 200": "^KS200", 
        "코스닥 150": "^KQ150", # 이 부분이 수정되었습니다
        "원/달러 환율": "KRW=X"
    },
    "해외 지수": {
        "나스닥": "^IXIC", 
        "나스닥 100 선물": "NQ=F", 
        "S&P 500": "^GSPC"
    },
    "원자재": {
        "WTI 원유": "CL=F", 
        "금 (Gold)": "GC=F", 
        "비트코인 (BTC)": "BTC-USD"
    }
}

while True:
    with container:
        for category, items in tickers.items():
            st.subheader(f"📍 {category}")
            cols = st.columns(3)
            for idx, (name, sym) in enumerate(items.items()):
                try:
                    # 개별 티커별로 최신 데이터를 가져와서 오류 최소화
                    t = yf.Ticker(sym)
                    df = t.history(period="2d", interval="1m")
                    
                    if not df.empty:
                        current_price = df['Close'].iloc[-1]
                        prev_close = df['Close'].iloc[0] # 전일 혹은 시작가 대비
                        
                        delta = current_price - prev_close
                        delta_pct = (delta / prev_close) * 100
                        
                        cols[idx % 3].metric(
                            label=name, 
                            value=f"{current_price:,.2f}", 
                            delta=f"{delta:,.2f} ({delta_pct:.2f}%)"
                        )
                    else:
                        cols[idx % 3].metric(label=name, value="휴장 또는 점검")
                except:
                    cols[idx % 3].metric(label=name, value="연결 재시도 중")
        
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_area.markdown(f"<p style='text-align: center; color: #666;'>🔄 5초 주기 자동 동기화 중... (마지막 갱신: {now})</p>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
