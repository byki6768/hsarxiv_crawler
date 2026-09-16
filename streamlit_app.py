"""hsarxiv crawler Streamlit entrypoint."""

import streamlit as st

st.set_page_config(
    page_title="hsarxiv crawler",
    page_icon=":material/auto_stories:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 반응형 네비:
# - 데스크톱(769px+): 사이드바 네비 유지
# - 모바일(768px-): 사이드바/햄버거 숨기고, 본문 상단 메뉴 표시
# JS 감지에 의존하지 않고 CSS 미디어쿼리로 전환한다.
st.html(
    """
<style>
/* ----- Desktop: bright sidebar ----- */
@media (min-width: 769px) {
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #F0FDFA 100%) !important;
    border-right: 2px solid #5EEAD4 !important;
    box-shadow: 4px 0 24px rgba(15, 118, 110, 0.10);
  }
  section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    border-radius: 0.55rem;
    margin: 0.15rem 0.35rem;
  }
  section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: #CCFBF1 !important;
    border: 1px solid #5EEAD4;
    font-weight: 600;
  }
  /* 데스크톱에서는 사이드바가 펼쳐진 상태를 유지 */
  div[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
  }
  /* 모바일 전용 상단 메뉴 숨김 */
  div[data-testid="stVerticalBlock"]:has(#mobile-nav-root),
  div[data-testid="stVerticalBlockBorderWrapper"]:has(#mobile-nav-root) {
    display: none !important;
  }
}

/* ----- Mobile: top menu, hide sidebar ----- */
@media (max-width: 768px) {
  section[data-testid="stSidebar"],
  div[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
  }
  header[data-testid="stHeader"] {
    background: #FFFFFF !important;
    border-bottom: 1px solid #99F6E4 !important;
  }
}
</style>
"""
)

home = st.Page("app_pages/home.py", title="홈", icon=":material/home:", default=True)
browse = st.Page("app_pages/browse.py", title="데이터 보기", icon=":material/table_view:")
stats = st.Page("app_pages/stats.py", title="통계", icon=":material/insights:")
crawl = st.Page("app_pages/crawl.py", title="논문 크롤링", icon=":material/travel_explore:")
single_paper = st.Page(
    "app_pages/single_paper.py", title="단일 논문 조회", icon=":material/description:"
)
summarize = st.Page("app_pages/summarize.py", title="단일 요약", icon=":material/edit_note:")
batch_summary = st.Page(
    "app_pages/batch_summary.py",
    title="일괄 요약",
    icon=":material/playlist_add_check:",
)

pages = {
    "개요": [home, browse, stats],
    "수집": [crawl, single_paper],
    "요약": [summarize, batch_summary],
}

mobile_links = [
    (home, "홈", ":material/home:"),
    (browse, "데이터", ":material/table_view:"),
    (stats, "통계", ":material/insights:"),
    (crawl, "크롤링", ":material/travel_explore:"),
    (single_paper, "조회", ":material/description:"),
    (summarize, "요약", ":material/edit_note:"),
    (batch_summary, "일괄요약", ":material/playlist_add_check:"),
]

# 데스크톱용 사이드바 네비게이션 (페이지 등록)
page = st.navigation(pages, position="sidebar")

# 모바일용 상단 메뉴 (CSS로 데스크톱에서는 숨김)
with st.container(border=True):
    st.html("<div id='mobile-nav-root'></div>")
    st.markdown("**메뉴**")
    row1 = mobile_links[:4]
    row2 = mobile_links[4:]
    cols1 = st.columns(len(row1))
    for col, (target, label, icon) in zip(cols1, row1, strict=True):
        with col:
            st.page_link(target, label=label, icon=icon, width="stretch")
    if row2:
        cols2 = st.columns(len(row2))
        for col, (target, label, icon) in zip(cols2, row2, strict=True):
            with col:
                st.page_link(target, label=label, icon=icon, width="stretch")

page.run()
