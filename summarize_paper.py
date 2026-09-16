"""Gemini API로 arXiv 논문을 쉬운 한국어로 요약한다."""

from __future__ import annotations

import json
import pprint
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, field_validator

# 신규 사용자에게 제공되는 최저가 Flash-Lite 계열
# (gemini-2.5-flash-lite는 신규 사용자에게 비활성, 문서 안내: gemini-3.5-flash-lite)
MODEL_NAME = "gemini-3.5-flash-lite"
ENV_PATH = Path(__file__).resolve().parent / ".env.local"
PAPERS_CSV = Path(__file__).resolve().parent / "arxiv_papers.csv"


class PaperSummary(BaseModel):
    summary_one_line: str = Field(..., description="한줄 요약(50자 이내)")
    summary_easy: str = Field(..., description="쉬운 설명(4~5문장)")
    real_world: str = Field(..., description="현실 적용(4~5줄)")
    limitations: str = Field(..., description="한계점(2~3줄)")

    @field_validator("summary_one_line")
    @classmethod
    def limit_one_line(cls, value: str) -> str:
        value = value.strip()
        if len(value) > 50:
            return value[:50].rstrip()
        return value


PROMPT_TEMPLATE = """당신은 학술 논문을 중학생도 이해할 수 있게 풀어 설명하는 한국어 과학 해설가입니다.

아래 논문의 제목과 초록만 보고 요약하세요.
추측으로 없는 실험을 만들어내지 말고, 주어진 내용에만 근거하세요.

반드시 아래 JSON 객체만 출력하세요. 다른 텍스트, 마크다운, 코드블록은 금지합니다.
키 이름은 정확히 다음 4개만 사용합니다:
- summary_one_line
- summary_easy
- real_world
- limitations

필드별 규칙:
1) summary_one_line
   - 한국어 한 문장
   - 공백 포함 50자 이내
   - 논문이 무엇을 했는지 핵심만 담기

2) summary_easy
   - 한국어
   - 정확히 4문장 또는 5문장
   - 어려운 용어는 쉬운 말로 바꿔 설명
   - 중학생도 이해할 수준

3) real_world
   - 한국어
   - 정확히 4줄 또는 5줄
   - 이 연구가 어디에 쓰일 수 있는지 구체적으로 적기
   - 각 줄은 한 가지 활용 장면

4) limitations
   - 한국어
   - 정확히 2줄 또는 3줄
   - 초록에서 드러나는 한계, 가정, 미해결 문제, 적용 범위 제한을 적기
   - 초록에 한계가 명시되지 않으면, 제목/초록 범위에서 합리적으로 추론되는 제한만 짧게 적기

논문 제목:
{title}

논문 초록:
{abstract}
"""


def _load_api_key() -> str:
    load_dotenv(ENV_PATH)
    import os

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(f".env.local에서 GEMINI_API_KEY를 찾지 못했습니다: {ENV_PATH}")
    return api_key


def _build_client() -> genai.Client:
    return genai.Client(api_key=_load_api_key())


def summarize_paper(title: str, abstract: str, model: str = MODEL_NAME) -> dict:
    """논문 제목·초록을 Gemini로 요약해 고정 형식 딕셔너리로 반환한다."""
    if not title or not str(title).strip():
        raise ValueError("title이 비어 있습니다.")
    if not abstract or not str(abstract).strip():
        raise ValueError("abstract가 비어 있습니다.")

    prompt = PROMPT_TEMPLATE.format(title=title.strip(), abstract=abstract.strip())
    client = _build_client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=PaperSummary,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        ),
    )

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise RuntimeError("Gemini 응답이 비어 있습니다.")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON 파싱 실패: {raw_text[:500]}") from exc

    summary = PaperSummary.model_validate(payload)
    return summary.model_dump()


def summarize_first_csv_paper(csv_path: Path = PAPERS_CSV) -> dict:
    """CSV 첫 행 논문으로 요약을 테스트한다."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    if df.empty:
        raise RuntimeError(f"CSV가 비어 있습니다: {csv_path}")

    row = df.iloc[0]
    title = str(row["title"])
    abstract = str(row["abstract"])
    result = summarize_paper(title, abstract)
    return {
        "arxiv_id": str(row.get("arxiv_id", "")),
        "title": title,
        "model": MODEL_NAME,
        **result,
    }


if __name__ == "__main__":
    result = summarize_first_csv_paper()
    print("=== Gemini Paper Summary ===")
    pprint.pprint(result, width=100, sort_dicts=False)
