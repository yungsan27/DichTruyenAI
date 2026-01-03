import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="AI Manga Translator Pro - Chế độ Hội thoại",
    page_icon="💬",
    layout="wide"
)

# --- 1. KHỞI TẠO SESSION STATE (Bộ nhớ tạm thời) ---
# Nơi lưu trữ lịch sử chat để AI nhớ mạch truyện và lịch sử hiển thị cho người dùng
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None # Đối tượng chat của Gemini
if "display_history" not in st.session_state:
    st.session_state.display_history = [] # Danh sách lưu [ảnh thumbnail, kết quả dịch] để hiển thị

# --- 2. SYSTEM PROMPT NÂNG CẤP CHO CHẾ ĐỘ HỘI THOẠI ---
SYSTEM_PROMPT = """
Bạn là một CHUYÊN GIA BIÊN DỊCH truyện tranh cấp cao (Senior Linguist), làm việc trong chế độ HỘI THOẠI LIÊN TỤC.

NHIỆM VỤ CỐT LÕI:
1.  Biên dịch hình ảnh truyện tranh được cung cấp sang Tiếng Việt.
2.  **QUAN TRỌNG NHẤT: GHI NHỚ BỐI CẢNH.** Bạn phải nhớ nội dung, tên nhân vật, mối quan hệ và cách xưng hô (tone & mood) từ các hình ảnh trước đó trong cùng cuộc hội thoại này để đảm bảo bản dịch liền mạch, thống nhất và không bị đứt quãng.
3.  Nếu đây là hình ảnh đầu tiên, hãy thiết lập bối cảnh. Nếu là hình ảnh tiếp theo, hãy tiếp nối câu chuyện một cách tự nhiên.

QUY TRÌNH XỬ LÝ 5 BƯỚC NGHIÊM NGẶT (Áp dụng cho mỗi ảnh):
BƯỚC 1: PHÂN TÍCH NHANH (Xác định lại bối cảnh hiện tại dựa trên các trang trước).
BƯỚC 2: TRÍCH XUẤT (Nhận diện text và các yếu tố ẩn ý liên kết với trang trước).
BƯỚC 3: DỊCH THÔ (Tín - Đạt - Nhã).
BƯỚC 4: HIỆU ĐÍNH (Đảm bảo tính thống nhất về xưng hô và thuật ngữ với các phần trước. Sử dụng từ ngữ đắt, tự nhiên).
BƯỚC 5: KẾT QUẢ (Chỉ trình bày bản dịch cuối cùng hoàn chỉnh, rõ ràng theo từng khung/bóng thoại. Không cần hiện lại các bước 1-4 để tiết kiệm không gian, trừ khi có chú thích quan trọng về sự thay đổi bối cảnh).
"""

# --- 3. SIDEBAR: Cấu hình & Quản lý bộ nhớ ---
st.sidebar.header("⚙️ Cấu hình & Công cụ")
api_key = st.sidebar.text_input("Nhập Google API Key", type="password")
st.sidebar.markdown("[Lấy API Key miễn phí](https://aistudio.google.com/app/apikey)")

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Quản lý bộ nhớ AI")
st.sidebar.info("AI đang ở chế độ nhớ mạch truyện. Nếu bắt đầu truyện mới hoặc AI bị loạn ngữ cảnh, hãy bấm nút dưới đây.")
if st.sidebar.button("🗑️ Xóa bộ nhớ & Bắt đầu lại", type="primary"):
    st.session_state.chat_session = None
    st.session_state.display_history = []
    st.rerun() # Tải lại trang ngay lập tức

# --- 4. HÀM XỬ LÝ CHÍNH ---
def initialize_chat_model(api_key):
    """Khởi tạo model và phiên chat nếu chưa có"""
    if api_key and st.session_state.chat_session is None:
        try:
            genai.configure(api_key=api_key)
            # Sử dụng system_instruction để cài đặt vai trò cốt lõi ngay từ đầu
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest", # Hoặc gemini-1.5-pro-latest nếu muốn xịn hơn (nhưng chậm hơn)
                system_instruction=SYSTEM_PROMPT
            )
            # Bắt đầu phiên chat mới với lịch sử trống
            st.session_state.chat_session = model.start_chat(history=[])
            return True
        except Exception as e:
            st.error(f"Lỗi khởi tạo API: {e}")
            return False
    return True if st.session_state.chat_session else False

# --- 5. GIAO DIỆN CHÍNH ---
st.title("💬 AI Manga Translator Pro - Chế độ Hội thoại")
st.markdown("Công cụ dịch thuật **ghi nhớ mạch truyện**. Tải lên từng trang để tiếp tục câu chuyện.")

# Khởi tạo model nếu có key
model_ready = initialize_chat_model(api_key)

if not api_key:
    st.warning("⚠️ Vui lòng nhập API Key ở cột bên trái để bắt đầu.")

# --- Khu vực tải ảnh và hiển thị kết quả hiện tại ---
col1, col2 = st.columns([1, 1.2])

uploaded_file = None
current_translation = ""

with col1:
    st.subheader("📤 Tải lên trang tiếp theo")
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Trang hiện tại", use_column_width=True)

with col2:
    st.subheader("📄 Bản dịch trang hiện tại")
    if uploaded_file is not None and model_ready:
        # Nút xử lý
        if st.button("🚀 Dịch và Tiếp nối câu chuyện", type="primary"):
            with st.spinner('Đang phân tích ảnh và đối chiếu với ngữ cảnh cũ...'):
                try:
                    # Gửi ảnh vào phiên chat hiện tại
                    response = st.session_state.chat_session.send_message(image)
                    current_translation = response.text
                    
                    # Hiển thị kết quả
                    st.markdown(current_translation)
                    
                    # Tạo thumbnail nhỏ để lưu vào lịch sử cho nhẹ
                    thumb = image.copy()
                    thumb.thumbnail((200, 200))
                    
                    # Lưu vào lịch sử hiển thị (Thêm vào đầu danh sách để cái mới nhất hiện trên cùng)
                    st.session_state.display_history.insert(0, {"img_thumb": thumb, "text": current_translation, "name": uploaded_file.name})
                    
                except Exception as e:
                    st.error(f"Có lỗi xảy ra khi dịch: {e}")
    elif uploaded_file is None:
        st.info("Vui lòng tải ảnh lên bên cột trái.")

# --- 6. KHU VỰC LỊCH SỬ (Mới) ---
st.markdown("---")
st.subheader("🕰️ Lịch sử phiên dịch (Phiên hiện tại)")
if len(st.session_state.display_history) > 0:
    # Duyệt qua lịch sử và hiển thị
    for item in st.session_state.display_history:
        with st.expander(f"Bản dịch: {item['name']} (Nhấn để mở rộng)", expanded=False):
            h_col1, h_col2 = st.columns([1, 3])
            with h_col1:
                st.image(item['img_thumb'], caption="Ảnh gốc (Thumbnail)")
            with h_col2:
                st.markdown(item['text'])
else:
    st.write("Chưa có lịch sử dịch trong phiên này.")

# --- CSS Tùy chỉnh nhẹ ---
st.markdown("""
<style>
    .stButton>button {width: 100%;}
    /* Tăng kích thước font chữ kết quả cho dễ đọc */
    .stMarkdown p { font-size: 1.1rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)