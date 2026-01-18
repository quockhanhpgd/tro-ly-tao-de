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
  # ==============================================================================
# PHẦN CODE MỚI - THẦY DÁN VÀO CUỐI FILE (THAY THẾ ĐOẠN TỪ DÒNG 222 TRỞ ĐI)
# ==============================================================================

def get_selected_context(curr_dir, selected_files):
    """Hàm đọc nội dung từ file Word/PDF Thầy đã chọn"""
    context = ""
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
        except Exception as e:
            st.error(f"❌ Không đọc được file {fname}. Lỗi: {str(e)}")
    return context

def generate_test_v19(mon, lop, loai, context):
    """Hàm gọi Gemini để sinh đề thi"""
    # 1. Cấu hình Model - Dùng bản Flash cho nhanh
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 2. Soạn câu lệnh (Prompt)
    prompt = f"""
    Đóng vai một Giáo viên Tin học giỏi (20 năm kinh nghiệm).
    Hãy soạn một ĐỀ KIỂM TRA MÔN {mon} LỚP {lop} - LOẠI ĐỀ: {loai}.
    
    DỮ LIỆU ĐẦU VÀO (Kiến thức nền):
    {context}
    
    YÊU CẦU CẤU TRÚC ĐỀ (Bắt buộc tuân thủ):
    1. Thời gian: 35 phút.
    2. Phần I: Trắc nghiệm (6-8 câu). 4 đáp án A,B,C,D.
    3. Phần II: Tự luận/Thực hành (2-3 câu).
    4. CÓ ĐÁP ÁN VÀ BIỂU ĐIỂM CHI TIẾT Ở CUỐI.
    5. Trình bày Markdown rõ ràng (Dùng ## cho tiêu đề, ** cho in đậm).
    """
    
    # 3. Gửi lệnh
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"LỖI KẾT NỐI AI: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.write("---")
col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    loai = st.selectbox("📌 Chọn loại đề:", ["Kiểm tra 15 Phút", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2", "Khảo sát đầu năm"])
with col_sel2:
    st.info("💡 Mẹo: Chọn file 'Ma Trận' và 'SGK Tóm tắt' để đề ra chuẩn nhất.")

# NÚT BẤM TẠO ĐỀ
if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY", type="primary"):
    # Kiểm tra điều kiện
    if not api_key:
        st.error("⚠️ QUÊN CHÌA KHÓA: Thầy chưa nhập API Key ở cột bên trái kìa!")
    elif not selected_files:
        st.error("⚠️ QUÊN TÀI LIỆU: Thầy chưa tích chọn file nào ở trên cả!")
    else:
        # Bắt đầu chạy
        with st.status("🤖 Trợ lý đang làm việc...", expanded=True) as status:
            st.write("1. Đang đọc tài liệu Thầy gửi...")
            ctx = get_selected_context(curr_dir, selected_files)
            
            # Kiểm tra xem có đọc được chữ nào không
            if len(ctx.strip()) < 10:
                st.error("❌ Tài liệu rỗng! (Có thể file PDF là dạng ảnh chụp/scan nên AI không đọc được).")
                status.update(label="Thất bại", state="error")
            else:
                st.write("2. Đang suy nghĩ và soạn câu hỏi (Mất khoảng 15s)...")
                try:
                    res = generate_test_v19(mon, lop, loai, ctx)
                    if "LỖI KẾT NỐI AI" in res:
                        st.error(res)
                        status.update(label="Lỗi kết nối", state="error")
                    else:
                        st.session_state['kq_v19'] = res
                        st.write("3. Hoàn tất! Đang xuất bản...")
                        status.update(label="Xong! ✅", state="complete")
                except Exception as e:
                    st.error(f"Lỗi lạ: {str(e)}")

# HIỂN THỊ KẾT QUẢ VÀ NÚT TẢI
if 'kq_v19' in st.session_state:
    st.markdown("---")
    st.subheader(f"📄 KẾT QUẢ: {loai}")
    st.markdown(st.session_state['kq_v19']) # Hiển thị đề lên màn hình
    
    st.markdown("---")
    # Nút tải về (File .TXT an toàn nhất, không lo lỗi định dạng Word)
    st.download_button(
        label="📥 TẢI ĐỀ VỀ MÁY (Dạng văn bản)",
        data=st.session_state['kq_v19'],
        file_name=f"De_TinHoc_{loai}.txt",
        mime="text/plain"
    )
    
    # Nếu Thầy muốn tải file Word và hàm create_word_file ở trên vẫn còn
    # thì có thể dùng nút này (Em rào lại để tránh lỗi nếu Thầy lỡ xóa mất hàm kia)
    try:
        doc_file = create_word_file(st.session_state['kq_v19'], mon, lop)
        st.download_button(
            label="📥 TẢI ĐỀ VỀ MÁY (Dạng Word đẹp)",
            data=doc_file,
            file_name=f"De_TinHoc_{loai}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except:
        st.warning("⚠️ Chức năng tải Word tạm ẩn do hàm create_word_file bị thiếu, Thầy dùng nút tải văn bản ở trên nhé!")
