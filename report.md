# BÁO CÁO ĐẦY ĐỦ: The Multi-Modal Minefield Lab
**Codelab 03 — Data Pipeline Engineering: Unstructured Data Orchestration**
**Tác giả**: Trần Nhật Hoàng, Nguyễn Ngọc Thắng, Phạm Đỗ Ngọc Minh
**Ngày**: 2026-04-24
**Kết quả cuối: 100/100**

---

## Phân công trách nhiệm

- Trần Nhật Hoàng: ROLE 1 — Lead Data Architect (The Strategist), ROLE 2 — ETL/ELT Builder (The Transformation Lead)
- Nguyễn Ngọc Thắng: ROLE 3 — Observability & QA Engineer (The Watchman)
- Phạm Đỗ Ngọc Minh: ROLE 4 — DevOps & Integration Specialist (The Connector)

---

## Tóm tắt điều hành (Executive Summary)

Mục tiêu bài lab là xây dựng một pipeline tự động ingest dữ liệu phi cấu trúc từ **2 nguồn khác nhau** (PDF OCR và Video Transcript) với schema xung đột (`camelCase` vs `snake_case`), sau đó hòa giải chúng thành một **Knowledge Base thống nhất**. Thách thức cốt lõi không nằm ở Python, mà ở:

1. **Schema Harmonization** — đưa 2 "phương ngữ" dữ liệu về 1 "ngôn ngữ" chung.
2. **Semantic Observability** — phát hiện dữ liệu trông có vẻ hợp lệ (JSON valid) nhưng nội dung rác/lỗi.

Pipeline xử lý 4 file đầu vào → 2 bản ghi hợp lệ qua cổng, 2 bản ghi rác bị từ chối đúng như thiết kế.

---

## ROLE 1 — Lead Data Architect (The Strategist)
**File phụ trách:** `starter_code/schema.py`
**Nhiệm vụ:** Định nghĩa "hợp đồng dữ liệu" duy nhất mà cả team phải tuân theo.

### Quyết định thiết kế
Chọn **Pydantic BaseModel** (thay vì `dataclass` hoặc `dict`) vì 3 lý do:
- **Runtime validation**: Tự động raise `ValidationError` nếu Builder đưa dữ liệu sai kiểu.
- **Self-documenting**: Model class chính là tài liệu cho các role khác đọc.
- **JSON serialization miễn phí**: Tích hợp sẵn với `model_dump()`.

### Lựa chọn 6 trường dữ liệu

| Trường | Kiểu | Lý do AI Agent cần |
|---|---|---|
| `document_id` | `str` | Khóa định danh duy nhất cho retrieval. |
| `source_type` | `str` | Cho Agent biết "đây là PDF hay Video" để xử lý context khác nhau. |
| `author` | `str` | Attribution / độ tin cậy nguồn. |
| `category` | `str` | Phân loại domain (ML, GenAI, …) cho filter. |
| `content` | `str` | Nội dung chính để embed/search. |
| `timestamp` | `str` | Recency ranking. Dùng `str` vì dữ liệu gốc không đồng nhất format ISO. |

### Code đã triển khai
```python
class UnifiedDocument(BaseModel):
    document_id: str
    source_type: str
    author: str
    category: str
    content: str
    timestamp: str
```

### Bài học kiến trúc
- Giữ mọi trường là `str` ở giai đoạn ingest — **normalize type sau** (type coercion ở bước downstream). Nếu ép `datetime` ngay, dữ liệu `"Invalid-Date-Format"` trong `doc2_corrupt.json` sẽ crash cả pipeline thay vì bị quality gate filter gọn gàng.

---

## ROLE 2 — ETL/ELT Builder (The Transformation Lead)
**File phụ trách:** `starter_code/process_unstructured.py`
**Nhiệm vụ:** Biến JSON thô lộn xộn thành dict đúng schema của Architect.

### Thách thức: 2 "phương ngữ" phải nói cùng một ngôn ngữ

| Unified Schema | PDF key (`camelCase`) | Video key (`snake_case`) |
|---|---|---|
| `document_id` | `docId` | `video_id` |
| `source_type` | hardcode `"PDF"` | hardcode `"Video"` |
| `author` | `authorName` | `creator_name` |
| `category` | `docCategory` | `category` |
| `content` | `extractedText` (cần clean) | `transcript` |
| `timestamp` | `createdAt` | `published_timestamp` |

### Regex làm sạch nhiễu OCR (PDF)
Dữ liệu PDF có pattern lặp `HEADER_PAGE_1`, `FOOTER_PAGE_1`, … do máy OCR chèn vào. Giải quyết bằng 2 lần `re.sub`:

```python
cleaned = re.sub(r"HEADER_PAGE_\d+", "", raw_text)
cleaned = re.sub(r"FOOTER_PAGE_\d+", "", cleaned)
cleaned = cleaned.strip()
```

`\d+` thay vì hardcode `_1` để bắt được mọi số trang (PAGE_1, PAGE_12, PAGE_99, …).

### Xử lý dữ liệu thiếu (Defensive Mapping)
File `vid2_missing_tags.json` thiếu hoàn toàn `creator_name` và `transcript`. Dùng `dict.get(key, default)` để không crash:

```python
"author": raw_json.get("creator_name", "Unknown").strip(),
"content": raw_json.get("transcript", ""),
```

Trách nhiệm **từ chối** dữ liệu rỗng sẽ được đẩy sang Role 3 (Quality Gate) — đúng nguyên tắc **Separation of Concerns**: Builder map dữ liệu, Watchman quyết định hợp lệ hay không.

### Bonus: `.strip()` cho `authorName`
`doc1_messy.json` có `"Dr. AI Researcher  "` (2 khoảng trắng trailing). `.strip()` xóa khoảng trắng thừa — một dạng làm sạch nhẹ trước khi chốt dữ liệu.

---

## ROLE 3 — Observability & QA Engineer (The Watchman)
**File phụ trách:** `starter_code/quality_check.py`
**Nhiệm vụ:** Quality Gate — chặn mọi bản ghi rác không cho vào Knowledge Base.

### Chiến lược 2 tầng lọc

**Tầng 1 — Length Guard (loại bỏ nội dung rỗng/quá ngắn)**
```python
if not content or len(content) < 10:
    return False
```
Bắt được `vid2_missing_tags.json` (transcript rỗng → content `""`).
Ngưỡng 10 ký tự là *semantic minimum* — không có nội dung nào < 10 ký tự đáng giá cho một AI Agent retrieve.

**Tầng 2 — Toxic Keyword Scan (phát hiện content là thông báo lỗi của hệ thống thượng nguồn)**
```python
toxic_keywords = ["Null pointer exception", "OCR Error", "Traceback"]
for keyword in toxic_keywords:
    if keyword in content:
        return False
```
Bắt được `doc2_corrupt.json` (content = `"Null pointer exception during OCR process."`).
Đây chính là **Semantic Observability** — JSON này parse thành công (syntax OK) nhưng content thực chất là error log bị coi nhầm là văn bản. Nếu không chặn, Agent sẽ học và trả lời người dùng bằng stack trace.

### Kết quả kiểm chứng
| File | Tầng bắt | Lý do |
|---|---|---|
| `doc1_messy.json` | pass cả 2 | Hợp lệ |
| `doc2_corrupt.json` | bị tầng 2 | Chứa "Null pointer exception" |
| `vid1_metadata.json` | pass cả 2 | Hợp lệ |
| `vid2_missing_tags.json` | bị tầng 1 | transcript rỗng, len(content) = 0 |

---

## ROLE 4 — DevOps & Integration Specialist (The Connector)
**File phụ trách:** `starter_code/orchestrator.py`
**Nhiệm vụ:** Chạy pipeline end-to-end, kết nối 3 role còn lại.

### Kiến trúc Pipeline (Extract → Transform → Validate → Load)

```
┌─────────────┐   ┌───────────────────┐   ┌───────────────┐   ┌─────────┐
│ raw_data/   │→→ │ process_*_data()  │→→ │ run_semantic_ │→→ │ JSON KB │
│ *.json      │   │ (Builder)         │   │   checks()    │   │ (list)  │
└─────────────┘   └───────────────────┘   │ (Watchman)    │   └─────────┘
                                          └───────────────┘
                                               │ nếu True
                                               ↓
                                     UnifiedDocument(**d)
                                         (Architect)
```

### Vòng lặp Group A (PDFs)
```python
for file_path in pdf_files:
    raw_data = json.load(open(file_path))
    processed = process_pdf_data(raw_data)
    if run_semantic_checks(processed):
        doc = UnifiedDocument(**processed)
        final_kb.append(doc.model_dump())
```
Lý do gọi `UnifiedDocument(**processed)` ngay cả khi đã pass quality check: đây là **tầng validation cuối** — nếu Builder vô tình bỏ sót 1 trường, Pydantic raise lỗi thay vì lưu dữ liệu thiếu vào KB.

### Dùng `model_dump()` thay `.dict()`
Pydantic 2.x đã deprecate `.dict()` thay bằng `model_dump()`. `requirements.txt` yêu cầu `pydantic>=2.0.0` nên phải dùng API mới.

### Logging quan sát được
```
[FAIL] doc2_corrupt.json -> rejected by quality gate
[PASS] doc1_messy.json -> added to KB
[FAIL] vid2_missing_tags.json -> rejected by quality gate
[PASS] vid1_metadata.json -> added to KB
Pipeline finished! Saved 2 records.
```
Mỗi file đi qua đều log rõ PASS/FAIL — DevOps không chỉ chạy pipeline mà còn phải **làm cho nó quan sát được**.

---

## Kết quả kiểm thử (Autograde)

```
==================================================
AUTOMATED GRADING SUITE
==================================================

Criteria             | Points  | Status
--------------------------------------------------
Execution            | 40      | PASSED
Observability        | 20      | PASSED
Harmonization        | 30      | PASSED
Final Result         | 10      | PASSED
--------------------------------------------------
TOTAL SCORE: 100/100
==================================================
```

### Kết quả đầu ra `processed_knowledge_base.json`
2 bản ghi đã được hòa giải về 1 schema duy nhất:

```json
[
  {
    "document_id": "pdf-001",
    "source_type": "PDF",
    "author": "Dr. AI Researcher",
    "category": "Machine Learning",
    "content": "1. Introduction to Vector DBs. The quick brown fox jumps over the vector... © 2026.",
    "timestamp": "2026-04-21T09:00:00Z"
  },
  {
    "document_id": "vid_993",
    "source_type": "Video",
    "author": "Data Guru",
    "category": "ML",
    "content": "Hello and welcome. Today we discuss Data Engineering. [Music playing] It's crucial.",
    "timestamp": "2026-04-20T14:30:00"
  }
]
```

---

## Bài học rút ra

1. **Schema là hợp đồng chính trị hơn là kỹ thuật** — Architect định ra schema trước, các role khác mới có thể làm việc song song. Đó là lý do student_guide.md ghi "Builder không thể xong việc nếu Architect chưa xong Schema".
2. **Quality Gate phải chạy ở layer ngữ nghĩa, không chỉ syntax** — JSON parse xong không có nghĩa dữ liệu dùng được.
3. **Tách bạch trách nhiệm** — Builder KHÔNG tự ý drop bản ghi rỗng; nó map data và chuyển tiếp, Watchman mới quyết định drop. Điều này làm hệ thống test và debug dễ hơn nhiều.
4. **`get()` với default > `[]` access** — khi làm việc với dữ liệu phi cấu trúc, luôn giả định key có thể thiếu.
5. **Regex động (`\d+`) > regex tĩnh (`_1`)** — cho phép pipeline sống sót với file dài vài trăm trang mà không cần sửa code.
