import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="🎆"
)

# CSS TÙY CHỈNH (GIAO DIỆN TẾT & CĂN CHỈNH KHOẢNG CÁCH)
st.markdown("""
<style>
    /* 1. TẠO KHOẢNG TRỐNG PHÍA TRÊN CÙNG (Fix lỗi dính sát mép) */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 5rem !important;
    }

    /* 2. Tiêu đề chính */
    .main-header {
        font-size: 32px; 
        font-weight: 900; 
        color: #D42426; /* Đỏ tết */
        text-align: center; 
        text-transform: uppercase;
        text-shadow: 1px 1px 0px #FFD700;
        margin-bottom: 20px;
        margin-top: 20px;
    }
    
    /* 3. Hiệu ứng chữ chạy (Marquee) - Tinh tế hơn */
    .marquee-container {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, #fff0f0, #ffecec);
        border-top: 2px solid #D42426;
        border-bottom: 2px solid #D42426;
        padding: 8px 0;
        margin-bottom: 30px;
    }
    .marquee-text {
        font-size: 18px;
        font-weight: bold;
        color: #ce0000;
        white-space: nowrap;
        animation: marquee 18s linear infinite;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* 4. Footer cố định */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0d5e38; /* Xanh lá đậm */
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 13px;
        font-weight: bold;
        z-index: 9999;
        border-top: 3px solid #FFD700;
    }
    
    /* 5. Nút bấm */
    .stButton>button {
        background-color: #0d5e38;
        color: white; 
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #D42426;
        color: #FFD700;
        border-color: #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API (BẢO MẬT) ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "KEY_DU_PHONG_CUA_THAY"

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Lỗi cấu hình API: {e}")

# --- 3. HÀM XỬ LÝ QUAN TRỌNG ---
BASE_DIR = "KHO_DU_LIEU_GD"

def get_folder_path(cap_hoc, lop_hoc, mon_hoc):
    path = os.path.join(BASE_DIR, cap_hoc, lop_hoc, mon_hoc)
    if not os.path.exists(path): os.makedirs(path)
    return path

def save_uploaded_file(uploaded_file, target_folder):
    file_path = os.path.join(target_folder, uploaded_file.name)
    if os.path.exists(file_path): return False
    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
    return True

def read_doc_text(file_path):
    text = ""
    try:
        if file_path.endswith('.docx'):
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages: text += page.extract_text()
    except: pass
    return text

def get_all_context(folder_path):
    all_text = ""
    files = [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]
    for file_name in files:
        full_path = os.path.join(folder_path, file_name)
        all_text += f"\n--- Tài liệu: {file_name} ---\n{read_doc_text(full_path)}"
    return all_text, files

# --- HÀM TÌM MODEL THÔNG MINH (KHẮC PHỤC LỖI 404) ---
def get_best_model():
    """Hàm này tự đi tìm xem có model nào dùng được không"""
    try:
        # Lấy danh sách tất cả model
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên tìm các model xịn
        preferred = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-1.0-pro', 'models/gemini-pro']
        
        for p in preferred:
            if p in models: return p
            
        # Nếu không thấy cái ưu tiên, lấy cái đầu tiên tìm được
        return models[0] if models else None
    except:
        return 'gemini-pro' # Đường cùng thì trả về cái cơ bản nhất

def generate_test_final(mon, lop, loai, context):
    model_name = get_best_model() # Tự động lấy tên model đúng
    if not model_name: return "Lỗi: Không tìm thấy Model AI nào khả dụng."
    
    model = genai.GenerativeModel(model_name)
    prompt = f"""
    Vai trò: Giáo viên {mon} lớp {lop}. Nhiệm vụ: Soạn đề {loai}.
    Yêu cầu: 
    - Có Ma trận, Trắc nghiệm (4 câu), Tự luận (2 câu), Đáp án.
    - Trình bày rõ ràng.
    Dữ liệu nguồn:
    {context}
    """
    return model.generate_content(prompt).text

# --- 4. GIAO DIỆN CHÍNH ---

# 4.1. Tiêu đề (Đã có khoảng cách phía trên)
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)

# 4.2. Chữ chạy (Marquee)
st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH MỘT NĂM MỚI AN KHANG THỊNH VƯỢNG 🌸</div>
</div>
""", unsafe_allow_html=True)

with st.expander("📖 HƯỚNG DẪN SỬ DỤNG NHANH"):
    st.info("Bước 1: Chọn Môn/Lớp > Bước 2: Tải tài liệu > Bước 3: Bấm nút Tạo đề.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 1️⃣ Thiết lập & Dữ liệu")
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ"])
    
    curr_dir = get_folder_path(cap, lop, mon)
    
    st.markdown("---")
    st.caption("Tải tài liệu (Word/PDF)")
    uploads = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.toast("Đã lưu tài liệu!", icon="✅")

with col2:
    context, files = get_all_context(curr_dir)
    st.markdown(f"### 2️⃣ Kho: {mon} - {lop} ({len(files)} file)")
    
    with st.container(height=150, border=True):
        if files:
            for f in files: st.text(f"📄 {f}")
        else: st.warning("Kho trống. Vui lòng tải file bên trái.")

    st.markdown("### 3️⃣ Tạo đề thi")
    loai = st.selectbox("Loại đề", ["15 Phút", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2"], label_visibility="collapsed")
    
    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not context:
            st.error("Chưa có tài liệu để soạn đề!")
        else:
            with st.spinner("AI đang soạn đề... (Thầy đợi khoảng 10s nhé)"):
                try:
                    res = generate_test_final(mon, lop, loai, context)
                    st.session_state['kq_final'] = res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if 'kq_final' in st.session_state:
        st.markdown("---")
        st.container(border=True).markdown(st.session_state['kq_final'])

# --- 5. FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
