import pytest
import sys
import os
import json

# Path setup: Thêm starter_code vào hệ thống để có thể import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'starter_code'))

# Thử import các hàm của học viên
try:
    from schema import UnifiedDocument
    from process_unstructured import process_pdf_data, process_video_data
    from quality_check import run_semantic_checks
except ImportError as e:
    # Nếu học viên chưa viết code hoặc sai tên file/hàm
    pass

# ==========================================
# CRITERIA 1: EXECUTION (40 Points)
# Kiểm tra khả năng xử lý/parse dữ liệu thô
# ==========================================

def test_execution_pdf_parsing():
    """Kiểm tra việc parse dữ liệu PDF thô"""
    raw_pdf = {
        "docId": "p1", 
        "extractedText": "HEADER_PAGE_1 Valid Content Here FOOTER_PAGE_1", 
        "docCategory": "A", 
        "createdAt": "2024"
    }
    result = process_pdf_data(raw_pdf)
    assert result["document_id"] == "p1"
    assert result["source_type"] == "PDF"
    # Kiểm tra xem đã làm sạch Header/Footer chưa
    assert "HEADER" not in result["content"]

def test_execution_video_parsing():
    """Kiểm tra việc parse dữ liệu Video thô"""
    raw_vid = {
        "video_id": "v1", 
        "transcript": "Valid Video Speech Content", 
        "category": "B", 
        "published_timestamp": "2024"
    }
    result = process_video_data(raw_vid)
    assert result["document_id"] == "v1"
    assert result["source_type"] == "Video"

# ==========================================
# CRITERIA 2: OBSERVABILITY (20 Points)
# Kiểm tra bộ lọc Quality Gates (Watchman Role)
# ==========================================

def test_observability_catch_toxic():
    """Phải bắt được lỗi Null pointer (Trả về False)"""
    toxic_data = {"content": "Critical Error: Null pointer exception found"}
    assert run_semantic_checks(toxic_data) == False

def test_observability_catch_short_content():
    """Phải bắt được nội dung quá ngắn"""
    short_data = {"content": "short"}
    assert run_semantic_checks(short_data) == False

# ==========================================
# CRITERIA 3: HARMONIZATION (30 Points)
# Kiểm tra việc hợp nhất dữ liệu về 1 Schema duy nhất (Không xung đột)
# ==========================================

def test_harmonization_schema_conformity():
    """Cả 2 nguồn dữ liệu sau khi xử lý phải khớp hoàn toàn với UnifiedDocument"""
    pdf_processed = process_pdf_data({
        "docId": "p1", "extractedText": "Valid content length", 
        "docCategory": "A", "createdAt": "2024"
    })
    vid_processed = process_video_data({
        "video_id": "v1", "transcript": "Valid content length", 
        "category": "B", "published_timestamp": "2024"
    })
    
    # Kiểm tra xem có tạo được Object từ Pydantic không (Kiểm tra Schema)
    doc_pdf = UnifiedDocument(**pdf_processed)
    doc_vid = UnifiedDocument(**vid_processed)
    
    assert doc_pdf.source_type == "PDF"
    assert doc_vid.source_type == "Video"

# ==========================================
# CRITERIA 4: FINAL RESULT (10 Points)
# Kiểm tra file output cuối cùng
# ==========================================

def test_final_output_structure():
    """Kiểm tra cấu trúc file processed_knowledge_base.json"""
    output_path = os.path.join(os.path.dirname(__file__), '..', 'processed_knowledge_base.json')
    
    # Nếu file không tồn tại, test này sẽ tạch 10đ cuối
    assert os.path.exists(output_path), "File processed_knowledge_base.json chưa được tạo!"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
        assert isinstance(data, list), "Dữ liệu lưu vào file phải là một danh sách (List)"
        if len(data) > 0:
            # Kiểm tra bản ghi đầu tiên có đúng schema không
            UnifiedDocument(**data[0])

def calculate_grade():
    print("\n" + "="*50)
    print("AUTOMATED GRADING SUITE")
    print("="*50)
    
    score = 0
    results = {}

    # Criteria 1: Execution (40 Points)
    try:
        test_execution_pdf_parsing()
        test_execution_video_parsing()
        results["Execution"] = (40, "PASSED")
        score += 40
    except Exception as e:
        results["Execution"] = (40, f"FAILED")

    # Criteria 2: Observability (20 Points)
    try:
        test_observability_catch_toxic()
        test_observability_catch_short_content()
        results["Observability"] = (20, "PASSED")
        score += 20
    except Exception as e:
        results["Observability"] = (20, f"FAILED")

    # Criteria 3: Harmonization (30 Points)
    try:
        test_harmonization_schema_conformity()
        results["Harmonization"] = (30, "PASSED")
        score += 30
    except Exception as e:
        results["Harmonization"] = (30, f"FAILED")

    # Criteria 4: Final Result (10 Points)
    # Force fail if all other core logic failed
    all_core_failed = all(results[k][1] == "FAILED" for k in ["Execution", "Observability", "Harmonization"])
    
    try:
        if all_core_failed:
            raise Exception("Final result is not accepted since the core logic failed.")
        test_final_output_structure()
        results["Final Result"] = (10, "PASSED")
        score += 10
    except Exception as e:
        results["Final Result"] = (10, f"FAILED")

    print(f"\n{'Criteria':<20} | {'Points':<7} | {'Status'}")
    print("-" * 50)
    for crit in ["Execution", "Observability", "Harmonization", "Final Result"]:
        pts, res = results[crit]
        print(f"{crit:<20} | {pts:<7} | {res}")
    
    print("-" * 50)
    print(f"TOTAL SCORE: {score}/100")
    print("="*50 + "\n")

if __name__ == "__main__":
    calculate_grade()
