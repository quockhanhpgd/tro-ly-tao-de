import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(layout="wide", page_title="Trợ lý Tin học 3 - Thầy Khánh", page_icon="📝")

# --- 2. CSS GIAO DIỆN (ĐÚNG THIẾT KẾ CỦA THẦY) ---
st.markdown("""
<style>
    /* Nút bấm lớn, đẹp như trong hình mô tả */
    .stButton>button {
        width: 100%;
        height: 70px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 12px;
        background-color: #f0f2f6;
        color: #004d40;
        border: 2px solid #004d40;
        margin-bottom: 10px;
    }
    .stButton>button:hover {
        background-color: #004d40;
        color: white;
        border-color: #004d40;
    }
    .title-box {
        text-align: center;
        background-color: #e0f7fa;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 2px solid #006064;
    }
    h1 { color: #006064; }
</style>
""", unsafe_allow_html=True)

# --- 3. CÁC HÀM XỬ LÝ (LOGIC CHẠY NGẦM) ---

def read_files(curr_dir, selected_files):
    """Đọc file Word/PDF Thầy upload"""
    context = ""
    if not selected_files: return ""
    
    for fname in selected_files:
        path = os.path.join(curr_dir, fname)
        try:
            if fname.endswith(".docx"):
                doc = Document(path)
                text = "\n".join([p.text for p in doc.paragraphs])
                context += f"\n--- TÀI LIỆU: {fname} ---\n{text}\n"
            elif fname.endswith(".pdf"):
                reader = PyPDF2.PdfReader(path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                context += f"\n--- TÀI LIỆU: {fname} ---\n{text}\n"
        except:
            pass # Bỏ qua lỗi nhỏ để chạy tiếp
    return context

def call_gemini_ai(api_key, context, request_type):
    """Gửi lệnh cho AI tạo đề"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Đóng vai Trợ lý Giáo dục của Thầy Khánh.
    Nhiệm vụ: Soạn ĐỀ KIỂM TRA TIN HỌC LỚP 3.
    Loại đề: {request_type}
    
    DỮ LIỆU NỀN TẢNG (SGK, Ma trận, NLS):
    {context}
    
    YÊU CẦU CẤU TRÚC:
    1. Thời gian: 35 phút.
    2. Phần Trắc nghiệm: 4 phương án A,B,C,D.
    3. Phần Thực hành/Tự luận: Có hướng dẫn chấm chi tiết.
    4. Bắt buộc: Tích hợp nội dung Năng lực số (Bảo vệ mắt, an toàn thông tin).
    5. Định dạng: Markdown chuẩn.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 4. GIAO DIỆN CHÍNH (LAYOUT) ---

# Tiêu đề
st.markdown('<div class="title-box"><h1>ỨNG DỤNG TẠO ĐỀ KIỂM TRA TIN HỌC LỚP 3</h1><h3>Tích hợp Chuẩn GDPT 2018 & Khung Năng Lực Số</h3></div>', unsafe_allow_html=True)

# SIDEBAR (Cấu hình)
with st.sidebar:
    st.header("📂 1. CẤU HÌNH & DỮ LIỆU")
    
    # Ô nhập API Key (QUAN TRỌNG ĐỂ CHẠY ĐƯỢC)
    api_key = st.text_input("🔑 Nhập API Key vào đây:", type="password")
    
    st.markdown("---")
    st.write("📂 **Chọn tài liệu nguồn:**")
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf')) and not f.startswith('~')]
    
    selected_files = []
    for f in files:
        if st.checkbox(f"📄 {f}", False): # Mặc định không chọn để tránh nặng
            selected_files.append(f)

# PHẦN NÚT BẤM (GRID LAYOUT NHƯ HÌNH)
st.header("🛠 2. CHỨC NĂNG TẠO ĐỀ (Bấm là có đề)")
col1, col2 = st.columns(2)

action = None # Biến lưu hành động

with col1:
    if st.button("📝 Đề kiểm tra Học Kì I"):
        action = "ĐỀ CUỐI HỌC KÌ 1 (Phạm vi: Bài 1 đến Bài 8)"
    if st.button("📝 Đề kiểm tra Giữa Kì I"):
        action = "ĐỀ GIỮA HỌC KÌ 1 (Phạm vi: Chủ đề A - Máy tính và em)"
    if st.button("📝 Đề kiểm tra Cả năm"):
        action = "ĐỀ TỔNG HỢP CẢ NĂM HỌC"

with col2:
    if st.button("📝 Đề kiểm tra Học Kì II"):
        action = "ĐỀ CUỐI HỌC KÌ 2 (Phạm vi: Cả năm, trọng tâm kì 2)"
    if st.button("📝 Đề kiểm tra Giữa Kì II"):
        action = "ĐỀ GIỮA HỌC KÌ 2 (Phạm vi: Bảo vệ thông tin, Giải trí)"
    if st.button("📚 Đề kiểm tra Theo bài học"):
        action = "ĐỀ KIỂM TRA 1 TIẾT (Theo bài học bất kỳ)"

# --- 5. XỬ LÝ KHI BẤM NÚT ---
if action:
    # Kiểm tra lỗi trước
    if not api_key:
        st.error("⚠️ THẦY CHƯA NHẬP API KEY Ở CỘT BÊN TRÁI Ạ!")
    elif not selected_files:
        st.error("⚠️ THẦY CHƯA CHỌN TÀI LIỆU (MA TRẬN/SGK) Ở CỘT TRÁI!")
    else:
        # Bắt đầu chạy
        st.markdown("---")
        st.info(f"🤖 Đang khởi động AI để tạo: **{action}**...")
        
        # Thanh tiến trình
        my_bar = st.progress(0)
        
        try:
            # Bước 1: Đọc file (30%)
            context_text = read_files(curr_dir, selected_files)
            if len(context_text) < 50:
                st.error("❌ Tài liệu thầy chọn bị rỗng hoặc không đọc được (Kiểm tra lại file PDF scan).")
                st.stop()
            my_bar.progress(30)
            
            # Bước 2: Gọi AI (80%)
            st.write("⏳ Đang phân tích ma trận và soạn câu hỏi...")
            result = call_gemini_ai(api_key, context_text, action)
            my_bar.progress(100)
            
            # Bước 3: Lưu vào session để không bị mất khi reload
            st.session_state['ket_qua'] = result
            st.session_state['loai_de'] = action
            
        except Exception as e:
            st.error(f"❌ Lỗi kết nối: {str(e)}")
            st.warning("Thầy kiểm tra lại API Key xem có đúng không nhé!")

# --- 6. HIỂN THỊ KẾT QUẢ ---
if 'ket_qua' in st.session_state:
    st.success("✅ ĐÃ SOẠN XONG! Thầy xem đề bên dưới:")
    st.markdown("---")
    
    # Hiển thị đề thi
    st.markdown(st.session_state['ket_qua'])
    
    # Nút tải về
    st.download_button(
        label="📥 TẢI ĐỀ VỀ MÁY TÍNH (File .txt)",
        data=st.session_state['ket_qua'],
        file_name=f"De_Tin_Hoc_Lop_3.txt",
        mime="text/plain"
    )
