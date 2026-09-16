"""paper.csv의 모든 논문에 Gemini 한국어 요약을 추가한다."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from summarize_paper import summarize_paper

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "paper.csv"
OUTPUT_CSV = BASE_DIR / "papers_with_summary.csv"
SUMMARY_COLUMNS = [
    "summary_one_line",
    "summary_easy",
    "real_world",
    "limitations",
]
REQUEST_DELAY_SECONDS = 2.0


def process_all_papers(
    input_csv: Path = INPUT_CSV,
    output_csv: Path = OUTPUT_CSV,
    delay: float = REQUEST_DELAY_SECONDS,
    progress_callback=None,
) -> pd.DataFrame:
    """paper.csv를 읽고 각 논문에 Gemini 요약을 붙여 저장한다."""
    if not input_csv.exists():
        raise FileNotFoundError(f"입력 CSV가 없습니다: {input_csv}")

    df = pd.read_csv(input_csv, encoding="utf-8-sig").fillna("")
    total = len(df)
    print(f"논문 {total}편 요약 시작: {input_csv.name}")

    for column in SUMMARY_COLUMNS:
        df[column] = ""

    success_count = 0
    for position, (index, row) in enumerate(df.iterrows(), start=1):
        arxiv_id = str(row.get("arxiv_id", "")).strip()
        title = str(row.get("title", "")).strip()
        abstract = str(row.get("abstract", "")).strip()

        print(f"[{position}/{total}] 요약 중: {arxiv_id} - {title[:60]}")
        if progress_callback:
            progress_callback(
                position,
                total,
                f"{arxiv_id} - {title[:60]}",
                "running",
            )

        if not title or not abstract:
            print("  건너뜀: title 또는 abstract가 비어 있습니다.")
            if progress_callback:
                progress_callback(position, total, arxiv_id, "skipped")
            continue

        try:
            summary = summarize_paper(title, abstract)
            for column in SUMMARY_COLUMNS:
                df.at[index, column] = summary[column]
            success_count += 1
            print(f"  완료: {summary['summary_one_line']}")
            if progress_callback:
                progress_callback(
                    position,
                    total,
                    summary["summary_one_line"],
                    "done",
                )
        except Exception as exc:
            print(f"  실패: {exc}")
            if progress_callback:
                progress_callback(position, total, str(exc), "error")

        if position < total:
            print(f"  API 제한 고려해 {int(delay)}초 대기...")
            time.sleep(delay)

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(
        f"\n저장 완료: {output_csv.resolve()} "
        f"(성공 {success_count}/{total})"
    )
    return df


if __name__ == "__main__":
    process_all_papers()
