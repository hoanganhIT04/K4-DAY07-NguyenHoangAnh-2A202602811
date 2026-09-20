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
- **Loại chiến lược:** Custom — `HeadingChunker` (heading đa cấp: markdown + mục đánh số) + retrieval hybrid có LLM rerank
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách Shopee có cấu trúc điều khoản đánh số rõ ràng (Điều 1, 2, 3...; mục 1.1, 1.2...) và nhiều bảng quy định — mỗi mục là một quy tắc độc lập. `HeadingChunker` nhận diện cả heading markdown lẫn mục đánh số dạng văn bản thuần ("1.2. Thời gian tối đa...") làm ranh giới, giữ bảng markdown nguyên vẹn, và prefix đường dẫn heading đầy đủ vào mỗi chunk. Sau 3 vòng thực nghiệm (ký tự → heading markdown → heading đa cấp + rerank), pipeline đạt 5/5 câu chuẩn 2đ: Q4 sửa lỗi agent trả lời sai ngữ cảnh, Q2/Q3 truy xuất đủ mọi nhánh chi tiết của gold answer.
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
| Nguyễn Hà Khuê | Custom `HeadingChunker` + hybrid LLM rerank | 10 | Chunk mang ngữ cảnh heading đầy đủ; bảng nguyên vẹn; rerank sửa lỗi "chunk đúng bị đẩy xuống top-3"; benchmark 5/5 câu đạt 2đ | Phụ thuộc format markdown + đánh số của tài liệu gốc; tốn thêm 1 call LLM cho rerank |
| Nguyễn Hoàng Anh | Recursive | 1 | Chia chunk theo cấu trúc đệ quy, giúp giữ các đoạn văn và điều kiện liên quan trong cùng chunk | MockEmbedder chưa biểu diễn tốt ngữ nghĩa tiếng Việt, nên nhiều câu hỏi không truy xuất được chunk liên quan trong Top-3 |
|  Nguyễn Huy Hoàng | SentenceChunker | 8 | Top-3 có thông tin liên quan ở 5/5 câu; câu 2 lấy được cả ngoại lệ thời hạn | Câu 3 thiếu yêu cầu chất lượng và giới hạn video; câu 5 thiếu thời gian hoàn phí và mức Xu |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với domain chính sách/các quy định, chunking theo heading/section là tốt nhất. Lý do: (1) mỗi mục của chính sách là một quy tắc độc lập với thời hạn/điều kiện riêng — tách đúng ranh giới mục giúp một chunk chứa trọn vẹn một quy tắc, tránh trả lời ghép nhầm điều kiện của mục khác; (2) các bảng quy định (thời gian hoàn tiền, phí trả hàng, bảng so sánh trước/sau) chứa câu trả lời dạng số liệu nhưng bị cắt làm hỏng ngữ nghĩa khi chunk theo ký tự — giữ nguyên bảng cộng với prefix heading giúp embedding khớp câu hỏi tự nhiên hơn nhiều (đo bằng thực nghiệm: Q4 từ "lệch" → khớp gold answer, Q2 chunk đúng từ hạng 3 → top-1); (3) prefix heading còn giúp truy vết nguồn dễ dàng khi demo. Chiến lược theo ký tự (fixed_size) chỉ phù hợp làm baseline để thấy rõ khác biệt.

### Failure Case tiêu biểu (chi tiết đầy đủ trong REPORT_CANHAN của từng thành viên)

**Failure case 1 — bảng bị cắt làm mất ngữ nghĩa (chunking theo ký tự):**
Bảng "Phương thức thanh toán → Thời gian hoàn tiền" trong tài liệu *Thời gian nhận tiền hoàn* chứa câu trả lời của benchmark Q1 ("Ví ShopeePay: 24 giờ"). Chunk theo ký tự làm bảng thành dòng rời rạc, chunk chứa bảng chỉ xếp hạng 3 (0.6648) sau chunk "⚠️ Lưu ý" (0.6665) — chunk này chứa dày đặc từ "hoàn tiền/khiếu nại" nên embedding cao dù KHÔNG trả lời được câu hỏi. Với top_k=1 pipeline sẽ trả lời sai. **Nguyên nhân:** nội dung bảng không có cấu trúc câu tự nhiên; các bullet ghi chú trùng từ khóa query. **Đã fix:** giữ bảng nguyên vẹn trong 1 chunk + LLM rerank đưa chunk bảng lên top-1.

**Failure case 2 — rerank bỏ sót chunk mạnh (regression thật khi fix):**
Khi thêm tầng LLM rerank, ở Q4 rerank một lần đã chọn các chunk của doc Shopee Mall và bỏ sót chunk embedding top-1 (bảng "Thông tin / Chi tiết" chứa deadline "2 ngày") — câu trả lời mất luôn mốc thời gian. **Nguyên nhân:** rerank của LLM không tương quan tuyệt đối với độ khớp embedding; chunk "nhiều chữ giống câu hỏi" lấn át. **Đã fix:** hybrid — luôn giữ chunk embedding top-1 trong top-3 sau rerank. Bài học: mọi tầng tự động (kể cả LLM) đều cần cơ chế dự phòng.

**Failure case 3 — heading dạng đánh số "vô hình":**
Shopee viết cấu trúc bằng mục đánh số thuần ("1.2. Thời gian tối đa...") chứ không phải markdown `#` — chunker markdown không nhận ra, dẫn tới Q2 thiếu nhánh "người bán tự vận chuyển 15/20 ngày". **Đã fix:** nhận diện pattern số `1.2.` (ngắn, không kết thúc dấu câu) làm ranh giới mục, kế thừa heading cha.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu? | 24 giờ kể từ khi Shopee chấp nhận hoàn tiền, với điều kiện Ví ShopeePay vẫn hoạt động bình thường | shopee-refund-time — bảng phương thức hoàn tiền (dòng COD/QR → Ví ShopeePay) |
| 2 | Trong bao nhiêu ngày kể từ khi giao hàng thành công, người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền? | 15 ngày kể từ khi đơn cập nhật "Giao hàng thành công" (riêng thực phẩm tươi sống/đông lạnh: 24 giờ; đơn người bán tự vận chuyển: 15 ngày từ khi bấm "Đã nhận được hàng" hoặc 20 ngày từ "Lấy hàng thành công") | shopee-return-refund-rules — mục 1.2 "Thời gian tối đa để gửi yêu cầu" |
| 3 | Video mở kiện hàng cần đảm bảo những yêu cầu gì để được chấp nhận làm bằng chứng? | Quay xuyên suốt, liên tục, không cắt ghép; góc quay rõ, không khuất; chất lượng tốt, không mờ nhòe; thể hiện rõ 6 mặt kiện hàng, mã vận đơn khớp đơn hàng và tình trạng sản phẩm (niêm phong, tem nhãn). Video tối đa 100 MB / 1 phút | shopee-return-evidence — mục 2 + mục 4 "Quy định về bằng chứng" |
| 4 | Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu và cần bằng chứng gì? | Người bán có 2 ngày để khiếu nại kể từ khi nhận hàng hoàn thành công hoặc sau ngày nhận hàng hoàn dự kiến; bằng chứng là video mở hàng thể hiện tình trạng sản phẩm nhận được | shopee-seller-mall-return-process — mục 2, bảng "Điểm khác biệt"; shopee-seller-return-refund-process — mục B (bảng "Thông tin / Chi tiết") |
| 5 | Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, phí trả hàng có được hoàn lại không? | Có — Shopee hỗ trợ phí trả hàng trong 3-5 ngày làm việc sau khi yêu cầu được chấp nhận: đơn Shopee Mall hoàn trực tiếp; ngoài Mall hoàn bằng Shopee Xu (25.000 Xu cùng tỉnh/thành phố với người bán, 40.000 Xu khác tỉnh) | shopee-return-shipping — mục 2.2 "Phí vận chuyển trả hàng" |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).


| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu? | HeadingChunker + hybrid rerank (Khuê) | Có (Khuê: top-1 sau rerank) | Không rerank thì bảng chứa đáp án chỉ ở hạng 3 — chunk "Lưu ý" nhiễu từ khóa thắng |
| 2 | Trong bao nhiêu ngày kể từ khi giao hàng thành công, người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền? | HeadingChunker + hybrid rerank (Khuê) | Có (Khuê: top-1) | Rerank đưa chunk "1.2 Thời gian tối đa" vào top-3 → agent trả lời đủ cả 3 nhánh thời hạn |
| 3 | Video mở kiện hàng cần đảm bảo những yêu cầu gì để được chấp nhận làm bằng chứng? | HeadingChunker (Khuê) | Có (Khuê: 2/3 top-3 cùng doc evidence) | Prompt "rà từng chunk" giúp agent tự lấy thêm giới hạn 100MB/1 phút ở chunk hạng 2 |
| 4 | Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu và cần bằng chứng gì? | HeadingChunker + filter seller + hybrid rerank (Khuê) | Có (Khuê: cả top-3 là doc seller) | Không filter → 2/3 top-3 là chunk buyer; filter là điều kiện bắt buộc để trả lời đúng đối tượng |
| 5 | Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, phí trả hàng có được hoàn lại không? | HeadingChunker (Khuê) | Có (Khuê: top-1) | Agent trả lời đủ 3-5 ngày + phân biệt Mall / Shopee Xu 25k-40k |

Kết quả chi tiết từng thành viên xem trong file `ket_qua_benchmark.txt` của mỗi người (nộp kèm).

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có — ở câu 4. Câu hỏi không nêu rõ người hỏi là ai, trong khi corpus có tài liệu cùng chủ đề nhưng khác đối tượng: doc buyer nói "gửi hàng hoàn trong 6 ngày", doc seller nói "khiếu nại trong 2 ngày". Không lọc, top-3 lẫn 2 chunk audience=buyer và agent mất đi ngữ cảnh đúng. Với filter `audience=seller`, cả top-3 đều là tài liệu hướng người bán và agent trả lời đúng "2 ngày + bằng chứng mở hàng". Bài học: khi corpus phục vụ nhiều đối tượng, metadata filter không phải tùy chọn mà là điều kiện để câu trả lời đúng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- **Embedding hiểu chủ đề nhưng không hiểu phủ định:** hai câu trái ý ("Shopee không hỗ trợ đổi hàng" vs "Shopee hỗ trợ hoàn tiền ngay") có cosine 0.71 — similarity thuần túy không phân biệt được điều kiện áp dụng với trường hợp loại trừ.
- **Metadata filter là bắt buộc, không phải tùy chọn:** benchmark Q4 (không nêu ai hỏi) không lọc `audience` thì top-3 lẫn 2 chunk buyer — corpus đa đối tượng cần filter để trả lời đúng người.
- **Lỗi RAG nằm rải rác ở nhiều tầng:** cùng một hệ thống, sửa chunking (heading đa cấp) chỉ giải quyết một nửa lỗi; phải thêm rerank + chỉnh prompt mới đạt 10/10. Demo từng tầng score/rank giúp chỉ ra chính xác tầng nào gây lỗi.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng bộ 9 tài liệu Shopee nhưng chiến lược khác nhau cho kết quả chênh lệch rất lớn: chunking theo ký tự (fixed_size) cắt hỏng bảng quy định và không nhận diện được điều khoản đánh số; RecursiveChunker bám sát đoạn văn hơn nhưng vẫn "mù" cấu trúc; HeadingChunker + rerank đạt 5/5 câu chuẩn 2đ. Khác biệt không nằm ở embedding model (ai cũng dùng text-embedding-3-small) mà nằm ở **cách chuẩn bị dữ liệu**: một chunk phải chứa trọn vẹn một quy tắc và mang đủ ngữ cảnh (heading path) thì embedding mới khớp câu hỏi tự nhiên.

**Failure case nhóm chọn để demo:** Q4 "Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu và cần bằng chứng gì?" — câu hỏi không nêu ai hỏi, corpus có 2 tài liệu cùng từ vựng nhưng khác đáp án (buyer: gửi hàng trong 6 ngày; seller: khiếu nại trong 2 ngày). Không lọc metadata, retrieval lẫn tài liệu buyer; thêm regression khi thêm rerank (rerank bỏ sót chunk chứa deadline). Chỉ khi kết hợp cả filter `audience` + hybrid rerank + prompt "rà từng chunk" câu trả lời mới khớp gold answer cả 2 phần. Đây là ví dụ trọn vẹn cho thấy độ chính xác phụ thuộc **chuỗi các tầng**, không phải một tầng duy nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> (1) Giữ cấu trúc tài liệu ngay từ khâu thu thập: chuyển bảng sang format bảng markdown thật thay vì dòng rời rạc, và giữ nguyên đánh số điều khoản — dữ liệu đầu vào sạch thì mọi chiến lược chunking phía sau đều đỡ tốn công sửa. (2) Thêm 2-3 tài liệu hướng người bán ngay từ đầu để filter `audience` có ý nghĩa từ vòng benchmark đầu tiên thay vì phải bổ sung sau. (3) Viết benchmark script trước khi thu thập dữ liệu: biết trước cần đo gì (top-1 vs top-3, đủ nhánh chi tiết) sẽ định hình được corpus cần những gì.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) |5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |