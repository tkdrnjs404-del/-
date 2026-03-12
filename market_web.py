import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from pykrx import stock

# 1. 페이지 설정
st.set_page_config(page_title="Custom Market Dashboard", layout="wide")

# CSS: 폰트 색상 유지 및 우측 하단 텍스트 고정 디자인
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* 지수 숫자 흰색, 이름 유채색(민트/청록) 고정 */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700;
    }
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
    }
    
    /* 우측 하단 구석 고정 텍스트 (작고 반투명하게) */
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
    """항상 한국 표준시(KST) 반환"""
    return datetime.utcnow() + timedelta(hours=9)

def is_market_open():
    """한국 장 중인지 확인 (평일 09:00 ~ 15:40)"""
    now = get_kst_now()
    if now.weekday() >= 5: # 주말
        return False
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=40, second=0, microsecond=0)
    return start_time <= now <= end_time

# 야후 파이낸스 티커 (나스닥 종합지수 제일 앞 배치)
yahoo_tickers = {
    "해외 지수 및 환율": {
        "나스닥 종합지수": "^IXIC", # <- 제일 앞으로 이동됨
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
        # --- 1. 국내 주요 지수 섹션 ---
        st.subheader("📍 국내 주요 지수")
        cols1 = st.columns(3)
        kr_data_success = False
        
        # [장중] 네이버 실시간 데이터 (pykrx) 시도
        if is_market_open():
            try:
                now = get_kst_now()
                today_str = now.strftime("%Y%m%d")
                df_k = stock.get_index_status_by_date(today_str, today_str, "KOSPI")
                df_q = stock.get_index_status_by_date(today_str, today_str, "KOSDAQ")
                
                if not df_k.empty and not df_q.empty:
                    cols1[0].metric("코스피 (KOSPI)", f"{df_k['종가'].iloc[-1]:,.2f}", f"{df_k['대비'].iloc[-1]:,.2f} ({df_k['등락률'].iloc[-1]:.2f}%)")
                    cols1[1].metric("코스닥 (KOSDAQ)", f"{df_q['종가'].iloc[-1]:,.2f}", f"{df_q['대비'].iloc[-1]:,.2f} ({df_q['등락률'].iloc[-1]:.2f}%)")
                    kr_data_success = True
            except:
                pass
                
        # [장외] 구글 검색처럼 고정된 최종 종가 표시 (수동 입력 방지용 야후 일봉 데이터)
        if not kr_data_success:
            try:
                kr_fallback = yf.download(["^KS11", "^KQ11"], period="5d", interval="1d", progress=False)['Close']
                
                k_val = kr_fallback['^KS11'].dropna().iloc[-1]
                k_prev = kr_fallback['^KS11'].dropna().iloc[-2]
                k_diff, k_rate = k_val - k_prev, ((k_val - k_prev) / k_prev) * 100
                
                q_val = kr_fallback['^KQ11'].dropna().iloc[-1]
                q_prev = kr_fallback['^KQ11'].dropna().iloc[-2]
                q_diff, q_rate = q_val - q_prev, ((q_val - q_prev) / q_prev) * 100
                
                cols1[0].metric("코스피 (KOSPI)", f"{k_val:,.2f}", f"{k_diff:,.2f} ({k_rate:.2f}%)")
                cols1[1].metric("코스닥 (KOSDAQ)", f"{q_val:,.2f}", f"{q_diff:,.2f} ({q_rate:.2f}%)")
            except:
                cols1[0].metric("코스피 (KOSPI)", "장외 데이터 대기", "0")
                cols1[1].metric("코스닥 (KOSDAQ)", "장외 데이터 대기", "0")

        # --- 2. 야후 파이낸스 실시간 다운로드 ---
        all_y_symbols = [sym for group in yahoo_tickers.values() for sym in group.values()]
        y_data = yf.download(all_y_symbols, period="2d", interval="1m", progress=False)['Close']

        # 환율 표시 (국내 지수 옆 3번째 칸)
        try:
            ex_rate = y_data['KRW=X'].dropna().iloc[-1]
            cols1[2].metric("원/달러 환율", f"{ex_rate:,.2f}", "")
        except: 
            cols1[2].metric("원/달러 환율", "대기 중", "")

        # --- 3. 해외 및 원자재 섹션 ---
        for category, items in yahoo_tickers.items():
            st.subheader(f"📍 {category}")
            cols = st.columns(3)
            
            # 환율은 위에 표시했으므로 제외
            display_items = {k: v for k, v in items.items() if k != "원/달러 환율"}
            
            for idx, (name, sym) in enumerate(display_items.items()):
                try:
                    current_val = y_data[sym].dropna().iloc[-1]
                    cols[idx % 3].metric(label=name, value=f"{current_val:,.2f}", delta="")
                except:
                    cols[idx % 3].metric(label=name, value="대기 중")

    # --- 우측 하단 갱신 텍스트 ---
    now_time_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
    market_status = "🟢 장중 실시간" if is_market_open() else "⚪ 장외 고정 데이터"
    
    status_area.markdown(
        f"<div class='bottom-right-text'>{market_status} 동기화 중... (갱신: {now_time_str} KST)</div>", 
        unsafe_allow_html=True
    )
    
    time.sleep(5)
    st.rerun()
