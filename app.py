import streamlit as st
import google.generativeai as genai
from docx import Document
import os
import PyPDF2

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN ---
st.set_page_config(layout="wide", page_title="App Soạn Đề - Thầy Khánh")

# CSS để giao diện giống hệt bản thiết kế của Thầy (Nút bấm to, rõ)
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 80px;  /* Chiều cao nút bấm lớn */
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        margin-bottom: 10px;
        background-color: #f0f2f6;
        color: #004d40;
        border: 2px solid #006064;
    }
    .stButton>button:hover {
        background-color: #006064;
        color: white;
    }
    h1 { color: #d32f2f; text-align: center; text-transform: uppercase; }
    h3 { text-align: center; color: #555; }
</style>
""", unsafe_allow_html=True)

# --- 2. TIÊU ĐỀ ỨNG DỤNG ---
st.markdown("<h1>ỨNG DỤNG TẠO ĐỀ KIỂM TRA TIN HỌC LỚP 3</h1>", unsafe_allow_html=True)
st.markdown("<h3>(Hỗ trợ Thầy Khánh - GDPT 2018)</h3>", unsafe_allow_html=True)
st.divider()

# --- 3. KHU VỰC CẤU HÌNH & UPLOAD (Cột bên trái) ---
with st.sidebar:
    st.header("1. KẾT NỐI & DỮ LIỆU")
    
    # Ô nhập Key bắt buộc để AI chạy
    api_key = st.text_input("🔑 Nhập API Key:", type="password")
    
    st.write("---")
    st.write("📂 **Upload Tài Liệu:**")
    
    # Lấy danh sách file trong thư mục hiện tại
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf'))]
    
    selected_files = []
    for f in files:
        if st.checkbox(f"📄 {f}", value=False):
            selected_files.append(f)

# --- 4. HÀM XỬ LÝ AI (SỬA LỖI TREO MÁY) ---
def tao_de_thi(loai_de, files, key):
    # Cấu hình AI
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Đọc nội dung file
    noi_dung_file = ""
    for fname in files:
        path = os.path.join(curr_dir, fname)
        try:
            if fname.endswith(".docx"):
                doc = Document(path)
                noi_dung_file += "\n".join([p.text for p in doc.paragraphs])
            elif fname.endswith(".pdf"):
                reader = PyPDF2.PdfReader(path)
                for page in reader.pages:
                    noi_dung_file += page.extract_text()
        except: pass

    # Gửi lệnh cho AI
    prompt = f"""
    Hãy đóng vai trợ lý giáo dục, soạn 01 ĐỀ KIỂM TRA TIN HỌC LỚP 3.
    - Loại đề: {loai_de}
    - Tài liệu tham khảo: {noi_dung_file}
    
    Yêu cầu:
    1. Thời gian: 35 phút.
    2. Gồm: Trắc nghiệm (4 đáp án) và Tự luận/Thực hành.
    3. Có đáp án chi tiết phía dưới.
    """
    
    return model.generate_content(prompt).text

# --- 5. GIAO DIỆN NÚT BẤM (ĐÚNG Y HỆT HÌNH THẦY GỬI) ---
col1, col2 = st.columns(2)

action = None # Biến lưu tên loại đề

with col1:
    if st.button("📝 Đề kiểm tra Học Kì I"):
        action = "Cuối Học Kì 1"
    if st.button("📝 Đề kiểm tra Giữa Kì I"):
        action = "Giữa Học Kì 1"
    if st.button("📝 Đề kiểm tra Cả năm"):
        action = "Tổng hợp Cả năm"

with col2:
    if st.button("📝 Đề kiểm tra Học Kì II"):
        action = "Cuối Học Kì 2"
    if st.button("📝 Đề kiểm tra Giữa Kì II"):
        action = "Giữa Học Kì 2"
    if st.button("📚 Đề kiểm tra Theo bài học"):
        action = "Kiểm tra 15 phút theo bài"

# --- 6. XỬ LÝ KHI BẤM NÚT ---
if action:
    if not api_key:
        st.error("⚠️ Thầy ơi, nhập API Key ở cột bên trái mới tạo đề được ạ!")
    elif not selected_files:
        st.error("⚠️ Thầy chưa chọn tài liệu (Ma trận/SGK) ở cột bên trái ạ!")
    else:
        # Hiển thị trạng thái đang chạy
        with st.status(f"🤖 Đang soạn {action}... Thầy đợi 10 giây nhé!", expanded=True):
            try:
                ket_qua = tao_de_thi(action, selected_files, api_key)
                st.write("✅ Đã soạn xong!")
                
                # Hiện kết quả
                st.markdown("---")
                st.subheader(f"📄 KẾT QUẢ: {action}")
                st.markdown(ket_qua)
                
                # Nút tải về
                st.download_button("📥 Tải đề về máy", ket_qua, file_name="De_Thi.txt")
            except Exception as e:
                st.error(f"Lỗi: {e}. (Thầy kiểm tra lại API Key nhé)")
