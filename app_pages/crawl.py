"""논문 크롤링 페이지."""

from __future__ import annotations

import time
from datetime import datetime

import pandas as pd
import streamlit as st

from crawler import (
    ABS_URL_TEMPLATE,
    DEFAULT_LIST_URL,
    PAPER_COLUMNS,
    REQUEST_DELAY_SECONDS,
    _paper_to_row,
    analyze_papers,
    collect_arxiv_ids,
    extract_paper_info,
    get_existing_arxiv_ids,
    load_existing_papers,
    save_papers_append,
)
from ui_helpers import PAPER_CSV, show_dataframe

st.title("논문 크롤링", icon=":material/travel_explore:")
st.caption("카테고리 최신 논문을 안전하게 수집하고 paper.csv에 저장합니다.")

with st.form("crawl_form"):
    list_url = st.text_input(
        "목록 URL",
        value=DEFAULT_LIST_URL,
        help="예: https://arxiv.org/list/cs.AI/recent",
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        max_papers = st.number_input("수집할 논문 수", min_value=1, max_value=50, value=5)
    with c2:
        delay = st.number_input(
            "요청 전 대기(초)",
            min_value=0.0,
            max_value=60.0,
            value=float(REQUEST_DELAY_SECONDS),
            step=1.0,
            help="arXiv 예의를 위해 기본 15초를 권장합니다.",
        )
    with c3:
        skip_duplicates = st.checkbox("이미 저장된 ID 건너뛰기", value=True)

    submitted = st.form_submit_button(
        "크롤링 시작",
        type="primary",
        icon=":material/play_arrow:",
    )

if submitted:
    progress = st.progress(0.0, text="ID 수집 중...")
    status = st.empty()
    log_box = st.container(border=True)

    try:
        all_ids = collect_arxiv_ids(list_url)
        target_ids = all_ids[: int(max_papers)]
        status.info(f"목록에서 {len(all_ids)}개 ID를 찾았고, 그중 {len(target_ids)}개를 대상으로 합니다.")

        if skip_duplicates:
            existing = get_existing_arxiv_ids(PAPER_CSV)
            new_ids = [i for i in target_ids if i not in existing]
            skipped = len(target_ids) - len(new_ids)
            if skipped:
                st.warning(f"{len(target_ids)}개 중 {skipped}개는 이미 있어서 건너뛰었어요.")
        else:
            new_ids = target_ids
            skipped = 0

        if not new_ids:
            st.success("새로 추가할 논문이 없습니다.")
            progress.empty()
        else:
            papers = []
            total = len(new_ids)
            for index, arxiv_id in enumerate(new_ids, start=1):
                remaining = total - index
                eta = remaining * delay + delay
                progress.progress(
                    (index - 1) / total,
                    text=(
                        f"[{index}/{total}] {arxiv_id} 대기 중 "
                        f"(남은 약 {int(eta)}초)"
                    ),
                )
                with log_box:
                    st.write(
                        f"{datetime.now():%H:%M:%S} · {arxiv_id} 요청 전 {delay:.0f}초 대기"
                    )
                time.sleep(float(delay))

                try:
                    paper = extract_paper_info(
                        ABS_URL_TEMPLATE.format(arxiv_id=arxiv_id)
                    )
                    papers.append(paper)
                    with log_box:
                        st.write(f"완료: {paper['title']}")
                except Exception as exc:
                    with log_box:
                        st.error(f"실패 {arxiv_id}: {exc}")

                progress.progress(index / total, text=f"[{index}/{total}] 처리 완료")

            if papers:
                combined = save_papers_append(papers, PAPER_CSV)
                progress.progress(1.0, text="저장 완료")
                st.success(
                    f"새 논문 {len(papers)}개 추가 · 총 {len(combined)}편 → {PAPER_CSV.name}"
                )
                stats = analyze_papers(papers)
                m1, m2, m3 = st.columns(3)
                m1.metric("이번 수집", stats["total_papers"])
                m2.metric("저자 수 평균", f"{stats['avg_authors']:.2f}")
                m3.metric(
                    "최빈 키워드",
                    stats["top_keyword"] or "없음",
                )
                show_dataframe(pd.DataFrame([_paper_to_row(p) for p in papers]))
            else:
                st.warning("저장할 새 논문이 없습니다.")
    except Exception as exc:
        st.error(f"크롤링 실패: {exc}")

st.subheader("현재 paper.csv", divider="green")
existing_df = load_existing_papers(PAPER_CSV)
st.caption(f"{len(existing_df)}편 저장됨")
show_dataframe(existing_df[PAPER_COLUMNS] if not existing_df.empty else existing_df)
