"""
reporter.py
매매 완료 후 CSV 리포트 저장
- 미국장/국내장 각각 하나의 파일에 누적 저장
- reports/미국장.csv, reports/국내장.csv
"""

import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")


def _ensure_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_report(market: str, trades: list, holdings: dict,
                cash: float, total_assets: float,
                tqqq_base: float, prices: dict, currency: str,
                total_assets_krw: float = 0.0, usd_krw_rate: float = 0.0):
    _ensure_dir()
    unit     = "$" if currency == "USD" else "₩"
    filename = os.path.join(REPORT_DIR, f"{market}.csv")
    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # 최초 생성 시 컬럼 헤더
        if not file_exists:
            writer.writerow([
                "기록시각", "현금잔고", "총자산",
                "원화환산총자산", "환율", "TQQQ기준금",
                "매매구분", "종목", "수량", "가격",
                "잔고종목", "보유수량", "현재가", "현재가치"
            ])

        now_str    = _now()
        cash_fmt   = f"{cash:,.2f}"          if currency == "USD" else f"{int(cash):,}"
        assets_fmt = f"{total_assets:,.2f}"  if currency == "USD" else f"{int(total_assets):,}"
        krw_fmt    = f"{int(total_assets_krw):,}" if total_assets_krw > 0 else ""
        rate_fmt   = f"{usd_krw_rate:,.2f}"  if usd_krw_rate > 0 else ""
        base_fmt   = f"{tqqq_base:,.2f}"     if tqqq_base > 0 else ""

        # 매매 내역
        if trades:
            for i, t in enumerate(trades):
                price_fmt = f"{t['price']:,.2f}" if currency == "USD" else f"{int(t['price']):,}"
                if i == 0:
                    writer.writerow([
                        now_str, cash_fmt, assets_fmt, krw_fmt, rate_fmt, base_fmt,
                        t["action"], t["ticker"], t["qty"], price_fmt,
                        "", "", "", ""
                    ])
                else:
                    writer.writerow([
                        "", "", "", "", "", "",
                        t["action"], t["ticker"], t["qty"], price_fmt,
                        "", "", "", ""
                    ])
        else:
            writer.writerow([
                now_str, cash_fmt, assets_fmt, krw_fmt, rate_fmt, base_fmt,
                "거래없음", "", "", "",
                "", "", "", ""
            ])

        # 잔고 현황
        for ticker, info in holdings.items():
            qty       = info["qty"]
            curr      = prices.get(ticker, 0)
            value     = qty * curr
            p_fmt     = f"{curr:,.2f}"  if currency == "USD" else f"{int(curr):,}"
            v_fmt     = f"{value:,.2f}" if currency == "USD" else f"{int(value):,}"
            writer.writerow([
                "", "", "", "", "", "",
                "", "", "", "",
                ticker, qty, p_fmt, v_fmt
            ])

        # 구분선
        writer.writerow(["─" * 10] + [""] * 13)

    logger.info(f"리포트 저장: {filename}")
    return filename
