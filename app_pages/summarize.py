"""단일 요약 페이지."""

import streamlit as st

from summarize_paper import MODEL_NAME, summarize_paper
from ui_helpers import PAPER_CSV, SUMMARY_CSV, has_gemini_key, load_csv

st.title("단일 요약", icon=":material/edit_note:")
st.caption(f"Gemini `{MODEL_NAME}`로 쉬운 한국어 요약을 만듭니다.")

if not has_gemini_key():
    st.error(".env.local에 GEMINI_API_KEY가 없습니다.")
    st.stop()

source = st.radio(
    "입력 방식",
    ["CSV에서 선택", "직접 입력", "최근 조회 논문"],
    horizontal=True,
)

title = ""
abstract = ""

if source == "CSV에서 선택":
    csv_name = st.selectbox("CSV", ["paper.csv", "papers_with_summary.csv"])
    path = PAPER_CSV if csv_name == "paper.csv" else SUMMARY_CSV
    df = load_csv(path)
    if df.empty:
        st.info(f"{csv_name}에 논문이 없습니다.")
    else:
        labels = [
            f"{row.arxiv_id} · {str(row.title)[:70]}"
            for row in df.itertuples()
        ]
        picked = st.selectbox("논문", labels)
        row = df.iloc[labels.index(picked)]
        title = str(row["title"])
        abstract = str(row["abstract"])
elif source == "최근 조회 논문":
    paper = st.session_state.get("last_paper")
    if not paper:
        st.info("먼저 '단일 논문 조회'에서 논문을 불러오세요.")
    else:
        title = paper["title"]
        abstract = paper["abstract"]
        st.write(f"**선택됨:** {title}")
else:
    title = st.text_input("제목")
    abstract = st.text_area("초록", height=180)

if title:
    with st.expander("입력 미리보기", expanded=False):
        st.write(title)
        st.write(abstract)

if st.button("요약 생성", type="primary", icon=":material/auto_awesome:", disabled=not (title and abstract)):
    with st.spinner("Gemini 요약 생성 중..."):
        try:
            result = summarize_paper(title, abstract)
            st.session_state["last_summary"] = result
            st.success("요약 완료")
        except Exception as exc:
            st.error(f"요약 실패: {exc}")

result = st.session_state.get("last_summary")
if result:
    st.subheader("한줄 요약", divider="green")
    st.info(result["summary_one_line"])
    st.subheader("쉬운 설명")
    st.write(result["summary_easy"])
    st.subheader("현실 적용")
    st.write(result["real_world"])
    st.subheader("한계점")
    st.write(result["limitations"])
    st.json(result)
