import streamlit as st
import pubchempy as pcp
import requests
import urllib.parse
from stmol import showmol
import py3Dmol
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from chempy import balance_stoichiometry, Substance
from chempy.util import periodic
import mendeleev 
import re 

# --- 1. CẤU HÌNH TRANG & CSS (ĐÃ SỬA LỖI SELECTBOX) ---
st.set_page_config(page_title="Hóa Học Online", page_icon="🎓", layout="wide")

# Khởi tạo Session State
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Trang chủ"

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def local_css():
    st.markdown("""
    <style>
        /* 1. Cài đặt chung */
        .stApp { background-color: #F0F4F8 !important; }
        
        /* Chỉ chỉnh màu chữ cho các thẻ văn bản chính, KHÔNG chỉnh toàn bộ div (tránh lỗi Selectbox) */
        h1, h2, h3, h4, h5, h6, p, span, label { 
            color: #1E293B !important; 
            font-family: 'Segoe UI', sans-serif; 
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] { 
            background-color: #FFFFFF !important; 
            border-right: 1px solid #E2E8F0; 
        }
        
        /* 2. FIX LỖI SELECTBOX (HỘP TÌM KIẾM) */
        /* Ép nền của hộp chọn thành màu trắng và chữ đen */
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
        }
        
        /* Ép màu chữ trong menu xổ xuống */
        ul[data-baseweb="menu"] li {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
        }
        
        /* Chỉnh màu icon mũi tên trong selectbox */
        div[data-baseweb="select"] svg {
            fill: #1E293B !important;
        }

        /* 3. Style cho Card Dashboard */
        .css-card {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            text-align: center;
            border: 1px solid #E2E8F0;
            margin-bottom: 10px;
            height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        /* 4. Nút bấm */
        .stButton>button {
            background-color: #2563EB !important;
            color: white !important;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
            border: none;
        }
        .stButton>button:hover { background-color: #1D4ED8 !important; }
        
        /* 5. Ô nhập liệu (Input) */
        .stTextInput input {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==========================================
# 2. HÀM HỖ TRỢ (UTILS)
# ==========================================
def draw_textbook_style(smiles):
    if not smiles: return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol: return None
        mol = Chem.AddHs(mol) 
        for atom in mol.GetAtoms():
            symbol = atom.GetSymbol()
            if symbol != 'H':
                h_count = sum(1 for n in atom.GetNeighbors() if n.GetSymbol() == 'H')
                if h_count > 0:
                    lbl = f"{symbol}H{h_count}" if h_count > 1 else f"{symbol}H"
                    atom.SetProp('atomLabel', lbl)
                elif symbol == 'C': 
                    atom.SetProp('atomLabel', symbol)
        mol = Chem.RemoveHs(mol)
        d = rdMolDraw2D.MolDraw2DCairo(600, 300)
        d.drawOptions().minFontSize = 20
        d.drawOptions().bondLineWidth = 2
        d.DrawMolecule(mol)
        d.FinishDrawing()
        return d.GetDrawingText()
    except: return None

def get_2d_url(smiles):
    return f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{urllib.parse.quote(smiles)}/PNG?record_type=2d&image_size=600x600"

def make_pretty_formula(text):
    if not text: return ""
    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return text.translate(SUB)

def get_cas_number(synonyms):
    if not synonyms: return None
    pattern = re.compile(r'^\d{2,7}-\d{2}-\d$')
    for syn in synonyms:
        if pattern.match(syn):
            return syn
    return None

def get_nist_image_url(cas_number, spec_type="IR"):
    if not cas_number: return None
    clean_cas = cas_number.replace("-", "")
    if spec_type == "IR":
        return f"https://webbook.nist.gov/cgi/cbook.cgi?Spec=C{clean_cas}&Index=0&Type=IR&Large=on"
    elif spec_type == "MS":
        return f"https://webbook.nist.gov/cgi/cbook.cgi?Spec=C{clean_cas}&Index=0&Type=Mass&Large=on"
    return None

def check_url_exists(url):
    try:
        r = requests.head(url, timeout=2)
        return r.status_code == 200
    except:
        return False

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding-bottom: 20px;">
            <h1 style="font-size: 3rem; margin:0;">⚗️</h1>
            <h2 style="color: #2563EB !important; font-weight: 800;">Hóa Học 4.0</h2>
            <p style="color: #64748B !important;">Trợ lý Giáo viên & Học sinh</p>
        </div>
    """, unsafe_allow_html=True)
    
    app_mode = st.radio("🎯 **CHỨC NĂNG CHÍNH:**", 
        ["🏠 Trang chủ", "🔍 Tra cứu & Cấu trúc", "⚖️ Cân bằng PT", "🧮 Tiện ích mở rộng"],
        key="current_page" 
    )
    st.markdown("---")
    st.info("💡 **Mẹo:** Nhập tên tiếng Anh (vd: Iron, Acid) để tìm nhanh hơn.")

# ==========================================
# 4. NỘI DUNG CHÍNH
# ==========================================

# --- TRANG CHỦ ---
if app_mode == "🏠 Trang chủ":
    st.markdown("# 👋 Chào mừng trở lại!")
    st.markdown("Hệ thống học liệu số hóa dành cho môn Hóa học.")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="css-card">
            <h1 style="font-size: 40px;">🔍</h1>
            <h3 style="margin: 0;">Tra Cứu Chất</h3>
            <p style="font-size: 14px; margin-top: 10px;">100 triệu chất hóa học, cấu trúc 3D & Phổ IR/MS.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Truy cập ngay", key="btn_tracuu", use_container_width=True):
            navigate_to("🔍 Tra cứu & Cấu trúc")
    with col2:
        st.markdown("""
        <div class="css-card">
            <h1 style="font-size: 40px;">⚖️</h1>
            <h3 style="margin: 0;">Cân Bằng PT</h3>
            <p style="font-size: 14px; margin-top: 10px;">Cân bằng phản ứng Oxi hóa - Khử siêu tốc.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Cân bằng ngay", key="btn_canbang", use_container_width=True):
            navigate_to("⚖️ Cân bằng PT")
    with col3:
        st.markdown("""
        <div class="css-card">
            <h1 style="font-size: 40px;">🧮</h1>
            <h3 style="margin: 0;">Tiện Ích</h3>
            <p style="font-size: 14px; margin-top: 10px;">Tính M, Bảng tuần hoàn, Cấu hình e.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Sử dụng ngay", key="btn_tienich", use_container_width=True):
            navigate_to("🧮 Tiện ích mở rộng")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.success("Mẹo: Bạn có thể dùng menu bên trái hoặc các nút bấm ở trên để di chuyển.")

# --- TRA CỨU (ĐÃ FIX GIAO DIỆN) ---
elif app_mode == "🔍 Tra cứu & Cấu trúc":
    st.markdown("## 🧪 **Thư Viện Hóa Chất Số**")
    with st.container():
        st.markdown('<div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #E2E8F0;">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        
        # Selectbox giờ sẽ hiển thị đúng màu trắng
        search_type = c1.selectbox("Phương thức tìm:", ["Tên (Name)", "Công thức (Formula)"])
        user_input = c2.text_input("Nhập dữ liệu:", placeholder="Ví dụ: Aspirin, C6H6, Ethanol...")
        
        if st.button("🚀 Tìm kiếm ngay", type="primary", use_container_width=True):
            st.markdown('</div>', unsafe_allow_html=True) 
            with st.spinner("Đang kết nối cơ sở dữ liệu quốc tế..."):
                try:
                    comps = []
                    if search_type == "Tên (Name)":
                        comps = pcp.get_compounds(user_input, 'name')
                    else:
                        full = pcp.get_compounds(user_input, 'formula')
                        comps = full[:5]

                    if not comps: st.error("❌ Không tìm thấy chất này.")
                    else:
                        st.success(f"✅ Tìm thấy {len(comps)} kết quả.")
                        for i, c in enumerate(comps):
                            st.markdown("---")
                            pretty = make_pretty_formula(c.molecular_formula)
                            st.subheader(f"{i+1}. {c.synonyms[0] if c.synonyms else user_input} ({pretty})")
                            
                            with st.container():
                                t1, t2, t3, t4 = st.tabs(["📘 Cấu tạo & Tên", "📊 Lý tính", "🧊 Mô hình 3D", "📈 Phổ IR & MS"])
                                with t1:
                                    c1_img, c2_info = st.columns([1, 2])
                                    with c1_img:
                                        img = draw_textbook_style(c.isomeric_smiles)
                                        if img: st.image(img, caption="Công thức cấu tạo")
                                        else: st.image(get_2d_url(c.isomeric_smiles))
                                    with c2_info:
                                        st.markdown(f"**Tên IUPAC:** `{c.iupac_name}`")
                                        st.markdown(f"**InChIKey:** `{c.inchikey}`")
                                        cas_no = get_cas_number(c.synonyms)
                                        st.markdown(f"**Mã CAS:** `{cas_no if cas_no else 'N/A'}`")
                                with t2:
                                    col_a, col_b = st.columns(2)
                                    col_a.metric("Phân tử khối (M)", f"{c.molecular_weight} g/mol")
                                    col_a.metric("Điện tích", c.charge)
                                    col_b.markdown(f"**Công thức:** {make_pretty_formula(c.molecular_formula)}")
                                    if c.xlogp: col_b.metric("Độ tan (LogP)", c.xlogp)
                                with t3:
                                    try:
                                        url3d = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/CID/{c.cid}/record/SDF/?record_type=3d"
                                        r = requests.get(url3d)
                                        if r.status_code==200:
                                            v = py3Dmol.view(width=500,height=300)
                                            v.addModel(r.text,"sdf")
                                            v.setStyle({'stick':{}})
                                            v.setBackgroundColor('white')
                                            v.zoomTo()
                                            showmol(v,height=300,width=500)
                                    except: st.warning("Chưa có dữ liệu 3D.")
                                with t4:
                                    st.info("💡 Dữ liệu phổ từ NIST Chemistry WebBook.")
                                    col_ir, col_ms = st.columns(2)
                                    cas_no = get_cas_number(c.synonyms)
                                    with col_ir:
                                        st.markdown("#### 🌡️ Phổ Hồng Ngoại (IR)")
                                        found_ir = False
                                        if cas_no:
                                            ir_url = get_nist_image_url(cas_no, "IR")
                                            if check_url_exists(ir_url):
                                                st.image(ir_url, use_container_width=True)
                                                found_ir = True
                                        if not found_ir: st.warning("Hệ thống chưa có dữ liệu")
                                    with col_ms:
                                        st.markdown("#### ⚡ Phổ Khối Lượng (MS)")
                                        found_ms = False
                                        if cas_no:
                                            ms_url = get_nist_image_url(cas_no, "MS")
                                            if check_url_exists(ms_url):
                                                st.image(ms_url, use_container_width=True)
                                                found_ms = True
                                        if not found_ms: st.warning("Hệ thống chưa có dữ liệu")
                except Exception as e: st.error(f"Lỗi kết nối: {e}")
        else: st.markdown('</div>', unsafe_allow_html=True)

# --- CÂN BẰNG PT ---
elif app_mode == "⚖️ Cân bằng PT":
    st.markdown("## ⚖️ **Cân Bằng Phương Trình**")
    st.markdown('<div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #E2E8F0;">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    reactants = c1.text_input("Chất tham gia:", "KMnO4 + HCl")
    products = c2.text_input("Sản phẩm:", "KCl + MnCl2 + Cl2 + H2O")
    
    if st.button("✨ Cân bằng ngay", type="primary", use_container_width=True):
        try:
            reac_set = {x.strip() for x in reactants.split('+')}
            prod_set = {x.strip() for x in products.split('+')}
            reac_dict, prod_dict = balance_stoichiometry(reac_set, prod_set)
            def fmt(d):
                parts = []
                for k, v in d.items():
                    coeff = str(v) if v > 1 else ""
                    parts.append(f"{coeff}{make_pretty_formula(k)}")
                return " + ".join(parts)
            st.markdown("### Kết quả:")
            st.latex(f"{fmt(reac_dict)} \\rightarrow {fmt(prod_dict)}")
            st.balloons()
        except Exception as e: st.error(f"Không thể cân bằng: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TIỆN ÍCH ---
elif app_mode == "🧮 Tiện ích mở rộng":
    st.markdown("## 🧮 **Công Cụ Tính Toán**")
    st.markdown('<div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #E2E8F0;">', unsafe_allow_html=True)
    tab_M, tab_BTH = st.tabs(["⚖️ Tính Phân Tử Khối", "⚛️ Tra Cứu Nguyên Tố"])
    with tab_M:
        st.write("Nhập công thức hóa học (kể cả tinh thể ngậm nước).")
        formula_input = st.text_input("Nhập công thức:", value="CuSO4.5H2O")
        if formula_input:
            try:
                clean = formula_input.replace(".", "*")
                sub = Substance.from_formula(clean)
                c1, c2 = st.columns(2)
                c1.metric("Phân tử khối (M)", f"{sub.mass:.2f} g/mol")
                st.caption("Thành phần % khối lượng:")
                comp = sub.composition
                for atomic_number, fraction in comp.items():
                    elem_sym = periodic.symbols[atomic_number]
                    pct = fraction * 100
                    st.progress(pct / 100, text=f"{elem_sym}: {pct:.2f}%")
            except: st.error("Công thức không hợp lệ.")
    with tab_BTH:
        elem = st.text_input("Ký hiệu nguyên tố:", value="Fe")
        if elem:
            try:
                el = mendeleev.element(elem)
                c1, c2, c3 = st.columns(3)
                c1.metric("Số hiệu (Z)", el.atomic_number)
                c2.metric("Nguyên tử khối", f"{el.atomic_weight:.2f}")
                c3.metric("Độ âm điện", el.en_pauling)
                st.markdown(f"**Cấu hình:** `{el.econf}`")
            except: st.warning("Không tìm thấy.")
    st.markdown('</div>', unsafe_allow_html=True)