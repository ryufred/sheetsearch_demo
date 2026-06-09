import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="시트 검색엔진",
    page_icon="🔍",
    layout="wide",
)

# ── 로그인 설정 ───────────────────────────────────────────────
def get_credentials():
    try:
        return st.secrets["credentials"]
    except Exception:
        return {"admin": "1234"}

def check_login(username, password):
    creds = get_credentials()
    return creds.get(username) == password

def login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
    html, body, [class*="css"] { background-color: #0d0d0d !important; color: #f0f0f0 !important; }
    .stTextInput > div > div > input {
        background: #1e1e1e !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 10px !important;
        color: #f0f0f0 !important;
        font-size: 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00e5a0 !important;
        box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #00e5a0, #00c478) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        width: 100% !important;
        padding: 0.6rem !important;
        font-size: 1rem !important;
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 4rem 0 2rem;">
        <div style="font-family:'Space Mono',monospace; font-size:2rem; font-weight:700;
                    background:linear-gradient(135deg,#00e5a0,#0099ff);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            🔍 SHEET SEARCH
        </div>
        <div style="color:#888; font-size:0.9rem; margin-top:0.5rem;">로그인 후 이용할 수 있어요</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        username = st.text_input("아이디", placeholder="아이디 입력", key="login_user")
        password = st.text_input("비밀번호", placeholder="비밀번호 입력", type="password", key="login_pw")
        login_btn = st.button("로그인", use_container_width=True)
        if login_btn:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 틀렸어요.")

# ── 로그인 체크 ──────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ── Google Sheets 연결 ───────────────────────────────────────
@st.cache_resource
def get_worksheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet_url = st.secrets["sheet"]["url"]
    spreadsheet = client.open_by_url(sheet_url)
    return spreadsheet.sheet1

def load_data():
    try:
        ws = get_worksheet()
        rows = ws.get_all_records()
        return rows
    except Exception as e:
        st.error(f"구글 시트 연결 오류: {e}")
        return []

def add_row(entry):
    ws = get_worksheet()
    ws.append_row([
        entry["id"],
        entry["name"],
        entry["url"],
        entry["tags"],
        entry["desc"],
    ])

def delete_row(row_index):
    ws = get_worksheet()
    ws.delete_rows(row_index + 2)  # 헤더(1행) + 0-index 보정

def clear_all():
    ws = get_worksheet()
    all_rows = ws.get_all_values()
    if len(all_rows) > 1:
        ws.delete_rows(2, len(all_rows))

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Space+Mono:wght@400;700&display=swap');
:root {
    --bg: #0d0d0d; --surface: #161616; --surface2: #1e1e1e;
    --border: #2a2a2a; --accent: #00e5a0; --accent2: #0099ff;
    --text: #f0f0f0; --muted: #888;
}
html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
.hero { text-align: center; padding: 2rem 0 1.5rem; }
.hero h1 {
    font-family: 'Space Mono', monospace; font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.hero p { color: var(--muted); font-size: 0.9rem; margin-top: 0.4rem; }
.section-title {
    font-family: 'Space Mono', monospace; font-size: 0.72rem;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 1rem;
    border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;
}
.stTextInput > div > div > input {
    background: var(--surface2) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; color: var(--text) !important; font-size: 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
}
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #00c478) !important;
    color: #000 !important; border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; font-family: 'Noto Sans KR', sans-serif !important;
    padding: 0.5rem 1.5rem !important; transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
div[data-testid="stExpander"] {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
.badge {
    display: inline-block; background: rgba(0,229,160,0.15); color: var(--accent);
    border: 1px solid rgba(0,229,160,0.3); border-radius: 20px;
    padding: 2px 10px; font-size: 0.78rem; font-family: 'Space Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── 유틸 ────────────────────────────────────────────────────
def highlight(text, query):
    if not query:
        return text
    return re.sub(f"({re.escape(query)})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)

def search(sheets, query, tags_filter):
    query = query.strip().lower()
    results = []
    for s in sheets:
        name_match = query and query in s["name"].lower()
        sheet_tags = [t.strip() for t in str(s.get("tags", "")).split(",") if t.strip()]
        tag_match = query and any(query in t.lower() for t in sheet_tags)
        tag_filter_match = (not tags_filter) or any(tf in sheet_tags for tf in tags_filter)
        score = 0
        if name_match: score += 2
        if tag_match: score += 1
        if (name_match or tag_match or not query) and tag_filter_match:
            results.append((score, s))
    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results]

def validate_url(url):
    return url.startswith("https://docs.google.com/")

# ── 헤더 ────────────────────────────────────────────────────
header_col, logout_col = st.columns([5, 1])
with header_col:
    st.markdown("""
    <div class="hero">
        <h1>🔍 SHEET SEARCH</h1>
        <p>구글 스프레드시트를 저장하고 검색하세요</p>
    </div>
    """, unsafe_allow_html=True)
with logout_col:
    st.write("")
    st.write("")
    st.markdown(f'<div style="color:#888;font-size:0.85rem;text-align:right;margin-bottom:0.3rem">👤 {st.session_state.username}</div>', unsafe_allow_html=True)
    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ── 데이터 로드 ──────────────────────────────────────────────
sheets_data = load_data()

# ── 레이아웃 ─────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.6], gap="large")

# ══ 왼쪽: 등록 ══════════════════════════════════════════════
with col_left:
    st.markdown('<div class="section-title">📋 시트 등록</div>', unsafe_allow_html=True)
    new_name     = st.text_input("시트 이름", placeholder="예) 2024 마케팅 예산", key="inp_name")
    new_url      = st.text_input("구글 시트 URL", placeholder="https://docs.google.com/spreadsheets/d/...", key="inp_url")
    new_tags_raw = st.text_input("태그 (쉼표 구분)", placeholder="예) 마케팅, 예산, 2024", key="inp_tags")
    new_desc     = st.text_input("간단한 설명 (선택)", placeholder="예) Q1~Q4 마케팅 비용 정리", key="inp_desc")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        add_btn = st.button("➕ 등록하기", use_container_width=True)
    with col_btn2:
        clear_btn = st.button("🗑️ 전체 삭제", use_container_width=True)

    if add_btn:
        if not new_name.strip():
            st.error("시트 이름을 입력해주세요.")
        elif not new_url.strip():
            st.error("URL을 입력해주세요.")
        else:
            if not validate_url(new_url.strip()):
                st.warning("⚠️ 구글 시트 URL 형식이 아닌 것 같아요. 그래도 저장할게요.")
            entry = {
                "id": datetime.now().isoformat(),
                "name": new_name.strip(),
                "url": new_url.strip(),
                "tags": new_tags_raw.strip(),
                "desc": new_desc.strip(),
            }
            add_row(entry)
            st.success(f"✅ '{new_name}' 등록 완료!")
            st.rerun()

    if clear_btn:
        clear_all()
        st.warning("전체 데이터가 삭제되었습니다.")
        st.rerun()

    # 목록
    if sheets_data:
        st.markdown('<div class="section-title" style="margin-top:2rem">📂 등록된 시트 목록</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge">총 {len(sheets_data)}개</span>', unsafe_allow_html=True)
        st.write("")
        for i, s in enumerate(sheets_data):
            with st.expander(f"📄 {s['name']}"):
                url_display = s['url'][:60] + "..." if len(s['url']) > 60 else s['url']
                st.markdown(f"**URL:** [{url_display}]({s['url']})")
                if s.get("tags"):
                    st.markdown(f"**태그:** {s['tags']}")
                if s.get("desc"):
                    st.markdown(f"**설명:** {s['desc']}")
                if st.button("🗑️ 이 항목 삭제", key=f"del_{i}"):
                    delete_row(i)
                    st.rerun()

# ══ 오른쪽: 검색 ════════════════════════════════════════════
with col_right:
    st.markdown('<div class="section-title">🔍 검색</div>', unsafe_allow_html=True)
    search_query = st.text_input("검색어 입력", placeholder="이름 또는 태그로 검색...",
                                  key="search_q", label_visibility="collapsed")

    all_tags = sorted(set(
        t.strip()
        for s in sheets_data
        for t in str(s.get("tags", "")).split(",")
        if t.strip()
    ))
    selected_tags = st.multiselect("태그 필터 (선택)", all_tags, key="tag_filter") if all_tags else []

    st.write("")
    results = search(sheets_data, search_query, selected_tags)

    if not sheets_data:
        st.markdown("""
        <div style="text-align:center;padding:4rem 0;color:#888">
            <div style="font-size:3rem;margin-bottom:1rem">📭</div>
            <p>아직 등록된 시트가 없어요.<br>왼쪽에서 구글 시트를 등록해보세요!</p>
        </div>
        """, unsafe_allow_html=True)
    elif not results:
        st.markdown(f"""
        <div style="text-align:center;padding:4rem 0;color:#888">
            <div style="font-size:3rem;margin-bottom:1rem">🔎</div>
            <p><b>'{search_query}'</b>에 대한 결과가 없어요.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        count_label = f"검색 결과: {len(results)}개" if search_query or selected_tags else f"전체 {len(results)}개"
        st.markdown(f'<span class="badge">{count_label}</span>', unsafe_allow_html=True)
        st.write("")

        cards_html = ""
        for s in results:
            sheet_tags = [t.strip() for t in str(s.get("tags","")).split(",") if t.strip()]
            highlighted_name = highlight(s["name"], search_query)
            tags_html = "".join(
                f'<span class="tag">#{highlight(t, search_query)}</span>'
                for t in sheet_tags
            )
            desc_html = f'<div class="desc">{s["desc"]}</div>' if s.get("desc") else ""
            cards_html += f"""
            <div class="result-card">
                <div class="result-name">📄 {highlighted_name}</div>
                {desc_html}
                <div class="result-tags">{tags_html}</div>
                <a class="result-url" href="{s['url']}" target="_blank">🔗 {s['url']}</a>
            </div>
            """

        components.html(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Mono&family=Noto+Sans+KR:wght@400;500&display=swap');
            body {{ margin:0; padding:0; background:transparent; font-family:'Noto Sans KR',sans-serif; }}
            .result-card {{
                background:#161616; border:1px solid #2a2a2a; border-radius:12px;
                padding:1.2rem 1.5rem; margin-bottom:0.8rem; position:relative; overflow:hidden;
            }}
            .result-card::before {{
                content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
                background:linear-gradient(180deg,#00e5a0,#0099ff); border-radius:3px 0 0 3px;
            }}
            .result-name {{ font-size:1.05rem; font-weight:500; color:#f0f0f0; margin-bottom:0.3rem; }}
            mark {{ background:rgba(0,229,160,0.25); color:#00e5a0; border-radius:3px; padding:0 2px; }}
            .desc {{ color:#888; font-size:0.85rem; margin-bottom:0.3rem; }}
            .result-tags {{ display:flex; flex-wrap:wrap; gap:0.4rem; margin:0.4rem 0; }}
            .tag {{ background:#1e1e1e; border:1px solid #2a2a2a; border-radius:6px;
                    padding:2px 8px; font-size:0.72rem; color:#888; }}
            .result-url {{ font-family:'Space Mono',monospace; font-size:0.75rem; color:#0099ff;
                           word-break:break-all; text-decoration:none; display:block; margin-top:0.4rem; }}
            .result-url:hover {{ text-decoration:underline; }}
        </style>
        {cards_html}
        """, height=max(160 * len(results), 160), scrolling=False)
