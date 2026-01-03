import streamlit as st
import google.generativeai as genai
from PIL import Image

# Cấu hình giao diện
st.set_page_config(page_title="AI Dịch Truyện - Senior Linguist", page_icon="📚", layout="wide")

# Thiết lập thanh bên
st.sidebar.header("Cấu hình API")
api_key = st.sidebar.text_input("Dán API Key vào đây:", type="password")
st.sidebar.info("Lấy Key tại: aistudio.google.com")

# PROMPT CHUYÊN GIA BIÊN DỊCH (Đừng sửa phần này nếu không hiểu rõ)
SYSTEM_PROMPT = """
Bạn là một CHUYÊN GIA BIÊN DỊCH ngôn ngữ cấp cao (Senior Linguist), phong cách: Tự nhiên, Tinh tế, Thoát ý.
Nhiệm vụ: Xử lý văn bản trong ảnh truyện tranh theo quy trình 5 bước:

BƯỚC 1: PHÂN TÍCH (Ngôn ngữ gốc, thể loại, tone giọng).
BƯỚC 2: TRÍCH XUẤT (Lấy text gốc, giải thích thuật ngữ/ẩn ý).
BƯỚC 3: DỊCH THÔ (Tín - Đạt - Nhã, chuyển đổi cấu trúc câu mượt mà).
BƯỚC 4: HIỆU ĐÍNH (Dùng từ ngữ "đắt", Hán Việt hoặc khẩu ngữ phù hợp, tránh văn dịch).
BƯỚC 5: KẾT QUẢ (Trình bày bản dịch cuối cùng rõ ràng theo từng khung tranh).
"""

def translate_image(image, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('models/gemini-3-flash-preview') # Model nhanh và xử lý ảnh tốt
    try:
        response = model.generate_content([SYSTEM_PROMPT, image])
        return response.text
    except Exception as e:
        return f"Lỗi: {str(e)}"

# Giao diện chính
st.title("📚 AI Manga Translator - Senior Linguist")
st.write("Công cụ dịch thuật chuyên sâu theo quy trình 5 bước.")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Tải ảnh truyện lên (PNG/JPG)...", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh gốc", use_column_width=True)
        if st.button("🚀 BẮT ĐẦU DỊCH", type="primary"):
            if not api_key:
                st.error("⚠️ Bạn chưa nhập API Key bên tay trái!")
            else:
                with st.spinner("Chuyên gia đang phân tích và dịch thuật..."):
                    st.session_state.result = translate_image(image, api_key)

with col2:
    st.header("Kết quả dịch thuật")
    if 'result' in st.session_state:
        st.markdown(st.session_state.result)
    else:
        st.info("Kết quả sẽ hiện ở đây.")