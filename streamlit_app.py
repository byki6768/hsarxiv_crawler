"""hsarxiv crawler Streamlit entrypoint."""

import streamlit as st

from viewport import get_nav_mode, nav_position_for_mode

st.set_page_config(
    page_title="hsarxiv crawler",
    page_icon=":material/auto_stories:",
    layout="wide",
    initial_sidebar_state="expanded",
)

nav_mode = get_nav_mode(breakpoint=769)
nav_position = nav_position_for_mode(nav_mode)

if nav_mode == "desktop":
    # 데스크톱: 사이드바를 더 밝고 또렷하게
    st.html(
        """
<style>
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #FFFFFF 0%, #F0FDFA 100%) !important;
  border-right: 2px solid #5EEAD4 !important;
  box-shadow: 4px 0 24px rgba(15, 118, 110, 0.10);
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
  background: transparent !important;
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
div[data-testid="stSidebarCollapsedControl"] {
  display: none;
}
</style>
""",
        unsafe_allow_javascript=False,
    )
else:
    # 모바일: 상단 네비 중심으로, 빈 사이드바는 감춤
    st.html(
        """
<style>
section[data-testid="stSidebar"] {
  display: none !important;
}
div[data-testid="stSidebarCollapsedControl"] {
  display: none !important;
}
header[data-testid="stHeader"] {
  background: #FFFFFF !important;
  border-bottom: 1px solid #99F6E4 !important;
}
</style>
""",
        unsafe_allow_javascript=False,
    )

pages = {
    "개요": [
        st.Page("app_pages/home.py", title="홈", icon=":material/home:", default=True),
        st.Page(
            "app_pages/browse.py",
            title="데이터 보기",
            icon=":material/table_view:",
        ),
        st.Page(
            "app_pages/stats.py",
            title="통계",
            icon=":material/insights:",
        ),
    ],
    "수집": [
        st.Page(
            "app_pages/crawl.py",
            title="논문 크롤링",
            icon=":material/travel_explore:",
        ),
        st.Page(
            "app_pages/single_paper.py",
            title="단일 논문 조회",
            icon=":material/description:",
        ),
    ],
    "요약": [
        st.Page(
            "app_pages/summarize.py",
            title="단일 요약",
            icon=":material/edit_note:",
        ),
        st.Page(
            "app_pages/batch_summary.py",
            title="일괄 요약",
            icon=":material/playlist_add_check:",
        ),
    ],
}

page = st.navigation(pages, position=nav_position)
page.run()
