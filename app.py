import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 設定網頁標題
st.set_page_config(page_title="台股永續高息投資助手", layout="centered")

st.title("📈 台股 ETF 蒙地卡羅模擬器")
st.write("針對 **00888, 00878, 00713** 的混合配置分析")

# 側邊欄設定
st.sidebar.header("投資參數設定")
initial_investment = st.sidebar.number_input("初始投入金額", value=100000, step=10000)
monthly_investment = st.sidebar.number_input("每月定期定額", value=10000, step=1000)
years = st.sidebar.slider("投資年限 (年)", 1, 20, 10)
simulations = st.sidebar.selectbox("模擬次數", [1000, 5000, 10000], index=0)

# 權重設定
st.sidebar.subheader("投資比例 (%)")
w_888 = st.sidebar.slider("00888 (產投高息)", 0, 100, 40)
w_878 = st.sidebar.slider("00878 (永續高息)", 0, 100, 30)
w_713 = st.sidebar.slider("00713 (高息低波)", 0, 100, 30)

if st.button("開始執行模擬"):
    if w_888 + w_878 + w_713 != 100:
        st.error("錯誤：投資比例總和必須等於 100%！")
    else:
        with st.spinner('數據抓取與計算中...'):
            # 1. 抓取數據
            tickers = ['00888.TW', '00878.TW', '00713.TW']
            weights = np.array([w_888, w_878, w_713]) / 100
            
            data = yf.download(tickers, period="5y")['Close']
            returns = data.pct_change().dropna()
            
            # 2. 計算投資組合報酬
            portfolio_returns = returns.dot(weights)
            mu = portfolio_returns.mean()
            sigma = portfolio_returns.std()
            
            # 3. 蒙地卡羅模擬 (定期定額路徑)
            months = years * 12
            all_paths = []
            
            for _ in range(simulations):
                balance = initial_investment
                path = [balance]
                for _ in range(months):
                    monthly_ret = np.random.normal(mu * 21, sigma * np.sqrt(21))
                    balance = (balance + monthly_investment) * (1 + monthly_ret)
                    path.append(balance)
                all_paths.append(path)
            
            all_paths = np.array(all_paths)
            final_values = all_paths[:, -1]
            
            # 4. 顯示結果指標
            total_invested = initial_investment + (monthly_investment * months)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("總投入本金", f"${total_invested:,.0f}")
            col2.metric("預期平均價值", f"${final_values.mean():,.0f}")
            col3.metric("勝率 (不賠本)", f"{np.mean(final_values > total_invested):.1%}")
            
            # 5. 繪製圖表
            st.subheader("未來資產走勢預測")
            fig, ax = plt.subplots()
            x_range = np.arange(months + 1)
            # 畫出部分路徑以增加可視化效果
            for i in range(min(simulations, 50)):
                ax.plot(x_range, all_paths[i], color='gray', alpha=0.1)
            
            ax.plot(x_range, np.percentile(all_paths, 50, axis=0), color='blue', label='中位數路徑')
            ax.plot(x_range, np.percentile(all_paths, 5, axis=0), color='red', linestyle='--', label='保守情況(5%)')
            ax.fill_between(x_range, np.percentile(all_paths, 5, axis=0), np.percentile(all_paths, 95, axis=0), color='blue', alpha=0.1)
            
            ax.set_xlabel("月份")
            ax.set_ylabel("資產價值")
            ax.legend()
            st.pyplot(fig)

            st.success("分析完成！這是一個基於歷史數據的機率預測，投資請謹慎評估風險。")
