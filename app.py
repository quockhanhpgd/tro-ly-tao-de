import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN CHUẨN ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="📝"
)

# CSS TÙY CHỈNH (CHUẨN HÓA FONT CHỮ TIMES NEW ROMAN & GIAO DIỆN)
st.markdown("""
<style>
    /* 1. ÉP TOÀN BỘ WEB DÙNG FONT TIMES NEW ROMAN */
    html, body, [class*="css"] {
        font-family: 'Times New Roman', Times, serif !important;
    }

    /* 2. Khoảng trống phía trên */
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }

    /* 3. Tiêu đề chính */
    .main-header {
        font-size: 32px; font-weight: 900; color: #cc0000; 
        text-align: center; text-transform: uppercase;
        margin-bottom: 20px; text-shadow: 1px 1px 1px #ddd;
    }
    
    /* 4. Chữ chạy Marquee */
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

    /* 5. Tiêu đề mục (1, 2, 3) */
    .section-header {
        font-size: 20px; font-weight: bold; color: #006633;
        border-bottom: 2px solid #006633; margin-top: 20px; margin-bottom: 10px;
        padding-bottom: 5px;
    }

    /* 6. Hướng dẫn sử dụng */
    .guide-box {
        background-color: #f4fcf6; border: 1px solid #006633;
        border-radius: 5px; padding: 20px; font-size: 16px; line-height: 1.6;
    }
    
    /* 7. Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #006633; color: white; text-align: center;
        padding: 10px; font-size: 14px; z-index: 9999;
    }
    
    /* 8. Nút bấm */
    .stButton>button {
        background-color: #006633; color: white; font-size: 18px;
        border-radius: 5px; height: 50px; border: none;
    }
    .stButton>button:hover { background-color: #cc0000; }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "KEY_DU_PHONG_CUA_THAY"

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
    except: pass
    return text

def get_selected_context(folder_path, selected_files):
    """Chỉ đọc nội dung của các file được Thầy giáo chọn"""
    all_text = ""
    # Nếu không chọn file nào thì mặc định lấy hết
    files_to_read = selected_files if selected_files else [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    for file_name in files_to_read:
        full_path = os.path.join(folder_path, file_name)
        if os.path.exists(full_path):
            all_text += f"\n--- TÀI LIỆU CĂN CỨ: {file_name} ---\n{read_doc_text(full_path)}\n"
            
    return all_text

# --- 4. HÀM AI ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for p in preferred:
            if p in models: return p
        return models[0] if models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_test_v5(mon, lop, loai, context):
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Vai trò: Giáo viên dạy giỏi môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn đề kiểm tra "{loai}" CHUẨN MỰC.
    
    DỮ LIỆU ĐƯỢC GIÁO VIÊN CUNG CẤP (CHỈ DÙNG DỮ LIỆU NÀY):
    {context}
    
    YÊU CẦU NGHIÊM NGẶT:
    1. CẤU TRÚC ĐỀ: 
       - Nếu dữ liệu có "Ma trận" hoặc "Đề minh họa": Phải tuân thủ 100% cấu trúc, số lượng câu và thang điểm của tài liệu đó.
       - Nếu không có: Mặc định làm 40% Trắc nghiệm, 60% Tự luận.
    2. NỘI DUNG: Câu hỏi phải nằm trong phạm vi kiến thức của tài liệu đã cung cấp. Không bịa đặt kiến thức ngoài.
    3. HÌNH THỨC: Trình bày rõ ràng, không dùng các ký tự lạ, dùng font chữ chuẩn.
    
    KẾT QUẢ TRẢ VỀ (Markdown):
    - Phần I: MA TRẬN ĐỀ (Mô tả ngắn gọn cấu trúc đã dùng)
    - Phần II: ĐỀ BÀI (Trình bày đẹp)
    - Phần III: HƯỚNG DẪN CHẤM (Đáp án chi tiết)
    """
    return model.generate_content(prompt).text

# --- 5. GIAO DIỆN CHÍNH ---

st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)

st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH NĂM MỚI THÀNH CÔNG RỰC RỠ 🌸</div>
</div>
""", unsafe_allow_html=True)

# --- PHẦN HƯỚNG DẪN SỬ DỤNG CHI TIẾT ---
with st.expander("📖 BẤM VÀO ĐÂY ĐỂ XEM HƯỚNG DẪN SỬ DỤNG CHI TIẾT", expanded=False):
    st.markdown("""
    <div class="guide-box">
        <b>Kính chào Quý Thầy Cô và các em Học sinh!</b><br>
        Để tạo ra một đề kiểm tra chính xác, bám sát ma trận mới nhất, xin hãy thực hiện đúng theo 4 bước sau:<br><br>
        
        <b>BƯỚC 1: THIẾT LẬP THÔNG TIN (Cột bên trái)</b><br>
        - Chọn đúng <b>Cấp học</b>, <b>Lớp</b> và <b>Môn học</b> mà thầy cô muốn ra đề.<br>
        - Hệ thống sẽ tự động mở "Kho dữ liệu" tương ứng của môn học đó.<br><br>
        
        <b>BƯỚC 2: TẢI TÀI LIỆU LÊN KHO (Nếu chưa có)</b><br>
        - Thầy cô tải các file quan trọng như: <i>Ma trận đề thi năm nay, Đề minh họa, Nội dung ôn tập...</i><br>
        - <b>Lưu ý:</b> Nên đặt tên file rõ ràng (Ví dụ: <i>Ma-tran-HK2-nam-2026.docx</i>) để dễ quản lý.<br><br>
        
        <b>BƯỚC 3: CHỌN TÀI LIỆU ĐỂ RA ĐỀ (Quan trọng!)</b><br>
        - Ở cột bên phải, mục <b>"Chọn tài liệu sử dụng"</b>, thầy cô hãy tích chọn chính xác những file muốn dùng.<br>
        - <i>Ví dụ:</i> Năm nay có ma trận mới, thầy cô chỉ tích chọn file "Ma trận 2026", bỏ chọn các file cũ.<br><br>
        
        <b>BƯỚC 4: TẠO ĐỀ</b><br>
        - Chọn loại đề (15 phút, Giữa kỳ...).<br>
        - Bấm nút <b>"🚀 BẮT ĐẦU TẠO ĐỀ NGAY"</b> và chờ kết quả trong giây lát.
    </div>
    """, unsafe_allow_html=True)

# --- GIAO DIỆN CHÍNH CHIA 2 CỘT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="section-header">1. THIẾT LẬP & TẢI TÀI LIỆU</div>', unsafe_allow_html=True)
    
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ", "Khoa Học"])
    
    # Xác định đường dẫn kho
    curr_dir = get_folder_path(cap, lop, mon)
    
    st.markdown("---")
    st.info("📤 Tải thêm tài liệu mới vào kho (Word/PDF)")
    uploads = st.file_uploader("Chọn file...", accept_multiple_files=True, label_visibility="collapsed")
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.success("Đã lưu file vào kho!")

with col2:
    # Lấy danh sách file đang có trong thư mục
    files_in_dir = [f for f in os.listdir(curr_dir) if f.endswith(('.docx', '.pdf', '.txt'))]
    
    st.markdown(f'<div class="section-header">2. LỰA CHỌN TÀI LIỆU TỪ KHO ({mon} - {lop})</div>', unsafe_allow_html=True)
    
    if not files_in_dir:
        st.warning("⚠️ Kho dữ liệu đang trống. Thầy hãy tải Ma trận hoặc Giáo án lên ở cột bên trái.")
        selected_files = []
    else:
        st.write("Thầy muốn dùng tài liệu nào để ra đề? (Hãy tích chọn)")
        # --- TÍNH NĂNG MỚI: CHO PHÉP CHỌN FILE CỤ THỂ ---
        selected_files = st.multiselect(
            "Danh sách tài liệu có sẵn:",
            options=files_in_dir,
            default=files_in_dir, # Mặc định chọn hết, thầy có thể bỏ bớt
            format_func=lambda x: f"📄 {x}"
        )
        
        if len(selected_files) == 0:
            st.error("🛑 Thầy chưa chọn tài liệu nào cả! Hãy tích chọn ít nhất 1 file.")

    st.markdown('<div class="section-header">3. CẤU HÌNH & TẠO ĐỀ</div>', unsafe_allow_html=True)
    
    loai = st.selectbox("Loại đề thi", ["15 Phút", "Giữa Học Kỳ 1", "Cuối Học Kỳ 1", "Giữa Học Kỳ 2", "Cuối Học Kỳ 2"], label_visibility="collapsed")
    
    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not selected_files:
            st.error("Vui lòng chọn tài liệu trước khi tạo đề!")
        else:
            # Chỉ lấy nội dung của các file ĐƯỢC CHỌN
            context = get_selected_context(curr_dir, selected_files)
            
            with st.spinner("AI đang đọc các tài liệu thầy chọn và soạn đề..."):
                try:
                    res = generate_test_v5(mon, lop, loai, context)
                    st.session_state['kq_v5'] = res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    # Hiển thị kết quả
    if 'kq_v5' in st.session_state:
        st.markdown("---")
        st.success("✅ Đề thi đã được tạo xong:")
        st.container(
