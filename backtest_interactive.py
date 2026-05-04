"""
backtest_interactive.py
대화형 백테스터 - 종목/기간 자유 설정!

실행: pip install yfinance pandas numpy
     python backtest_interactive.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")


def get_date_input(prompt):
    """날짜 입력 받기"""
    print(prompt)
    while True:
        try:
            year = int(input("  년 (예: 2018): "))
            month = int(input("  월 (예: 1): "))
            day = int(input("  일 (예: 1): "))
            date = datetime(year, month, day)
            return date.strftime("%Y-%m-%d")
        except:
            print("⚠️ 올바른 날짜를 입력해주세요.")


def get_user_config():
    """사용자 입력으로 설정 생성"""
    print("="*60)
    print("  🎯 GBV 백테스터")
    print("="*60)
    print()
    
    # 기간 설정
    print("-" * 60)
    print("  📅 백테스트 기간 설정")
    print("-" * 60)
    start_date = get_date_input("\n백테스트 시작일 입력")
    end_date = get_date_input("\n백테스트 종료일 입력")
    print()
    
    # 초기 자산
    while True:
        try:
            initial_cash = float(input("초기 자산 (USD) (예: 10000): "))
            if initial_cash > 0:
                break
            print("⚠️ 양수를 입력해주세요.")
        except:
            print("⚠️ 숫자를 입력해주세요.")
    
    print()
    
    # 월 납입금 (원화)
    print("-" * 60)
    print("  💴 월 납입금 설정 (원화 → 달러 환전 후 현금 버킷 적립)")
    print("-" * 60)
    while True:
        try:
            monthly_deposit_krw = float(input("월 납입금 (원화, 없으면 0): ₩"))
            if monthly_deposit_krw >= 0:
                break
            print("⚠️ 0 이상의 값을 입력해주세요.")
        except:
            print("⚠️ 숫자를 입력해주세요.")
    print()
    
    # 종목 추가
    tickers = []
    
    while True:
        print("-" * 60)
        print("  📊 종목 추가")
        print("-" * 60)
        
        # 티커
        ticker = input("티커 입력 (예: TQQQ, UGL, SOXL): ").strip().upper()
        if not ticker:
            print("⚠️ 티커를 입력해주세요.")
            continue
        
        # 비중
        while True:
            try:
                weight = float(input("비중 (%) (예: 40): "))
                if 0 < weight <= 100:
                    break
                print("⚠️ 0~100 사이의 값을 입력해주세요.")
            except:
                print("⚠️ 숫자를 입력해주세요.")
        
        # 월 증액률
        while True:
            try:
                monthly_rate = float(input("월 증액률 (%) (예: 2, 증액 없으면 0): "))
                if monthly_rate >= 0:
                    break
                print("⚠️ 0 이상의 값을 입력해주세요.")
            except:
                print("⚠️ 숫자를 입력해주세요.")
        
        # 저장
        base_amount = initial_cash * (weight / 100)
        tickers.append({
            "ticker": ticker,
            "base_amount": base_amount,
            "monthly_rate": monthly_rate / 100,
        })
        
        print(f"\n✅ {ticker} 추가 완료!")
        print(f"   기준금: ${base_amount:,.0f}")
        print(f"   월증액: {monthly_rate}%")
        print()
        
        # 계속?
        continue_input = input("종목을 더 추가하시겠습니까? (y/n): ").strip().lower()
        if continue_input != 'y':
            break
        print()
    
    # 설정 완성
    config = {
        "start_date": start_date,
        "end_date": end_date,
        "initial_cash_usd": initial_cash,
        "monthly_deposit_krw": monthly_deposit_krw,
        "tickers": tickers,
        "commission": 0.0015,
    }
    
    # 확인
    print()
    print("="*60)
    print("  📋 설정 확인")
    print("="*60)
    print(f"기간: {start_date} ~ {end_date}")
    print(f"초기 자산: ${initial_cash:,.0f}")
    print(f"\n종목 목록:")
    for t in tickers:
        print(f"  - {t['ticker']}: ${t['base_amount']:,.0f}, 월증액 {t['monthly_rate']*100:.1f}%")
    if monthly_deposit_krw > 0:
        print(f"\n월 납입금:     ₩{monthly_deposit_krw:,.0f} (매월 첫 거래일 환전 후 현금 적립)")
    else:
        print(f"\n월 납입금:     없음")
    print("="*60)
    print()
    
    input("Enter 키를 눌러 백테스트를 시작하세요...")
    
    return config


def fetch_data(config):
    """데이터 수집"""
    print("\n📥 데이터 수집 중...")
    
    start_date = config["start_date"]
    end_date = config["end_date"]
    
    ticker_list = [t["ticker"] for t in config["tickers"]]
    ticker_list.append("KRW=X")
    
    prices = {}
    adjusted_start = start_date
    
    for ticker in ticker_list:
        try:
            # 전체 기간 다운로드 (시작일 확인용)
            df = yf.download(ticker, start="2000-01-01", end=end_date, progress=False)
            
            if df.empty:
                print(f"  ⚠️ {ticker} 데이터 없음")
                continue
            
            # 실제 시작일 확인
            actual_start = df.index[0].strftime("%Y-%m-%d")
            
            if actual_start > start_date:
                print(f"  ⚠️ {ticker}는 {actual_start}부터 데이터가 있습니다.")
                print(f"     → {actual_start}부터 시작합니다.")
                
                # 가장 늦은 시작일로 조정
                if actual_start > adjusted_start:
                    adjusted_start = actual_start
            
            # 데이터 저장
            if isinstance(df.columns, pd.MultiIndex):
                prices[ticker if ticker != "KRW=X" else "USDKRW"] = df["Close"].squeeze()
            else:
                prices[ticker if ticker != "KRW=X" else "USDKRW"] = df["Close"]
            
            print(f"  ✅ {ticker} 수집 완료")
            
        except Exception as e:
            print(f"  ⚠️ {ticker} 수집 실패: {e}")
    
    # 조정된 시작일 적용
    if adjusted_start > start_date:
        print(f"\n⚠️ 실제 백테스트 시작일: {adjusted_start}")
        config["actual_start_date"] = adjusted_start
    else:
        config["actual_start_date"] = start_date
    
    return prices


def run_backtest(prices, config):
    """백테스트 실행"""
    print("\n🚀 백테스트 시작...")
    
    # 활성 종목
    ticker_configs = {t["ticker"]: t for t in config["tickers"]}
    active_tickers = list(ticker_configs.keys())
    
    # 공통 인덱스
    common_idx = None
    for ticker in active_tickers:
        if ticker not in prices:
            continue
        if common_idx is None:
            common_idx = prices[ticker].index
        else:
            common_idx = common_idx.intersection(prices[ticker].index)
    
    if common_idx is None:
        print("⚠️ 공통 데이터가 없습니다!")
        return None
    
    # 시작일/종료일로 필터링
    actual_start = pd.to_datetime(config["actual_start_date"])
    end_date = pd.to_datetime(config["end_date"])
    common_idx = common_idx[(common_idx >= actual_start) & (common_idx <= end_date)]
    common_idx = common_idx.sort_values()
    
    if len(common_idx) == 0:
        print("⚠️ 해당 기간에 데이터가 없습니다!")
        return None
    
    # 초기값
    cash = config["initial_cash_usd"]
    holdings = {}
    
    # 종목별 기준금
    bases = {}
    for ticker in active_tickers:
        bases[ticker] = ticker_configs[ticker]["base_amount"]
    
    last_increased_month = None
    records = []
    
    for date in common_idx:
        # 현재가
        current_prices = {}
        for ticker in active_tickers:
            if ticker not in prices:
                continue
            p = float(prices[ticker].get(date, 0) or 0)
            if p <= 0:
                continue
            current_prices[ticker] = p
        
        p_usdkrw = float(prices.get("USDKRW", pd.Series()).get(date, 1300) or 1300)
        
        if not current_prices:
            continue
        
        # 월 증액 + 납입금 처리
        current_month = date.strftime("%Y-%m")
        deposited_usd = 0.0
        if current_month != last_increased_month:
            # 기준금 증액
            for ticker in active_tickers:
                rate = ticker_configs[ticker]["monthly_rate"]
                if rate > 0:
                    bases[ticker] *= (1 + rate)
            # 월 납입금: 원화 → 당일 환율로 달러 환전 → 현금 버킷 적립
            deposit_krw = config.get("monthly_deposit_krw", 0)
            if deposit_krw > 0:
                deposited_usd = deposit_krw / p_usdkrw
                cash += deposited_usd
            last_increased_month = current_month
        
        trades = []
        
        # 각 종목 GBV 리밸런싱
        for ticker in active_tickers:
            if ticker not in current_prices:
                continue
            
            price = current_prices[ticker]
            base = bases[ticker]
            current_qty = holdings.get(ticker, 0)
            current_value = current_qty * price
            
            diff = base - current_value
            if abs(diff) >= price:
                if diff > 0:
                    buy_qty = int(abs(diff) / price)
                    if buy_qty > 0:
                        cost = buy_qty * price * (1 + config["commission"])
                        if cost <= cash:
                            holdings[ticker] = holdings.get(ticker, 0) + buy_qty
                            cash -= cost
                            trades.append(f"매수 {ticker} {buy_qty}주")
                else:
                    sell_qty = min(int(abs(diff) / price), current_qty)
                    if sell_qty > 0:
                        proceeds = sell_qty * price * (1 - config["commission"])
                        holdings[ticker] = holdings.get(ticker, 0) - sell_qty
                        cash += proceeds
                        trades.append(f"매도 {ticker} {sell_qty}주")
        
        # 총 자산
        total_usd = cash
        for ticker, qty in holdings.items():
            total_usd += qty * current_prices.get(ticker, 0)
        
        total_krw = total_usd * p_usdkrw
        
        records.append({
            "date": date,
            "cash_usd": cash,
            **{f"{t}_qty": holdings.get(t, 0) for t in active_tickers},
            "total_usd": total_usd,
            "total_krw": total_krw,
            "usdkrw": p_usdkrw,
            "deposited_usd": deposited_usd,
            "trades": " | ".join(trades) if trades else "",
        })
    
    df = pd.DataFrame(records).set_index("date")
    print(f"  ✅ 백테스트 완료: {len(df)}일")
    return df


def calc_metrics(df, config):
    """성과 분석 - USD / KRW 두 가지 기준"""
    print("\n📊 성과 분석 중...")

    total_days = (df.index[-1] - df.index[0]).days
    years      = total_days / 365.25
    trade_days = (df["trades"] != "").sum()
    period_str = f"{df.index[0].date()} ~ {df.index[-1].date()} ({total_days}일)"

    def _m(series, initial):
        final     = series.iloc[-1]
        tot_ret   = (final - initial) / initial
        cagr      = (final / initial) ** (1 / years) - 1 if years > 0 else 0
        roll_max  = series.cummax()
        mdd       = ((series - roll_max) / roll_max).min()
        mar       = abs(cagr / mdd) if mdd != 0 else float("inf")
        dr        = series.pct_change().dropna()
        sharpe    = (dr.mean() / dr.std()) * np.sqrt(252) if dr.std() > 0 else 0
        win_rate  = (series.resample("ME").last().pct_change().dropna() > 0).mean()
        return tot_ret, cagr, mdd, mar, sharpe, win_rate

    # USD 기준
    initial_usd = config["initial_cash_usd"]
    final_usd   = df["total_usd"].iloc[-1]
    u = _m(df["total_usd"], initial_usd)

    # KRW 기준 (환율 알파 포함)
    initial_krw = initial_usd * df["usdkrw"].iloc[0]
    final_krw   = df["total_krw"].iloc[-1]
    k = _m(df["total_krw"], initial_krw)

    # 환율 기여
    fx_start  = df["usdkrw"].iloc[0]
    fx_end    = df["usdkrw"].iloc[-1]
    fx_alpha  = (fx_end / fx_start) ** (1 / years) - 1 if years > 0 else 0

    return {
        "백테스트 기간":       period_str,
        "거래일수":            f"{trade_days}일 / {len(df)}일",
        # USD
        "초기 자산 (USD)":     f"${initial_usd:,.0f}",
        "최종 자산 (USD)":     f"${final_usd:,.0f}",
        "총 수익률 (USD)":     f"{u[0]:.2%}",
        "CAGR (USD)":          f"{u[1]:.2%}",
        "MDD (USD)":           f"{u[2]:.2%}",
        "MAR (USD)":           f"{u[3]:.3f}",
        "Sharpe (USD)":        f"{u[4]:.2f}",
        "월간 승률 (USD)":     f"{u[5]:.2%}",
        # KRW
        "초기 자산 (KRW)":     f"₩{int(initial_krw):,}",
        "최종 자산 (KRW)":     f"₩{int(final_krw):,}",
        "총 수익률 (KRW)":     f"{k[0]:.2%}",
        "CAGR (KRW)":          f"{k[1]:.2%}",
        "MDD (KRW)":           f"{k[2]:.2%}",
        "MAR (KRW)":           f"{k[3]:.3f}",
        "Sharpe (KRW)":        f"{k[4]:.2f}",
        "월간 승률 (KRW)":     f"{k[5]:.2%}",
        # 환율
        "USD/KRW 시작":        f"{fx_start:,.1f}",
        "USD/KRW 종료":        f"{fx_end:,.1f}",
        "환율 기여 CAGR":      f"{fx_alpha:.2%}  (KRW-USD = {k[1]-u[1]:.2%})",
        # 내부값 (save_results 참조용)
        "_usd_initial":        initial_usd,
        "_usd_final":          final_usd,
        "_krw_initial":        initial_krw,
        "_krw_final":          final_krw,
        # 납입금
        "_has_deposit":        config.get("monthly_deposit_krw", 0) > 0,
        "_deposit_krw":        config.get("monthly_deposit_krw", 0),
        "_total_deposited_usd": df["deposited_usd"].sum() if "deposited_usd" in df.columns else 0,
        "_total_deposited_krw": (df["deposited_usd"] * df["usdkrw"]).sum() if "deposited_usd" in df.columns else 0,
    }


def save_results(df, metrics):
    """결과 저장"""
    W = 62

    # 공통 정보
    print()
    print("=" * W)
    print("  📊 GBV 백테스트 결과")
    print("=" * W)
    print(f"  {'백테스트 기간':<22} {metrics['백테스트 기간']}")
    print(f"  {'거래일수':<22} {metrics['거래일수']}")

    # USD 섹션
    print()
    print(f"  💵 달러(USD) 기준")
    print("  " + "-" * (W - 2))
    usd_keys = ["초기 자산 (USD)", "최종 자산 (USD)", "총 수익률 (USD)",
                "CAGR (USD)", "MDD (USD)", "MAR (USD)",
                "Sharpe (USD)", "월간 승률 (USD)"]
    for k in usd_keys:
        print(f"  {k:<22} {metrics[k]}")

    # KRW 섹션
    print()
    print(f"  🇰🇷 원화(KRW) 기준  (환율 알파 포함)")
    print("  " + "-" * (W - 2))
    krw_keys = ["초기 자산 (KRW)", "최종 자산 (KRW)", "총 수익률 (KRW)",
                "CAGR (KRW)", "MDD (KRW)", "MAR (KRW)",
                "Sharpe (KRW)", "월간 승률 (KRW)"]
    for k in krw_keys:
        print(f"  {k:<22} {metrics[k]}")

    # 환율
    print()
    print(f"  💱 환율")
    print("  " + "-" * (W - 2))
    for k in ["USD/KRW 시작", "USD/KRW 종료", "환율 기여 CAGR"]:
        print(f"  {k:<22} {metrics[k]}")
    # 납입금 섹션 (있을 때만)
    if metrics.get("_has_deposit"):
        dep_krw = metrics["_deposit_krw"]
        total_dep_usd = metrics["_total_deposited_usd"]
        total_dep_krw = metrics["_total_deposited_krw"]
        print()
        print(f"  💴 월 납입금 효과")
        print("  " + "-" * (W - 2))
        print(f"  {'월 납입금':22} ₩{dep_krw:,.0f}")
        print(f"  {'총 납입 합계 (USD)':22} ${total_dep_usd:,.0f}")
        print(f"  {'총 납입 합계 (KRW)':22} ₩{total_dep_krw:,.0f}")
        # 납입금 제외 순수 투자 수익
        init_usd = metrics["_usd_initial"]
        final_usd = metrics["_usd_final"]
        pure_profit_usd = final_usd - init_usd - total_dep_usd
        print(f"  {'순수 투자수익 (USD)':22} ${pure_profit_usd:,.0f}  "
              f"(최종 - 초기 - 납입합계)")
    print("=" * W)

    # CSV 저장 (내부 키 _로 시작하는 것 제외)
    export = {k: v for k, v in metrics.items() if not k.startswith("_")}

    df.to_csv("backtest_result.csv", encoding="utf-8-sig")
    pd.DataFrame([export]).to_csv("backtest_metrics.csv",
                                   index=False, encoding="utf-8-sig")

    # 월별 수익률 USD / KRW 동시 저장
    monthly_usd = df["total_usd"].resample("ME").last().pct_change().dropna()
    monthly_krw = df["total_krw"].resample("ME").last().pct_change().dropna()
    monthly_df  = pd.DataFrame({"월별수익률_USD": monthly_usd,
                                 "월별수익률_KRW": monthly_krw})
    monthly_df.to_csv("backtest_monthly.csv", encoding="utf-8-sig")

    trades_df = df[df["trades"] != ""][["trades", "cash_usd", "total_usd", "total_krw"]]
    trades_df.to_csv("backtest_trades.csv", encoding="utf-8-sig")

    print("\n✅ 결과 저장 완료:")
    print("  - backtest_result.csv")
    print("  - backtest_metrics.csv  (USD + KRW 지표)")
    print("  - backtest_monthly.csv  (USD / KRW 월별 수익률)")
    print("  - backtest_trades.csv")


if __name__ == "__main__":
    config = get_user_config()
    prices = fetch_data(config)
    df = run_backtest(prices, config)
    
    if df is not None:
        metrics = calc_metrics(df, config)
        save_results(df, metrics)
    else:
        print("\n⚠️ 백테스트 실패!")
