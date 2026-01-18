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

# --- CSS GIAO DIỆN (Giữ nguyên của Thầy) ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Times New Roman', Times, serif !important; }
    .main-header { font-size: 34px; font-weight: 900; color: #cc0000; text-align: center; text-transform: uppercase; margin: 20px 0; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #006633; color: white; text-align: center; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# PHẦN EM ĐÃ SỬA: CẤU HÌNH API KEY TẠI ĐÂY
# =========================================================
with st.sidebar:
    st.header("🔐 CẤU HÌNH KẾT NỐI")
    # Tạo ô nhập password để Thầy điền API Key
    api_key = st.text_input("AIzaSyDAJBQ02elLsixO9RmgVzk6MtzTRuhCWQ0", type="password", placeholder="AIzaSy...")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.success("Đã kết nối Gemini thành công! ✅")
        except Exception as e:
            st.error(f"Key không đúng: {e}")
    else:
        st.warning("⚠️ Thầy cần nhập API Key để tạo đề.")
        
    st.divider()
    # (Phần upload file cũ của Thầy giữ nguyên ở dưới đây)
# =========================================================

# --- 2. KẾT NỐI API (TỪ SECRETS) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.warning("⚠️ Chưa nhập API Key trong Secrets.")
except: pass

# --- 3. CÁC HÀM XỬ LÝ FILE ---
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
            content = read_doc_text(full_path)
            # Giới hạn nội dung để tránh treo máy (Quan trọng)
            all_text += f"\n--- TÀI LIỆU: {file_name} ---\n{content[:20000]}\n" 
    return all_text

def create_word_file(content, mon_hoc, lop_hoc):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    
    # Header chuẩn mẫu
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    cell_1 = table.cell(0, 0)
    p1 = cell_1.paragraphs[0]
    r1 = p1.add_run(f"PHÒNG GD&ĐT HUYỆN........\nTRƯỜNG TH HUA NGUỐNG\n-------")
    r1.bold = True; r1.font.size = Pt(11); r1.font.name = 'Times New Roman'
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_2 = table.cell(0, 1)
    p2 = cell_2.paragraphs[0]
    r2 = p2.add_run(f"ĐỀ KIỂM TRA CHẤT LƯỢNG\nMÔN: {mon_hoc.upper()} - {lop_hoc.upper()}\nNăm học: 2025 - 2026")
    r2.bold = True; r2.font.size = Pt(11); r2.font.name = 'Times New Roman'
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    p_info = doc.add_paragraph(f"Họ và tên:................................................................Lớp:....................")
    p_info.runs[0].font.name = 'Times New Roman'; p_info.runs[0].font.size = Pt(13)
    doc.add_paragraph("-------------------------------------------------------------------------------------------------------------------------------")

    # Xử lý nội dung
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        clean_line = line.replace("**", "")
        p = doc.add_paragraph()
        run = p.add_run(clean_line)
        run.font.name = 'Times New Roman'; run.font.size = Pt(13)
        
        if line.startswith(("Câu", "Bài", "PHẦN", "I.", "II.", "III.", "A.", "B.")):
            run.bold = True; p.space_before = Pt(6)
        if line.startswith("ĐỀ BÀI") or line.startswith("ĐỀ KIỂM TRA"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run.bold = True; run.font.size = Pt(14)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 4. HÀM AI THÔNG MINH (PHIÊN BẢN MỚI NHẤT 2026) ---
def generate_test_v19(mon, lop, loai, context):
    # Tắt bộ lọc an toàn để tránh lỗi "Finish Reason 1"
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # Dùng model 'gemini-1.5-flash' (Nhanh và ổn định nhất hiện nay)
    # Nếu lỗi, tự động chuyển sang 'gemini-1.5-pro'
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    for m in models_to_try:
        try:
            model = genai.GenerativeModel(m, safety_settings=safety_settings)
            prompt = f"""
            Vai trò: Giáo viên {mon} lớp {lop} chuyên nghiệp.
            Nhiệm vụ: Soạn đề kiểm tra "{loai}" để xuất ra file Word.
            TÀI LIỆU CĂN CỨ: {context}
            YÊU CẦU:
            1. Cấu trúc đề: PHẦN I. TRẮC NGHIỆM, PHẦN II. TỰ LUẬN, PHẦN III. ĐÁP ÁN.
            2. Nội dung bám sát tài liệu. Không dùng bảng biểu.
            3. Trình bày rõ ràng các câu hỏi.
            """
            response = model.generate_content(prompt)
            if response.text: return response.text
        except:
            continue
            
    return "Hệ thống đang quá tải. Thầy vui lòng F5 và thử lại nhé!"

# --- 5. GIAO DIỆN CHÍNH (ĐÚNG NHƯ THẦY YÊU CẦU) ---
st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)
st.markdown("""
<div style="background:#fff5f5; border:1px solid #cc0000; padding:10px; margin-bottom:20px; text-align:center;">
    <marquee style="color:#cc0000; font-weight:bold; font-size:18px;">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH NĂM MỚI THÀNH CÔNG RỰC RỠ 🌸</marquee>
</div>""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 1. THIẾT LẬP KHO DỮ LIỆU")
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Khoa Học", "Lịch Sử"])
    curr_dir = get_folder_path(cap, lop, mon)
    st.caption(f"📂 Đang mở kho: {cap} > {lop} > {mon}")
    
    st.markdown("---")
    uploads = st.file_uploader("Tải tài liệu lên kho:", accept_multiple_files=True)
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.success("Đã lưu!")

with col2:
    st.markdown("### 2. CHỌN TÀI LIỆU & TẠO ĐỀ")
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
            with st.spinner("Đang soạn đề..."):
                try:
                    res = generate_test_v19(mon, lop, loai, ctx)
                    st.session_state['kq_v19'] = res
                except Exception as e: st.error(f"Lỗi: {e}")

    # KẾT QUẢ & NÚT TẢI
    if 'kq_v19' in st.session_state:
        st.markdown("---")
        st.success("✅ Đã tạo xong! Thầy kiểm tra và tải về:")
        
        doc_file = create_word_file(st.session_state['kq_v19'], mon, lop)
        st.download_button(
            label="📥 TẢI ĐỀ VỀ MÁY (.DOCX)",
            data=doc_file,
            file_name=f"De_{mon}_{lop}_{loai}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )

        with st.expander("👁️ Xem trước nội dung thô", expanded=True):
            st.write(st.session_state['kq_v19'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)

