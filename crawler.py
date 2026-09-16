import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

DEFAULT_LIST_URL = "https://arxiv.org/list/cs.AI/recent"
ABS_URL_TEMPLATE = "https://arxiv.org/abs/{arxiv_id}"
ARXIV_ID_PATTERN = re.compile(r"arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)
ARXIV_ID_FROM_URL = re.compile(r"/abs/(\d{4}\.\d{4,5}(?:v\d+)?)")
HEADERS = {
    "User-Agent": "Educational Crawler(contact: byki0304@gmail.com)",
}
REQUEST_DELAY_SECONDS = 15.0
DEFAULT_CSV_PATH = "arxiv_papers.csv"
PAPER_CSV_PATH = "paper.csv"
LOG_PATH = "crawl.log"
SAMPLE_ABS_URL = "https://arxiv.org/abs/2301.00001"


def setup_logger(log_path: str | Path = LOG_PATH) -> logging.Logger:
    """파일·콘솔에 크롤링 로그를 남기는 로거를 설정한다."""
    logger = logging.getLogger("hsarxiv_crawler")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


LOGGER = setup_logger()


class ParseError(Exception):
    """HTML 파싱 중 필수 정보를 추출하지 못했을 때 발생한다."""


def collect_arxiv_ids(url: str = DEFAULT_LIST_URL) -> list[str]:
    """카테고리 목록 페이지의 dt 태그에서 최신 논문 arXiv ID를 수집한다."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    ids: list[str] = []
    seen: set[str] = set()

    for dt in soup.find_all("dt"):
        match = ARXIV_ID_PATTERN.search(dt.get_text(" ", strip=True))
        if not match:
            continue
        arxiv_id = match.group(1)
        if arxiv_id not in seen:
            seen.add(arxiv_id)
            ids.append(arxiv_id)

    return ids


def _strip_descriptor(element, descriptor: str) -> str:
    if element is None:
        return ""
    text = element.get_text(" ", strip=True)
    prefix = f"{descriptor}:"
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix) :].strip()
    return text


def _arxiv_id_from_url(url: str) -> str:
    match = ARXIV_ID_FROM_URL.search(urlparse(url).path)
    if not match:
        raise ParseError(f"URL에서 arXiv ID를 찾을 수 없습니다: {url}")
    return match.group(1)


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}시간 {minutes}분 {secs}초"
    if minutes:
        return f"{minutes}분 {secs}초"
    return f"{secs}초"


def extract_paper_info(url: str = SAMPLE_ABS_URL) -> dict:
    """초록 페이지에서 논문의 주요 정보를 추출해 딕셔너리로 반환한다."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise requests.HTTPError(
            f"HTTP 오류({status}): {url}",
            response=exc.response,
        ) from exc
    except requests.RequestException as exc:
        raise requests.RequestException(f"네트워크 오류: {url} ({exc})") from exc

    try:
        soup = BeautifulSoup(response.text, "lxml")
        arxiv_id = _arxiv_id_from_url(url)

        title = _strip_descriptor(soup.find("h1", class_="title"), "Title")
        if not title:
            raise ParseError(f"제목(h1.title)을 찾지 못했습니다: {url}")

        authors = [
            author.get_text(" ", strip=True)
            for author in soup.select("div.authors a")
        ]
        if not authors:
            raise ParseError(f"저자(div.authors a)를 찾지 못했습니다: {url}")

        abstract = _strip_descriptor(
            soup.find("blockquote", class_="abstract"), "Abstract"
        )
        if not abstract:
            raise ParseError(f"초록(blockquote.abstract)을 찾지 못했습니다: {url}")

        dateline = soup.find("div", class_="dateline")
        dateline_text = dateline.get_text(" ", strip=True) if dateline else ""
        submitted_match = re.search(r"Submitted on ([^\]\n]+)", dateline_text)
        submitted_date = (
            submitted_match.group(1).strip() if submitted_match else dateline_text
        )

        primary_subject = soup.select_one("span.primary-subject")
        categories = (
            primary_subject.get_text(" ", strip=True) if primary_subject else ""
        )
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"파싱 오류: {url} ({exc})") from exc

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "submitted_date": submitted_date,
        "categories": categories,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
    }


def crawl_papers_safely(
    arxiv_ids: list[str],
    delay: float = REQUEST_DELAY_SECONDS,
) -> list[dict]:
    """여러 논문을 안전하게 크롤링한다(대기, 진행 표시, 오류 처리, 로그)."""
    papers: list[dict] = []
    total = len(arxiv_ids)

    if total == 0:
        LOGGER.info("크롤링할 논문 ID가 없습니다.")
        return papers

    estimated_total = total * delay
    LOGGER.info(
        "안전한 크롤링 시작: %d편 (요청 전 대기 %ss, 예상 소요 약 %s)",
        total,
        int(delay),
        _format_duration(estimated_total),
    )

    for index, arxiv_id in enumerate(arxiv_ids, start=1):
        remaining_after = total - index
        remaining_seconds = remaining_after * delay
        eta = datetime.now() + timedelta(seconds=delay + remaining_seconds)

        print(
            f"[{index}/{total}] {arxiv_id} 요청 전 {int(delay)}초 대기 "
            f"(남은 논문 {remaining_after}개, "
            f"예상 남은 시간 약 {_format_duration(remaining_seconds + delay)})"
        )
        LOGGER.info(
            "진행 %d/%d: %s 대기 시작 (예상 완료 시각 %s)",
            index,
            total,
            arxiv_id,
            eta.strftime("%H:%M:%S"),
        )
        time.sleep(delay)

        crawled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        abs_url = ABS_URL_TEMPLATE.format(arxiv_id=arxiv_id)

        try:
            paper = extract_paper_info(abs_url)
            papers.append(paper)
            LOGGER.info(
                "크롤링 성공: arxiv_id=%s title=%s crawled_at=%s",
                paper["arxiv_id"],
                paper["title"],
                crawled_at,
            )
            print(f"  완료: {paper['title']}")
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            message = f"HTTP 오류({status}): {arxiv_id}"
            LOGGER.error("%s | %s | crawled_at=%s", message, abs_url, crawled_at)
            print(f"  {message}")
        except requests.RequestException as exc:
            message = f"네트워크 오류: {arxiv_id} ({exc})"
            LOGGER.error("%s | crawled_at=%s", message, crawled_at)
            print(f"  {message}")
        except ParseError as exc:
            message = f"파싱 오류: {arxiv_id} ({exc})"
            LOGGER.error("%s | crawled_at=%s", message, crawled_at)
            print(f"  {message}")
        except Exception as exc:
            message = f"알 수 없는 오류: {arxiv_id} ({exc})"
            LOGGER.exception("%s | crawled_at=%s", message, crawled_at)
            print(f"  {message}")

    LOGGER.info("안전한 크롤링 종료: 성공 %d / 전체 %d", len(papers), total)
    print(f"완료: 성공 {len(papers)}/{total}")
    return papers


PAPER_COLUMNS = [
    "arxiv_id",
    "title",
    "authors",
    "abstract",
    "submitted_date",
    "categories",
    "pdf_url",
]


def _paper_to_row(paper: dict) -> dict:
    return {
        "arxiv_id": paper.get("arxiv_id", ""),
        "title": paper.get("title", ""),
        "authors": ", ".join(paper["authors"])
        if isinstance(paper.get("authors"), list)
        else paper.get("authors", ""),
        "abstract": paper.get("abstract", ""),
        "submitted_date": paper.get("submitted_date", ""),
        "categories": paper.get("categories", ""),
        "pdf_url": paper.get("pdf_url", ""),
    }


def load_existing_papers(csv_path: str | Path = PAPER_CSV_PATH) -> pd.DataFrame:
    """paper.csv가 있으면 읽고, 없으면 빈 DataFrame을 반환한다."""
    output_path = Path(csv_path)
    if not output_path.exists():
        return pd.DataFrame(columns=PAPER_COLUMNS)

    df = pd.read_csv(output_path, encoding="utf-8-sig", dtype=str).fillna("")
    for column in PAPER_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[PAPER_COLUMNS]


def get_existing_arxiv_ids(csv_path: str | Path = PAPER_CSV_PATH) -> set[str]:
    """이미 저장된 arxiv_id 집합을 반환한다."""
    df = load_existing_papers(csv_path)
    if df.empty or "arxiv_id" not in df.columns:
        return set()
    return set(df["arxiv_id"].astype(str).tolist())


def save_paper_csv(paper: dict, csv_path: str | Path = PAPER_CSV_PATH) -> Path:
    """논문 딕셔너리를 CSV 한 행으로 저장한다(덮어쓰기)."""
    output_path = Path(csv_path)
    pd.DataFrame([_paper_to_row(paper)], columns=PAPER_COLUMNS).to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )
    return output_path


def save_papers_append(
    papers: list[dict],
    csv_path: str | Path = PAPER_CSV_PATH,
) -> pd.DataFrame:
    """기존 CSV에 새 논문들을 이어 붙여 저장한다."""
    existing_df = load_existing_papers(csv_path)
    new_df = pd.DataFrame(
        [_paper_to_row(paper) for paper in papers], columns=PAPER_COLUMNS
    )
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    output_path = Path(csv_path)
    combined.to_csv(output_path, index=False, encoding="utf-8-sig")
    return combined


def crawl_new_papers(
    arxiv_ids: list[str],
    csv_path: str | Path = PAPER_CSV_PATH,
    delay: float = REQUEST_DELAY_SECONDS,
) -> pd.DataFrame:
    """이미 저장된 ID는 건너뛰고, 새 논문만 안전하게 크롤링해 paper.csv에 추가한다."""
    total = len(arxiv_ids)
    existing_ids = get_existing_arxiv_ids(csv_path)
    new_ids = [arxiv_id for arxiv_id in arxiv_ids if arxiv_id not in existing_ids]
    skipped = total - len(new_ids)

    if total == 0:
        print("크롤링할 논문이 없습니다.")
        return load_existing_papers(csv_path)

    if skipped:
        print(f"{total}개 중 {skipped}개는 이미 있어서 건너뛰었어요.")
        LOGGER.info("%d개 중 %d개는 이미 있어서 건너뜀", total, skipped)
    else:
        print(f"{total}개 모두 새로운 논문이라 크롤링합니다.")

    if not new_ids:
        print("새로 추가할 논문이 없습니다.")
        return load_existing_papers(csv_path)

    print(f"새로운 논문 {len(new_ids)}개를 크롤링합니다.")
    new_papers = crawl_papers_safely(new_ids, delay=delay)

    if not new_papers:
        print("저장할 새 논문이 없습니다.")
        return load_existing_papers(csv_path)

    combined = save_papers_append(new_papers, csv_path)
    print(
        f"새 논문 {len(new_papers)}개 추가 완료. "
        f"총 {len(combined)}개를 {Path(csv_path).resolve()}에 저장했습니다."
    )
    return combined


def fetch_paper_title(url: str = SAMPLE_ABS_URL) -> str:
    """초록 페이지를 가져와 h1.title에서 논문 제목을 추출한다."""
    return extract_paper_info(url)["title"]


def fetch_paper(arxiv_id: str, session: requests.Session | None = None) -> dict:
    """개별 논문 초록 페이지에서 메타데이터를 수집한다."""
    abs_url = ABS_URL_TEMPLATE.format(arxiv_id=arxiv_id)
    paper = extract_paper_info(abs_url)
    return {
        "arxiv_id": paper["arxiv_id"],
        "title": paper["title"],
        "authors": ", ".join(paper["authors"])
        if isinstance(paper["authors"], list)
        else paper["authors"],
        "abstract": paper["abstract"],
        "subjects": paper["categories"],
        "comments": "",
        "submitted": paper["submitted_date"],
        "abs_url": abs_url,
        "pdf_url": paper["pdf_url"],
    }


def crawl_papers(
    arxiv_ids: list[str],
    delay: float = REQUEST_DELAY_SECONDS,
) -> list[dict]:
    """여러 논문 메타데이터를 안전하게 크롤링한다."""
    return crawl_papers_safely(arxiv_ids, delay=delay)


def papers_to_dataframe(papers: list[dict]) -> pd.DataFrame:
    columns = [
        "arxiv_id",
        "title",
        "authors",
        "abstract",
        "subjects",
        "comments",
        "submitted",
        "abs_url",
        "pdf_url",
    ]
    return pd.DataFrame(papers, columns=columns)


def save_papers_csv(df: pd.DataFrame, csv_path: str | Path = DEFAULT_CSV_PATH) -> Path:
    output_path = Path(csv_path)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def analyze_papers(papers: list[dict]) -> dict:
    """크롤링 결과의 총 논문 수, 저자 수 평균, 최빈 키워드를 계산한다."""
    stopwords = {
        "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "with",
        "from", "by", "as", "at", "is", "are", "be", "this", "that", "these",
        "those", "we", "our", "via", "using", "based", "into", "over", "under",
        "between", "through", "their", "its", "it", "can", "may", "also", "such",
        "than", "then", "which", "what", "how", "when", "where", "who", "whom",
        "not", "no", "all", "any", "each", "both", "more", "most", "other",
        "new", "towards", "toward", "across", "within", "without", "about",
    }
    keyword_counts: dict[str, int] = {}
    author_counts: list[int] = []

    for paper in papers:
        authors = paper.get("authors", [])
        if isinstance(authors, str):
            author_list = [a.strip() for a in authors.split(",") if a.strip()]
        else:
            author_list = list(authors)
        author_counts.append(len(author_list))

        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        tokens = re.findall(r"[a-z][a-z0-9\-]{2,}", text)
        for token in tokens:
            if token in stopwords:
                continue
            keyword_counts[token] = keyword_counts.get(token, 0) + 1

    total = len(papers)
    avg_authors = (sum(author_counts) / total) if total else 0.0
    top_keyword = None
    top_count = 0
    if keyword_counts:
        top_keyword, top_count = max(keyword_counts.items(), key=lambda item: item[1])

    return {
        "total_papers": total,
        "avg_authors": avg_authors,
        "top_keyword": top_keyword,
        "top_keyword_count": top_count,
    }


def print_paper_stats(papers: list[dict]) -> None:
    stats = analyze_papers(papers)
    print("\n=== 통계 ===")
    print(f"총 논문 수: {stats['total_papers']}")
    print(f"저자 수 평균: {stats['avg_authors']:.2f}")
    if stats["top_keyword"]:
        print(
            f"가장 많이 나온 키워드: {stats['top_keyword']} "
            f"({stats['top_keyword_count']}회)"
        )
    else:
        print("가장 많이 나온 키워드: 없음")


def main(
    list_url: str = DEFAULT_LIST_URL,
    csv_path: str | Path = DEFAULT_CSV_PATH,
    delay: float = REQUEST_DELAY_SECONDS,
) -> pd.DataFrame:
    """ID 수집 → 논문 크롤링 → DataFrame 변환 → CSV 저장."""
    print(f"collecting IDs from {list_url}")
    arxiv_ids = collect_arxiv_ids(list_url)
    print(f"collected {len(arxiv_ids)} IDs")

    papers = crawl_papers_safely(arxiv_ids, delay=delay)
    df = papers_to_dataframe(papers)
    output_path = save_papers_csv(df, csv_path)
    print(f"saved {len(df)} papers to {output_path.resolve()}")
    return df


if __name__ == "__main__":
    list_url = DEFAULT_LIST_URL
    output_csv = Path("cs_ai_recent_10.csv")

    print(f"cs.AI 최신 논문 ID 수집 중: {list_url}")
    recent_ids = collect_arxiv_ids(list_url)[:10]
    print(f"수집된 최신 ID {len(recent_ids)}개: {recent_ids}")

    papers = crawl_papers_safely(recent_ids)
    if papers:
        rows = [_paper_to_row(paper) for paper in papers]
        df = pd.DataFrame(rows, columns=PAPER_COLUMNS)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"\nCSV 저장 완료: {output_csv.resolve()}")
        print_paper_stats(papers)
    else:
        print("저장할 논문이 없습니다.")
