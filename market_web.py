import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정 및 다크 테마 디자인
st.set_page_config(page_title="Real-time Dashboard", layout="wide")

# CSS: 숫자 흰색 고정 및 디자인 개선
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
        font-size: 1.1rem !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ 실시간 시장 대시보드 (3초 동기화)")

# 데이터 표시 공간
container = st.container()

# 하단 상태 표시 공간
st.divider()
status_area = st.empty() 

# 티커 설정 (코스피200, 코스닥150으로 교체)
tickers = {
    "국내 지수 (대표 200/150)": {
        "코스피 200": "^KS200", 
        "코스닥 150": "^KQS150", 
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
        # 전체 티커 리스트 추출
        all_symbols = [sym for group in tickers.values() for sym in group.values()]
        
        # 최신 데이터 다운로드
        data = yf.download(all_symbols, period="2d", interval="1m", progress=False)
        
        if not data.empty:
            for category, items in tickers.items():
                st.subheader(f"📍 {category}")
                cols = st.columns(3)
                for idx, (name, sym) in enumerate(items.items()):
                    try:
                        # 최신가 추출
                        valid_series = data['Close'][sym].dropna()
                        current_price = valid_series.iloc[-1]
                        
                        # 전일 종가 기준 변동폭 계산 (yfinance 특성상 별도 호출이 가장 정확)
                        ticker_obj = yf.Ticker(sym)
                        hist = ticker_obj.history(period="2d")
                        prev_close = hist['Close'].iloc[-2]
                        
                        delta = current_price - prev_close
                        delta_pct = (delta / prev_close) * 100
                        
                        cols[idx % 3].metric(
                            label=name, 
                            value=f"{current_price:,.2f}", 
                            delta=f"{delta:,.2f} ({delta_pct:.2f}%)"
                        )
                    except:
                        cols[idx % 3].metric(label=name, value="데이터 수신 중...")
        
    # 하단 상태 업데이트
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_area.markdown(f"<p style='text-align: center; color: #666;'>🔄 3초 주기 자동 동기화 중... (마지막 갱신: {now})</p>", unsafe_allow_html=True)
    
    # 3초 대기
    time.sleep(3)
    st.rerun()
