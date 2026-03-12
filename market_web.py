import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="My Real-time Market", layout="wide")

st.title("📊 실시간 시장 데이터 대시보드")
st.caption(f"최종 업데이트 (KST): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 티커 리스트
tickers = {
    "국내 지수": {"코스피": "^KS11", "코스닥": "^KQ11", "원/달러 환율": "KRW=X"},
    "해외 지수": {"나스닥": "^IXIC", "나스닥100 선물": "NQ=F", "S&P 500": "^GSPC"},
    "원자재": {"WTI 원유": "CL=F", "금 (Gold)": "GC=F", "코스피 200": "^KS200"}
}

def fetch_data():
    results = {}
    all_symbols = [sym for group in tickers.values() for sym in group.values()]
    
    # 데이터 가져오기 (기간을 5일로 늘려 휴장일 에러 방지)
    data = yf.download(all_symbols, period="5d", interval="1m", progress=False)['Close']
    
    for category, items in tickers.items():
        results[category] = []
        for name, sym in items.items():
            try:
                # 해당 심볼의 유효한 데이터만 추출
                valid_series = data[sym].dropna()
                if not valid_series.empty:
                    current_val = valid_series.iloc[-1]
                    prev_val = valid_series.iloc[-2] if len(valid_series) > 1 else current_val
                    delta = current_val - prev_val
                    delta_pct = (delta / prev_val) * 100
                    
                    results[category].append({
                        "label": name,
                        "value": f"{current_val:,.2f}",
                        "delta": f"{delta:,.2f} ({delta_pct:.2f}%)"
                    })
                else:
                    results[category].append({"label": name, "value": "점검 중", "delta": "0"})
            except:
                results[category].append({"label": name, "value": "에러", "delta": "0"})
    return results

# 데이터 불러오기
with st.spinner('시장에서 데이터를 가져오는 중...'):
    market_data = fetch_data()

# 화면 레이아웃
for category, items in market_data.items():
    st.subheader(f"📍 {category}")
    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            st.metric(label=item["label"], value=item["value"], delta=item["delta"])

st.divider()
if st.button('🔄 새로고침'):
    st.rerun()
