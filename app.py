import streamlit as st
import google.generativeai as genai
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
    
    /* Khoảng trống phía trên */
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
    
    /* Tiêu đề chính */
    .main-header {
        font-size: 32px; font-weight: 900; color: #cc0000; 
        text-align: center; text-transform: uppercase;
        margin-bottom: 20px; text-shadow: 1px 1px 1px #ddd;
    }
    
    /* Chữ chạy Marquee */
    .marquee-container {
        width: 100%; overflow: hidden; background-color: #fff5f5;
        border: 1px solid #cc0000;
        padding: 10px 0; margin-bottom: 20px; border-radius: 5px;
    }
    .marquee-text {
        font-size: 18px; font-weight: bold; color: #cc0000;
        white-space: nowrap; animation: marquee 25s linear infinite;
    }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    
    /* Tiêu đề mục */
    .section-header {
        font-size: 20px; font-weight: bold; color: #006633;
        border-bottom: 2px solid #006633; margin-top: 20px; margin-bottom: 10px;
        padding-bottom: 5px;
    }
    
    /* Hướng dẫn sử dụng */
    .guide-box {
        background-color: #f4fcf6; border: 1px solid #006633;
        border-radius: 5px; padding: 20px; font-size: 16px; line-height: 1.6;
    }

    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #006633; color: white; text-align: center;
        padding: 10px; font-size: 14px; z-index: 9999;
    }

    /* Nút bấm */
    .stButton>button {
        background-color: #006633; color: white; font-size: 18px;
        border-radius: 5px; height: 50px; border: none;
    }
    .stButton>button:hover { background-color: #cc0000; }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API (ĐÃ TỐI ƯU ĐỂ TRÁNH LỖI KẾT NỐI) ---
try:
    api_key = None
    # Ưu tiên lấy từ Secrets (Online)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    
    # Nếu không có Secrets, dùng mã dự phòng (Thầy điền vào đây nếu cần chạy offline)
    if not api_key:
        api_key = "AIzaSy_MÃ_CỦA_THẦY_VÀO_ĐÂY"

    # Quan trọng: Làm sạch mã Key (xóa khoảng trắng thừa - nguyên nhân gây lỗi 503)
    if api_key:
        api_key = api_key.strip()
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

def get_selected_context(folder_path, selected_files):
    all_text = ""
    if selected_files:
        files_to_read = selected_files 
    else:
        files_to_read = [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]

    for file_name in files_to_read:
        full_path = os.path.join(folder_path, file_name)
        if os.path.exists(full_path):
            content = read_doc_text(full_path)
            # Giới hạn nội dung mỗi file để tránh quá tải bộ nhớ đệm
            all_text += f"\n--- TÀI LIỆU CĂN CỨ: {file_name} ---\n{content[:20000]}\n"
    return all_text

# --- 4. HÀM AI (CHỐNG TREO & TỰ ĐỘNG THỬ LẠI) ---
def generate_test_final(mon, lop, loai, context):
    # Sử dụng Flash 1.5 - Model nhanh nhất hiện nay để tránh Timeout
    model_name = 'gemini-1.5-flash' 
    
    # Cấu hình thử lại 3 lần nếu mạng nghẽn
    max_retries = 3
    
    prompt = f"""
    Vai trò: Giáo viên dạy giỏi môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}" CHUẨN MỰC.

    DỮ LIỆU ĐƯỢC CUNG CẤP:
    {context[:30000]} 

    YÊU CẦU:
    1. Tuân thủ 100% cấu trúc Ma trận/Đề minh họa (nếu có trong dữ liệu).
    2. Nếu không có mẫu: Làm 40% Trắc nghiệm, 60% Tự luận.
    3. Trình bày rõ ràng, font chữ chuẩn.

    KẾT QUẢ TRẢ VỀ:
    - Phần I: MA TRẬN ĐỀ
    - Phần II: ĐỀ BÀI
    - Phần III: HƯỚNG DẪN CHẤM
    """

    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            time.sleep(2) # Nghỉ 2 giây rồi thử lại
            if attempt == max_retries - 1:
                return f"Hệ thống đang bận (Lỗi kết nối Google). Thầy vui lòng bấm nút tạo lại lần nữa nhé! (Lỗi: {str(e)})"

    return "Không thể kết nối."

# --- 5. GIAO DIỆN CHÍNH (GIỮ NGUYÊN) ---
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)
st.markdown("""
<div class="marquee-container">
<div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH NĂM MỚI THÀNH CÔNG RỰC RỠ 🌸</div>
</div>
""", unsafe_allow_html=True)

with st.expander("📖 BẤM VÀO ĐÂY ĐỂ XEM HƯỚNG DẪN SỬ DỤNG CHI TIẾT", expanded=False):
    st.markdown("""
    <div class="guide-box">
    <b>BƯỚC 1: THIẾT LẬP THÔNG TIN (Cột trái)</b><br>
    Chọn Cấp học, Lớp, Môn học để mở kho dữ liệu tương ứng.<br><br>
    <b>BƯỚC 2: TẢI TÀI LIỆU (Cột trái)</b><br>
    Tải Ma trận, Đề minh họa hoặc Nội dung ôn tập lên kho.<br><br>
    <b>BƯỚC 3: CHỌN TÀI LIỆU & TẠO ĐỀ (Cột phải)</b><br>
    Tích chọn các file muốn sử dụng, chọn loại đề và bấm nút Tạo đề.
    </div>
    """, unsafe_allow_html=True)

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
            # Thêm dòng cảnh báo nếu không đọc được nội dung
            if not context.strip():
                 st.warning("⚠️ Cảnh báo: Không đọc được nội dung từ file (file trống hoặc lỗi). AI sẽ tự biên soạn dựa trên kiến thức chung.")
            
            with st.spinner("Đang kết nối AI và soạn đề (Vui lòng đợi khoảng 10-20 giây)..."):
                res = generate_test_final(mon, lop, loai, context)
                st.session_state['kq_v5'] = res

    if 'kq_v5' in st.session_state:
        st.markdown("---")
        st.success("✅ Đề thi đã tạo xong:")
        with st.container(border=True):
            st.markdown(st.session_state['kq_v5'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - Trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
