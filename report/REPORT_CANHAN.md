# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hoàng Anh
**Nhóm:** ABU
**Ngày:** 20/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector có hướng gần nhau, cho thấy hai câu có ý nghĩa hoặc nội dung ngữ nghĩa tương đồng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua có thể yêu cầu trả hàng trong bao lâu?
- Câu B: Thời hạn để người mua gửi yêu cầu trả hàng là bao nhiêu ngày?
- Tại sao tương đồng: Cả hai câu đều hỏi về thời hạn người mua được yêu cầu trả hàng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người mua có thể yêu cầu trả hàng trong bao lâu?
- Câu B: Làm thế nào để chuẩn bị bằng chứng khi trả hàng?
- Tại sao khác: Hai câu đều liên quan đến trả hàng nhưng tập trung vào hai thông tin khác nhau: thời hạn và bằng chứng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào góc giữa các vector thay vì độ lớn tuyệt đối của vector, nên phù hợp để so sánh mức độ tương đồng về hướng/ngữ nghĩa của text embeddings. Điều này đặc biệt hữu ích khi độ dài hoặc độ lớn vector có thể khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Trình bày phép tính:
>
> Bước nhảy giữa hai chunk là:
>
> `500 - 50 = 450`
>
> Số chunk:
>
> `ceil((10000 - 500) / 450) + 1`
>
> `= ceil(9500 / 450) + 1`
>
> `= ceil(21.111...) + 1`
>
> `= 22 + 1 = 23`

> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm còn `500 - 100 = 400`, nên số chunk tăng lên. Overlap lớn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk, giảm nguy cơ tách rời thông tin liên quan, nhưng cũng làm tăng số chunk cần xử lý và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Hàm chia văn bản dựa trên các dấu kết thúc câu như `.`, `!`, `?` và xử lý các khoảng trắng hoặc xuống dòng giữa các câu. Sau khi tách câu, các câu được gom thành các chunk theo kích thước giới hạn; trường hợp văn bản rỗng hoặc không có câu phù hợp cần được xử lý để tránh tạo chunk không hợp lệ.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán chia văn bản đệ quy theo các separator từ lớn đến nhỏ, ưu tiên giữ nguyên cấu trúc văn bản trước khi chia nhỏ hơn. Base case xảy ra khi đoạn văn đã đủ nhỏ hoặc không còn separator phù hợp để tiếp tục chia; khi đó đoạn hiện tại được giữ lại làm chunk.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` nhận các document/chunk, tạo embedding và lưu vector cùng metadata của từng chunk trong vector store. `search` tạo embedding cho query, tính độ tương tự giữa query vector và các vector đã lưu, sau đó sắp xếp theo score để trả về các kết quả liên quan nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` kết hợp tìm kiếm vector với điều kiện metadata để chỉ xét các document phù hợp với filter, ví dụ `audience="buyer"`. `delete_document` xác định các chunk thuộc document cần xóa dựa trên metadata/document ID rồi loại chúng khỏi vector store.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` xây dựng prompt gồm câu hỏi của người dùng và context được lấy từ kết quả retrieval. Context được inject vào prompt để agent chỉ dựa trên các thông tin đã truy xuất khi tạo câu trả lời, đồng thời yêu cầu trả lời phù hợp với nội dung knowledge base.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
========================================================= 42 passed in 0.08s =========================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có thể yêu cầu trả hàng trong bao lâu? | Thời hạn yêu cầu trả hàng là bao nhiêu ngày? | cao | 0.3068 | Đúng |
| 2 | Làm thế nào để gửi yêu cầu trả hàng? | Các bước thực hiện yêu cầu trả hàng hoàn tiền là gì? | cao | 0.4805 | Đúng |
| 3 | Khi nào người mua nhận được tiền hoàn? | Thời gian nhận tiền hoàn là bao lâu? | cao | 0.0299 | Không |
| 4 | Cần chuẩn bị bằng chứng gì khi trả hàng? | Phí vận chuyển hàng hoàn trả là bao nhiêu? | thấp | 0.0626 | Đúng |
| 5 | Điều kiện nào được trả hàng hoàn tiền? | Làm thế nào để chuẩn bị bằng chứng trả hàng? | thấp | -0.0526 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Kết quả bất ngờ nhất là ba cặp câu được dự đoán có độ tương đồng cao nhưng điểm cosine thực tế lại rất thấp hoặc âm. Điều này cho thấy MockEmbedder chưa biểu diễn tốt ngữ nghĩa của các câu tiếng Việt, nên những câu có ý nghĩa gần nhau chưa chắc có vector gần nhau. Vì vậy, kết quả similarity phụ thuộc nhiều vào chất lượng của mô hình embedding được sử dụng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tiền hoàn qua Ví ShopeePay sẽ nhận được trong bao lâu? | `shopee-return-refund-policy#59` — thông tin về ngày đăng tải và hiệu lực chính sách | 0.6308 | Có liên quan (dẫn được đúng file ở top 2) | truy xuất được thông tin cụ thể về thời gian hoàn tiền qua ShopeePay. dẫn được đúng file ở top 2 |
| 2 | Trong bao nhiêu ngày kể từ khi giao hàng thành công, người mua vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền? | `shopee-seller-mall-return-process#0` — phần giới thiệu quy trình xử lý trả hàng dành cho Shopee Mall | 0.5705 | Có liên quan (dẫn được đúng file ở top 3) | truy xuất được chính xác thời hạn yêu cầu Trả hàng/Hoàn tiền. dẫn đc đúng file ở top 3|
| 3 | Video mở kiện hàng cần đảm bảo những yêu cầu gì để được chấp nhận làm bằng chứng? | `shopee-return-refund-policy#38` — thông tin về chi phí vận chuyển chiều hoàn trả | 0.6165 | có liên quan (dẫn được đúng file ở top 3) | Top-1 không chứa thông tin cần thiết; tuy nhiên `shopee-return-evidence#0` xuất hiện ở Top-2 và chứa nội dung hướng dẫn chuẩn bị bằng chứng. |
| 4 | Sau khi nhận hàng hoàn trả, cần khiếu nại trong bao lâu và cần bằng chứng gì? | `shopee-seller-return-refund-process#20` — lưu ý dành cho người bán về tuân thủ quy tắc kinh doanh | 0.4968 | Không | Top-1 không chứa thông tin cần thiết; kết quả Top-3 chưa truy xuất đúng nội dung về thời hạn khiếu nại và bằng chứng. |
| 5 | Nếu chọn hình thức Tự sắp xếp để gửi hàng hoàn trả, phí trả hàng có được hoàn lại không? | `shopee-return-refund-rules#9` — quy định về hoàn lại Mã giảm giá/Shopee Xu | 0.6070 | có liên quan ( thông tin gọi đúng ở top 3) | truy xuất được chính xác quy định về hoàn phí khi tự sắp xếp gửi hàng hoàn trả. thông tin gọi đúng ở top 3|

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Tôi học được cách lựa chọn chiến lược chunking phù hợp với cấu trúc của tài liệu để giữ được nhiều ngữ cảnh hơn khi truy xuất. Qua phần demo, tôi cũng nhận ra rằng việc chọn embedding model có ảnh hưởng rất lớn đến chất lượng tìm kiếm, vì cùng một câu hỏi nhưng embedding khác nhau có thể cho kết quả retrieval khác nhau.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60 + điểm Competition Results** |
