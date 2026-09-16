"""통계 페이지."""

import pandas as pd
import streamlit as st

from crawler import analyze_papers
from ui_helpers import CSV_CHOICES, load_csv

st.title("통계", icon=":material/insights:")
st.caption("선택한 CSV의 논문 수, 저자 수 평균, 최빈 키워드를 계산합니다.")

choice = st.selectbox("분석할 CSV", list(CSV_CHOICES.keys()), key="stats_csv")
df = load_csv(CSV_CHOICES[choice])

if df.empty:
    st.info("분석할 데이터가 없습니다. 먼저 논문을 크롤링하세요.")
else:
    records = df.to_dict(orient="records")
    stats = analyze_papers(records)

    m1, m2, m3 = st.columns(3)
    m1.metric("총 논문 수", stats["total_papers"])
    m2.metric("저자 수 평균", f"{stats['avg_authors']:.2f}")
    if stats["top_keyword"]:
        m3.metric(
            "가장 많이 나온 키워드",
            f"{stats['top_keyword']} ({stats['top_keyword_count']}회)",
        )
    else:
        m3.metric("가장 많이 나온 키워드", "없음")

    if "categories" in df.columns:
        st.subheader("카테고리 분포", divider="green")
        cat_counts = (
            df["categories"]
            .astype(str)
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .head(15)
            .rename_axis("category")
            .reset_index(name="count")
        )
        if not cat_counts.empty:
            st.bar_chart(cat_counts, x="category", y="count", horizontal=True)
        else:
            st.caption("카테고리 값이 없습니다.")
