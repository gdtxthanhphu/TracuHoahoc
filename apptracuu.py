import re
import urllib.parse

import matplotlib.pyplot as plt
import mendeleev
import pubchempy as pcp
import py3Dmol
import requests
import streamlit as st
from bs4 import BeautifulSoup
from chempy import Substance, balance_stoichiometry
from stmol import showmol
import jcamp  # thư viện đọc JCAMP-DX

# ==========================================
# 1. CẤU HÌNH TRANG & CSS
# ==========================================
st.set_page_config(page_title="Hóa Học Online 4.0", page_icon="⚗️", layout="wide")

# --- QUẢN LÝ SESSION STATE ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Trang chủ"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "search_type_saved" not in st.session_state:
    st.session_state.search_type_saved = "Tên (Name)"


def navigate_to(page_name: str):
    st.session_state.current_page = page_name


def local_css():
    st.markdown(
        """
    <style>
        /* ===========================
           FONT & BODY
           =========================== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        .stApp {
            background: linear-gradient(180deg, #e0f2fe 0%, #f9fafb 45%, #e5e7eb 100%) !important;
            color: #0f172a !important;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 15px;
            line-height: 1.6;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2.6rem;   /* đẩy nội dung xuống dưới thanh top */
            padding-bottom: 3rem;
        }

        .block-container h1 {
            margin-top: 0 !important;
            padding-top: 0.2rem;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #0f172a !important;
            font-weight: 700;
        }

        h1 { font-size: 2.0rem !important; margin-bottom: 0.6rem; }
        h2 { font-size: 1.6rem !important; margin-bottom: 0.4rem; }
        h3 { font-size: 1.25rem !important; }

        p, span, label {
            font-size: 0.95rem !important;
            color: #111827 !important;
        }

        /* ===========================
           SIDEBAR & MENU TRÁI
           =========================== */
        [data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid #e2e8f0;
        }

        [data-testid="stSidebar"] h2 {
            color: #2563eb !important;
            font-weight: 700;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #475569 !important;
        }

        /* Ẩn radio gốc */
        [data-testid="stSidebar"] [data-baseweb="radio"] input {
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] svg {
            display: none !important;
        }

        /* Container các item */
        [data-testid="stSidebar"] [data-baseweb="radio"] > div {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        /* Label là vùng click */
        [data-testid="stSidebar"] [data-baseweb="radio"] label {
            padding: 0;
            margin: 0;
            cursor: pointer;
        }

        /* Ẩn div “chấm tròn” đầu tiên, giữ div sau làm pill */
        [data-testid="stSidebar"] [data-baseweb="radio"] label > div:nth-of-type(1) {
            display: none !important;
        }

        /* PILL MENU – div cuối cùng trong label */
        [data-testid="stSidebar"] [data-baseweb="radio"] label > div:last-of-type {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 999px;
            border: 1px solid transparent;

            font-size: 0.94rem;
            line-height: 1.3;

            white-space: nowrap;
            max-width: 195px;          /* chỉnh chiều rộng menu ở đây */
            overflow: hidden;
            text-overflow: ellipsis;

            transition: background-color 0.14s ease-in-out,
                        color 0.14s ease-in-out,
                        transform 0.08s ease-in-out,
                        box-shadow 0.12s ease-in-out;
        }

        /* Icon menu */
        [data-testid="stSidebar"] [data-baseweb="radio"] label > div:last-of-type span:first-child {
            font-size: 1.0rem !important;
        }

        /* Hover pill */
        [data-testid="stSidebar"] [data-baseweb="radio"] label > div:last-of-type:hover {
            background-color: #eff6ff;
            transform: translateX(2px);
            box-shadow: 0 2px 4px rgba(15,23,42,0.08);
        }

        /* Active: input:checked + div (ẩn) + div (pill)  */
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div + div {
            background: linear-gradient(90deg, #2563eb, #38bdf8);
            color: #f9fafb !important;
            font-weight: 600;
            border-radius: 999px;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
            transform: translateX(2px);
            border-color: transparent;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div + div * {
            color: #f9fafb !important;
        }

        /* ===========================
           SELECTBOX & TEXT INPUT
           =========================== */

        /* Ô select: cao hơn, căn giữa dọc, không cắt dấu */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 999px !important;

            display: flex !important;
            align-items: center !important;

            padding: 8px 16px;
            min-height: 44px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
            font-size: 0.95rem !important;
        }
        div[data-baseweb="select"] > div:hover {
            border-color: #2563eb !important;
        }
        div[data-baseweb="select"] svg {
            fill: #64748b !important;
        }
        div[data-baseweb="select"] span {
            line-height: 1.3 !important;   /* tránh cắt dấu tiếng Việt */
        }

        .stTextInput input {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 999px !important;
            padding: 0.5rem 0.9rem;
            font-size: 0.95rem !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
        }
        .stTextInput input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.35);
        }

        /* ===========================
           BUTTON
           =========================== */
        .stButton>button {
            background: linear-gradient(135deg, #2563eb, #38bdf8) !important;
            color: #ffffff !important;
            border-radius: 999px;
            font-weight: 600;
            border: none;
            padding: 0.5rem 1.2rem;
            font-size: 0.96rem;
            box-shadow: 0 8px 16px rgba(37, 99, 235, 0.35);
            transition: transform 0.08s ease-in-out, box-shadow 0.12s ease-in-out,
                        filter 0.12s ease-in-out;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 22px rgba(37, 99, 235, 0.45);
            filter: brightness(1.02);
        }
        .stButton>button:active {
            transform: translateY(0px) scale(0.99);
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.45);
        }

        /* ===========================
           CARD TRANG CHỦ
           =========================== */
        .css-card {
            background-color: #ffffff;
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.25);
            text-align: left;
            margin-bottom: 10px;
            height: auto;
            min-height: 185px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
            transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out,
                        border-color 0.15s ease-in-out;
        }

        .css-card h1 { font-size: 2.2rem !important; margin-bottom: 0.35rem; }
        .css-card h3 { font-size: 1.12rem !important; margin-bottom: 0.35rem; }
        .css-card p  { font-size: 0.93rem !important; color: #64748b !important; }

        .css-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.18);
            border-color: #2563eb;
        }

        /* ===========================
           TABS, METRIC, EXPANDER
           =========================== */
        .stTabs [role="tablist"] {
            border-bottom: 1px solid #e2e8f0;
            gap: 0.25rem;
        }
        .stTabs [role="tab"] {
            border-radius: 999px;
            padding: 0.35rem 0.9rem;
            font-weight: 500;
            color: #64748b !important;
            border: none;
            background-color: transparent;
            font-size: 0.95rem !important;
        }
        .stTabs [role="tab"]:hover {
            color: #0f172a !important;
            background-color: #e5f0ff;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            color: #0f172a !important;
            background-color: #ffffff;
            box-shadow: 0 3px 8px rgba(15, 23, 42, 0.14);
            border: 1px solid #bfdbfe;
        }

        [data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-weight: 700;
            font-size: 1.02rem !important;
        }
        [data-testid="stMetricLabel"] {
            color: #6b7280 !important;
            font-size: 0.88rem !important;
        }

        details {
            border-radius: 18px !important;
            border: 1px solid #e2e8f0 !important;
            background: #ffffff !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
            padding: 4px 0 !important;
        }
        details summary {
            font-weight: 600;
            color: #0f172a !important;
            font-size: 0.95rem !important;
        }

        .stCheckbox>label {
            font-size: 0.93rem !important;
            font-weight: 500;
            color: #0f172a !important;
        }

        .main > div { padding-top: 0.5rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )


local_css()

# ==========================================
# 2. BACKEND: NIST WEBBOOK & PHỔ
# ==========================================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
BASE_URL = "https://webbook.nist.gov"


def classify_phase(desc: str) -> str:
    d = desc.lower()
    if any(k in d for k in ["gas", "vapor"]):
        return "Gas (Khí)"
    if any(k in d for k in ["solid", "kbr", "nujol", "pellet", "disk"]):
        return "Solid (Rắn)"
    if any(k in d for k in ["solution", "liquid", "ccl4", "cs2", "condensed"]):
        return "Liquid (Lỏng)"
    return "Phổ IR"


@st.cache_data(show_spinner=False)
def get_nist_id(name: str):
    cleaned = name.strip()
    if re.match(r"^\d{2,7}-\d{2}-\d$", cleaned):
        return cleaned  # CAS

    safe_name = urllib.parse.quote(cleaned)
    url = f"{BASE_URL}/cgi/cbook.cgi?Name={safe_name}&Units=SI"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if "ID=" in res.url:
            match = re.search(r"ID=([^&]+)", res.url)
            if match:
                return match.group(1)

        soup = BeautifulSoup(res.content, "html.parser")
        link = soup.find("a", href=re.compile(r"ID="))
        if link:
            match = re.search(r"ID=([^&]+)", link["href"])
            if match:
                return match.group(1)
    except Exception:
        return None
    return None


@st.cache_data(show_spinner=False)
def get_ir_spectra_links(nist_id: str):
    """Lấy danh sách link phổ IR (JCAMP) từ NIST, Mask=80."""
    url = f"{BASE_URL}/cgi/cbook.cgi?ID={nist_id}&Units=SI&Mask=80"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        html_text = res.text
        results = []

        found_indices = re.findall(r"Index=(\d+)", html_text)
        unique_indices = sorted(set(found_indices), key=lambda x: int(x))

        if not unique_indices:
            return []

        soup = BeautifulSoup(html_text, "html.parser")

        for idx in unique_indices:
            jcamp_link = f"{BASE_URL}/cgi/cbook.cgi?JCAMP={nist_id}&Index={idx}&Type=IR"

            desc = f"Spectrum #{idx}"
            try:
                a_tag = soup.find("a", href=re.compile(f"Index={idx}"))
                if a_tag:
                    txt = a_tag.get_text(" ", strip=True)
                    if len(txt) > 3:
                        desc = txt
                    else:
                        p = a_tag.find_parent("li")
                        if p:
                            desc = p.get_text(" ", strip=True)
            except Exception:
                pass

            clean_desc = (
                desc.replace("View", "")
                .replace("Spectrum", "")
                .replace("Download", "")
                .strip()
            )
            if not clean_desc:
                clean_desc = f"Spectrum #{idx}"

            results.append(
                {
                    "phase": classify_phase(clean_desc),
                    "desc": clean_desc,
                    "url": jcamp_link,
                }
            )

        return results
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def get_ms_spectra_links(nist_id: str):
    """Lấy danh sách link phổ MS (Mass spectrum) từ NIST, Mask=2000."""
    url = f"{BASE_URL}/cgi/cbook.cgi?ID={nist_id}&Units=SI&Mask=2000"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        html_text = res.text
        results = []

        found_indices = re.findall(r"Index=(\d+)", html_text)
        unique_indices = sorted(set(found_indices), key=lambda x: int(x))

        if not unique_indices:
            return []

        soup = BeautifulSoup(html_text, "html.parser")

        for idx in unique_indices:
            jcamp_link = f"{BASE_URL}/cgi/cbook.cgi?JCAMP={nist_id}&Index={idx}&Type=Mass"

            desc = f"Mass spectrum #{idx}"
            try:
                a_tag = soup.find("a", href=re.compile(f"Index={idx}"))
                if a_tag:
                    txt = a_tag.get_text(" ", strip=True)
                    if len(txt) > 3:
                        desc = txt
                    else:
                        p = a_tag.find_parent("li")
                        if p:
                            desc = p.get_text(" ", strip=True)
            except Exception:
                pass

            clean_desc = (
                desc.replace("View", "")
                .replace("Spectrum", "")
                .replace("Download", "")
                .strip()
            )
            if not clean_desc:
                clean_desc = f"Mass spectrum #{idx}"

            results.append(
                {
                    "desc": clean_desc,
                    "url": jcamp_link,
                }
            )

        return results
    except Exception:
        return []


def parse_jcamp(jdx_text: str):
    """Đọc file JCAMP-DX, ưu tiên dùng thư viện jcamp, fallback sang parser đơn giản."""
    try:
        lines = jdx_text.splitlines()
        data = jcamp.jcamp_read(lines)
        x = data.get("x")
        y = data.get("y")
        if x is not None and y is not None and len(x) and len(y):
            return list(x), list(y)
    except Exception:
        pass

    x_data, y_data = [], []
    start_data = False
    try:
        for raw_line in jdx_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.upper().startswith("##XYDATA") or line.upper().startswith("##PEAK TABLE"):
                start_data = True
                continue
            if line.upper().startswith("##END"):
                break
            if start_data and not line.startswith("##"):
                parts = re.split(r"[,\s;]+", line)
                nums = []
                for p in parts:
                    if not p:
                        continue
                    try:
                        nums.append(float(p))
                    except ValueError:
                        pass
                if len(nums) >= 2:
                    x_data.append(nums[0])
                    y_data.append(nums[1])
    except Exception:
        pass

    return x_data, y_data


def find_nist_spectra_links(c, query: str, get_links_fn):
    """
    Tìm NIST ID + danh sách phổ cho 1 chất:
    - thử CAS,
    - thử synonym đầu tiên,
    - thử chính query.
    get_links_fn: hàm lấy IR/MS links (get_ir_spectra_links hoặc get_ms_spectra_links)
    """
    synonyms = getattr(c, "synonyms", None)
    cas = get_cas_number(synonyms) if synonyms else None

    name_candidates = []
    if synonyms:
        name_candidates.append(synonyms[0])
    name_candidates.append(query)

    # 1. thử CAS
    if cas:
        nid = get_nist_id(cas)
        if nid:
            ls = get_links_fn(nid)
            if ls:
                return nid, ls

    # 2. thử theo tên
    for name_try in name_candidates:
        nid = get_nist_id(name_try)
        if not nid:
            continue
        ls = get_links_fn(nid)
        if ls:
            return nid, ls

    return None, []


# ==========================================
# 3. HỖ TRỢ KHÁC
# ==========================================
def draw_textbook_style(smiles: str):
    return None  # RDKit không dùng, fallback sang ảnh 2D PubChem


def get_2d_url(smiles: str):
    if not smiles:
        return None
    return (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/"
        f"{urllib.parse.quote(smiles)}/PNG?record_type=2d&image_size=600x600"
    )


def make_pretty_formula(text: str) -> str:
    if not text:
        return ""
    sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return text.translate(sub)


def get_cas_number(synonyms):
    if not synonyms:
        return None
    pattern = re.compile(r"^\d{2,7}-\d{2}-\d$")
    for syn in synonyms:
        if pattern.match(syn):
            return syn
    return None


# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: left; margin-bottom: 1rem;">
            <h2 style="margin:0;">⚗️ Hóa Học 4.0</h2>
            <p style="font-size:0.9rem; color:#64748b;">
                Người bạn đồng hành học hóa của bạn.
            </p>
        </div>
        <p style="font-size:0.9rem; color:#64748b; margin-bottom:0.4rem;">
            🌈 Chọn chế độ
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.radio(
        "",
        ["🏠 Trang chủ", "🔍 Tra cứu & Cấu trúc", "⚖️ Cân bằng PT", "🧮 Tiện ích mở rộng"],
        key="current_page",
    )

page = st.session_state.current_page

# ------------------------------------------
# 🏠 TRANG CHỦ
# ------------------------------------------
if page == "🏠 Trang chủ":
    st.markdown("## Xin chào 👋")
    st.caption("Cùng khám phá thế giới hóa học theo cách trực quan và dễ hiểu nhất.")

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
        <div class="css-card">
            <div>
                <h1>🔍</h1>
                <h3>Tra cứu chất</h3>
                <p>Xem cấu trúc, 3D, tính chất và phổ IR/MS của hàng triệu chất.</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.button("Vào tra cứu", on_click=navigate_to, args=("🔍 Tra cứu & Cấu trúc",))

    with c2:
        st.markdown(
            """
        <div class="css-card">
            <div>
                <h1>⚖️</h1>
                <h3>Cân bằng phương trình</h3>
                <p>Tự động tìm hệ số, giúp bạn tập trung hiểu bản chất phản ứng.</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.button("Cân bằng ngay", on_click=navigate_to, args=("⚖️ Cân bằng PT",))

    with c3:
        st.markdown(
            """
        <div class="css-card">
            <div>
                <h1>🧮</h1>
                <h3>Tiện ích học tập</h3>
                <p>Tính phân tử khối, tra bảng tuần hoàn, cấu hình electron,...</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.button("Xem tiện ích", on_click=navigate_to, args=("🧮 Tiện ích mở rộng",))

# ------------------------------------------
# 🔍 TRA CỨU & CẤU TRÚC
# ------------------------------------------
elif page == "🔍 Tra cứu & Cấu trúc":
    st.markdown("## Tra cứu & Cấu trúc")

    with st.container():
        st.markdown(
            """
        <div style="
            background-color: #ffffff;
            padding: 18px 20px;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 12px 26px rgba(15,23,42,0.18);
        ">
        """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns([1, 3])
        search_type = c1.selectbox(
            "Phương thức:",
            ["Tên (Name)", "Công thức (Formula)"],
            key="search_type_widget",
        )
        user_input = c2.text_input(
            "Nhập dữ liệu:",
            value=st.session_state.search_query,
            placeholder="Ví dụ: ethanol, C2H5OH...",
        )

        clicked = st.button("🚀 Tìm kiếm ngay", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if clicked:
        st.session_state.search_query = user_input
        st.session_state.search_type_saved = search_type

    query = st.session_state.search_query.strip()
    saved_type = st.session_state.search_type_saved

    if query:
        with st.spinner("Đang tìm kiếm trên PubChem & NIST..."):
            try:
                by = "name" if saved_type == "Tên (Name)" else "formula"
                comps = pcp.get_compounds(query, by)

                if not comps:
                    st.error("Không tìm thấy chất này trên PubChem.")
                else:
                    c = comps[0]
                    main_name = c.synonyms[0] if getattr(c, "synonyms", None) else query
                    st.success(f"Đã tìm thấy: {main_name}")
                    st.markdown("---")

                    t1, t2, t3, t4, t5 = st.tabs(
                        [
                            "📘 Cấu tạo",
                            "📊 Lý tính",
                            "🧊 Mô hình 3D",
                            "📈 Phổ IR (NIST)",
                            "💥 Phổ MS (NIST)",
                        ]
                    )

                    # ---------- TAB 1: CẤU TẠO ----------
                    with t1:
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            smiles = getattr(c, "isomeric_smiles", None) or getattr(
                                c, "canonical_smiles", None
                            )
                            if smiles:
                                img = draw_textbook_style(smiles)
                                if img:
                                    st.image(img)
                                else:
                                    url2d = get_2d_url(smiles)
                                    if url2d:
                                        st.image(url2d)
                                    else:
                                        st.warning("Không tạo được hình 2D từ SMILES.")
                            else:
                                st.warning(
                                    "PubChem không cung cấp SMILES cho chất này."
                                )

                        with col2:
                            iupac = getattr(c, "iupac_name", None)
                            formula = getattr(c, "molecular_formula", None)
                            synonyms = getattr(c, "synonyms", None)
                            cas = get_cas_number(synonyms) if synonyms else None

                            st.write(f"**Tên IUPAC:** {iupac if iupac else 'N/A'}")
                            st.write(
                                f"**Công thức phân tử:** {make_pretty_formula(formula) if formula else 'N/A'}"
                            )
                            st.write(f"**Mã CAS:** {cas if cas else 'N/A'}")
                            st.write(f"**CID (PubChem):** {c.cid}")

                    # ---------- TAB 2: LÝ TÍNH ----------
                    with t2:
                        cA, cB = st.columns(2)
                        mw = getattr(c, "molecular_weight", None)
                        charge = getattr(c, "charge", None)

                        cA.metric(
                            "Khối lượng mol",
                            f"{mw:.3f} g/mol" if mw is not None else "N/A",
                        )
                        cB.metric("Điện tích", str(charge) if charge is not None else "0")

                    # ---------- TAB 3: 3D MODEL ----------
                    with t3:
                        try:
                            sdf_url = (
                                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
                                f"compound/CID/{c.cid}/record/SDF/?record_type=3d"
                            )
                            r = requests.get(sdf_url, timeout=10)
                            if r.status_code == 200 and r.text.strip():
                                v = py3Dmol.view(width=500, height=320)
                                v.addModel(r.text, "sdf")
                                v.setStyle({"stick": {}})
                                v.zoomTo()
                                showmol(v, height=320, width=500)
                            else:
                                st.warning("Không có mô hình 3D cho chất này.")
                        except Exception:
                            st.warning("Không lấy được mô hình 3D.")

                    # ---------- TAB 4: PHỔ IR ----------
                    with t4:
                        st.info(
                            "Phổ hồng ngoại được lấy trực tiếp từ NIST Chemistry WebBook."
                        )

                        nist_id, links = find_nist_spectra_links(
                            c, query, get_ir_spectra_links
                        )

                        if nist_id and links:
                            st.success(
                                f"Tìm thấy {len(links)} phổ IR (NIST ID: {nist_id})."
                            )

                            options = [
                                f"{i+1}. {l['phase']} - {l['desc']}"
                                for i, l in enumerate(links)
                            ]
                            selected_label = st.selectbox(
                                "Chọn phổ IR muốn xem:",
                                options,
                                index=0,
                            )
                            selected_index = options.index(selected_label)
                            l = links[selected_index]

                            with st.expander(selected_label, expanded=True):
                                show_plot = st.checkbox(
                                    "Hiển thị biểu đồ",
                                    key=f"ir_plot_{nist_id}_{selected_index}",
                                    value=True,
                                )
                                if show_plot:
                                    try:
                                        resp = requests.get(
                                            l["url"], headers=HEADERS, timeout=10
                                        )
                                        text = resp.content.decode(
                                            "utf-8", errors="ignore"
                                        )
                                        x, y = parse_jcamp(text)
                                        if x and y:
                                            fig, ax = plt.subplots(figsize=(8, 3))
                                            ax.plot(x, y)
                                            ax.set_xlabel("Số sóng (cm⁻¹)")
                                            ax.set_ylabel("Cường độ")
                                            ax.invert_xaxis()
                                            ax.grid(True, alpha=0.3)
                                            st.pyplot(fig)
                                        else:
                                            with st.expander(
                                                "Xem 30 dòng đầu JCAMP (debug)"
                                            ):
                                                st.code(
                                                    "\n".join(text.splitlines()[:30])
                                                )
                                            st.warning(
                                                "Không đọc được dữ liệu phổ từ file JCAMP."
                                            )
                                    except Exception:
                                        st.error("Lỗi tải dữ liệu JCAMP từ NIST.")

                                st.markdown(
                                    "<p style='font-size: 0.85rem; color:#64748b;'>Nguồn: NIST Chemistry WebBook</p>",
                                    unsafe_allow_html=True,
                                )
                        elif nist_id and not links:
                            st.warning("Có trên NIST nhưng không có phổ IR.")
                        else:
                            st.warning(
                                "Không tìm thấy dữ liệu IR trên NIST Chemistry WebBook."
                            )

                    # ---------- TAB 5: PHỔ MS ----------
                    with t5:
                        st.info(
                            "Phổ khối phổ (Mass spectrum) được lấy từ NIST Chemistry WebBook nếu có."
                        )

                        nist_id_ms, links_ms = find_nist_spectra_links(
                            c, query, get_ms_spectra_links
                        )

                        if nist_id_ms and links_ms:
                            st.success(
                                f"Tìm thấy {len(links_ms)} phổ MS (NIST ID: {nist_id_ms})."
                            )

                            options_ms = [
                                f"{i+1}. {l['desc']}" for i, l in enumerate(links_ms)
                            ]
                            selected_label_ms = st.selectbox(
                                "Chọn phổ MS muốn xem:",
                                options_ms,
                                index=0,
                            )
                            selected_index_ms = options_ms.index(selected_label_ms)
                            l_ms = links_ms[selected_index_ms]

                            with st.expander(selected_label_ms, expanded=True):
                                show_plot_ms = st.checkbox(
                                    "Hiển thị biểu đồ",
                                    key=f"ms_plot_{nist_id_ms}_{selected_index_ms}",
                                    value=True,
                                )
                                if show_plot_ms:
                                    try:
                                        resp = requests.get(
                                            l_ms["url"], headers=HEADERS, timeout=10
                                        )
                                        text = resp.content.decode(
                                            "utf-8", errors="ignore"
                                        )
                                        x, y = parse_jcamp(text)
                                        if x and y:
                                            fig, ax = plt.subplots(figsize=(8, 3))
                                            ax.stem(x, y, use_line_collection=True)
                                            ax.set_xlabel("m/z")
                                            ax.set_ylabel("Cường độ (Intensity)")
                                            ax.grid(True, alpha=0.3)
                                            st.pyplot(fig)
                                        else:
                                            with st.expander(
                                                "Xem 30 dòng đầu JCAMP (debug)"
                                            ):
                                                st.code(
                                                    "\n".join(text.splitlines()[:30])
                                                )
                                            st.warning(
                                                "Không đọc được dữ liệu phổ từ file JCAMP."
                                            )
                                    except Exception:
                                        st.error("Lỗi tải dữ liệu JCAMP từ NIST.")

                                st.markdown(
                                    "<p style='font-size: 0.85rem; color:#64748b;'>Nguồn: NIST Chemistry WebBook</p>",
                                    unsafe_allow_html=True,
                                )
                        elif nist_id_ms and not links_ms:
                            st.warning("Có trên NIST nhưng không có phổ MS.")
                        else:
                            st.warning(
                                "Không tìm thấy dữ liệu MS trên NIST Chemistry WebBook."
                            )

            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {e}")

# ------------------------------------------
# ⚖️ CÂN BẰNG PHƯƠNG TRÌNH
# ------------------------------------------
elif page == "⚖️ Cân bằng PT":
    st.markdown("## Cân bằng phương trình hóa học")
    st.caption("Nhập reagant và sản phẩm, công cụ sẽ giúp bạn tìm hệ số thích hợp.")

    c1, c2 = st.columns(2)
    reactants = c1.text_input("Chất tham gia:", "KMnO4 + HCl")
    products = c2.text_input("Sản phẩm:", "KCl + MnCl2 + Cl2 + H2O")

    if st.button("✨ Cân bằng ngay"):
        try:
            reac_set = {x.strip() for x in reactants.split("+") if x.strip()}
            prod_set = {x.strip() for x in products.split("+") if x.strip()}

            reac_dict, prod_dict = balance_stoichiometry(reac_set, prod_set)

            def fmt(d):
                return " + ".join(
                    [
                        f"{str(v) if v > 1 else ''}{make_pretty_formula(k)}"
                        for k, v in d.items()
                    ]
                )

            st.success("Kết quả cân bằng:")
            st.latex(f"{fmt(reac_dict)} \\rightarrow {fmt(prod_dict)}")
        except Exception as e:
            st.error(f"Lỗi cân bằng: {e}")

# ------------------------------------------
# 🧮 TIỆN ÍCH MỞ RỘNG
# ------------------------------------------
elif page == "🧮 Tiện ích mở rộng":
    st.markdown("## Tiện ích mở rộng")
    st.caption("Một vài công cụ nhỏ nhưng hữu ích khi học và dạy hóa học.")

    tab_M, tab_BTH = st.tabs(["⚖️ Tính M (phân tử khối)", "⚛️ Tra cứu nguyên tố"])

    with tab_M:
        f_in = st.text_input("Công thức hóa học:", "CuSO4.5H2O")
        if f_in:
            try:
                formula = f_in.replace(".", "*")
                sub = Substance.from_formula(formula)
                st.metric("Phân tử khối", f"{sub.mass:.2f} g/mol")
            except Exception:
                st.error("Công thức không hợp lệ, vui lòng kiểm tra lại.")

    with tab_BTH:
        el_in = st.text_input("Ký hiệu nguyên tố (vd: H, He, Fe...):", "Fe")
        if el_in.strip():
            try:
                el = mendeleev.element(el_in.strip())
                st.metric("Tên nguyên tố", el.name)
                st.metric("Số hiệu nguyên tử (Z)", el.atomic_number)
                st.metric("Nguyên tử khối", f"{el.atomic_weight:.2f}")
                st.write(f"**Cấu hình e⁻:** {el.econf}")
                if el.group_id is not None and el.period is not None:
                    st.write(
                        f"Thuộc chu kỳ {el.period}, nhóm {el.group_id} trong bảng tuần hoàn."
                    )
            except Exception:
                st.error("Không tìm thấy nguyên tố, vui lòng kiểm tra ký hiệu.")
