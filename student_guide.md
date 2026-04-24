# Student Guide: The Multi-Modal Minefield Lab

## 1. Tổng quan
Chào mừng bạn đến với bài lab về **Data Pipeline Engineering**. Trong bài tập này, bạn sẽ làm việc với dữ liệu phi cấu trúc (Unstructured Data) - loại dữ liệu chiếm 80% thế giới thực nhưng cực kỳ khó xử lý.

**Mục tiêu**: Xây dựng một đường ống (Pipeline) tự động để đọc, làm sạch, kiểm tra chất lượng và hợp nhất dữ liệu từ hai nguồn: **PDF (Văn bản OCR)** và **Video (Metadata & Transcript)**.

---

## 2. Phân vai trong nhóm (Roles)
Để mô phỏng một đội ngũ kỹ sư thực tế, nhóm bạn sẽ chia thành 4 vai trò:

| Vai trò | File phụ trách | Nhiệm vụ chính |
| :--- | :--- | :--- |
| **Lead Data Architect** | `schema.py` | Thiết kế "Hợp đồng dữ liệu" chung cho cả team. |
| **ETL Builder** | `process_unstructured.py` | Viết logic chuyển đổi dữ liệu thô và làm sạch text (Regex). |
| **Observability Engineer** | `quality_check.py` | Xây dựng "Cổng kiểm soát chất lượng" (Quality Gates). |
| **DevOps Specialist** | `orchestrator.py` | Kết nối các thành phần và vận hành toàn bộ Pipeline. |

---

## 3. Hướng dẫn các bước thực hiện

### Bước 1: Chuẩn bị môi trường (Venv)
Việc sử dụng môi trường ảo giúp tránh xung đột thư viện giữa các bài tập khác nhau.

1.  **Tạo môi trường ảo**:
    ```powershell
    python -m venv .venv
    ```
2.  **Kích hoạt môi trường ảo**:
    *   **Trên Windows (PowerShell)**:
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    *   **Trên Windows (CMD)**:
        ```cmd
        .venv\Scripts\activate
        ```
    *   **Trên Mac/Linux**:
        ```bash
        source .venv/bin/activate
        ```
3.  **Cài đặt thư viện**:
    Sau khi đã kích hoạt (thấy chữ `(.venv)` ở đầu dòng lệnh), hãy chạy:
    ```bash
    pip install -r requirements.txt
    ```

### Bước 2: Thực hiện bài tập (Starter Code)
Các bạn di chuyển vào thư mục `starter_code/` và hoàn thiện các phần có đánh dấu `TODO`:

1.  **Thiết kế Schema**: Architect định nghĩa các trường dữ liệu chuẩn.
2.  **Xử lý dữ liệu**: Builder viết logic map dữ liệu từ PDF/Video sang Schema chuẩn. Đừng quên dùng Regex để xóa Header/Footer trong PDF.
3.  **Kiểm soát chất lượng**: Watchman viết logic để chặn dữ liệu rác hoặc dữ liệu có chứa mã lỗi (Toxic content).
4.  **Vận hành**: Connector viết vòng lặp để xử lý tất cả các file trong thư mục `raw_data`.

### Bước 3: Chạy và Kiểm tra
*   **Chạy Pipeline**:
    ```bash
    python starter_code/orchestrator.py
    ```
    Nếu thành công, bạn sẽ thấy file `processed_knowledge_base.json` xuất hiện ở thư mục gốc.
*   **Chạy Test tự động (Autograde)**:
    ```bash
    pytest tests/test_lab.py
    ```

---

## 4. Tiêu chí chấm điểm
*   **Execution (40%)**: Pipeline chạy trơn tru, làm sạch được nhiễu trong PDF.
*   **Observability (20%)**: Phát hiện và loại bỏ được các bản ghi lỗi (ví dụ: `doc2_corrupt.json`).
*   **Harmonization (30%)**: Không có xung đột schema (Dữ liệu từ 2 nguồn phải đồng nhất).
*   **Final Result (10%)**: File kết quả đúng định dạng JSON List.
