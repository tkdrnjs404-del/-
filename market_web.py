import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# 페이지 설정 및 다크모드 스타일
st.set_page_config(page_title="Real-time Dashboard", layout="wide")
st.markdown("""
    <style>
    .stMetric { background-color: #1e1e1e; padding: 20px; border-radius: 15px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ 실시간 시장 스트리밍 대시보드")
status_text = st.empty() # 업데이트 시간을 표시할 빈 공간
container = st.container() # 지수들이 표시될 공간

# 티커 설정 (요청하신 지표들)
tickers = {
    "국내 지수": {"코스피": "^KS11", "코스닥": "^KQ11", "원/달러 환율": "KRW=X"},
    "해외 지수": {"나스닥": "^IXIC", "나스닥100 선물": "NQ=F", "S&P 500": "^GSPC"},
    "원자재": {"WTI 원유": "CL=F", "금 (Gold)": "GC=F", "코스피 200": "^KS200"}
}

# 무한 루프로 실시간 연동 시뮬레이션
while True:
    with container:
        # 데이터 가져오기
        all_symbols = [sym for group in tickers.values() for sym in group.values()]
        data = yf.download(all_symbols, period="1d", interval="1m", progress=False)
        
        if not data.empty:
            now = datetime.now().strftime('%H:%M:%S')
            status_text.write(f"🟢 실시간 동기화 중... (마지막 갱신: {now})")
            
            # 섹션별 출력
            for category, items in tickers.items():
                st.subheader(f"📍 {category}")
                cols = st.columns(3)
                for idx, (name, sym) in enumerate(items.items()):
                    try:
                        current_price = data['Close'][sym].dropna().iloc[-1]
                        # 전일 종가 대비 변동 계산을 위해 별도로 전일 데이터 호출 (최적화)
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
        
        # 5초 대기 후 다시 루프 (무료 API 과부하 방지를 위해 5~10초 권장)
        time.sleep(5)
        st.rerun() # 화면을 즉시 갱신
