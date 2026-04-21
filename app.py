import streamlit as st
from google import genai
from docx import Document
import PyPDF2
import os
import time

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN CHUẨN ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="📝"
)

# CSS TÙY CHỈNH (CHUẨN HÓA FONT TIMES NEW ROMAN - GIỮ NGUYÊN GIAO DIỆN CŨ)
st.markdown("""
<style>
    /* Ép toàn bộ web dùng font Times New Roman */
    html, body, [class*="css"] {
        font-family: 'Times New Roman', Times, serif !important;
    }
    
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
    
    .main-header {
        font-size: 32px; font-weight: 900; color: #cc0000; 
        text-align: center; text-transform: uppercase;
        margin-bottom: 20px; text-shadow: 1px 1px 1px #ddd;
    }
    
    .section-header {
        font-size: 20px; font-weight: bold; color: #006633;
        border-bottom: 2px solid #006633; margin-top: 20px; margin-bottom: 10px;
        padding-bottom: 5px;
    }
    
    .guide-box {
        background-color: #f4fcf6; border: 1px solid #006633;
        border-radius: 5px; padding: 20px; font-size: 16px; line-height: 1.6;
    }

    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #006633; color: white; text-align: center;
        padding: 10px; font-size: 14px; z-index: 9999;
    }

    .stButton>button {
        background-color: #006633; color: white; font-size: 18px;
        border-radius: 5px; height: 50px; border: none;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #cc0000; }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API (THƯ VIỆN MỚI) ---
api_key = st.secrets.get("GOOGLE_API_KEY", "")
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key.strip())
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
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                for page in PyPDF2.PdfReader(f).pages: text += page.extract_text() or ""
    except: pass
    return text

def get_selected_context(folder_path, selected_files):
    all_text = ""
    files_to_read = selected_files if selected_files else [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]

    for file_name in files_to_read:
        full_path = os.path.join(folder_path, file_name)
        if os.path.exists(full_path):
            content = read_doc_text(full_path)
            all_text += f"\n--- TÀI LIỆU CĂN CỨ: {file_name} ---\n{content[:30000]}\n"
    return all_text

# --- 4. HÀM AI (CƠ CHẾ TỰ ĐỘNG LẤY DANH SÁCH BẢN QUYỀN TỪ GOOGLE) ---
def generate_test_final(mon, lop, loai, context):
    if not client: 
        return "Lỗi: Không kết nối được API. Thầy vui lòng kiểm tra lại mã Key trong phần Secrets."
        
    prompt = f"""
    Vai trò: Giáo viên dạy giỏi môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}" CHUẨN MỰC.

    DỮ LIỆU ĐƯỢC CUNG CẤP:
    {context[:30000]}

    YÊU CẦU:
    1. Tuân thủ 100% cấu trúc Ma trận/Đề minh họa (nếu có trong dữ liệu).
    2. Nếu không có mẫu: Làm 40% Trắc nghiệm, 60% Tự luận.
    3. Trình bày rõ ràng, không dùng bảng biểu phức tạp.

    KẾT QUẢ TRẢ VỀ CHỈ HIỂN THỊ VĂN BẢN:
    - Phần I: MA TRẬN ĐỀ
    - Phần II: ĐỀ BÀI
    - Phần III: HƯỚNG DẪN CHẤM
    """
    
    try:
        # BƯỚC 1: Gọi lệnh ListModels để xin danh sách các model hợp lệ
        available_models = []
        for m in client.models.list():
            if 'gemini' in m.name.lower():
                available_models.append(m.name)
        
        if not available_models:
            return "Lỗi: Mã Key của Thầy hiện không được Google cấp quyền sử dụng AI Gemini. Thầy vui lòng tạo một mã Key mới nhé!"
            
        # BƯỚC 2: Ưu tiên chọn các bản Flash vì nó ra đề cực nhanh
        model_to_use = available_models[0] # Chọn đại bản đầu tiên làm dự phòng
        for m in available_models:
            if 'flash' in m.name.lower():
                model_to_use = m
                break
                
        # BƯỚC 3: Ra đề bằng đúng model đã được cấp phép
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model_to_use, contents=prompt)
                if response.text: 
                    return response.text
            except Exception as e:
                if attempt == 2:
                    return f"Lỗi khi chạy bộ não {model_to_use}. Chi tiết: {str(e)}"
                time.sleep(2) # Nghỉ 2 giây rồi thử lại
                
    except Exception as main_e:
        return f"Lỗi kiểm tra bản quyền hệ thống: {str(main_e)}"
        
    return "Hệ thống đang bận. Thầy vui lòng F5 và tạo lại nhé!"

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="section-header">1. THIẾT LẬP & TẢI TÀI LIỆU</div>', unsafe_allow_html=True)
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ", "Khoa Học"])

    curr_dir = get_folder_path(cap, lop, mon)

    st.markdown("---")
    st.info("📤 Tải tài liệu vào kho")
    uploads = st.file_uploader("Chọn file...", accept_multiple_files=True, label_visibility="collapsed")
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.success("Đã lưu file!")

with col2:
    try:
        files_in_dir = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
    except:
        files_in_dir = []

    st.markdown(f'<div class="section-header">2. LỰA CHỌN TÀI LIỆU TỪ KHO ({mon} - {lop})</div>', unsafe_allow_html=True)

    if not files_in_dir:
        st.warning("⚠️ Kho trống. Hãy tải tài liệu lên ở cột bên trái.")
        selected_files = []
    else:
        st.write("Chọn tài liệu để ra đề:")
        selected_files = st.multiselect("Danh sách:", options=files_in_dir, default=files_in_dir, format_func=lambda x: f"📄 {x}")

    st.markdown('<div class="section-header">3. CẤU HÌNH & TẠO ĐỀ</div>', unsafe_allow_html=True)
    loai = st.selectbox("Loại đề thi", ["15 Phút", "Giữa Học Kỳ 1", "Cuối Học Kỳ 1", "Giữa Học Kỳ 2", "Cuối Học Kỳ 2"], label_visibility="collapsed")

    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not selected_files:
            st.error("Vui lòng chọn tài liệu trước!")
        else:
            context = get_selected_context(curr_dir, selected_files)
            with st.spinner("Đang kiểm tra bản quyền AI và tự động soạn đề (Vui lòng đợi khoảng 15 giây)..."):
                res = generate_test_final(mon, lop, loai, context)
                st.session_state['kq_final'] = res

    # KẾT QUẢ ĐẦU RA (HIỂN THỊ TRỰC TIẾP TRÊN WEB)
    if 'kq_final' in st.session_state:
        st.markdown("---")
        st.success("✅ Đề thi đã tạo xong:")
        with st.container(border=True):
            st.markdown(st.session_state['kq_final'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - Trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
