"""데이터 보기 페이지."""

import streamlit as st

from ui_helpers import CSV_CHOICES, download_csv_button, load_csv, show_dataframe

st.title("데이터 보기", icon=":material/table_view:")
st.caption("저장된 CSV를 선택해 미리보고 다운로드합니다.")

choice = st.selectbox("CSV 파일", list(CSV_CHOICES.keys()))
path = CSV_CHOICES[choice]
df = load_csv(path)

if not path.exists():
    st.warning(f"{choice} 파일이 아직 없습니다.")
else:
    st.caption(f"{path} · {len(df)}행 · {len(df.columns)}열")
    show_dataframe(df)
    download_csv_button(df, choice, f"{choice} 다운로드")

    if "summary_one_line" in df.columns and not df.empty:
        st.subheader("요약 미리보기", divider="green")
        preview_cols = [
            c
            for c in [
                "arxiv_id",
                "title",
                "summary_one_line",
                "summary_easy",
                "real_world",
                "limitations",
            ]
            if c in df.columns
        ]
        show_dataframe(df[preview_cols], height=360)
