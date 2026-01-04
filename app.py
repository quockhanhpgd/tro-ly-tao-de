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

# CSS TÙY CHỈNH (KHẮC PHỤC LỖI DÍNH CHỮ)
st.markdown("""
<style>
    /* 1. TẠO KHOẢNG TRỐNG PHÍA TRÊN */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }

    /* 2. TIÊU ĐỀ CHÍNH (Sửa lỗi hiển thị) */
    .main-header {
        font-family: 'Arial', sans-serif;
        font-size: 30px; 
        font-weight: 900; 
        color: #D42426; /* Đỏ tết */
        text-align: center; 
        text-transform: uppercase;
        text-shadow: 1px 1px 0px #FFD700;
        margin-bottom: 20px;
        line-height: 1.5; /* Giãn dòng để không bị mất chóp chữ */
        padding: 10px;
    }
    
    /* 3. TIÊU ĐỀ MỤC CON (1, 2, 3...) - Sửa lỗi dính chữ */
    .section-header {
        font-size: 20px;
        font-weight: bold;
        color: #146B3A; /* Xanh lá đậm */
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 2px solid #eee;
        padding-bottom: 5px;
    }
    .section-number {
        background-color: #D42426;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        margin-right: 10px;
        font-size: 18px;
    }
    
    /* 4. CHỮ CHẠY MARQUEE */
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
        animation: marquee 20s linear infinite;
    }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* 5. FOOTER */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0d5e38; color: white; text-align: center;
        padding: 10px; font-size: 13px; font-weight: bold;
        z-index: 9999; border-top: 3px solid #FFD700;
    }
    
    /* 6. NÚT BẤM */
    .stButton>button {
        background-color: #0d5e38; color: white; border-radius: 8px; font-weight: bold; height: 3em;
        border: 1px solid #FFD700;
    }
    .stButton>button:hover {
        background-color: #D42426; color: #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "KEY_DU_PHONG_CUA_THAY"

try:
    genai.configure(api_key=api_key)
except: pass

# --- 3. HÀM XỬ LÝ FILE ---
BASE_DIR = "KHO_DU_LIEU_GD"

def get_folder_path(cap, lop, mon):
    path = os.path.join(BASE_DIR, cap, lop, mon)
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
        all_text += f"\n--- TÊN TÀI LIỆU: {file_name} ---\n{read_doc_text(full_path)}\n"
    return all_text, files

# --- 4. HÀM AI THÔNG MINH ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for p in preferred:
            if p in models: return p
        return models[0] if models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_test_strict(mon, lop, loai, context):
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Vai trò: Chuyên gia biên soạn đề thi môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn thảo đề kiểm tra "{loai}" CHẤT LƯỢNG CAO.
    
    DỮ LIỆU ĐẦU VÀO (QUAN TRỌNG):
    {context}
    
    YÊU CẦU TUÂN THỦ:
    1. Nếu có file Ma trận/Đặc tả: PHẢI tuân thủ 100% số lượng câu, mức độ kiến thức và điểm số trong đó.
    2. Nếu có Đề mẫu: Hãy bắt chước cách trình bày, font chữ, phong cách đặt câu hỏi.
    3. Nếu không có mẫu: Soạn theo chuẩn Thông tư 27 (40% Trắc nghiệm, 60% Tự luận/Thực hành).
    
    ĐẦU RA:
    - I. MA TRẬN ĐỀ (Mô tả lại cấu trúc bạn đã dùng)
    - II. ĐỀ BÀI CHI TIẾT
    - III. HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN
    """
    return model.generate_content(prompt).text

# --- 5. GIAO DIỆN CHÍNH ---

# 5.1 Tiêu đề chính (Dùng thẻ H1 chuẩn để không bị lỗi font)
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)

# 5.2 Chữ chạy
st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH MỘT NĂM MỚI AN KHANG THỊNH VƯỢNG 🌸</div>
</div>
""", unsafe_allow_html=True)

# 5.3 Hướng dẫn
with st.expander("📖 HƯỚNG DẪN SỬ DỤNG (Bấm vào đây)", expanded=False):
    st.info("Bước 1: Chọn Môn/Lớp (Bên trái) -> Bước 2: Tải tài liệu Ma trận/Đề mẫu -> Bước 3: Bấm nút Tạo đề (Bên phải).")

col1, col2 = st.columns([1, 2])

with col1:
    # Dùng HTML thuần để hiển thị tiêu đề mục 1 rõ ràng
    st.markdown('<div class="section-header"><span class="section-number">1</span>Thiết lập & Dữ liệu</div>', unsafe_allow_html=True)
    
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ"])
    
    curr_dir = get_folder_path(cap, lop, mon)
    
    st.markdown("---")
    # Tiêu đề mục 2
    st.markdown('<div class="section-header"><span class="section-number">2</span>Tải tài liệu lên kho</div>', unsafe_allow_html=True)
    st.caption("Gợi ý: Tải file Ma trận và Đề mẫu (Word/PDF)")
    
    uploads = st.file_uploader("Chọn file...", accept_multiple_files=True, label_visibility="collapsed")
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.toast("Đã lưu tài liệu!", icon="✅")

with col2:
    context, files = get_all_context(curr_dir)
    
    # Tiêu đề bên phải
    st.markdown(f'<div class="section-header">📂 Kho dữ liệu: {mon} - {lop} ({len(files)} file)</div>', unsafe_allow_html=True)
    
    with st.container(height=150, border=True):
        if files:
            for f in files: 
                icon = "📏" if "ma tran" in f.lower() else "📝" if "de" in f.lower() else "📄"
                st.text(f"{icon} {f}")
        else: st.warning("Kho trống. Vui lòng tải tài liệu ở cột bên trái.")

    # Tiêu đề mục 3
    st.markdown('<div class="section-header"><span class="section-number">3</span>Cấu hình & Tạo đề</div>', unsafe_allow_html=True)
    
    loai = st.selectbox("Loại đề thi", ["15 Phút", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2"], label_visibility="collapsed")
    
    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not context:
            st.error("Chưa có dữ liệu! Hãy tải Ma trận hoặc Giáo án lên trước.")
        else:
            with st.spinner("AI đang đọc Ma trận và biên soạn đề..."):
                try:
                    res = generate_test_strict(mon, lop, loai, context)
                    st.session_state['kq_fix'] = res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if 'kq_fix' in st.session_state:
        st.markdown("---")
        st.container(border=True).markdown(st.session_state['kq_fix'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
