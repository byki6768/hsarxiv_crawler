"""브라우저 너비로 desktop/mobile 네비 모드를 감지한다."""

from __future__ import annotations

import streamlit as st

_BREAKPOINT_PX = 769

_VIEWPORT_COMPONENT = st.components.v2.component(
    "hsarxiv_viewport_nav_mode",
    html="<div id='viewport-sensor' aria-hidden='true'></div>",
    css="#viewport-sensor{display:none;width:0;height:0;overflow:hidden;}",
    js="""
export default function (component) {
  const { data, setStateValue } = component;
  const breakpoint = (data && data.breakpoint) || 769;

  const report = () => {
    const mode = window.innerWidth >= breakpoint ? "desktop" : "mobile";
    if (window.__hsarxiv_nav_mode !== mode) {
      window.__hsarxiv_nav_mode = mode;
      setStateValue("mode", mode);
      setStateValue("width", window.innerWidth);
    }
  };

  report();

  if (!window.__hsarxiv_vp_bound) {
    window.__hsarxiv_vp_bound = true;
    window.addEventListener("resize", () => {
      clearTimeout(window.__hsarxiv_vp_timer);
      window.__hsarxiv_vp_timer = setTimeout(report, 120);
    });
  }
}
""",
)


def _guess_mode_from_user_agent() -> str:
    try:
        user_agent = (st.context.headers.get("User-Agent") or "").lower()
    except Exception:
        user_agent = ""
    mobile_tokens = ("mobile", "android", "iphone", "ipod", "ipad", "webos", "opera mini")
    if any(token in user_agent for token in mobile_tokens):
        return "mobile"
    return "desktop"


def get_nav_mode(*, breakpoint: int = _BREAKPOINT_PX) -> str:
    """769px 이상이면 desktop(sidebar), 이하면 mobile(top nav)."""
    key = "hsarxiv_viewport_detector"
    guessed = _guess_mode_from_user_agent()

    result = _VIEWPORT_COMPONENT(
        key=key,
        data={"breakpoint": breakpoint},
        default={"mode": guessed, "width": breakpoint if guessed == "desktop" else 375},
        on_mode_change=lambda: None,
        on_width_change=lambda: None,
        height=1,
        width=1,
    )

    mode = getattr(result, "mode", None) or st.session_state.get(key, {}).get("mode")
    if mode not in {"desktop", "mobile"}:
        mode = guessed

    st.session_state["nav_mode"] = mode
    return mode


def nav_position_for_mode(mode: str) -> str:
    return "sidebar" if mode == "desktop" else "top"
