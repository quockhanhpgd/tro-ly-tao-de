import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os
import PyPDF2

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(layout="wide", page_title="Tạo Đề Thi 2026 - Thầy Khánh", page_icon="📝")

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Times New Roman', serif !important; }
    .main-header {
        font-size: 36px; font-weight: 900; color: #cc0000; text-align: center;
        text-transform: uppercase; margin-top: 40px; margin-bottom: 20px;
        text-shadow: 1px 1px 2px #ddd; line-height: 1.8;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #006633; color: white; text-align: center;
        padding: 10px; font-size: 14px; z-index: 9999; border-top: 3px solid #FFD700;
        font-weight: bold;
    }
    .section-title { color: #006633; font-weight: bold; font-size: 18px; border-bottom: 2px solid #006633; margin-bottom: 15px; }
    .stButton>button {
        background-color: #cc0000; color: white; font-size: 20px; font-weight: bold;
        width: 100%; height: 55px; border-radius: 8px; border: 1px solid white;
    }
    .stButton>button:hover { background-color: #b30000; border-color: #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API ---
API_KEY_DU_PHONG = "AIzaSy_MÃ_API_CỦA_THẦY_VÀO_ĐÂY"
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = API_KEY_DU_PHONG
except: api_key = API_KEY_DU_PHONG

try: genai.configure(api_key=api_key)
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
    except: return ""
    return text

def get_selected_context(folder_path, selected_files):
    all_text = ""
    for file_name in selected_files:
        full_path = os.path.join(folder_path, file_name)
        if os.path.exists(full_path):
            all_text += f"\n--- TÀI LIỆU: {file_name} ---\n{read_doc_text(full_path)}\n"
    return all_text

# --- 4. HÀM XUẤT FILE WORD CHUẨN MẪU ---
def create_word_file(content, mon_hoc, lop_hoc):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    
    # Header Table
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    cell_1 = table.cell(0, 0)
    p1 = cell_1.paragraphs[0]
    r1 = p1.add_run(f"PHÒNG GD&ĐT HUYỆN........\nTRƯỜNG TH HUA NGUỐNG\n-------")
    r1.bold = True
    r1.font.size = Pt(11)
    r1.font.name = 'Times New Roman'
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_2 = table.cell(0, 1)
    p2 = cell_2.paragraphs[0]
    r2 = p2.add_run(f"ĐỀ KIỂM TRA CHẤT LƯỢNG\nMÔN: {mon_hoc.upper()} - {lop_hoc.upper()}\nNăm học: 2025 - 2026")
    r2.bold = True
    r2.font.size = Pt(11)
    r2.font.name = 'Times New Roman'
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    p_info = doc.add_paragraph(f"Họ và tên:................................................................Lớp:....................")
    p_info.runs[0].font.name = 'Times New Roman'
    p_info.runs[0].font.size = Pt(13)
    doc.add_paragraph("-------------------------------------------------------------------------------------------------------------------------------")

    # Content Processing
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        clean_line = line.replace("**", "")
        p = doc.add_paragraph()
        run = p.add_run(clean_line)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        
        if line.startswith(("Câu", "Bài", "PHẦN", "I.", "II.", "III.", "A.", "B.")):
            run.bold = True
            p.space_before = Pt(6)
        
        if line.startswith("ĐỀ BÀI") or line.startswith("ĐỀ KIỂM TRA"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run.bold = True
            run.font.size = Pt(14)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 5. HÀM AI (ĐÃ SỬA LỖI MODEL) ---
def generate_test_v11(mon, lop, loai, context):
    # SỬA LỖI QUAN TRỌNG: Chuyển sang dùng model 'gemini-1.5-flash' mới nhất
    # để tránh lỗi 404 của bản cũ
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        # Nếu vẫn lỗi thì thử fallback sang bản pro
        model = genai.GenerativeModel('gemini-1.5-pro')

    prompt = f"""
    Vai trò: Giáo viên {mon} lớp {lop} chuyên nghiệp.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}" để xuất ra file Word.
    
    TÀI LIỆU CĂN CỨ: {context}
    
    YÊU CẦU QUAN TRỌNG VỀ ĐỊNH DẠNG (Để xuất Word đẹp):
    1. KHÔNG dùng bảng (table) trong đề bài.
    2. KHÔNG dùng Markdown phức tạp. Dùng I., II., 1., 2. rõ ràng.
    3. Cấu trúc đề phải gồm:
       - PHẦN I. TRẮC NGHIỆM
       - PHẦN II. TỰ LUẬN
       - PHẦN III. ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM
    4. Nội dung câu hỏi phải chính xác, bám sát tài liệu.
    """
    return model.generate_content(prompt).text

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)
st.markdown("""
<div style="background:#fff5f5; border:1px solid #cc0000; padding:10px; margin-bottom:20px; text-align:center;">
    <marquee style="color:#cc0000; font-weight:bold; font-size:18px;">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 🌸</marquee>
</div>""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="section-title">1. KHO DỮ LIỆU</div>', unsafe_allow_html=True)
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Khoa Học", "Lịch Sử"])
    curr_dir = get_folder_path(cap, lop, mon)
    st.caption(f"📂 Kho: {cap}/{lop}/{mon}")
    
    st.markdown("---")
    uploads = st.file_uploader("Tải tài liệu lên kho:", accept_multiple_files=True)
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.success("Đã lưu!")

with col2:
    st.markdown('<div class="section-title">2. CHỌN TÀI LIỆU & TẠO ĐỀ</div>', unsafe_allow_html=True)
    files = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    if not files:
        st.warning("⚠️ Kho trống. Hãy tải tài liệu bên trái.")
        selected_files = []
    else:
        st.write("▼ **Tích chọn tài liệu cần dùng:**")
        with st.container(border=True):
            cols = st.columns(2)
            selected_files = []
            for i, f in enumerate(files):
                with cols[i%2]:
                    if st.checkbox(f"📄 {f}", True, key=f"c_{i}"): selected_files.append(f)
    
    st.write("---")
    loai = st.selectbox("Loại đề:", ["15 Phút", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2"])
    
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not selected_files: st.error("Chưa chọn tài liệu!")
        else:
            ctx = get_selected_context(curr_dir, selected_files)
            with st.spinner("Đang thiết lập định dạng Word..."):
                try:
                    res = generate_test_v11(mon, lop, loai, ctx)
                    st.session_state['kq_v11'] = res
                except Exception as e: st.error(f"Lỗi: {e}")

    if 'kq_v11' in st.session_state:
        st.markdown("---")
        st.success("✅ Đã tạo xong! Bấm nút dưới để tải về:")
        
        doc_file = create_word_file(st.session_state['kq_v11'], mon, lop)
        
        st.download_button(
            label="📥 TẢI FILE WORD (.DOCX) - ĐÚNG ĐỊNH DẠNG",
            data=doc_file,
            file_name=f"De_{mon}_{lop}_{loai}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
        
        with st.expander("Xem trước nội dung thô:"):
            st.markdown(st.session_state['kq_v11'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
