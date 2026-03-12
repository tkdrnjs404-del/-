import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
from pykrx import stock # 네이버 시세 기반 라이브러리

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Real-time Pro Dashboard", layout="wide")

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

st.title("📈 네이버급 실시간 시장 대시보드")

container = st.container()
st.divider()
status_area = st.empty() 

def get_domestic_data():
    """국내 지수를 실시간에 가깝게 가져오는 함수"""
    try:
        now = datetime.now().strftime("%Y%m%d")
        # 코스피(1001), 코스닥(2001) 실시간 시세
        df_kospi = stock.get_index_status_by_date(now, now, "KOSPI")
        df_kosdaq = stock.get_index_status_by_date(now, now, "KOSDAQ")
        
        return {
            "KOSPI": float(df_kospi['종가'].iloc[-1]),
            "KOSPI_DIFF": float(df_kospi['대비'].iloc[-1]),
            "KOSPI_RATE": float(df_kospi['등락률'].iloc[-1]),
            "KOSDAQ": float(df_kosdaq['종가'].iloc[-1]),
            "KOSDAQ_DIFF": float(df_kosdaq['대비'].iloc[-1]),
            "KOSDAQ_RATE": float(df_kosdaq['등락률'].iloc[-1]),
        }
    except:
        return None

while True:
    with container:
        # 국내 데이터 호출 (네이버 기반)
        kr_data = get_domestic_data()
        
        # 해외/환율 데이터 호출 (야후 기반)
        foreign_symbols = ["KRW=X", "NQ=F", "CL=F", "GC=F", "BTC-USD", "^IXIC"]
        f_data = yf.download(foreign_symbols, period="2d", interval="1m", progress=False)['Close']

        # --- 📍 국내 주요 지수 ---
        st.subheader("📍 국내 주요 지수 (네이버 기반)")
        cols1 = st.columns(3)
        if kr_data:
            cols1[0].metric("코스피 (KOSPI)", f"{kr_data['KOSPI']:,.2f}", f"{kr_data['KOSPI_DIFF']:,.2f} ({kr_data['KOSPI_RATE']:.2f}%)")
            cols1[1].metric("코스닥 (KOSDAQ)", f"{kr_data['KOSDAQ']:,.2f}", f"{kr_data['KOSDAQ_DIFF']:,.2f} ({kr_data['KOSDAQ_RATE']:.2f}%)")
        
        # 환율은 야후에서 가져옴
        try:
            ex_rate = f_data['KRW=X'].dropna().iloc[-1]
            cols1[2].metric("원/달러 환율", f"{ex_rate:,.2f}", "")
        except: pass

        # --- 📍 미국 시장 및 원자재 ---
        st.subheader("📍 미국 시장 및 원자재")
        cols2 = st.columns(3)
        try:
            nasdaq = f_data['NQ=F'].dropna().iloc[-1]
            wti = f_data['CL=F'].dropna().iloc[-1]
            gold = f_data['GC=F'].dropna().iloc[-1]
            
            cols2[0].metric("나스닥 100 선물", f"{nasdaq:,.2f}", "")
            cols2[1].metric("WTI 원유 선물", f"{wti:,.2f}", "")
            cols2[2].metric("금 (Gold)", f"{gold:,.2f}", "")
        except: pass
        
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_area.markdown(f"<p style='text-align: center; color: #666;'>🔄 네이버 시세 동기화 중... (마지막 갱신: {now_time})</p>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
