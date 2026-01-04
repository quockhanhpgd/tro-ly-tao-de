import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    layout="wide", 
    page_title="Tạo Đề Thi 2026 - Thầy Khánh",
    page_icon="🎆"
)

# CSS TÙY CHỈNH (GIAO DIỆN TẾT & CĂN CHỈNH)
st.markdown("""
<style>
    /* Khoảng trống phía trên */
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }

    /* Tiêu đề chính */
    .main-header {
        font-size: 32px; font-weight: 900; color: #D42426; 
        text-align: center; text-transform: uppercase;
        text-shadow: 1px 1px 0px #FFD700; margin-bottom: 10px;
    }
    
    /* Chữ chạy Marquee */
    .marquee-container {
        width: 100%; overflow: hidden; background: linear-gradient(90deg, #fff0f0, #ffecec);
        border-top: 2px solid #D42426; border-bottom: 2px solid #D42426;
        padding: 8px 0; margin-bottom: 20px;
    }
    .marquee-text {
        font-size: 18px; font-weight: bold; color: #ce0000;
        white-space: nowrap; animation: marquee 20s linear infinite;
    }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* Hướng dẫn sử dụng */
    .guide-box {
        background-color: #f8f9fa; border: 1px solid #146B3A;
        border-radius: 8px; padding: 15px; font-size: 16px; line-height: 1.6;
    }
    .guide-step { font-weight: bold; color: #146B3A; }

    /* Footer & Button */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0d5e38; color: white; text-align: center;
        padding: 10px; font-size: 13px; font-weight: bold;
        z-index: 9999; border-top: 3px solid #FFD700;
    }
    .stButton>button {
        background-color: #0d5e38; color: white; border-radius: 8px; font-weight: bold; height: 3em;
    }
    .stButton>button:hover {
        background-color: #D42426; color: #FFD700; border-color: #FFD700;
    }
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

def get_all_context(folder_path):
    all_text = ""
    files = [f for f in os.listdir(folder_path) if f.endswith(('.docx', '.pdf', '.txt'))]
    for file_name in files:
        full_path = os.path.join(folder_path, file_name)
        # Đánh dấu rõ tên file để AI biết đâu là Ma trận, đâu là Đề mẫu
        all_text += f"\n--- TÊN TÀI LIỆU: {file_name} ---\n{read_doc_text(full_path)}\n"
    return all_text, files

# --- 4. HÀM AI THÔNG MINH (LOGIC MỚI) ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for p in preferred:
            if p in models: return p
        return models[0] if models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_test_strict(mon, lop, loai, context):
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)
    
    # PROMPT MỚI: Yêu cầu tuân thủ Ma trận và Mẫu đề
    prompt = f"""
    Vai trò: Chuyên gia biên soạn đề thi môn {mon} lớp {lop}.
    Nhiệm vụ: Soạn thảo đề kiểm tra "{loai}" CHẤT LƯỢNG CAO.
    
    DỮ LIỆU ĐẦU VÀO (QUAN TRỌNG):
    {context}
    
    YÊU CẦU XỬ LÝ (TUÂN THỦ TUYỆT ĐỐI):
    1. PHÂN TÍCH MA TRẬN: Hãy tìm trong dữ liệu trên xem có file nào chứa bảng "Ma trận" hoặc "Đặc tả" không.
       - Nếu CÓ: Bạn PHẢI tuân thủ chính xác số lượng câu hỏi, mức độ nhận thức (Nhận biết/Thông hiểu/Vận dụng) và điểm số quy định trong ma trận đó.
       - Không được tự ý thay đổi cấu trúc nếu ma trận đã quy định.
       
    2. PHÂN TÍCH MẪU ĐỀ: Hãy tìm xem có file nào là "Đề mẫu" hoặc "Đề cũ" không.
       - Nếu CÓ: Hãy bắt chước phong cách trình bày, cách đặt câu hỏi, font chữ, cách chia phần (Trắc nghiệm/Tự luận) y hệt như mẫu.
       
    3. NẾU KHÔNG CÓ MA TRẬN/MẪU:
       - Mới được dùng cấu trúc mặc định: 40% Trắc nghiệm (Khoảng 4-6 câu), 60% Tự luận/Thực hành.
       
    4. ĐẦU RA YÊU CẦU:
       - Phần 1: Ma trận đề (Tóm tắt lại cấu trúc bạn đã dùng).
       - Phần 2: Đề bài chi tiết (Trình bày đẹp, rõ ràng).
       - Phần 3: Hướng dẫn chấm và Biểu điểm chi tiết.
    """
    
    return model.generate_content(prompt).text

# --- 5. GIAO DIỆN CHÍNH ---

st.markdown('<div class="main-header">ỨNG DỤNG TẠO ĐỀ KIỂM TRA THÔNG MINH</div>', unsafe_allow_html=True)

st.markdown("""
<div class="marquee-container">
    <div class="marquee-text">🌸 CUNG CHÚC TÂN XUÂN CHÀO NĂM BÍNH NGỌ 2026 - CHÚC QUÝ THẦY CÔ VÀ CÁC EM HỌC SINH MỘT NĂM MỚI AN KHANG THỊNH VƯỢNG 🌸</div>
</div>
""", unsafe_allow_html=True)

# HƯỚNG DẪN SỬ DỤNG CHI TIẾT (ĐÃ NÂNG CẤP)
with st.expander("📖 HƯỚNG DẪN SỬ DỤNG CHI TIẾT (Dành cho Giáo viên & Học sinh)", expanded=False):
    st.markdown("""
    <div class="guide-box">
        <p class="guide-step">BƯỚC 1: CHUẨN BỊ TÀI LIỆU</p>
        <ul>
            <li>Thầy cô cần chuẩn bị sẵn các file Word hoặc PDF.</li>
            <li><b>Mẹo quan trọng:</b> Hãy đặt tên file rõ ràng để Trợ lý ảo hiểu. Ví dụ: "Ma tran de thi giua ky 1.docx", "De thi mau nam ngoai.pdf", "Noi dung bai hoc.docx".</li>
        </ul>
        <p class="guide-step">BƯỚC 2: TẢI TÀI LIỆU LÊN KHO</p>
        <ul>
            <li>Chọn đúng Cấp học, Lớp và Môn học ở cột bên trái.</li>
            <li>Kéo thả các file đã chuẩn bị vào ô "Upload". Hệ thống sẽ tự động lưu vào kho dữ liệu.</li>
        </ul>
        <p class="guide-step">BƯỚC 3: RA LỆNH TẠO ĐỀ</p>
        <ul>
            <li>Chọn loại đề kiểm tra (15 phút, 1 tiết, học kì...).</li>
            <li>Nhấn nút <b>"🚀 BẮT ĐẦU TẠO ĐỀ NGAY"</b>.</li>
            <li>Trợ lý ảo sẽ đọc Ma trận của Thầy cô và tạo ra đề thi bám sát cấu trúc đó.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 1️⃣ Thiết lập & Dữ liệu")
    cap = st.selectbox("Cấp học", ["Tiểu Học", "THCS", "THPT"])
    lop = st.selectbox("Lớp", [f"Lớp {i}" for i in range(1, 13)], index=2)
    mon = st.selectbox("Môn học", ["Tin học", "Toán", "Tiếng Việt", "Công Nghệ"])
    
    curr_dir = get_folder_path(cap, lop, mon)
    
    st.markdown("---")
    st.caption("Tải Ma trận, Đề mẫu, Giáo án (Word/PDF)")
    uploads = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")
    if uploads:
        for f in uploads: save_uploaded_file(f, curr_dir)
        st.toast("Đã lưu tài liệu vào kho!", icon="✅")

with col2:
    context, files = get_all_context(curr_dir)
    st.markdown(f"### 2️⃣ Kho dữ liệu: {mon} - {lop} ({len(files)} file)")
    
    with st.container(height=150, border=True):
        if files:
            for f in files: 
                # Thêm icon để phân biệt loại file
                icon = "📏" if "ma tran" in f.lower() else "📝" if "de" in f.lower() else "📄"
                st.text(f"{icon} {f}")
        else: st.warning("Kho trống. Hãy tải Ma trận và Đề mẫu lên nhé.")

    st.markdown("### 3️⃣ Cấu hình & Tạo đề")
    loai = st.selectbox("Loại đề", ["15 Phút", "Giữa Kỳ 1", "Cuối Kỳ 1", "Giữa Kỳ 2", "Cuối Kỳ 2"], label_visibility="collapsed")
    
    st.write("")
    if st.button("🚀 BẮT ĐẦU TẠO ĐỀ NGAY"):
        if not context:
            st.error("Chưa có dữ liệu! Vui lòng tải Ma trận hoặc Giáo án lên.")
        else:
            with st.spinner("Đang phân tích Ma trận và Đề mẫu..."):
                try:
                    # Gọi hàm tạo đề với logic "Strict" (Nghiêm ngặt)
                    res = generate_test_strict(mon, lop, loai, context)
                    st.session_state['kq_strict'] = res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if 'kq_strict' in st.session_state:
        st.markdown("---")
        st.container(border=True).markdown(st.session_state['kq_strict'])

# --- FOOTER ---
st.markdown("""
<div class="footer">
    Ứng dụng tạo đề kiểm tra được tạo bởi thầy Phan Quốc Khánh và trợ lý ảo Gemini - trường Tiểu học Hua Nguống.<br>
    Số điện thoại: 0389655141
</div>
""", unsafe_allow_html=True)
