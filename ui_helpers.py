"""공통 UI 헬퍼."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
PAPER_CSV = BASE_DIR / "paper.csv"
SUMMARY_CSV = BASE_DIR / "papers_with_summary.csv"
ARXIV_PAPERS_CSV = BASE_DIR / "arxiv_papers.csv"
CS_AI_RECENT_CSV = BASE_DIR / "cs_ai_recent_10.csv"
LOG_PATH = BASE_DIR / "crawl.log"
ENV_PATH = BASE_DIR / ".env.local"

CSV_CHOICES = {
    "paper.csv": PAPER_CSV,
    "papers_with_summary.csv": SUMMARY_CSV,
    "arxiv_papers.csv": ARXIV_PAPERS_CSV,
    "cs_ai_recent_10.csv": CS_AI_RECENT_CSV,
}


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig").fillna("")


def csv_info(path: Path) -> tuple[bool, int]:
    if not path.exists():
        return False, 0
    try:
        return True, len(pd.read_csv(path, encoding="utf-8-sig"))
    except Exception:
        return True, 0


def has_gemini_key() -> bool:
    try:
        if "GEMINI_API_KEY" in st.secrets and str(st.secrets["GEMINI_API_KEY"]).strip():
            return True
    except Exception:
        pass

    if not ENV_PATH.exists():
        return False
    text = ENV_PATH.read_text(encoding="utf-8")
    return "GEMINI_API_KEY=" in text and len(text.split("=", 1)[-1].strip()) > 0


def show_dataframe(df: pd.DataFrame, *, height: int = 420) -> None:
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return
    st.dataframe(df, height=height, width="stretch")


def download_csv_button(df: pd.DataFrame, filename: str, label: str) -> None:
    if df.empty:
        return
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        width="content",
    )
