import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(layout="wide", page_title="Tạo Đề Thi 2026 - Thầy Khánh", page_icon="📝")

# --- CSS TÙY CHỈNH (GIAO DIỆN & FONT CHỮ) ---
st.markdown("""
<style>
    /* Ép toàn bộ web dùng font Times New Roman */
    html, body, [class*="css"] {
        font-family: 'Times New Roman', Times, serif !important;
    }
    
    /* Chỉnh tiêu đề không bị mất dấu mũ */
    .main-header {
        font-size: 36px; 
        font-weight: 900; 
        color: #cc0000; 
        text-align: center; 
        text-transform: uppercase;
        margin-top: 10px;
        margin-bottom: 30px; 
        text-shadow: 1px 1px 2px #ddd;
        line-height: 1.6; /* Tăng chiều cao dòng */
        padding: 20px 0;
    }

    /* Khung cuộn xem trước nội dung */
    .preview-box {
        background-color: #fff;
        border: 1px solid #006633;
        border-radius: 5px;
        padding: 15px;
        height: 500px; /* Chiều cao cố định */
        overflow-y: scroll; /* Cho phép cuộn */
        font-size: 14px;
        line-height: 1.5;
        white-space: pre-wrap; /* Giữ nguyên xuống dòng */
        box-shadow: inset 0 0 10px #f0f0f0;
    }

    /* Các tiêu đề mục */
    .section-title {
        color: #006633;
        font-weight: bold;
        font-size: 18px;
        border-bottom: 2px solid #006633;
        margin-bottom: 10px;
        padding-bottom: 5px;
    }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #006633; color: white; text-align: center;
        padding: 8px; font-size: 13px; z-index: 9999;
    }
    
    /* Nút tạo đề */
    .stButton>button {
        background-color: #cc0000; color: white; font-size: 20px; font-weight: bold;
        width: 100%; height: 60px; border-radius: 10px;
    }
    .stButton>button:hover { background-color: #b30000; }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API ---
# Thay mã API của thầy vào dòng dưới
API_KEY_DU_PHONG = "AIzaSy_MÃ_API_CỦA_THẦY_VÀO_ĐÂY"

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
            all_text += f"\n--- TÀI LIỆU: {file_name} ---\n{read_doc_text(full_path)}\n"
    return all_text

# --- 4. HÀM AI ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return models[0] if models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_test_v8(mon, lop, loai, context):
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)
    prompt = f"""
    Vai trò: Giáo viên bộ môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}".
    TÀI LIỆU CĂN CỨ: {context}
    YÊU CẦU:
    1. Tuân thủ 100% Ma trận/Đề minh họa (nếu có).
    2. Nếu không có ma trận: 40% Trắc nghiệm, 60% Tự luận.
    KẾT QUẢ TRẢ VỀ:
    - Phần I: MA TRẬN ĐỀ
    - Phần II: ĐỀ BÀI
    - Phần III: HƯỚNG DẪN CHẤM
    """
    return model.generate_content(prompt).text

# --- 5. GIAO DIỆN CHÍNH ---

st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)
st.markdown("""
<div style="background:#fff5f5; border:1px solid #cc0000; padding:10px; margin-bottom:20px; text-align:center; color:#cc0000; font-weight:bold;">
🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 🌸
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="section-title">1. THIẾT LẬP KHO DỮ LIỆU</div>', unsafe_allow_html=True)
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Khoa Học", "Lịch Sử"])
    
    curr_dir = get_folder_path(cap, lop, mon)
    st.caption(f"📂 Đang mở kho: {cap} > {lop} > {mon}")
    
    st.markdown("---")
    st.markdown('**📤 Tải tài liệu (Ma trận/Đề cũ) vào đây:**')
    uploads = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.success("Đã lưu xong!")

with col2:
    st.markdown('<div class="section-title">2. KIỂM TRA & CHỌN TÀI LIỆU</div>', unsafe_allow_html=True)
    
    files_in_dir = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    if not files_in_dir:
        st.warning("⚠️ Kho trống. Vui lòng tải tài liệu bên cột trái.")
        selected_files = []
    else:
        # --- A. DANH SÁCH CHECKBOX (THAY CHO MULTISELECT) ---
        st.write("🔽 **Tích chọn tài liệu muốn dùng (Bỏ tích nếu không dùng):**")
        
        # Tạo một container có viền để chứa danh sách
        with st.container(border=True):
            cols_check = st.columns(2) # Chia làm 2 cột cho gọn
            selected_files = []
            
            # Duyệt qua từng file và tạo ô checkbox
            for i, file_name in enumerate(files_in_dir):
                # Chia đều các file vào 2 cột
                with cols_check[i % 2]:
                    # Mặc định là Tích (value=True)
                    if st.checkbox(f"📄 {file_name}", value=True, key=f"chk_{i}"):
                        selected_files.append(file_name)
        
        if not selected_files:
            st.error("🛑 Thầy chưa chọn file nào cả!")

        # --- B. SOI NỘI DUNG (FULL VĂN BẢN) ---
        st.write("---")
        st.write("👁️ **Soi nội dung file (Xem toàn bộ):**")
        file_preview = st.selectbox("Chọn file để xem:", ["-- Chọn file --"] + files_in_dir)
        
        if file_preview != "-- Chọn file --":
            full_path = os.path.join(curr_dir, file_preview)
            content = read_doc_text(full_path)
            # Hiển thị full nội dung trong khung cuộn 500px
            st.markdown(f"<div class='preview-box'>{content}</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">3. TẠO ĐỀ THI</div>', unsafe_allow_html=True)
    loai = st.selectbox("Loại đề thi", ["15 Phút", "Giữa Học Kỳ 1", "Cuối Học Kỳ 1", "Giữa Học Kỳ 2", "Cuối Học Kỳ 2"])
    
    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not selected_files:
            st.error("Vui lòng tích chọn tài liệu trước!")
        else:
            context = get_selected_context(curr_dir, selected_files)
            with st.spinner("AI đang làm việc..."):
                try:
                    res = generate_test_v8(mon, lop, loai, context)
                    st.session_state['kq_v8'] = res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if 'kq_v8' in st.session_state:
        st.markdown("---")
        st.success("✅ Kết quả:")
        st.container(border=True).markdown(st.session_state['kq_v8'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra - Thầy Phan Quốc Khánh & Trợ lý ảo Gemini - Tiểu học Hua Nguống
</div>
""", unsafe_allow_html=True)
