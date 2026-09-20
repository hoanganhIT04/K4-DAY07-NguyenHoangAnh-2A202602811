# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** ABU
**Thành viên:** Nguyễn Hà Khuê, Nguyễn Hoàng Anh, Nguyễn Huy Hoàng
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Trả hàng/Hoàn tiền của Shopee Việt Nam (thương mại điện tử — biến thể K4-L3B)

**Tại sao nhóm chọn chủ đề này?**
> Chính sách trả hàng/hoàn tiền là domain có cấu trúc rõ ràng (điều kiện, quy trình, thời hạn, phí) nhưng phân bố dài/không đồng đều giữa các tài liệu, phù hợp để so sánh các chiến lược chunking. Nguồn Shopee Help Center là công khai, tiếng Việt, có ngày hiệu lực rõ ràng và đủ 9 tài liệu (cả hướng người mua và người bán) để xây dựng knowledge base có thể kiểm chứng.

### Danh mục tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / effective-2026-03-11 | 19,444 | audience=both, category=returns-policy, language=vi |
| 2 | Quy định chung về trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | 6,032 | audience=buyer, category=returns-policy, language=vi |
| 3 | Quy trình xử lý yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/190242 | 2026-09-20 / not-stated | 7,816 | audience=buyer, category=refund-process, language=vi |
| 4 | Hướng dẫn gửi yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/79233 | 2026-09-20 / not-stated | 2,217 | audience=buyer, category=return-request, language=vi |
| 5 | Các phương thức gửi hàng hoàn trả và phí hoàn trả | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / not-stated | 5,650 | audience=buyer, category=return-shipping, language=vi |
| 6 | Thời gian nhận tiền hoàn | https://help.shopee.vn/portal/4/article/189473 | 2026-09-20 / not-stated | 3,614 | audience=buyer, category=refund-process, language=vi |
| 7 | Hướng dẫn chuẩn bị bằng chứng trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/79467 | 2026-09-20 / not-stated | 3,152 | audience=buyer, category=return-evidence, language=vi |
| 8 | Quy trình Trả hàng/Hoàn tiền trên Shopee dành cho Người bán | https://banhang.shopee.vn/edu/article/563 | 2026-09-20 / published-2026-08-20 | 7,539 | audience=seller, category=refund-process, language=vi |
| 9 | Cập nhật Quy trình xử lý yêu cầu Trả hàng/Hoàn tiền dành cho Người bán thuộc Shopee Mall | https://banhang.shopee.vn/edu/article/22227 | 2026-09-20 / published-2025-09-22 | 6,783 | audience=seller, category=refund-process, language=vi |

Tổng: 9 tài liệu, ~62,200 ký tự. Manifest truy vết nguồn: `data/ecommerce/sources.csv`. Corpus gồm 6 tài liệu hướng người mua (buyer), 2 tài liệu hướng người bán (seller), 1 tài liệu chung (both) — cho phép so sánh truy xuất có/không có bộ lọc `audience`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| doc_id | str | `shopee-return-refund-policy` | Định danh ổn định để truy vết câu trả lời về tài liệu gốc và xóa/cập nhật tài liệu |
| source_url | str | `https://help.shopee.vn/portal/4/article/77251` | Kiểm chứng câu trả lời và truy vết nguồn |
| retrieved_at | str (ISO date) | `2026-09-20` | Đánh giá độ mới của dữ liệu so với chính sách hiện hành |
| document_version | str | `effective-2026-03-11` | Biết chính sách đang dùng phiên bản hiệu lực nào, tránh trả lời theo phiên bản cũ |
| audience | str | `buyer` / `seller` / `both` | Lọc truy vấn theo đối tượng (người mua vs người bán) — bắt buộc theo K4_VARIANT |
| category | str | `refund-process`, `returns-policy` | Thu hẹp vùng tìm kiếm theo chủ đề của câu hỏi |
| language | str | `vi` | Lọc theo ngôn ngữ khi corpus đa ngôn ngữ |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(chunk_size=500)` trên 3 tài liệu đại diện (dài / có bảng / ngắn):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee-return-refund-policy (19,444 ký tự) | FixedSizeChunker (`fixed_size`) | 44 | 491 | Kém — cắt ngang điều khoản, ranh giới chunk rơi giữa câu |
| shopee-return-refund-policy (19,444 ký tự) | SentenceChunker (`by_sentences`) | 47 | 410 | Khá — không cắt giữa câu nhưng trộn lẫn các điều khoản khác nhau vào 1 chunk |
| shopee-return-refund-policy (19,444 ký tự) | RecursiveChunker (`recursive`) | 60 | 322 | Khá — tách theo `\n\n` nên bám sát cấu trúc mục hơn 2 chiến lược trên |
| shopee-return-shipping (5,650 ký tự, nhiều bảng) | FixedSizeChunker (`fixed_size`) | 13 | 481 | Kém — các bảng hoàn tiền/bảng phí bị cắt đôi giữa 2 chunk |
| shopee-return-shipping (5,650 ký tự, nhiều bảng) | SentenceChunker (`by_sentences`) | 9 | 625 | Kém — các ô của bảng bị coi là "câu" và trộn lẫn với nội dung mục khác |
| shopee-return-shipping (5,650 ký tự, nhiều bảng) | RecursiveChunker (`recursive`) | 13 | 433 | Trung bình — bảng còn nguyên hơn nhưng không biết ranh giới mục/tiêu đề |
| shopee-return-refund-request (2,217 ký tự) | FixedSizeChunker (`fixed_size`) | 5 | 483 | Trung bình |
| shopee-return-refund-request (2,217 ký tự) | SentenceChunker (`by_sentences`) | 7 | 311 | Khá |
| shopee-return-refund-request (2,217 ký tự) | RecursiveChunker (`recursive`) | 5 | 441 | Khá — gần với ranh giới mục tự nhiên |

**Nhận xét baseline:** cả 3 chiến lược đều "mù" về cấu trúc tài liệu — không chiến lược nào nhận diện được heading của điều khoản hay giữ bảng nguyên vẹn. Với domain chính sách (mỗi mục là một quy tắc độc lập), đây là điểm yếu lớn nhất.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Hà Khuê**
- **Loại chiến lược:** Custom — `HeadingChunker` (chunking theo heading/section)
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách Shopee có cấu trúc điều khoản rõ ràng (Điều 1, 2, 3...; mục 1.1, 1.2...) và nhiều bảng quy định — mỗi mục là một quy tắc độc lập. `HeadingChunker` tách tài liệu theo heading markdown, KHÔNG cắt giữa bảng (bảng "Thời gian hoàn tiền", "Điểm khác biệt" luôn nguyên vẹn trong 1 chunk), và prefix tiêu đề mục vào mỗi chunk để embedding mang đủ ngữ cảnh. Khi benchmark, chiến lược này sửa được lỗi Q4 (agent trả lời lệch → khớp gold answer) và đưa chunk đúng của Q2 lên top-1, trong khi chunking theo ký tự để lại lỗi "top-1 sai, top-3 cứu" ở Q1/Q2.
- **Code snippet (nếu custom):** xem đầy đủ trong `scripts/benchmark_queries.py`
```python
class HeadingChunker:
    """Tách theo heading markdown; không cắt giữa bảng; prefix heading vào chunk."""
    def __init__(self, max_chars: int = 1200):
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        sections = []                       # tách theo dòng bắt đầu bằng '#'
        current = []
        for line in text.split("\n"):
            if line.startswith("#") and current:
                sections.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append("\n".join(current).strip())

        chunks, heading = [], ""
        for section in sections:
            lines = section.split("\n")
            if lines and lines[0].startswith("#"):
                heading = lines[0].lstrip("#").strip()
            if len(section) <= self.max_chars:
                chunks.append(f"[{heading}]\n{section}" if heading else section)
                continue
            buffer, size = [], 0            # gộp đoạn, không cắt giữa bảng markdown
            for para in section.split("\n\n"):
                is_table_row = para.lstrip().startswith("|")
                in_table = bool(buffer) and buffer[-1].lstrip().startswith("|")
                if size + len(para) + 2 > self.max_chars and buffer and not (is_table_row and in_table):
                    body = "\n\n".join(buffer)
                    chunks.append(f"[{heading}]\n{body}" if heading else body)
                    buffer, size = [], 0
                buffer.append(para)
                size += len(para) + 2
            if buffer:
                body = "\n\n".join(buffer)
                chunks.append(f"[{heading}]\n{body}" if heading else body)
        return [c for c in chunks if c.strip()] or self._fallback.chunk(text)
```

**Thành viên 2 — Nguyễn Hoàng Anh**
- **Loại chiến lược:** Recursive
- **Mô tả & lý do chọn:** Sử dụng `RecursiveChunker` với `chunk_size=500` để chia tài liệu theo cấu trúc từ lớn đến nhỏ, ưu tiên giữ các đoạn văn và câu có liên quan trong cùng một chunk. Chiến lược này phù hợp với tài liệu chính sách Shopee vì nội dung có nhiều mục, tiểu mục, danh sách và các điều kiện quan trọng như thời hạn, mức phí và đối tượng áp dụng.
- **Code snippet (nếu custom):**

**Thành viên 3 — Nguyễn Huy Hoàng**
- **Loại chiến lược:** SentenceChunker
- **Mô tả & lý do chọn:** Tôi chia văn bản theo dấu kết thúc câu rồi gom tối đa 3 câu thành một chunk nhằm hạn chế cắt ngang câu và giữ các ý gần nhau. Chiến lược tạo ra 131 chunk trong lần benchmark này, tìm được thông tin liên quan cho cả 5 câu hỏi trong top-3. Tuy nhiên, các yêu cầu và điều kiện nằm ở nhiều câu có thể bị chia rời, khiến kết quả chưa đủ ý như câu 3 và câu 5.
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Hà Khuê | Custom `HeadingChunker` | 9 | Giữ nguyên bảng quy định; chunk mang ngữ cảnh heading; Q4 khớp gold answer cả 2 phần sau khi fix | Phụ thuộc format markdown gốc; mục rất dài vẫn phải cắt theo đoạn |
| Nguyễn Hoàng Anh | Recursive | 8 | Chia chunk theo cấu trúc đệ quy; Top-3 truy xuất được nội dung liên quan ở 4/5 câu, bao gồm Q1, Q2, Q3 và Q5 |Q4 chưa truy xuất được đúng nội dung về thời hạn khiếu nại và bằng chứng; một số câu có Top-1 chưa liên quan nhưng chunk đúng xuất hiện ở Top-2/Top-3 |
|  Nguyễn Huy Hoàng | SentenceChunker | 8 | Top-3 có thông tin liên quan ở 5/5 câu; câu 2 lấy được cả ngoại lệ thời hạn | Câu 3 thiếu yêu cầu chất lượng và giới hạn video; câu 5 thiếu thời gian hoàn phí và mức Xu |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với domain chính sách/các quy định, chunking theo heading/section là tốt nhất. Lý do: (1) mỗi mục của chính sách là một quy tắc độc lập với thời hạn/điều kiện riêng — tách đúng ranh giới mục giúp một chunk chứa trọn vẹn một quy tắc, tránh trả lời ghép nhầm điều kiện của mục khác; (2) các bảng quy định (thời gian hoàn tiền, phí trả hàng, bảng so sánh trước/sau) chứa câu trả lời dạng số liệu nhưng bị cắt làm hỏng ngữ nghĩa khi chunk theo ký tự — giữ nguyên bảng cộng với prefix heading giúp embedding khớp câu hỏi tự nhiên hơn nhiều (đo bằng thực nghiệm: Q4 từ "lệch" → khớp gold answer, Q2 chunk đúng từ hạng 3 → top-1); (3) prefix heading còn giúp truy vết nguồn dễ dàng khi demo. Chiến lược theo ký tự (fixed_size) chỉ phù hợp làm baseline để thấy rõ khác biệt.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu? | 24 giờ kể từ khi Shopee chấp nhận hoàn tiền, với điều kiện Ví ShopeePay vẫn hoạt động bình thường | shopee-refund-time — bảng phương thức hoàn tiền (dòng COD/QR → Ví ShopeePay) |
| 2 | Trong bao nhiêu ngày kể từ khi giao hàng thành công, người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền? | 15 ngày kể từ khi đơn cập nhật "Giao hàng thành công" (riêng thực phẩm tươi sống/đông lạnh: 24 giờ; đơn người bán tự vận chuyển: 15 ngày từ khi bấm "Đã nhận được hàng" hoặc 20 ngày từ "Lấy hàng thành công") | shopee-return-refund-rules — mục 1.2 "Thời gian tối đa để gửi yêu cầu" |
| 3 | Video mở kiện hàng cần đảm bảo những yêu cầu gì để được chấp nhận làm bằng chứng? | Quay xuyên suốt, liên tục, không cắt ghép; góc quay rõ, không khuất; chất lượng tốt, không mờ nhòe; thể hiện rõ 6 mặt kiện hàng, mã vận đơn khớp đơn hàng và tình trạng sản phẩm (niêm phong, tem nhãn). Video tối đa 100 MB / 1 phút | shopee-return-evidence — mục 2 + mục 4 "Quy định về bằng chứng" |
| 4 | Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu và cần bằng chứng gì? *(chạy kèm `metadata_filter={"audience": "seller"}` — câu hỏi không nêu rõ ai hỏi, corpus có tài liệu cùng chủ đề nhưng khác đối tượng, không lọc sẽ lẫn tài liệu buyer)* | Người bán có 2 ngày để khiếu nại kể từ khi nhận hàng hoàn thành công hoặc sau ngày nhận hàng hoàn dự kiến; bằng chứng là video mở hàng thể hiện tình trạng sản phẩm nhận được | shopee-seller-mall-return-process — mục 2, bảng "Điểm khác biệt"; shopee-seller-return-refund-process — mục B (bảng "Thông tin / Chi tiết") |
| 5 | Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, phí trả hàng có được hoàn lại không? | Có — Shopee hỗ trợ phí trả hàng trong 3-5 ngày làm việc sau khi yêu cầu được chấp nhận: đơn Shopee Mall hoàn trực tiếp; ngoài Mall hoàn bằng Shopee Xu (25.000 Xu cùng tỉnh/thành phố với người bán, 40.000 Xu khác tỉnh) | shopee-return-shipping — mục 2.2 "Phí vận chuyển trả hàng" |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 |Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu?| | | |
| 2 |Trong bao nhiêu ngày kể từ khi giao hàng thành công, người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền?| | | |
| 3 |Video mở kiện hàng cần đảm bảo những yêu cầu gì để được chấp nhận làm bằng chứng?| | | |
| 4 |Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu và cần bằng chứng gì?| | | |
| 5 |Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, phí trả hàng có được hoàn lại không?| | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |