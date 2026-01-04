import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN TẾT 2026 ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="🎆"
)

# CSS TÙY CHỈNH (Màu sắc & Hiệu ứng chữ chạy)
st.markdown("""
<style>
    /* 1. Tiêu đề chính */
    .main-header {
        font-size: 35px; 
        font-weight: bold; 
        color: #D42426; /* Đỏ may mắn */
        text-align: center; 
        text-transform: uppercase;
        text-shadow: 2px 2px #FFD700; /* Bóng vàng */
        margin-bottom: 5px;
    }
    
    /* 2. Hiệu ứng chữ chạy (Marquee) */
    .marquee-container {
        width: 100%;
        overflow: hidden;
        background-color: #FFF0F0; /* Nền hồng nhạt */
        border: 2px solid #D42426;
        border-radius: 10px;
        padding: 10px 0;
        margin-bottom: 30px;
    }
    .marquee-text {
        font-size: 20px;
        font-weight: bold;
        color: #D42426;
        white-space: nowrap;
        animation: marquee 15s linear infinite;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* 3. Nút bấm đẹp mắt */
    .stButton>button {
        background-color: #146B3A; /* Xanh lá */
        color: white; 
        font-size: 18px; 
        font-weight: bold; 
        border-radius: 8px;
        border: none;
        width: 100%;
        height: 50px;
    }
    .stButton>button:hover {
        background-color: #D42426; /* Hover chuyển đỏ */
        color: #FFD700;
    }

    /* 4. Footer cố định */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #146B3A;
        color: white;
        text-align: center;
        padding: 8px;
        font-size: 13px;
        font-weight: bold;
        z-index: 999;
        border-top: 3px solid #FFD700;
    }
    
    /* 5. Khung file */
    .file-box {
        border: 1px dashed #146B3A;
        padding: 10px;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. XỬ LÝ API KEY (BẢO MẬT) ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Key dự phòng (Thầy thay key nếu chạy máy nhà)
    api_key = "KEY_DU_PHONG_CUA_THAY"

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Lỗi cấu hình API: {e}")

# --- 3. CÁC HÀM XỬ LÝ ---
BASE_DIR = "KHO_DU_LIEU_GD"

def get_folder_path(cap_hoc, lop_hoc, mon_hoc):
    path = os.path.join(BASE_DIR, cap_hoc, lop_hoc, mon_hoc)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def save_uploaded_file(uploaded_file, target_folder):
    file_path = os.path.join(target_folder, uploaded_file.name)
    if os.path.exists(file_path):
        return False, f"⚠️ File '{uploaded_file.name}' đã có. Đã bỏ qua."
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return True, f"✅ Đã lưu: {uploaded_file.name}"

def read_doc_text(file_path):
    text = ""
    try:
        if file_path.endswith('.docx'):
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text()
    except: pass
    return text

def get_all_context(folder_path):
    all_text = ""
    files = [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]
    for file_name in files:
        full_path = os.path.join(folder_path, file_name)
        all_text += f"\n--- Tài liệu: {file_name} ---\n{read_doc_text(full_path)}"
    return all_text, files

# HÀM AI THÔNG MINH (SỬA LỖI 404)
def generate_test_smart(mon, lop, loai, context):
    prompt = f"""
    Vai trò: Giáo viên bộ môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra {loai}.
    Yêu cầu:
    1. Trắc nghiệm (4 câu) + Tự luận (2 câu).
    2. Có Ma trận + Đáp án chi tiết.
    3. Dựa vào tài liệu:
    {context}
    """
    
    # Thử dùng Model xịn nhất
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except:
        # Nếu lỗi 404, tự động chuyển sang Model ổn định hơn
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content(prompt).text
        except Exception as e:
            return f"Vẫn lỗi: {e}. Thầy vui lòng kiểm tra lại API Key nhé."

# --- 4. GIAO DIỆN CHÍNH ---

# 4.1. Tiêu đề chính
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)

# 4.2. Dòng chữ chạy (Marquee)
st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH MỘT NĂM MỚI AN KHANG THỊNH VƯỢNG 🌸</div>
</div>
""", unsafe_allow_html=True)

# 4.3. Hướng dẫn nhanh
with st.expander("📖 HƯỚNG DẪN SỬ DỤNG NHANH", expanded=False):
    st.info("1. Chọn Môn/Lớp -> 2. Tải tài liệu lên -> 3. Bấm 'Bắt đầu tạo đề'")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("### 1️⃣ Thiết lập & Dữ liệu")
    
    cap_hoc = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop_hoc = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon_hoc = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ", "Khoa học"])
    
    current_folder = get_folder_path(cap_hoc, lop_hoc, mon_hoc)
    
    st.markdown("---")
    st.caption("Tải tài liệu (Word/PDF)")
    uploaded_files = st.file_uploader("Chọn file...", accept_multiple_files=True, label_visibility="collapsed")
    
    if uploaded_files:
        for f in uploaded_files:
            status, msg = save_uploaded_file(f, current_folder)
            if status: st.toast(msg, icon="✅")

with col_right:
    # Hiển thị file trong kho
    context_text, list_files = get_all_context(current_folder)
    
    st.markdown(f"### 2️⃣ Kho dữ liệu: {mon_hoc} - {lop_hoc}")
    
    with st.container(height=150, border=True):
        if list_files:
            for f in list_files: st.text(f"📄 {f}")
        else:
            st.warning("⚠️ Kho đang trống. Thầy hãy tải tài liệu ở bên trái nhé!")

    st.markdown("### 3️⃣ Cấu hình & Tạo đề")
    
    loai_de = st.selectbox("Chọn loại bài kiểm tra", 
                           ["15 Phút", "Giữa Học Kì 1", "Cuối Học Kì 1", "Giữa Học Kì 2", "Cuối Học Kì 2"],
                           label_visibility="collapsed")
    
    st.write("") # Tạo khoảng cách
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not context_text:
            st.error("🛑 Chưa có tài liệu! Vui lòng tải giáo án lên trước.")
        else:
            with st.spinner(f"AI đang đọc {len(list_files)} tài liệu và soạn đề..."):
                result = generate_test_smart(mon_hoc, lop_hoc, loai_de, context_text)
                st.session_state['kq_tet'] = result

    # Hiển thị kết quả
    if 'kq_tet' in st.session_state:
        st.markdown("---")
        st.success("✅ Kết quả:")
        st.container(border=True).markdown(st.session_state['kq_tet'])

# --- 5. FOOTER (CHỮ KÝ) ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
