"""홈 페이지."""

from pathlib import Path

import streamlit as st

from ui_helpers import (
    ARXIV_PAPERS_CSV,
    CS_AI_RECENT_CSV,
    LOG_PATH,
    PAPER_CSV,
    SUMMARY_CSV,
    csv_info,
    has_gemini_key,
)

st.title("hsarxiv crawler", icon=":material/auto_stories:")
st.caption("arXiv 논문 수집 · 안전 크롤링 · Gemini 쉬운 한국어 요약")

cols = st.columns(4)
files = [
    ("paper.csv", PAPER_CSV),
    ("요약 CSV", SUMMARY_CSV),
    ("arxiv_papers.csv", ARXIV_PAPERS_CSV),
    ("cs.AI 10편", CS_AI_RECENT_CSV),
]
for col, (label, path) in zip(cols, files, strict=True):
    exists, count = csv_info(path)
    col.metric(label, f"{count}편" if exists else "없음")

st.divider()

with st.container(border=True):
    st.subheader("할 수 있는 일", divider="green")
    st.markdown(
        """
1. **논문 크롤링** — 카테고리 최신 논문 ID 수집 후 안전하게 크롤링  
2. **단일 논문 조회** — abs URL/ID로 메타데이터 추출  
3. **단일 요약** — Gemini로 쉬운 한국어 요약 4항목 생성  
4. **일괄 요약** — CSV 전체에 요약 칼럼 추가  
5. **데이터 보기 / 통계** — 결과 확인과 키워드·저자 통계
        """
    )

status_cols = st.columns(3)
with status_cols[0]:
    st.write("Gemini API")
    if has_gemini_key():
        st.success(".env.local 키 감지됨", icon=":material/check_circle:")
    else:
        st.warning(".env.local에 GEMINI_API_KEY를 넣어 주세요", icon=":material/key:")
with status_cols[1]:
    st.write("크롤 로그")
    if LOG_PATH.exists():
        st.info(f"{LOG_PATH.name} 있음", icon=":material/history:")
    else:
        st.caption("아직 로그 없음")
with status_cols[2]:
    st.write("작업 폴더")
    st.code(str(Path(__file__).resolve().parents[1]), language=None)
