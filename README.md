# hsarxiv crawler

arXiv 논문을 안전하게 수집하고, Gemini로 쉬운 한국어 요약을 만드는 도구입니다.  
Streamlit UI로 크롤링·조회·요약·통계를 한곳에서 사용할 수 있습니다.

## 주요 기능

- 카테고리 목록에서 arXiv ID 수집 (`/list/{category}/recent`)
- 논문 메타데이터 크롤링 (제목, 저자, 초록, 카테고리, PDF URL 등)
- 요청 전 대기 · 진행 표시 · HTTP/네트워크/파싱 오류 처리 · 로그 기록
- `paper.csv` 기준 중복 ID 건너뛰기
- Gemini API로 쉬운 한국어 요약
  - `summary_one_line` / `summary_easy` / `real_world` / `limitations`
- Streamlit 반응형 UI
  - 데스크톱(769px+): 사이드바 네비
  - 모바일(768px 이하): 상단 네비

## 요구 사항

- Python 3.10+
- Gemini API 키 ([Google AI Studio](https://aistudio.google.com/))

## 설치

```bash
git clone https://github.com/<USERNAME>/hsarxiv_crawler.git
cd hsarxiv_crawler

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

## 환경 변수

`.env.example`을 복사해 `.env.local`을 만들고 API 키를 넣습니다.

```bash
# Windows
copy .env.example .env.local

# macOS / Linux
# cp .env.example .env.local
```

`.env.local` 예시:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> `.env.local`은 Git에 올리지 마세요. (`.gitignore`에 포함되어 있습니다.)

## Streamlit UI 실행

```bash
streamlit run streamlit_app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

### UI 메뉴

| 메뉴 | 설명 |
|------|------|
| 홈 | CSV 현황, API 키 상태 |
| 논문 크롤링 | 카테고리 최신 논문 수집 → `paper.csv` |
| 단일 논문 조회 | abs URL/ID로 메타데이터 추출 |
| 단일 요약 | Gemini 한국어 요약 4항목 |
| 일괄 요약 | CSV 전체에 요약 칼럼 추가 |
| 데이터 보기 / 통계 | 결과 확인, 키워드·저자 통계 |

## CLI 사용

### 1) 논문 크롤링

```bash
python crawler.py
```

주요 함수:

- `collect_arxiv_ids()` — 목록 페이지에서 ID 수집
- `extract_paper_info(url)` — 단일 논문 메타데이터 추출
- `crawl_papers_safely(ids)` — 안전 다중 크롤링
- `crawl_new_papers(ids)` — 중복 제외 후 `paper.csv`에 추가

### 2) 단일 논문 요약

```bash
python summarize_paper.py
```

### 3) CSV 일괄 요약

```bash
python process_all_papers.py
```

입력: `paper.csv`  
출력: `papers_with_summary.csv`

## 프로젝트 구조

```text
hsarxiv_crawler/
├── streamlit_app.py          # Streamlit 진입점
├── app_pages/                # UI 페이지
├── crawler.py                # arXiv 크롤링
├── summarize_paper.py        # Gemini 요약
├── process_all_papers.py     # 일괄 요약
├── viewport.py               # 반응형 네비 감지
├── ui_helpers.py             # UI 공통 헬퍼
├── .streamlit/config.toml    # 테마 설정
├── .env.example              # 환경 변수 예시
├── requirements.txt
└── README.md
```

## Streamlit Community Cloud 배포

1. [share.streamlit.io](https://share.streamlit.io)에 GitHub 계정으로 로그인합니다.
2. **Create app** → 저장소 `byki6768/hsarxiv_crawler`, 브랜치 `main`, 파일 `streamlit_app.py`를 선택합니다.
3. **Advanced settings → Secrets**에 아래를 붙여넣습니다.

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

4. Deploy 후 `*.streamlit.app` URL로 접속합니다.

빠른 배포 링크(로그인 후 값 확인):

https://share.streamlit.io/deploy?repository=byki6768/hsarxiv_crawler&branch=main&mainModule=streamlit_app.py

## 주의 사항

- arXiv 서버 부하를 줄이기 위해 요청 사이 대기(기본 15초)를 권장합니다.
- User-Agent에 연락처가 포함되어 있습니다.
- 크롤링·요약 결과 CSV와 `crawl.log`는 기본적으로 Git에 포함되지 않습니다.

## 라이선스

개인/교육 목적 사용을 전제로 합니다. arXiv 이용 정책과 Gemini API 이용 약관을 함께 확인해 주세요.
