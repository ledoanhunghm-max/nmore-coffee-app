import streamlit as st
import json
import re
import asyncio
import edge_tts
import os
import zipfile
import io
import csv
from google import genai
from PIL import Image

# --- 1. CẤU HÌNH API KEY ---
# BẠN ĐIỀN API KEY VÀO GIỮA 2 DẤU NGOẶC KÉP Ở DÒNG DƯỚI NHÉ
API_KEY = "AIzaSyAS0Y6fh5-2LPXQ2TyLqon1wpeKRTG85TA"
client = genai.Client(api_key=API_KEY)

# --- KHỞI TẠO BỘ NHỚ SESSION STATE ---
if "project_completed" not in st.session_state:
    st.session_state.project_completed = False
    st.session_state.ket_qua_txt = ""
    st.session_state.ket_qua_csv = "" 
    st.session_state.audio_files = [] 

# --- 2. HÀM TẠO ÂM THANH TIẾNG VIỆT (GIỌNG NAM MIỀN BẮC) ---
async def generate_voice(text, output_file):
    # vi-VN-NamMinhNeural là giọng nam thanh niên chuẩn, khá năng lượng
    communicate = edge_tts.Communicate(text, "vi-VN-NamMinhNeural")
    await communicate.save(output_file)

# --- 3. HÀM TẠO KỊCH BẢN SHORTS CHO N'MORE COFFEE ---
def tao_chien_luoc_shorts(y_tuong, so_canh, danh_sach_anh_boi_canh=None, danh_sach_anh_nhan_vat=None):
    huan_luyen_ai = f"""
    VAI TRÒ: Bạn là một Chuyên gia Marketing xuất chúng cho quán cà phê "N'More Coffee", đồng thời là Đạo diễn phim hoạt hình 3D phong cách Pixar/Disney hiện đại. 
    MỤC TIÊU: Tạo ra ý tưởng video thật hấp dẫn, vui nhộn, hài hước để marketing cho quán cà phê.
    
    THÔNG TIN ĐẦU VÀO:
    - Ý tưởng cốt lõi: "{y_tuong}"
    - Số cảnh: {so_canh} cảnh.

    [QUY TẮC NGÔN NGỮ & PHONG CÁCH - SỐNG CÒN]:
    1. TOÀN BỘ CÂU LỆNH PROMPT BẮT BUỘC VIẾT BẰNG TIẾNG VIỆT 100%.
    2. Phong cách hình ảnh/video: Hoạt hình 3D Pixar/Disney hiện đại. Ánh sáng trong phim phải ấm áp, mềm mại (soft lighting).

    [QUY TẮC ĐỒNG NHẤT TỐI THƯỢNG (MÔ TẢ DÀI - KHÔNG VIẾT TẮT)]:
    1. MASTER BACKGROUND (Dựa vào ảnh bối cảnh tham chiếu nếu có): Viết MỘT ĐOẠN VĂN TIẾNG VIỆT SIÊU DÀI, CHI TIẾT mô tả không gian quán cà phê, ánh sáng ấm áp, đồ vật cố định. Không được viết tắt.
    2. MASTER CHARACTER (Dựa vào ảnh nhân vật tham chiếu nếu có): Viết MỘT ĐOẠN VĂN TIẾNG VIỆT SIÊU DÀI, CHI TIẾT mô tả khuôn mặt, màu da, kiểu tóc, và trang phục. Không được viết tắt.

    [QUY TẮC THOẠI (VOICEOVER) THEO CẢNH]:
    - Tại MỖI CẢNH QUAY, viết một câu thoại tiếng Việt ("voiceover_vietnamese") dài khoảng 15-20 từ.
    - Giọng điệu: Là giọng nam thanh niên miền Bắc trẻ tuổi năng lượng, hài hước, dí dỏm, mang phong cách hoạt hình chủ đề cà phê và sinh hoạt đời thường.

    [QUY TẮC GHÉP PROMPT CẢNH QUAY]:
    COPY VÀ DÁN Y NGUYÊN toàn bộ đoạn văn tiếng Việt của MASTER BACKGROUND và MASTER CHARACTER vào từng cảnh.

    [QUY TẮC MEDIA SẠCH (CỰC KỲ QUAN TRỌNG)]:
    - KHÔNG CÓ CHỮ, KHÔNG TEXT trong bất kỳ hình ảnh hay video nào.
    - KHÔNG CÓ TIẾNG NHẠC.
    - KHÔNG CÓ GIỌNG NÓI CỦA NHÂN VẬT, KHÔNG mấp máy môi, KHÔNG nói chuyện trong video.
    - CHỈ CÓ âm thanh hành động (SFX) trong phần mô tả âm thanh video.

    [YÊU CẦU JSON]: Trả về JSON hợp lệ, KHÔNG dùng ngoặc kép (") trong nội dung văn bản để tránh lỗi.
    
    {{
        "shorts_strategy": "Chiến lược Marketing hài hước (Tiếng Việt)",
        "master_background_long": "Đoạn văn Tiếng Việt SIÊU DÀI tả bối cảnh quán cà phê, ánh sáng ấm áp Pixar",
        "master_character_long": "Đoạn văn Tiếng Việt SIÊU DÀI tả chi tiết nhân vật",
        "scenes": [
            {{
                "scene_number": 1,
                "image_prompt": "Phong cách hoạt hình 3D Pixar/Disney hiện đại, ánh sáng ấm áp mềm mại (soft lighting). BỐI CẢNH: [DÁN Y NGUYÊN TOÀN BỘ master_background_long VÀO ĐÂY]. NHÂN VẬT: [DÁN Y NGUYÊN TOÀN BỘ master_character_long VÀO ĐÂY]. HÀNH ĐỘNG: [Mô tả chi tiết hành động vui nhộn bằng tiếng Việt]. LƯU Ý: KHÔNG CÓ CHỮ TRONG ẢNH.",
                "video_prompt": "Phong cách chuyển động 3D Pixar/Disney. BỐI CẢNH: [DÁN Y NGUYÊN TOÀN BỘ master_background_long VÀO ĐÂY]. NHÂN VẬT: [DÁN Y NGUYÊN TOÀN BỘ master_character_long VÀO ĐÂY]. HÀNH ĐỘNG: [Mô tả hành động hài hước bằng tiếng Việt]. ÂM THANH: [Mô tả âm thanh hành động SFX bằng tiếng Việt, ví dụ: tiếng rót cà phê, tiếng lạch cạch]. LƯU Ý: KHÔNG CÓ CHỮ. NHÂN VẬT KHÔNG NÓI CHUYỆN, KHÔNG MẤP MÁY MÔI.",
                "voiceover_vietnamese": "Câu thoại Tiếng Việt hài hước, năng lượng cho 8 giây cảnh này."
            }}
        ]
    }}
    """
    
    noi_dung_gui_ai = []
    if danh_sach_anh_boi_canh:
        noi_dung_gui_ai.append("Đây là các ảnh BỐI CẢNH quán cà phê tham chiếu:")
        for anh in danh_sach_anh_boi_canh: noi_dung_gui_ai.append(Image.open(anh))
        
    if danh_sach_anh_nhan_vat:
        noi_dung_gui_ai.append("Đây là các ảnh NHÂN VẬT tham chiếu:")
        for anh in danh_sach_anh_nhan_vat: noi_dung_gui_ai.append(Image.open(anh))
        
    noi_dung_gui_ai.append(huan_luyen_ai)

    response = client.models.generate_content(model='gemini-2.5-flash', contents=noi_dung_gui_ai)
    match = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise ValueError("AI gặp lỗi khi tạo JSON. Hãy thử lại!")

# --- 4. HÀM XUẤT TEXT CHUẨN ĐẦY ĐỦ ---
def xuat_text_tong_hop(du_lieu_json, y_tuong):
    txt = f"🎯 DỰ ÁN MARKETING N'MORE COFFEE: {y_tuong}\n" + "="*70 + "\n\n"
    
    txt += f"🚫 LƯU Ý NEGATIVE PROMPT CHUNG (Nhớ dán vào tool AI):\n"
    txt += "xấu xí, biến dạng, thêm ngón tay, có chữ, text, logo, đang nói chuyện, nhép môi, đổi quần áo, đổi bối cảnh mờ nhạt\n"
    txt += "="*70 + "\n\n"
    
    txt += f"📍 BỐI CẢNH XUYÊN SUỐT (MASTER BACKGROUND):\n{du_lieu_json.get('master_background_long', 'Không có dữ liệu')}\n\n"
    txt += f"🧍 NHÂN VẬT THEO BỐI CẢNH (MASTER CHARACTER):\n{du_lieu_json.get('master_character_long', 'Không có dữ liệu')}\n"
    txt += "="*70 + "\n\n"
    
    txt += "🎙️ KỊCH BẢN THU ÂM (VOICEOVER - VIETNAMESE):\n"
    for s in du_lieu_json.get('scenes', []):
        vo_text = s.get('voiceover_vietnamese', '')
        if vo_text:
            txt += f"{vo_text}\n"
    txt += "\n" + "="*70 + "\n\n"
    
    for s in du_lieu_json.get('scenes', []):
        txt += f"🎬 CẢNH {s['scene_number']} (Thời lượng 8s)\n"
        txt += f"🗣️ Voiceover Cảnh {s['scene_number']}: {s.get('voiceover_vietnamese', '')}\n\n"
        txt += f"🖼️ IMAGE PROMPT:\n{s['image_prompt']}\n\n🎥 VIDEO PROMPT:\n{s['video_prompt']}\n" + "-"*70 + "\n\n"
    return txt

# --- HÀM TẠO FILE CSV CHO AUTOMA BOT ---
def tao_csv_cho_automa(du_lieu_json):
    output = io.StringIO()
    output.write('\ufeff') 
    writer = csv.writer(output)
    writer.writerow(['Image_Prompt', 'Video_Prompt'])
    for s in du_lieu_json.get('scenes', []):
        writer.writerow([s.get('image_prompt', ''), s.get('video_prompt', '')])
    return output.getvalue()

# --- 5. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="N'More Coffee Marketing", page_icon="☕", layout="wide")

if not st.session_state.project_completed:
    st.title("☕ AUTO PROMPT FOR N'MORE COFFEE MARKETING")
    
    col_in1, col_in2 = st.columns([2, 1])
    with col_in1:
        y_tuong_input = st.text_area("💡 1. Ý tưởng video:", height=120)
        danh_sach_anh_boi_canh = st.file_uploader("📍 2. Tải ảnh bối cảnh tham chiếu (Nhiều ảnh):", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        
        # Hiển thị ảnh bối cảnh xem trước
        if danh_sach_anh_boi_canh:
            cols_bc = st.columns(min(len(danh_sach_anh_boi_canh), 5))
            for i, anh in enumerate(danh_sach_anh_boi_canh):
                with cols_bc[i % 5]: st.image(anh, use_container_width=True)
                
    with col_in2:
        so_canh_input = st.number_input("🎞️ 3. Số cảnh quay:", min_value=1, max_value=20, value=5)
        danh_sach_anh_nhan_vat = st.file_uploader("🖼️ 4. Tải ảnh nhân vật tham chiếu (Nhiều ảnh):", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        
        # Hiển thị ảnh nhân vật xem trước
        if danh_sach_anh_nhan_vat:
            cols_nv = st.columns(min(len(danh_sach_anh_nhan_vat), 3))
            for i, anh in enumerate(danh_sach_anh_nhan_vat):
                with cols_nv[i % 3]: st.image(anh, use_container_width=True)

    st.divider()
    if st.button("🚀 Sản Xuất Kịch Bản & Voiceover", type="primary", use_container_width=True):
        if not y_tuong_input:
            st.warning("Vui lòng nhập ý tưởng!")
        elif API_KEY == "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
            st.error("Chưa có API Key! Vui lòng điền Key vào dòng 16 trong mã nguồn.")
        else:
            with st.spinner("⏳ Đang xử lý kịch bản N'More Coffee, thu âm giọng nam miền Bắc..."):
                try:
                    ket_qua = tao_chien_luoc_shorts(y_tuong_input, so_canh_input, danh_sach_anh_boi_canh, danh_sach_anh_nhan_vat)
                    
                    st.session_state.ket_qua_txt = xuat_text_tong_hop(ket_qua, y_tuong_input)
                    st.session_state.ket_qua_csv = tao_csv_cho_automa(ket_qua)
                    st.session_state.audio_files = []
                    
                    full_voiceover_text = ""
                    for s in ket_qua.get('scenes', []):
                        full_voiceover_text += s.get('voiceover_vietnamese', '') + " "
                        
                    full_voiceover_text = full_voiceover_text.strip().replace("'", "")
                    
                    if full_voiceover_text:
                        audio_file = "voice_temp_full.mp3"
                        asyncio.run(generate_voice(full_voiceover_text, audio_file))
                        with open(audio_file, "rb") as f:
                            audio_data = f.read()
                        os.remove(audio_file) 
                        st.session_state.audio_files.append({
                            "name": "Giọng Nam Miền Bắc Năng Lượng (Full Video)", 
                            "data": audio_data, 
                            "filename": "Voiceover_VN_Male.mp3"
                        })
                    
                    st.session_state.project_completed = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Lỗi: {e}.")

else:
    st.title("✅ Dự Án Đã Hoàn Thành!")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("Kich_Ban_va_Prompts_NMore.txt", st.session_state.ket_qua_txt)
        zip_file.writestr("Data_Prompts_Automa.csv", st.session_state.ket_qua_csv)
        for audio in st.session_state.audio_files:
            zip_file.writestr(audio['filename'], audio['data'])
    
    st.success("Tất cả dữ liệu đã được đóng gói! Bạn có thể tải về để nạp vào tool Auto.")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.download_button(
            label="📦 TẢI TOÀN BỘ DỰ ÁN (.ZIP)", 
            data=zip_buffer.getvalue(), 
            file_name="NMore_Coffee_Marketing.zip", 
            mime="application/zip", 
            use_container_width=True,
            type="primary"
        )
    with col_btn2:
        if st.button("🔄 Bắt Đầu Dự Án Mới (New Project)", use_container_width=True):
            st.session_state.project_completed = False
            st.session_state.ket_qua_txt = ""
            st.session_state.ket_qua_csv = ""
            st.session_state.audio_files = []
            st.rerun()
            
    st.divider()

    col_res1, col_res2 = st.columns([1, 1.5])
    with col_res1:
        st.subheader("🔊 Nghe thử Voiceover Tiếng Việt")
        if len(st.session_state.audio_files) > 0:
            for audio in st.session_state.audio_files:
                st.markdown(f"**{audio['name']}**")
                st.audio(audio['data'], format="audio/mp3")
        else:
            st.warning("⚠️ Không có lời thoại nào được sinh ra.")

    with col_res2:
        st.subheader("📝 Kịch Bản & Prompts (Pixar Style)")
        st.text_area("Kết quả chi tiết:", st.session_state.ket_qua_txt, height=600)