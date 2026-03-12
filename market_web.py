import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정 및 다크 테마 디자인
st.set_page_config(page_title="Real-time Dashboard", layout="wide")

# CSS를 사용하여 숫자를 흰색으로 강제 설정하고 디자인 수정
st.markdown("""
    <style>
    /* 배경색 및 전체 텍스트 색상 */
    .main { background-color: #0e1117; }
    
    /* 지수 숫자(Metric Value)를 흰색으로 고정 */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2rem !important;
    }
    
    /* 지수 이름(Label) 색상 */
    [data-testid="stMetricLabel"] {
        color: #AAAAAA !important;
    }

    /* 카드 형태 디자인 */
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ 실시간 시장 대시보드")

# 지수들이 표시될 메인 공간
container = st.container()

# 하단에 고정될 상태 표시 공간
st.divider()
status_area = st.empty() 

# 티커 설정
tickers = {
    "국내 지수": {"코스피": "^KS11", "코스닥": "^KQ11", "원/달러 환율": "KRW=X"},
    "해외 지수": {"나스닥": "^IXIC", "나스닥100 선물": "NQ=F", "S&P 500": "^GSPC"},
    "원자재": {"WTI 원유": "CL=F", "금 (Gold)": "GC=F", "코스피 200": "^KS200"}
}

# 무한 루프 시작
while True:
    with container:
        all_symbols = [sym for group in tickers.values() for sym in group.values()]
        # 데이터 가져오기
        data = yf.download(all_symbols, period="1d", interval="1m", progress=False)
        
        if not data.empty:
            # 섹션별 출력
            for category, items in tickers.items():
                st.subheader(f"📍 {category}")
                cols = st.columns(3)
                for idx, (name, sym) in enumerate(items.items()):
                    try:
                        current_price = data['Close'][sym].dropna().iloc[-1]
                        
                        # 전일 대비 변동폭 계산용
                        hist = yf.Ticker(sym).history(period="2d")
                        prev_close = hist['Close'].iloc[-2]
                        delta = current_price - prev_close
                        delta_pct = (delta / prev_close) * 100
                        
                        cols[idx % 3].metric(
                            label=name, 
                            value=f"{current_price:,.2f}", 
                            delta=f"{delta:,.2f} ({delta_pct:.2f}%)"
                        )
                    except:
                        cols[idx % 3].metric(label=name, value="연결 중...")
        
    # 최하단 상태 메시지 업데이트
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_area.markdown(f"<p style='text-align: center; color: gray;'>🟢 실시간 동기화 중... (마지막 갱신: {now})</p>", unsafe_allow_html=True)
    
    # 5초 대기 후 화면 갱신
    time.sleep(5)
    st.rerun()
