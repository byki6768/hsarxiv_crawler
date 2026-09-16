"""일괄 요약 페이지."""

from pathlib import Path

import streamlit as st

from process_all_papers import SUMMARY_COLUMNS, process_all_papers
from ui_helpers import (
    CSV_CHOICES,
    PAPER_CSV,
    SUMMARY_CSV,
    download_csv_button,
    has_gemini_key,
    load_csv,
    show_dataframe,
)

st.title("일괄 요약", icon=":material/playlist_add_check:")
st.caption("CSV의 모든 논문에 Gemini 한국어 요약 칼럼을 추가합니다.")

if not has_gemini_key():
    st.error(".env.local에 GEMINI_API_KEY가 없습니다.")
    st.stop()

with st.form("batch_summary_form"):
    input_name = st.selectbox(
        "입력 CSV",
        [name for name, path in CSV_CHOICES.items() if path.exists() or name == "paper.csv"],
        index=0,
    )
    output_name = st.text_input("출력 파일명", value="papers_with_summary.csv")
    delay = st.number_input("요청 사이 대기(초)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)
    submitted = st.form_submit_button(
        "일괄 요약 시작",
        type="primary",
        icon=":material/play_arrow:",
    )

if submitted:
    input_csv = CSV_CHOICES.get(input_name, PAPER_CSV)
    output_csv = SUMMARY_CSV if output_name.strip() == "papers_with_summary.csv" else Path(output_name.strip())
    if not output_csv.is_absolute():
        output_csv = PAPER_CSV.parent / output_csv

    if not input_csv.exists():
        st.error(f"입력 파일이 없습니다: {input_csv}")
    else:
        progress = st.progress(0.0, text="준비 중...")
        status = st.empty()

        def on_progress(position, total, message, state):
            progress.progress(
                position / total if total else 1.0,
                text=f"[{position}/{total}] {message}",
            )
            if state == "error":
                status.error(message)
            elif state == "done":
                status.success(message)
            else:
                status.info(message)

        try:
            df = process_all_papers(
                input_csv=input_csv,
                output_csv=output_csv,
                delay=float(delay),
                progress_callback=on_progress,
            )
            filled = df[SUMMARY_COLUMNS].astype(str).ne("").all(axis=1).sum()
            st.success(f"저장 완료: {output_csv.name} (요약 채움 {filled}/{len(df)})")
            st.session_state["batch_summary_df"] = df
        except Exception as exc:
            st.error(f"일괄 요약 실패: {exc}")

df = st.session_state.get("batch_summary_df")
if df is None and SUMMARY_CSV.exists():
    df = load_csv(SUMMARY_CSV)

if df is not None and not df.empty:
    st.subheader("결과 미리보기", divider="green")
    cols = [c for c in ["arxiv_id", "title", *SUMMARY_COLUMNS] if c in df.columns]
    show_dataframe(df[cols])
    download_csv_button(df, "papers_with_summary.csv", "결과 CSV 다운로드")
