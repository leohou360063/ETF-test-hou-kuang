import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 設定網頁
st.set_page_config(page_title="台股投資助手", layout="centered")
st.title("📈 台股 ETF 蒙地卡羅模擬器")
st.write("針對 00888, 00878, 00713 的混合配置分析")

# 側邊欄設定
st.sidebar.header("投資參數設定")
init_inv = st.sidebar.number_input("初始投入金額", value=100000, step=10000)
mon_inv = st.sidebar.number_input("每月定期定額", value=10000, step=1000)
years = st.sidebar.slider("投資年限 (年)", 1, 20, 10)

# 權重設定
st.sidebar.subheader("投資比例 (%)")
w_888 = st.sidebar.slider("00888 (產投高息)", 0, 100, 40)
w_878 = st.sidebar.slider("00878 (永續高息)", 0, 100, 30)
w_713 = st.sidebar.slider("00713 (高息低波)", 0, 100, 30)

if st.button("開始執行模擬"):
    if w_888 + w_878 + w_713 != 100:
        st.error("錯誤：投資比例總和必須等於 100%！請重新調整拉桿。")
    else:
        with st.spinner('正在與 Yahoo Finance 連線中... (為了穩定度，採用分批抓取)'):
            tickers = ['00888.TW', '00878.TW', '00713.TW']
            weights = np.array([w_888, w_878, w_713]) / 100
            
            # --- 終極穩定抓取法：逐一抓取 ---
            df = pd.DataFrame()
            try:
                for ticker in tickers:
                    # 一檔一檔要資料，避開 Yahoo 阻擋機制
                    data = yf.Ticker(ticker).history(period="1y")
                    if not data.empty:
                        df[ticker] = data['Close']
                        
                # 確保我們有抓到這三檔的資料
                if len(df.columns) == 3:
                    df = df.ffill().dropna()
                    rets = df.pct_change().dropna()
                    
                    if not rets.empty:
                        # 核心計算
                        port_rets = rets.dot(weights)
                        mu, sigma = port_rets.mean(), port_rets.std()
                        months = years * 12
                        all_paths = []
                        
                        # 手機版跑 500 次最順暢
                        for _ in range(500): 
                            m_rets = np.random.normal(mu * 21, sigma * np.sqrt(21), months)
                            path = [init_inv]
                            for r in m_rets:
                                path.append((path[-1] + mon_inv) * (1 + r))
                            all_paths.append(path)
                        
                        all_paths = np.array(all_paths)
                        final_v = all_paths[:, -1]
                        total_in = init_inv + (mon_inv * months)
                        
                        # 顯示數據
                        st.divider()
                        c1, c2, c3 = st.columns(3)
                        c1.metric("總投入本金", f"${total_in:,.0f}")
                        c2.metric("預期平均價值", f"${final_v.mean():,.0f}")
                        c3.metric("勝率 (不賠本)", f"{np.mean(final_v > total_in):.1%}")
                        
                        # 繪圖
                        st.subheader("未來資產走勢預測")
                        fig, ax = plt.subplots(figsize=(8, 5))
                        ax.plot(np.percentile(all_paths, 50, axis=0), color='#1f77b4', label='預期中位數路徑', linewidth=2)
                        ax.fill_between(range(months+1), np.percentile(all_paths, 5, axis=0), np.percentile(all_paths, 95, axis=0), alpha=0.2, color='#1f77b4', label='90% 機率落點區間')
                        ax.axhline(total_in, color='#d62728', linestyle='--', label='總投入本金水位')
                        ax.set_xlabel("投資月份")
                        ax.set_ylabel("資產價值 (TWD)")
                        ax.legend()
                        st.pyplot(fig)
                    else:
                        st.error("計算時發生問題，請稍後再試。")
                else:
                    st.warning("Yahoo 目前限制了雲端伺服器的連線，請過 1 分鐘後再點擊一次按鈕。")
            except Exception as e:
                st.error("網路連線不穩，請重新整理網頁後再試一次。")
