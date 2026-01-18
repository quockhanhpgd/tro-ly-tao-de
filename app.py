import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN CHUẨN ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="📝"
)

# CSS TÙY CHỈNH (GIAO DIỆN TIMES NEW ROMAN)
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Times New Roman', Times, serif !important;
    }
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
    .main-header {
        font-size: 32px; font-weight: 900; color: #cc0000; 
        text-align: center; text-transform: uppercase;
        margin-bottom: 20px; text-shadow: 1px 1px 1px #ddd;
    }
    .marquee-container {
        width: 100%; overflow: hidden; background-color: #fff5f5;
        border: 1px solid #cc0000; padding: 10px 0; margin-bottom: 20px; border-radius: 5px;
    }
    .marquee-text {
        font-size: 18px; font-weight: bold; color: #cc0000;
        white-space: nowrap; animation: marquee 25s linear infinite;
    }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .section-header {
        font-size: 20px; font-weight: bold; color: #006633;
        border-bottom: 2px solid #006633; margin-top: 20px; margin-bottom: 10px; padding-bottom: 5px;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #006633; color: white; text-align: center;
        padding: 10px; font-size: 14px; z-index: 9999;
    }
    .stButton>button {
        background-color: #006633; color: white; font-size: 18px;
        border-radius: 5px; height: 50px; border: none;
    }
    .stButton>button:hover { background-color: #cc0000; }
    
    /* Khung xem trước tài liệu */
    .preview-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ccc;
        height: 300px;
        overflow-y: scroll;
        font-family: 'Times New Roman';
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API ---
# Thay mã API thật của thầy vào dòng dưới (giữ nguyên dấu ngoặc kép)
API_KEY_DU_PHONG = "AIzaSyCz3EXlGx1SC99IPpJmQjr2L75KDo4TN5Y"

try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = API_KEY_DU_PHONG
except:
    api_key = API_KEY_DU_PHONG

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
    except Exception as e: return f"Lỗi đọc file: {e}"
    return text

def get_selected_context(folder_path, selected_files):
    all_text = ""
    for file_name in selected_files:
        full_path = os.path.join(folder_path, file_name)
        if os.path.exists(full_path):
            all_text += f"\n--- TÀI LIỆU CĂN CỨ: {file_name} ---\n{read_doc_text(full_path)}\n"
    return all_text

# --- 4. HÀM AI ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return models[0] if models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_test_v6(mon, lop, loai, context):
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Vai trò: Giáo viên bộ môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}" CHÍNH XÁC.
    
    TÀI LIỆU CĂN CỨ (CHỈ DÙNG THÔNG TIN TRONG NÀY):
    {context}
    
    YÊU CẦU:
    1. Kiểm tra kỹ xem trong tài liệu trên có "Ma trận" hoặc "Đề minh họa" không.
    2. Nếu có, PHẢI TUÂN THỦ 100% cấu trúc, số lượng câu hỏi và thang điểm.
    3. Nếu không có ma trận, hãy tự cân đối: 40% Trắc nghiệm, 60% Tự luận.
    4. Trình bày đẹp, chuẩn Tiếng Việt.
    
    KẾT QUẢ (Markdown):
    - Phần 1: MA TRẬN ĐỀ (Mô tả cấu trúc đã dùng)
    - Phần 2: ĐỀ BÀI
    - Phần 3: ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM
    """
    return model.generate_content(prompt).text

# --- 5. GIAO DIỆN CHÍNH ---

st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)
st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH NĂM MỚI THÀNH CÔNG 🌸</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="section-header">1. THIẾT LẬP KHO DỮ LIỆU</div>', unsafe_allow_html=True)
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Khoa Học", "Lịch Sử"])
    
    curr_dir = get_folder_path(cap, lop, mon)
    
    st.info(f"📂 Đang mở kho: {cap} > {lop} > {mon}")
    
    st.markdown("---")
    st.markdown("<b>📤 Tải tài liệu vào kho này:</b>", unsafe_allow_html=True)
    uploads = st.file_uploader("Kéo thả Ma trận/Đề cũ vào đây", accept_multiple_files=True)
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.success("Đã lưu file!")

with col2:
    st.markdown('<div class="section-header">2. CHỌN LỌC & KIỂM TRA TÀI LIỆU</div>', unsafe_allow_html=True)
    
    files_in_dir = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    if not files_in_dir:
        st.warning("⚠️ Kho này chưa có tài liệu. Thầy hãy tải lên ở cột bên trái.")
        selected_files = []
    else:
        # A. KHUNG CHỌN TÀI LIỆU (MULTISELECT)
        st.write("🔽 **Bước 2.1: Tích chọn những file thầy muốn dùng để ra đề:**")
        selected_files = st.multiselect(
            "Danh sách file trong kho:",
            options=files_in_dir,
            default=files_in_dir, # Mặc định chọn hết
            format_func=lambda x: f"📄 {x}"
        )
        
        # B. KHUNG XEM TRƯỚC (PREVIEW) - TÍNH NĂNG MỚI
        st.write("👁️ **Bước 2.2: Soi nội dung file (Kiểm tra lại xem đúng chưa):**")
        file_to_preview = st.selectbox("Chọn 1 file để xem nội dung:", ["-- Chưa chọn --"] + files_in_dir)
        
        if file_to_preview != "-- Chưa chọn --":
            full_path = os.path.join(curr_dir, file_to_preview)
            content = read_doc_text(full_path)
            st.markdown(f"<div class='preview-box'>{content[:1500]}... (Còn tiếp)</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-header">3. CẤU HÌNH & TẠO ĐỀ</div>', unsafe_allow_html=True)
    loai = st.selectbox("Loại đề thi", ["15 Phút", "Giữa Học Kỳ 1", "Cuối Học Kỳ 1", "Giữa Học Kỳ 2", "Cuối Học Kỳ 2"])
    
    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not selected_files:
            st.error("🛑 Thầy chưa tích chọn tài liệu nào cả!")
        else:
            # Chỉ gửi những file được tích chọn cho AI
            context = get_selected_context(curr_dir, selected_files)
            
            with st.spinner("AI đang đọc các tài liệu đã chọn và soạn đề..."):
                try:
                    res = generate_test_v6(mon, lop, loai, context)
                    st.session_state['kq_v6'] = res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if 'kq_v6' in st.session_state:
        st.markdown("---")
        st.success("✅ Kết quả:")
        st.container(border=True).markdown(st.session_state['kq_v6'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini.<br>
    Trường Tiểu học Hua Nguống - Điện Biên.
</div>
""", unsafe_allow_html=True)


