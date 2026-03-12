import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
from pykrx import stock

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Real-time Multi-Source Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 하이브리드 실시간 대시보드")

container = st.container()
st.divider()
status_area = st.empty() 

def get_kr_indices():
    """네이버 시세 기반으로 코스피, 코스닥 지수 가져오기"""
    try:
        # 오늘 날짜 기준으로 지수 상태 가져오기
        today = datetime.now().strftime("%Y%m%d")
        df_k = stock.get_index_status_by_date(today, today, "KOSPI")
        df_q = stock.get_index_status_by_date(today, today, "KOSDAQ")
        
        return {
            "KOSPI": {"val": df_k['종가'].iloc[-1], "diff": df_k['대비'].iloc[-1], "rate": df_k['등락률'].iloc[-1]},
            "KOSDAQ": {"val": df_q['종가'].iloc[-1], "diff": df_q['대비'].iloc[-1], "rate": df_q['등락률'].iloc[-1]}
        }
    except:
        return None

# 야후 파이낸스에서 가져올 티커들
yahoo_tickers = {
    "미국 및 환율": {
        "나스닥 100 선물": "NQ=F",
        "S&P 500 선물": "ES=F",
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
        # --- 1. 국내 지수 (네이버 기반) ---
        st.subheader("📍 국내 주요 지수 (네이버 실시간)")
        kr_data = get_kr_indices()
        cols1 = st.columns(3)
        
        if kr_data:
            cols1[0].metric("코스피 (KOSPI)", f"{kr_data['KOSPI']['val']:,.2f}", f"{kr_data['KOSPI']['diff']:,.2f} ({kr_data['KOSPI']['rate']:.2f}%)")
            cols1[1].metric("코스닥 (KOSDAQ)", f"{kr_data['KOSDAQ']['val']:,.2f}", f"{kr_data['KOSDAQ']['diff']:,.2f} ({kr_data['KOSDAQ']['rate']:.2f}%)")
        else:
            cols1[0].metric("코스피 (KOSPI)", "연결 중...")
            cols1[1].metric("코스닥 (KOSDAQ)", "연결 중...")

        # --- 2. 해외 및 원자재 (야후 기반) ---
        all_y_symbols = [sym for group in yahoo_tickers.values() for sym in group.values()]
        y_data = yf.download(all_y_symbols, period="2d", interval="1m", progress=False)['Close']

        # 환율 (국내 지수 옆 세 번째 칸)
        try:
            ex_rate = y_data['KRW=X'].dropna().iloc[-1]
            cols1[2].metric("원/달러 환율", f"{ex_rate:,.2f}", "")
        except: pass

        for category, items in yahoo_tickers.items():
            st.subheader(f"📍 {category} (Yahoo Finance)")
            cols = st.columns(3)
            for idx, (name, sym) in enumerate(items.items()):
                if name == "원/달러 환율": continue # 위에서 이미 표시함
                try:
                    current_val = y_data[sym].dropna().iloc[-1]
                    cols[idx % 3].metric(label=name, value=f"{current_val:,.2f}", delta="")
                except:
                    cols[idx % 3].metric(label=name, value="갱신 중...")

    # 하단 상태 업데이트
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_area.markdown(f"<p style='text-align: center; color: #666;'>🔄 국내(네이버) + 해외(야후) 혼합 동기화 중... (갱신: {now_time})</p>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
