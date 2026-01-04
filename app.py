import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os
import shutil

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(layout="wide", page_title="Kho Học Liệu & Tạo Đề - Thầy Khánh")

# THƯ MỤC GỐC ĐỂ LƯU TRỮ (Thầy có thể đổi tên folder này)
BASE_DIR = "KHO_DU_LIEU_GD"

# --- CẤU HÌNH API KEY (Sửa lại đoạn này) ---
import os

# Kiểm tra xem đang chạy trên mạng (Secrets) hay ở máy nhà
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Nếu chạy ở máy nhà mà không có secrets, Thầy có thể điền tạm key vào đây để test
    api_key = "MÃ_KEY_CỦA_THẦY_NẾU_CHẠY_OFFLINE"

genai.configure(api_key=api_key)

# --- 2. CÁC HÀM XỬ LÝ FILE HỆ THỐNG ---

def get_folder_path(cap_hoc, lop_hoc, mon_hoc):
    """Tạo đường dẫn thư mục: KHO/Cap/Lop/Mon"""
    # Xử lý tên để tạo folder không dấu, tránh lỗi
    path = os.path.join(BASE_DIR, cap_hoc, lop_hoc, mon_hoc)
    if not os.path.exists(path):
        os.makedirs(path) # Tự tạo thư mục nếu chưa có
    return path

def save_uploaded_file(uploaded_file, target_folder):
    """Lưu file vào thư mục và kiểm tra trùng lặp"""
    file_path = os.path.join(target_folder, uploaded_file.name)
    
    if os.path.exists(file_path):
        return False, f"⚠️ File '{uploaded_file.name}' đã có trong kho dữ liệu cũ. Đã bỏ qua upload."
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return True, f"✅ Đã lưu mới: {uploaded_file.name}"

def read_doc_text(file_path):
    """Đọc nội dung text từ đường dẫn file trong máy"""
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
    except Exception as e:
        print(f"Lỗi đọc file {file_path}: {e}")
    return text

def get_all_context(folder_path):
    """Lấy toàn bộ nội dung của tất cả các file trong thư mục"""
    all_text = ""
    files = [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    if not files:
        return "", []
        
    for file_name in files:
        full_path = os.path.join(folder_path, file_name)
        all_text += f"\n--- Tài liệu: {file_name} ---\n"
        all_text += read_doc_text(full_path)
        
    return all_text, files

# --- 3. HÀM AI ---
def get_smart_model():
    """Tự động chọn Model AI"""
    try:
        ds_model = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        uu_tien = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for m in uu_tien:
            if m in ds_model: return m
        return ds_model[0] if ds_model else None
    except: return None

def generate_test(mon, lop, loai, context, model_name):
    model = genai.GenerativeModel(model_name)
    prompt = f"""
    Vai trò: Giáo viên bộ môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra {loai}.
    Yêu cầu: Có Ma trận, Trắc nghiệm, Tự luận, Đáp án.
    Tài liệu tham khảo (Nội dung giảng dạy):
    {context}
    """
    return model.generate_content(prompt).text

# --- 4. GIAO DIỆN NGƯỜI DÙNG ---
st.markdown('<h2 style="text-align: center; color: #004aad;">🗄️ KHO HỌC LIỆU SỐ & TẠO ĐỀ KIỂM TRA</h2>', unsafe_allow_html=True)

# Kiểm tra kết nối
model_name = get_smart_model()
if not model_name:
    st.error("Lỗi kết nối API Key!")
    st.stop()

col_setting, col_main = st.columns([1, 2])

with col_setting:
    st.info("1. CẤU HÌNH LƯU TRỮ")
    cap_hoc = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop_hoc = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)])
    mon_hoc = st.selectbox("Môn học", ["Tin học", "Toán", "Văn", "Tiếng Anh", "KHTN", "Lịch Sử", "Địa Lý"])
    
    # Xác định thư mục hiện tại
    current_folder = get_folder_path(cap_hoc, lop_hoc, mon_hoc)
    
    st.markdown("---")
    st.info("2. TẢI TÀI LIỆU LÊN KHO")
    uploaded_files = st.file_uploader("Chọn file giáo án/đề cũ (Word/PDF)", accept_multiple_files=True)
    
    if uploaded_files:
        for f in uploaded_files:
            status, msg = save_uploaded_file(f, current_folder)
            if status: st.success(msg)
            else: st.warning(msg)

with col_main:
    st.success(f"📂 Đang làm việc tại thư mục: **{current_folder}**")
    
    # Hiển thị danh sách file đang có trong kho
    context_text, list_files = get_all_context(current_folder)
    
    with st.expander(f"👁️ Xem danh sách tài liệu hiện có trong kho ({len(list_files)} file)", expanded=True):
        if list_files:
            for f in list_files:
                st.text(f"📄 {f}")
        else:
            st.warning("⚠️ Chưa có tài liệu nào trong thư mục này. Thầy hãy tải lên ở cột bên trái nhé!")

    st.markdown("---")
    st.markdown("### 📝 TẠO ĐỀ KIỂM TRA")
    loai_de = st.selectbox("Chọn loại đề", ["15 Phút", "1 Tiết", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2"])
    
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ", type="primary"):
        if not context_text:
            st.error("🛑 Không có dữ liệu! Vui lòng tải tài liệu lên kho trước.")
        else:
            with st.spinner(f"Đang đọc {len(list_files)} tài liệu và soạn đề..."):
                try:
                    result = generate_test(mon_hoc, lop_hoc, loai_de, context_text, model_name)
                    st.session_state['kq_pro'] = result
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")

    if 'kq_pro' in st.session_state:

        st.markdown(st.session_state['kq_pro'])
