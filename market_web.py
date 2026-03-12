import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from pykrx import stock

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Custom Market Dashboard", layout="wide")

# CSS: 지수 이름 색상을 유채색(#4FD1C5 - 민트/청록)으로 유지
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #4FD1C5 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 맞춤형 실시간 대시보드")

container = st.container()
st.divider()
status_area = st.empty() 

def get_kst_now():
    """서버 시간에 의존하지 않고 항상 한국 표준시(KST)를 반환"""
    return datetime.utcnow() + timedelta(hours=9)

def is_market_open():
    """한국 장 중인지 확인 (평일 09:00 ~ 15:40)"""
    now = get_kst_now()
    if now.weekday() >= 5: # 주말
        return False
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=40, second=0, microsecond=0)
    return start_time <= now <= end_time

def get_kr_indices():
    """장중 실시간 / 장외 고정 데이터 안정적으로 가져오기"""
    try:
        now = get_kst_now()
        today_str = now.strftime("%Y%m%d")
        
        # 오늘 하루만 검색하면 휴장일/새벽에 에러가 나므로, 최근 7일치 중 가장 마지막 데이터를 무조건 가져옵니다.
        past_str = (now - timedelta(days=7)).strftime("%Y%m%d")
        
        df_k = stock.get_index_status_by_date(past_str, today_str, "KOSPI")
        df_q = stock.get_index_status_by_date(past_str, today_str, "KOSDAQ")
        
        if not df_k.empty and not df_q.empty:
            return {
                "KOSPI": {"val": df_k['종가'].iloc[-1], "diff": df_k['대비'].iloc[-1], "rate": df_k['등락률'].iloc[-1]},
                "KOSDAQ": {"val": df_q['종가'].iloc[-1], "diff": df_q['대비'].iloc[-1], "rate": df_q['등락률'].iloc[-1]}
            }
        return None
    except:
        return None

# 야후 파이낸스 티커 (나스닥 종합지수 추가)
yahoo_tickers = {
    "해외 지수 및 환율": {
        "S&P 500 지수": "^GSPC",
        "나스닥 100 선물": "NQ=F",
        "나스닥 종합지수": "^IXIC", # 새로 추가됨
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
        # --- 1. 국내 지수 섹션 ---
        st.subheader("📍 국내 주요 지수")
        kr_data = get_kr_indices()
        cols1 = st.columns(3)
        
        # 데이터가 없어도 칸이 사라지지 않도록 방어 코드 추가
        if kr_data:
            cols1[0].metric("코스피 (KOSPI)", f"{kr_data['KOSPI']['val']:,.2f}", f"{kr_data['KOSPI']['diff']:,.2f} ({kr_data['KOSPI']['rate']:.2f}%)")
            cols1[1].metric("코스닥 (KOSDAQ)", f"{kr_data['KOSDAQ']['val']:,.2f}", f"{kr_data['KOSDAQ']['diff']:,.2f} ({kr_data['KOSDAQ']['rate']:.2f}%)")
        else:
            cols1[0].metric("코스피 (KOSPI)", "데이터 계산 중...", "0")
            cols1[1].metric("코스닥 (KOSDAQ)", "데이터 계산 중...", "0")
        
        # 야후 데이터 호출
        all_y_symbols = [sym for group in yahoo_tickers.values() for sym in group.values()]
        y_data = yf.download(all_y_symbols, period="2d", interval="1m", progress=False)['Close']

        # 환율 표시 (국내 지수 옆 3번째 칸)
        try:
            ex_rate = y_data['KRW=X'].dropna().iloc[-1]
            cols1[2].metric("원/달러 환율", f"{ex_rate:,.2f}", "")
        except: 
            cols1[2].metric("원/달러 환율", "대기 중", "")

        # --- 2. 해외 및 원자재 섹션 ---
        for category, items in yahoo_tickers.items():
            st.subheader(f"📍 {category}")
            cols = st.columns(3)
            
            # 원/달러 환율은 위에서 표시했으니 반복문에서는 제외
            display_items = {k: v for k, v in items.items() if k != "원/달러 환율"}
            
            for idx, (name, sym) in enumerate(display_items.items()):
                try:
                    current_val = y_data[sym].dropna().iloc[-1]
                    cols[idx % 3].metric(label=name, value=f"{current_val:,.2f}", delta="")
                except:
                    cols[idx % 3].metric(label=name, value="대기 중")

    # 하단 상태 업데이트 (한국 시간 적용)
    now_time_str = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
    market_status = "장중 실시간" if is_market_open() else "장외/휴장 데이터 고정"
    status_area.markdown(f"<p style='text-align: center; color: #666;'>{market_status} 동기화 중... (갱신: {now_time_str} KST)</p>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()
