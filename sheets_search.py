import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="시트 검색엔진",
    page_icon="🔍",
    layout="wide",
)

# ── 로그인 ───────────────────────────────────────────────────
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
        background: #1e1e1e !important; border: 1px solid #2a2a2a !important;
        border-radius: 10px !important; color: #f0f0f0 !important; font-size: 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00e5a0 !important; box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #00e5a0, #00c478) !important;
        color: #000 !important; border: none !important; border-radius: 10px !important;
        font-weight: 700 !important; padding: 0.6rem !important; font-size: 1rem !important;
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
        if st.button("로그인", use_container_width=True):
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 틀렸어요.")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ── Google 연결 ──────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_google_creds():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )

@st.cache_resource
def get_worksheet():
    client = gspread.authorize(get_google_creds())
    spreadsheet = client.open_by_url(st.secrets["sheet"]["url"])
    return spreadsheet.sheet1

def get_drive_service():
    return build("drive", "v3", credentials=get_google_creds())

def load_data():
    try:
        return get_worksheet().get_all_records()
    except Exception as e:
        st.error(f"구글 시트 연결 오류: {e}")
        return []

def add_row(entry):
    get_worksheet().append_row([
        entry["id"], entry["name"], entry["url"], entry["tags"], entry["desc"]
    ])

def delete_row(row_index):
    get_worksheet().delete_rows(row_index + 2)

def clear_all():
    all_rows = get_worksheet().get_all_values()
    if len(all_rows) > 1:
        get_worksheet().delete_rows(2, len(all_rows))

def get_sheet_id_from_url(url):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

@st.cache_data(ttl=300)
def get_shared_users(sheet_url):
    try:
        drive = get_drive_service()
        file_id = get_sheet_id_from_url(sheet_url)
        if not file_id:
            return []
        perms = drive.permissions().list(
            fileId=file_id,
            fields="permissions(emailAddress,role,type,displayName)"
        ).execute()
        return perms.get("permissions", [])
    except Exception as e:
        return [{"error": str(e)}]

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Space+Mono:wght@400;700&display=swap');
:root {
    --bg:#0d0d0d; --surface:#161616; --surface2:#1e1e1e;
    --border:#2a2a2a; --accent:#00e5a0; --accent2:#0099ff;
    --text:#f0f0f0; --muted:#888;
}
html,body,[class*="css"] { background-color:var(--bg)!important; color:var(--text)!important; font-family:'Noto Sans KR',sans-serif!important; }
.hero { text-align:center; padding:2rem 0 1.5rem; }
.hero h1 { font-family:'Space Mono',monospace; font-size:2.4rem; font-weight:700;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; }
.hero p { color:var(--muted); font-size:0.9rem; margin-top:0.4rem; }
.section-title { font-family:'Space Mono',monospace; font-size:0.72rem;
    letter-spacing:0.12em; text-transform:uppercase; color:var(--accent);
    margin-bottom:1rem; border-bottom:1px solid var(--border); padding-bottom:0.5rem; }
.stTextInput>div>div>input { background:var(--surface2)!important; border:1px solid var(--border)!important;
    border-radius:10px!important; color:var(--text)!important; font-size:1rem!important; }
.stTextInput>div>div>input:focus { border-color:var(--accent)!important; box-shadow:0 0 0 2px rgba(0,229,160,0.15)!important; }
.stButton>button { background:linear-gradient(135deg,var(--accent),#00c478)!important; color:#000!important;
    border:none!important; border-radius:10px!important; font-weight:700!important;
    font-family:'Noto Sans KR',sans-serif!important; transition:opacity 0.2s!important; }
.stButton>button:hover { opacity:0.85!important; }
div[data-testid="stExpander"] { background:var(--surface)!important; border:1px solid var(--border)!important; border-radius:12px!important; }
.badge { display:inline-block; background:rgba(0,229,160,0.15); color:var(--accent);
    border:1px solid rgba(0,229,160,0.3); border-radius:20px;
    padding:2px 10px; font-size:0.78rem; font-family:'Space Mono',monospace; }
.stTabs [data-baseweb="tab-list"] { background:var(--surface)!important; border-radius:12px!important; padding:4px!important; }
.stTabs [data-baseweb="tab"] { color:var(--muted)!important; border-radius:8px!important; }
.stTabs [aria-selected="true"] { background:var(--surface2)!important; color:var(--accent)!important; }
</style>
""", unsafe_allow_html=True)

# ── 유틸 ────────────────────────────────────────────────────
def highlight(text, query):
    if not query:
        return text
    return re.sub(f"({re.escape(query)})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)

def search_by_name(sheets, query, tags_filter):
    query = query.strip().lower()
    results = []
    for s in sheets:
        sheet_tags = [t.strip() for t in str(s.get("tags","")).split(",") if t.strip()]
        name_match = query and query in s["name"].lower()
        tag_match = query and any(query in t.lower() for t in sheet_tags)
        tag_filter_match = (not tags_filter) or any(tf in sheet_tags for tf in tags_filter)
        score = 0
        if name_match: score += 2
        if tag_match: score += 1
        if (name_match or tag_match or not query) and tag_filter_match:
            results.append((score, s))
    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results]

PAGE_SIZE = 5

def paginate(items, page_key):
    total = len(items)
    total_pages = max(1, -(-total // PAGE_SIZE))  # ceiling division
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    # 페이지 범위 보정
    st.session_state[page_key] = max(1, min(st.session_state[page_key], total_pages))
    page = st.session_state[page_key]
    start = (page - 1) * PAGE_SIZE
    paged_items = items[start:start + PAGE_SIZE]

    # 페이지 버튼 렌더링
    if total_pages > 1:
        cols = st.columns([1, 1, 3, 1, 1])
        with cols[0]:
            if st.button("◀◀", key=f"{page_key}_first", disabled=(page == 1)):
                st.session_state[page_key] = 1
                st.rerun()
        with cols[1]:
            if st.button("◀", key=f"{page_key}_prev", disabled=(page == 1)):
                st.session_state[page_key] -= 1
                st.rerun()
        with cols[2]:
            st.markdown(f'<div style="text-align:center;color:#888;padding-top:0.4rem;font-size:0.85rem">{page} / {total_pages} 페이지</div>', unsafe_allow_html=True)
        with cols[3]:
            if st.button("▶", key=f"{page_key}_next", disabled=(page == total_pages)):
                st.session_state[page_key] += 1
                st.rerun()
        with cols[4]:
            if st.button("▶▶", key=f"{page_key}_last", disabled=(page == total_pages)):
                st.session_state[page_key] = total_pages
                st.rerun()
    return paged_items

def normalize_url(url):
    """URL에서 시트 ID만 추출해서 비교용으로 사용"""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else url.strip()

def find_duplicate(sheets, url):
    """같은 시트 ID를 가진 항목 반환"""
    new_id = normalize_url(url)
    for s in sheets:
        if normalize_url(s.get("url", "")) == new_id:
            return s
    return None

def search_by_url(sheets, url):
    """URL로 동일 시트 검색"""
    target_id = normalize_url(url)
    return [s for s in sheets if normalize_url(s.get("url", "")) == target_id]


def role_label(role):
    return {"owner": "👑 소유자", "writer": "✏️ 편집자", "reader": "👁️ 뷰어", "commenter": "💬 댓글"}.get(role, role)

def render_cards(results, query="", show_role=False):
    cards_html = ""
    for s in results:
        sheet_tags = [t.strip() for t in str(s.get("tags","")).split(",") if t.strip()]
        highlighted_name = highlight(s["name"], query)
        tags_html = "".join(f'<span class="tag">#{highlight(t, query)}</span>' for t in sheet_tags)
        desc_html = f'<div class="desc">{s["desc"]}</div>' if s.get("desc") else ""
        role_html = f'<span class="role-badge">{role_label(s["_role"])}</span>' if show_role and s.get("_role") else ""
        cards_html += f"""
        <div class="result-card">
            <div class="result-name">📄 {highlighted_name} {role_html}</div>
            {desc_html}
            <div class="result-tags">{tags_html}</div>
            <a class="result-url" href="{s['url']}" target="_blank">🔗 {s['url']}</a>
        </div>"""

    components.html(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono&family=Noto+Sans+KR:wght@400;500&display=swap');
        body {{ margin:0; padding:0; background:transparent; font-family:'Noto Sans KR',sans-serif; }}
        .result-card {{ background:#161616; border:1px solid #2a2a2a; border-radius:12px;
            padding:1.2rem 1.5rem; margin-bottom:0.8rem; position:relative; overflow:hidden; }}
        .result-card::before {{ content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
            background:linear-gradient(180deg,#00e5a0,#0099ff); border-radius:3px 0 0 3px; }}
        .result-name {{ font-size:1.05rem; font-weight:500; color:#f0f0f0; margin-bottom:0.3rem; }}
        mark {{ background:rgba(0,229,160,0.25); color:#00e5a0; border-radius:3px; padding:0 2px; }}
        .desc {{ color:#888; font-size:0.85rem; margin-bottom:0.3rem; }}
        .result-tags {{ display:flex; flex-wrap:wrap; gap:0.4rem; margin:0.4rem 0; }}
        .tag {{ background:#1e1e1e; border:1px solid #2a2a2a; border-radius:6px; padding:2px 8px; font-size:0.72rem; color:#888; }}
        .result-url {{ font-family:'Space Mono',monospace; font-size:0.75rem; color:#0099ff;
            word-break:break-all; text-decoration:none; display:block; margin-top:0.4rem; }}
        .result-url:hover {{ text-decoration:underline; }}
        .role-badge {{ background:rgba(0,229,160,0.15); color:#00e5a0; border:1px solid rgba(0,229,160,0.3);
            border-radius:20px; padding:1px 8px; font-size:0.75rem; margin-left:6px; vertical-align:middle; }}
    </style>
    {cards_html}
    """, height=max(160 * len(results), 160), scrolling=False)

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
        st.rerun()

sheets_data = load_data()

# ── 레이아웃 ─────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.6], gap="large")

# ══ 왼쪽: 등록 ══════════════════════════════════════════════
with col_left:
    st.markdown('<div class="section-title">📋 시트 등록</div>', unsafe_allow_html=True)
    new_name     = st.text_input("시트 이름", placeholder="예) 2024 마케팅 예산")
    new_url      = st.text_input("구글 시트 URL", placeholder="https://docs.google.com/spreadsheets/d/...")
    new_tags_raw = st.text_input("태그 (쉼표 구분)", placeholder="예) 마케팅, 예산, 2024")
    new_desc     = st.text_input("간단한 설명 (선택)", placeholder="예) Q1~Q4 마케팅 비용 정리")

    c1, c2 = st.columns(2)
    with c1:
        add_btn = st.button("➕ 등록하기", use_container_width=True)
    with c2:
        if st.button("🗑️ 전체 삭제", use_container_width=True):
            clear_all()
            st.warning("전체 삭제 완료")
            st.rerun()

    if add_btn:
        if not new_name.strip():
            st.error("시트 이름을 입력해주세요.")
        elif not new_url.strip():
            st.error("URL을 입력해주세요.")
        else:
            dup = find_duplicate(sheets_data, new_url.strip())
            if dup:
                st.warning(f"⚠️ 이미 등록된 시트예요! → **{dup['name']}**")
            else:
                add_row({"id": datetime.now().isoformat(), "name": new_name.strip(),
                         "url": new_url.strip(), "tags": new_tags_raw.strip(), "desc": new_desc.strip()})
                st.success(f"✅ '{new_name}' 등록 완료!")
                st.rerun()

    if sheets_data:
        st.markdown('<div class="section-title" style="margin-top:2rem">📂 등록된 시트 목록</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge">총 {len(sheets_data)}개</span>', unsafe_allow_html=True)
        st.write("")
        paged_list = paginate(sheets_data, "list_page")
        st.write("")
        for s in paged_list:
            i = sheets_data.index(s)
            with st.expander(f"📄 {s['name']}"):
                url_d = s['url'][:55]+"..." if len(s['url'])>55 else s['url']
                st.markdown(f"**URL:** [{url_d}]({s['url']})")
                if s.get("tags"): st.markdown(f"**태그:** {s['tags']}")
                if s.get("desc"): st.markdown(f"**설명:** {s['desc']}")
                if st.button("🗑️ 삭제", key=f"del_{i}"):
                    delete_row(i)
                    st.rerun()

# ══ 오른쪽: 검색 ════════════════════════════════════════════
with col_right:
    st.markdown('<div class="section-title">🔍 검색</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📄 시트 검색", "🔗 링크로 검색", "👤 이메일로 검색", "👥 시트 공유 목록"])

    # ── 탭1: 시트 검색 ──────────────────────────────────────
    with tab1:
        search_query = st.text_input("시트 이름 또는 태그 검색", placeholder="예) 마케팅, 예산...", key="sq")
        # 검색어 바뀌면 페이지 리셋
        if "prev_sq" not in st.session_state: st.session_state["prev_sq"] = ""
        if search_query != st.session_state["prev_sq"]:
            st.session_state["search_page"] = 1
            st.session_state["prev_sq"] = search_query
        all_tags = sorted(set(t.strip() for s in sheets_data for t in str(s.get("tags","")).split(",") if t.strip()))
        selected_tags = st.multiselect("태그 필터", all_tags) if all_tags else []
        st.write("")

        results = search_by_name(sheets_data, search_query, selected_tags)

        if not sheets_data:
            st.markdown('<div style="text-align:center;padding:3rem 0;color:#888"><div style="font-size:2.5rem">📭</div><p>등록된 시트가 없어요</p></div>', unsafe_allow_html=True)
        elif not results:
            st.markdown(f'<div style="text-align:center;padding:3rem 0;color:#888"><div style="font-size:2.5rem">🔎</div><p><b>{search_query}</b> 결과 없음</p></div>', unsafe_allow_html=True)
        else:
            label = f"검색 결과: {len(results)}개" if search_query or selected_tags else f"전체 {len(results)}개"
            st.markdown(f'<span class="badge">{label}</span>', unsafe_allow_html=True)
            st.write("")
            paged_results = paginate(results, "search_page")
            st.write("")
            render_cards(paged_results, search_query)


    # ── 탭2: 링크로 검색 ────────────────────────────────────
    with tab2:
        url_query = st.text_input("구글 시트 URL 입력", placeholder="https://docs.google.com/spreadsheets/d/...", key="uq")
        st.write("")

        if url_query.strip():
            url_results = search_by_url(sheets_data, url_query.strip())
            if url_results:
                st.markdown(f'<span class="badge">✅ 동일한 시트 {len(url_results)}개 발견</span>', unsafe_allow_html=True)
                st.write("")
                render_cards(url_results)
            else:
                sheet_id = normalize_url(url_query.strip())
                if sheet_id != url_query.strip():
                    st.markdown(f"""
                    <div style="text-align:center;padding:3rem 0;color:#888">
                        <div style="font-size:2.5rem">🔎</div>
                        <p>등록된 시트가 없어요.<br>
                        <span style="font-family:monospace;font-size:0.8rem;color:#555">{sheet_id}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align:center;padding:3rem 0;color:#888"><div style="font-size:2.5rem">⚠️</div><p>구글 시트 URL 형식이 아닌 것 같아요.</p></div>', unsafe_allow_html=True)

    # ── 탭3: 이메일로 검색 ──────────────────────────────────
    with tab3:
        email_query = st.text_input("이메일 주소 입력", placeholder="예) hong@gmail.com", key="eq")
        search_email_btn = st.button("🔍 검색", key="email_search_btn")
        st.write("")

        if search_email_btn and email_query.strip():
            matched = []
            progress = st.progress(0, text="공유 목록 조회 중...")
            for idx, s in enumerate(sheets_data):
                perms = get_shared_users(s["url"])
                emails = [p.get("emailAddress","").lower() for p in perms if "emailAddress" in p]
                if email_query.strip().lower() in emails:
                    role = next((p.get("role") for p in perms if p.get("emailAddress","").lower() == email_query.strip().lower()), "")
                    matched.append({**s, "_role": role})
                progress.progress((idx+1)/max(len(sheets_data),1), text=f"조회 중... ({idx+1}/{len(sheets_data)})")
            progress.empty()

            if matched:
                st.markdown(f'<span class="badge">{email_query} — {len(matched)}개 시트에 권한 있음</span>', unsafe_allow_html=True)
                st.write("")
                render_cards(matched, show_role=True)
            else:
                st.markdown(f'<div style="text-align:center;padding:3rem 0;color:#888"><div style="font-size:2.5rem">🔎</div><p><b>{email_query}</b>이 공유된 시트가 없어요</p></div>', unsafe_allow_html=True)

    # ── 탭4: 시트 공유 목록 ─────────────────────────────────
    with tab4:
        if not sheets_data:
            st.markdown('<div style="text-align:center;padding:3rem 0;color:#888"><div style="font-size:2.5rem">📭</div><p>등록된 시트가 없어요</p></div>', unsafe_allow_html=True)
        else:
            sheet_names = [s["name"] for s in sheets_data]
            selected_sheet = st.selectbox("시트 선택", sheet_names)
            selected = next((s for s in sheets_data if s["name"] == selected_sheet), None)

            sort_col, btn_col = st.columns([2, 1])
            with sort_col:
                sort_option = st.selectbox("정렬 기준", [
                    "📧 이메일 오름차순 (A→Z)",
                    "📧 이메일 내림차순 (Z→A)",
                    "🔑 권한순 (소유자→편집자→뷰어)",
                    "🕐 추가된 순서 (기본)",
                ], key="perm_sort")
            with btn_col:
                st.write("")
                load_btn = st.button("👥 공유 목록 불러오기", use_container_width=True)

            if selected and load_btn:
                with st.spinner("공유 목록 조회 중..."):
                    perms = get_shared_users(selected["url"])

                if perms and "error" in perms[0]:
                    st.error(f"조회 실패: {perms[0]['error']}\n\n봇이 이 시트의 편집자로 추가되어 있는지 확인해주세요.")
                elif not perms:
                    st.info("공유된 사람이 없어요.")
                else:
                    # 정렬 적용
                    role_order = {"owner": 0, "writer": 1, "commenter": 2, "reader": 3}
                    if "오름차순" in sort_option:
                        perms = sorted(perms, key=lambda p: p.get("emailAddress", "🌐").lower())
                    elif "내림차순" in sort_option:
                        perms = sorted(perms, key=lambda p: p.get("emailAddress", "🌐").lower(), reverse=True)
                    elif "권한순" in sort_option:
                        perms = sorted(perms, key=lambda p: role_order.get(p.get("role",""), 9))

                    st.markdown(f'<span class="badge">총 {len(perms)}명</span>', unsafe_allow_html=True)
                    st.write("")
                    rows_html = ""
                    for p in perms:
                        email = p.get("emailAddress", "")
                        name = p.get("displayName", "")
                        role = role_label(p.get("role",""))
                        ptype = p.get("type","")
                        if ptype == "anyone":
                            email = "🌐 링크가 있는 누구나"
                        elif not email:
                            email = "알 수 없음"
                        rows_html += f"""
                        <div class="perm-row">
                            <div class="perm-email">{email}{f' <span class="perm-name">({name})</span>' if name else ''}</div>
                            <div class="perm-role">{role}</div>
                        </div>"""
                    components.html(f"""
                    <style>
                        body {{ margin:0; padding:0; background:transparent; font-family:'Noto Sans KR',sans-serif; }}
                        .perm-row {{ display:flex; justify-content:space-between; align-items:center;
                            background:#161616; border:1px solid #2a2a2a; border-radius:10px;
                            padding:0.8rem 1.2rem; margin-bottom:0.5rem; }}
                        .perm-email {{ color:#f0f0f0; font-size:0.9rem; }}
                        .perm-name {{ color:#888; font-size:0.8rem; }}
                        .perm-role {{ color:#00e5a0; font-size:0.85rem; font-weight:500;
                            background:rgba(0,229,160,0.1); border:1px solid rgba(0,229,160,0.2);
                            border-radius:20px; padding:2px 10px; white-space:nowrap; }}
                    </style>
                    {rows_html}
                    """, height=max(65 * len(perms), 65), scrolling=False)
