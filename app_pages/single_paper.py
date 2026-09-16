"""단일 논문 조회 페이지."""

import streamlit as st

from crawler import ABS_URL_TEMPLATE, SAMPLE_ABS_URL, extract_paper_info

st.title("단일 논문 조회", icon=":material/description:")
st.caption("arXiv abs URL 또는 ID로 메타데이터를 추출합니다.")

with st.form("single_paper_form"):
    source = st.text_input(
        "논문 URL 또는 arXiv ID",
        value=SAMPLE_ABS_URL,
        placeholder="https://arxiv.org/abs/2301.00001 또는 2301.00001",
    )
    submitted = st.form_submit_button(
        "조회",
        type="primary",
        icon=":material/search:",
    )

if submitted:
    value = source.strip()
    if not value:
        st.error("URL 또는 ID를 입력하세요.")
    else:
        url = value if value.startswith("http") else ABS_URL_TEMPLATE.format(arxiv_id=value)
        with st.spinner(f"가져오는 중: {url}"):
            try:
                paper = extract_paper_info(url)
            except Exception as exc:
                st.error(f"조회 실패: {exc}")
            else:
                st.session_state["last_paper"] = paper

paper = st.session_state.get("last_paper")
if paper:
    st.subheader(paper["title"], divider="green")
    st.write(f"**arXiv ID:** `{paper['arxiv_id']}`")
    st.write(f"**저자:** {', '.join(paper['authors']) if isinstance(paper['authors'], list) else paper['authors']}")
    st.write(f"**제출일:** {paper['submitted_date']}")
    st.write(f"**카테고리:** {paper['categories']}")
    st.markdown(f"[초록 페이지]({ABS_URL_TEMPLATE.format(arxiv_id=paper['arxiv_id'])}) · [PDF]({paper['pdf_url']})")
    with st.expander("초록", expanded=True):
        st.write(paper["abstract"])
    st.json(paper)
