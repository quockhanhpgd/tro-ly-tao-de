import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os
import shutil

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN LỄ HỘI ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="🎄"
)

# CSS TÙY CHỈNH (Màu sắc Giáng sinh & Năm mới)
st.markdown("""
<style>
    /* 1. Hiệu ứng tiêu đề rực rỡ */
    .main-header {
        font-size: 40px; 
        font-weight: bold; 
        color: #D42426; /* Màu đỏ giáng sinh */
        text-align: center; 
        text-shadow: 2px 2px #FFD700; /* Bóng vàng kim loại */
        margin-bottom: 10px;
        padding: 20px;
        border-bottom: 3px solid #146B3A; /* Viền xanh thông */
    }
    
    /* 2. Style cho các tiêu đề phụ */
    .sub-header {
        color: #146B3A; /* Xanh lá đậm */
        font-weight: bold;
        font-size: 20px;
        margin-top: 20px;
    }

    /* 3. Nút bấm đẹp mắt */
    .stButton>button {
        background-color: #D42426; /* Nút màu đỏ */
        color: white; 
        font-size: 18px; 
        font-weight: bold; 
        border-radius: 10px;
        border: 2px solid #FFD700;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #146B3A; /* Di chuột vào chuyển màu xanh */
        color: #FFD700;
    }

    /* 4. Footer cố định dưới đáy */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #146B3A;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        z-index: 999;
    }
    
    /* 5. Khung hướng dẫn */
    .instruction-box {
        background-color: #f0fdf4;
        border: 1px solid #146B3A;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. XỬ LÝ API KEY (BẢO MẬT) ---
# Tự động lấy key từ Secrets (Online) hoặc biến tạm (Offline)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Key dự phòng khi chạy trên máy cá nhân
    api_key = "DIEN_KEY_CUA_THAY_VAO_DAY_NEU_CHAY_OFFLINE"

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Lỗi cấu hình API: {e}")

# --- 3. CÁC HÀM XỬ LÝ (GIỮ NGUYÊN LOGIC CŨ) ---
BASE_DIR = "KHO_DU_LIEU_GD"

def get_folder_path(cap_hoc, lop_hoc, mon_hoc):
    path = os.path.join(BASE_DIR, cap_hoc, lop_hoc, mon_hoc)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def save_uploaded_file(uploaded_file, target_folder):
    file_path = os.path.join(target_folder, uploaded_file.name)
    if os.path.exists(file_path):
        return False, f"⚠️ File '{uploaded_file.name}' đã có trong kho dữ liệu. Đã bỏ qua."
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

def generate_test_final(mon, lop, loai, context):
    # Dùng model ổn định nhất
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Vai trò: Giáo viên bộ môn {mon} lớp {lop} tại Việt Nam.
    Nhiệm vụ: Soạn đề kiểm tra {loai}.
    Yêu cầu:
    1. Cấu trúc: Trắc nghiệm (4 câu) + Tự luận/Thực hành (2 câu).
    2. Nội dung: Bám sát tài liệu cung cấp bên dưới.
    3. Định dạng: Có Ma trận đề, Đề bài và Đáp án chi tiết.
    
    Tài liệu tham khảo:
    {context}
    """
    return model.generate_content(prompt).text

# --- 4. GIAO DIỆN CHÍNH ---

# Tiêu đề
st.markdown('<div class="main-header">🎄 ỨNG DỤNG TẠO ĐỀ THÔNG MINH - CHÀO XUÂN 2026 🎆</div>', unsafe_allow_html=True)

# Phần Hướng dẫn sử dụng (Nằm trong hộp đóng mở)
with st.expander("📖 HƯỚNG DẪN SỬ DỤNG (Bấm vào đây để xem chi tiết)", expanded=False):
    st.markdown("""
    <div class="instruction-box">
        <b>Chào mừng quý Thầy Cô! Để tạo đề kiểm tra, hãy làm theo 3 bước sau:</b><br><br>
        <b>Bước 1: Cấu hình lưu trữ</b><br>
        - Chọn Cấp học, Lớp và Môn học ở cột bên trái.<br>
        - Hệ thống sẽ tự động tạo kho lưu trữ riêng cho môn học đó.<br><br>
        <b>Bước 2: Tải tài liệu nguồn</b><br>
        - Tải lên các file Giáo án, Sách giáo khoa hoặc Đề cương (Word/PDF).<br>
        - Nếu tài liệu đã có sẵn trong kho từ trước, Thầy Cô không cần tải lại.<br><br>
        <b>Bước 3: Ra lệnh cho AI</b><br>
        - Chọn loại đề kiểm tra (15 phút, Giữa kỳ, Cuối kỳ...).<br>
        - Bấm nút <b>"🚀 BẮT ĐẦU TẠO ĐỀ"</b> và chờ khoảng 10-20 giây để nhận kết quả.
    </div>
    """, unsafe_allow_html=True)

col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown('<p class="sub-header">⚙️ 1. THIẾT LẬP KHO DỮ LIỆU</p>', unsafe_allow_html=True)
    
    cap_hoc = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop_hoc = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2) # Mặc định lớp 3
    mon_hoc = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ", "Khoa học"])
    
    current_folder = get_folder_path(cap_hoc, lop_hoc, mon_hoc)
    
    st.markdown("---")
    st.markdown('<p class="sub-header">📂 2. TẢI TÀI LIỆU (WORD/PDF)</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Kéo thả file vào đây", accept_multiple_files=True)
    
    if uploaded_files:
        for f in uploaded_files:
            status, msg = save_uploaded_file(f, current_folder)
            if status: st.success(msg)
            # Không hiển thị lỗi trùng lặp để giao diện sạch hơn

with col_right:
    st.markdown(f'<div style="background-color: #e6fffa; padding: 10px; border-radius: 5px;">📂 Đang làm việc tại kho: <b>{mon_hoc} - {lop_hoc}</b></div>', unsafe_allow_html=True)
    
    # Hiển thị file trong kho
    context_text, list_files = get_all_context(current_folder)
    with st.expander(f"👁️ Xem danh sách {len(list_files)} tài liệu đang có trong kho", expanded=True):
        if list_files:
            for f in list_files: st.text(f"📄 {f}")
        else:
            st.warning("Chưa có tài liệu nào. Vui lòng tải lên ở cột bên trái.")

    st.markdown('<p class="sub-header">📝 3. CẤU HÌNH ĐỀ THI & TẠO</p>', unsafe_allow_html=True)
    
    loai_de = st.selectbox("Chọn loại bài kiểm tra", 
                           ["Kiểm tra Thường xuyên (15p)", "Kiểm tra Giữa Học Kì 1", "Kiểm tra Cuối Học Kì 1", "Kiểm tra Giữa Học Kì 2", "Kiểm tra Cuối Học Kì 2"])
    
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not context_text:
            st.error("🛑 Kho dữ liệu đang trống! Vui lòng tải giáo án lên trước.")
        else:
            with st.spinner(f"❄️ AI Gemini đang đọc {len(list_files)} tài liệu và soạn đề cho Thầy..."):
                try:
                    result = generate_test_final(mon_hoc, lop_hoc, loai_de, context_text)
                    st.session_state['kq_2026'] = result
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

    # Hiển thị kết quả
    if 'kq_2026' in st.session_state:
        st.markdown("---")
        st.success("✅ Đã tạo đề thành công! Thầy có thể copy nội dung bên dưới:")
        st.container(border=True).markdown(st.session_state['kq_2026'])

# --- 5. FOOTER (CHỮ KÝ BẢN QUYỀN) ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống. <br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
