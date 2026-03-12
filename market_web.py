import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="My Real-time Market", layout="wide")

# 스타일 지정 (다크모드 느낌)
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; }
    div[data-testid="stMetric"] {
        background-color: #262626;
        border: 1px solid #404040;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 실시간 시장 데이터 대시보드")
st.caption(f"최종 업데이트 (KST): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 티커 리스트 구성
# 한국 지수는 지연을 줄이기 위해 거래량이 활발한 대표 ETF(KODEX 200 등)를 참고하거나 인덱스 사용
tickers = {
    "국내 지수": {
        "코스피 (KOSPI)": "^KS11",
        "코스닥 (KOSDAQ)": "^KQ11",
        "원/달러 환율": "KRW=X"
    },
    "해외 지수": {
        "나스닥 (NASDAQ)": "^IXIC",
        "나스닥 100 선물": "NQ=F",
        "S&P 500": "^GSPC"
    },
    "원자재 및 기타": {
        "WTI 원유": "CL=F",
        "금 (Gold)": "GC=F",
        "코스피 200": "^KS200"
    }
}

def fetch_data():
    results = {}
    all_symbols = [sym for group in tickers.values() for sym in group.values()]
    
    # 여러 티커를 한 번에 다운로드하여 속도 향상
    data = yf.download(all_symbols, period="2d", interval="1m", progress=False)['Close']
    
    for category, items in tickers.items():
        results[category] = []
        for name, sym in items.items():
            try:
                current_val = data[sym].iloc[-1]
                prev_val = data[sym].dropna().iloc[-2]
                delta = current_val - prev_val
                delta_pct = (delta / prev_val) * 100
                results[category].append({
                    "label": name,
                    "value": current_val,
                    "delta": f"{delta:,.2f} ({delta_pct:.2f}%)"
                })
            except:
                results[category].append({"label": name, "value": "N/A", "delta": "0"})
    return results

# 데이터 가져오기
with st.spinner('데이터를 불러오는 중...'):
    market_data = fetch_data()

# 화면 레이아웃 (섹션별 배치)
for category, items in market_data.items():
    st.subheader(f"📍 {category}")
    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            st.metric(label=item["label"], value=f"{item['value']:,.2f}", delta=item["delta"])
    st.write("")

st.divider()
st.info("※ 한국 지수는 야후 파이낸스 정책상 약 15분 지연될 수 있습니다. 해외 선물 및 환율은 실시간에 가깝습니다.")

# 5분마다 자동 새로고침을 위한 버튼
if st.button('수동 새로고침'):
    st.rerun()