import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os
import PyPDF2
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(layout="wide", page_title="Tạo Đề Thi 2026 - Thầy Khánh", page_icon="⚡")

# --- CSS ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Times New Roman', serif !important; }
    .main-header { font-size: 30px; font-weight: bold; color: #cc0000; text-align: center; margin-top: 20px; }
    .status-box { padding: 10px; border-radius: 5px; background-color: #e6fffa; border: 1px solid #006633; color: #006633; margin-bottom: 10px; }
    .stButton>button { background-color: #cc0000; color: white; width: 100%; height: 50px; font-size: 18px; }
</style>
""", unsafe_allow_html=True)

# --- 2. KẾT NỐI API ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.warning("⚠️ Chưa nhập API Key trong Secrets.")
except: pass

# --- 3. HÀM XỬ LÝ FILE (CÓ TỐI ƯU) ---
BASE_DIR = "KHO_DU_LIEU_GD"
def get_folder_path(cap, lop, mon):
    path = os.path.join(BASE_DIR, cap, lop, mon)
    if not os.path.exists(path): os.makedirs(path)
    return path

def save_uploaded_file(uploaded_file, target_folder):
    with open(os.path.join(target_folder, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

def read_doc_text(file_path):
    text = ""
    try:
        if file_path.endswith('.docx'):
            doc = Document(file_path)
            # Chỉ lấy văn bản, bỏ qua định dạng phức tạp gây nặng
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip() != ""])
        elif file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages: 
                    text += page.extract_text() or ""
    except: return ""
    return text

def create_word_file(content, mon, lop):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    
    p_title = doc.add_paragraph(f"ĐỀ KIỂM TRA MÔN {mon.upper()} - {lop.upper()}")
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.runs[0].bold = True
    p_title.runs[0].font.size = Pt(14)
    
    doc.add_paragraph(content)
    
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 4. HÀM TẠO ĐỀ (CÓ BÁO CÁO TIẾN ĐỘ) ---
def generate_test_v17(mon, lop, loai, selected_files, folder_path, status_container):
    
    # BƯỚC 1: ĐỌC FILE
    status_container.info("1/3: Đang đọc nội dung tài liệu...")
    full_context = ""
    for file_name in selected_files:
        path = os.path.join(folder_path, file_name)
        file_content = read_doc_text(path)
        if file_content:
            full_context += f"\n--- TÀI LIỆU {file_name} ---\n{file_content}\n"
    
    if not full_context:
        return "Lỗi: Không đọc được nội dung từ file. Thầy hãy kiểm tra lại file Word/PDF."

    # BƯỚC 2: KẾT NỐI AI
    status_container.info("2/3: Đang gửi dữ liệu lên 'Bộ não AI' (Gemini 1.5 Flash)...")
    
    # Dùng model nhanh nhất
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Vai trò: Giáo viên {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}" CHUẨN MỰC.
    
    DỮ LIỆU ĐẦU VÀO:
    {full_context[:30000]}  # Giới hạn 30.000 ký tự để tránh quá tải
    
    YÊU CẦU ĐẦU RA:
    1. Soạn đề thi gồm: TRẮC NGHIỆM và TỰ LUẬN (theo đúng ma trận nếu có).
    2. Trình bày rõ ràng, không dùng bảng biểu (table).
    3. Có đáp án chi tiết ở cuối.
    """

    # BƯỚC 3: NHẬN KẾT QUẢ
    try:
        response = model.generate_content(prompt)
        status_container.success("3/3: Xong! Đang hiển thị kết quả...")
        return response.text
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}. (Có thể do mạng hoặc tài liệu quá dài)"

# --- 5. GIAO DIỆN ---
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH (V17)</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.write("### 1. KHO DỮ LIỆU")
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Khoa Học"])
    curr_dir = get_folder_path(cap, lop, mon)
    
    uploads = st.file_uploader("Tải thêm tài liệu:", accept_multiple_files=True)
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.toast("Đã lưu file!")

with col2:
    st.write("### 2. TẠO ĐỀ")
    files = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    if not files:
        st.warning("Kho trống.")
        selected_files = []
    else:
        with st.container(border=True):
            st.write("Chọn tài liệu sử dụng:")
            cols = st.columns(2)
            selected_files = []
            for i, f in enumerate(files):
                with cols[i%2]:
                    if st.checkbox(f"📄 {f}", True, key=f"c_{i}"): selected_files.append(f)
    
    loai = st.selectbox("Loại đề:", ["15 Phút", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2"])
    
    # Khung hiển thị trạng thái chạy
    status_box = st.empty()
    
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not selected_files:
            st.error("Chưa chọn tài liệu!")
        else:
            # Gọi hàm tạo đề mới
            res = generate_test_v17(mon, lop, loai, selected_files, curr_dir, status_box)
            st.session_state['kq_v17'] = res

    # Hiển thị kết quả
    if 'kq_v17' in st.session_state:
        st.success("✅ Đã tạo xong!")
        
        doc_file = create_word_file(st.session_state['kq_v17'], mon, lop)
        st.download_button("📥 TẢI ĐỀ VỀ MÁY (.DOCX)", doc_file, file_name="De_Thi.docx", mime="application/msword", type="primary")
        
        with st.container(border=True):
            st.markdown(st.session_state['kq_v17'])

# --- FOOTER ---
st.markdown("""<div style="text-align:center; margin-top:50px; color:grey; font-size:12px;">Hỗ trợ bởi Thầy Khánh & Gemini AI</div>""", unsafe_allow_html=True)
