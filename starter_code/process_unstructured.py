import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================

def process_pdf_data(raw_json: dict) -> dict:
    # Bước 1: Làm sạch nhiễu (Header/Footer) khỏi văn bản
    raw_text = raw_json.get("extractedText", "")
    # TODO: Dùng re.sub để xóa 'HEADER_PAGE_X' và 'FOOTER_PAGE_X'
    cleaned_content = ""
    
    # Bước 2: Map dữ liệu thô sang định dạng chuẩn của UnifiedDocument
    # TODO: Trả về dictionary với các key: document_id, source_type, author, category, content, timestamp
    return {}

def process_video_data(raw_json: dict) -> dict:
    # TODO: Map dữ liệu thô từ Video sang định dạng chuẩn (giống PDF)
    # Lưu ý các key của Video: video_id, creator_name, transcript, category, published_timestamp
    return {}
