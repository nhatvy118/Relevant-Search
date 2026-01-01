# Giải Thích Chi Tiết UI - Image Retrieval System

## 📋 Tổng Quan Cấu Trúc

UI được chia thành 4 phần chính:
1. **Header** - Tiêu đề và mô tả
2. **Control Panel** - 3 nhóm điều khiển
3. **Results Section** - Hiển thị kết quả tìm kiếm
4. **Loading Overlay** - Màn hình loading

---

## 1. 🎨 HEADER (Phần Đầu)

```html
<header>
    <h1>🖼️ Image Retrieval with Relevance Feedback</h1>
    <p class="subtitle">Fashion Image Search using Rocchio Method</p>
</header>
```

**Chức năng:**
- Hiển thị tên ứng dụng và mô tả ngắn
- Tạo ấn tượng ban đầu cho người dùng

**Thiết kế:**
- Background: Gradient xanh pastel nhẹ nhàng (#a8d5e2 → #b8e0d2)
- Text: Màu xám đậm (#2c3e50) để dễ đọc
- Padding: 30px để có không gian thoáng

---

## 2. 🎛️ CONTROL PANEL (Bảng Điều Khiển)

Panel này chứa 3 nhóm chức năng chính:

### 2.1. Index Management (Quản Lý Index)

```html
<div class="control-group">
    <h3>Index Management</h3>
    <input type="text" id="imageFolder" placeholder="images/">
    <button id="buildIndexBtn">Build Index</button>
    <button id="loadIndexBtn">Load Index</button>
    <div id="indexStatus"></div>
</div>
```

**Các thành phần:**

1. **Input Folder** (`imageFolder`)
   - **Chức năng**: Nhập đường dẫn folder chứa ảnh
   - **Mặc định**: "images/"
   - **Sử dụng**: Người dùng có thể thay đổi folder khác

2. **Button "Build Index"** (`buildIndexBtn`)
   - **Chức năng**: 
     - Extract features từ tất cả ảnh trong folder
     - Tạo file index (`image_index.pkl`)
     - Lưu features để tìm kiếm nhanh
   - **Quy trình**:
     1. Click button
     2. Nhập số lượng ảnh muốn index (hoặc để trống = tất cả)
     3. Hiển thị loading
     4. Hiển thị kết quả trong `indexStatus`

3. **Button "Load Index"** (`loadIndexBtn`)
   - **Chức năng**: Load index đã build trước đó
   - **Sử dụng**: Khi đã có file `image_index.pkl`
   - **Lợi ích**: Không cần build lại, tiết kiệm thời gian

4. **Status Text** (`indexStatus`)
   - **Chức năng**: Hiển thị trạng thái index
   - **Màu sắc**:
     - Xanh lá: Index đã load thành công
     - Đỏ: Chưa có index hoặc lỗi
   - **Ví dụ**: "✓ Index loaded: 5000 images"

---

### 2.2. Search (Tìm Kiếm)

```html
<div class="control-group">
    <h3>Search</h3>
    <label for="queryImage" class="upload-label">
        <span>📁 Select Query Image</span>
        <input type="file" id="queryImage" accept="image/*">
    </label>
    <div id="queryPreview" class="query-preview"></div>
    <button id="searchBtn" disabled>🔍 Search</button>
</div>
```

**Các thành phần:**

1. **Upload Label** (`queryImage`)
   - **Chức năng**: Button để chọn ảnh query từ máy tính
   - **Thiết kế**: 
     - Ẩn input file gốc (xấu)
     - Tạo label đẹp với icon 📁
     - Màu xanh nhạt (#a8d5e2)
   - **Khi click**: Mở dialog chọn file

2. **Query Preview** (`queryPreview`)
   - **Chức năng**: Hiển thị preview ảnh đã chọn
   - **Kích thước**: 150x150px
   - **Border**: Xanh nhạt (#d4e4f0)
   - **Trạng thái ban đầu**: Trống, hiển thị placeholder

3. **Button "Search"** (`searchBtn`)
   - **Chức năng**: 
     - Gửi ảnh query lên server
     - Extract features từ ảnh
     - Tìm kiếm ảnh tương tự trong database
     - Hiển thị kết quả
   - **Trạng thái**: 
     - Disabled ban đầu (chưa chọn ảnh)
     - Enabled sau khi chọn ảnh
   - **Màu**: Xanh lá nhạt (#b8e0d2)

---

### 2.3. Relevance Feedback (Phản Hồi Liên Quan)

```html
<div class="control-group">
    <h3>Relevance Feedback</h3>
    <button id="applyFeedbackBtn" disabled>Apply Feedback</button>
    <button id="resetBtn" disabled>Reset</button>
    <div id="feedbackInfo">Relevant: 0 | Irrelevant: 0</div>
</div>
```

**Các thành phần:**

1. **Button "Apply Feedback"** (`applyFeedbackBtn`)
   - **Chức năng**: 
     - Thu thập feedback từ checkboxes (relevant/irrelevant)
     - Gửi lên server
     - Server áp dụng Rocchio method để cải thiện query
     - Tìm kiếm lại với query mới
     - Hiển thị kết quả cải thiện
   - **Trạng thái**: 
     - Disabled ban đầu
     - Enabled sau khi có kết quả tìm kiếm
   - **Màu**: Vàng nhạt (#ffe4b5)

2. **Button "Reset"** (`resetBtn`)
   - **Chức năng**: 
     - Xóa tất cả feedback đã đánh dấu
     - Reset query về ban đầu
     - Clear tất cả checkboxes
   - **Trạng thái**: Enabled sau khi có feedback
   - **Màu**: Hồng nhạt (#f5c2c2)

3. **Feedback Info** (`feedbackInfo`)
   - **Chức năng**: Hiển thị số lượng ảnh đã đánh dấu
   - **Format**: "Relevant: X | Irrelevant: Y"
   - **Cập nhật**: Tự động sau mỗi lần apply feedback
   - **Màu nền**: Vàng rất nhạt (#fff9e6)

---

## 3. 📊 RESULTS SECTION (Phần Kết Quả)

```html
<div class="results-section">
    <h2>Search Results</h2>
    <div id="resultsContainer" class="results-grid">
        <!-- Results sẽ được render ở đây -->
    </div>
</div>
```

**Cấu trúc:**

1. **Tiêu đề "Search Results"**
   - Màu xanh nhẹ (#6b9bd1)
   - Font size lớn (1.8em)

2. **Results Grid** (`resultsContainer`)
   - **Layout**: CSS Grid, responsive
   - **Columns**: Tự động điều chỉnh (min 200px mỗi cột)
   - **Gap**: 20px giữa các ảnh
   - **Trạng thái ban đầu**: Hiển thị empty state

**Mỗi Result Item chứa:**

```html
<div class="result-item">
    <img src="..." class="result-image">
    <div class="result-info">
        <div class="result-score">Similarity: 0.856</div>
        <div class="feedback-checkboxes">
            <label>
                <input type="checkbox" class="relevant-checkbox">
                <span>✓ Relevant</span>
            </label>
            <label>
                <input type="checkbox" class="irrelevant-checkbox">
                <span>✗ Irrelevant</span>
            </label>
        </div>
    </div>
</div>
```

**Chi tiết:**

1. **Result Image**
   - **Kích thước**: 200px height, width 100%
   - **Object-fit**: Cover (giữ tỷ lệ, cắt nếu cần)
   - **Background**: Xám rất nhạt (#fafbfc)

2. **Result Score**
   - **Chức năng**: Hiển thị similarity score (0-1)
   - **Màu**: Xanh nhẹ (#6b9bd1)
   - **Format**: "Similarity: 0.856" (3 chữ số thập phân)

3. **Feedback Checkboxes**
   - **Relevant Checkbox**: Đánh dấu ảnh liên quan
   - **Irrelevant Checkbox**: Đánh dấu ảnh không liên quan
   - **Hover**: Background xám nhạt (#f5f7fa)
   - **Lưu ý**: Chỉ chọn một trong hai

**Hover Effect:**
- Khi hover vào result item:
  - Nâng lên 3px (translateY)
  - Border đổi màu xanh (#a8d5e2)
  - Shadow tăng lên

---

## 4. ⏳ LOADING OVERLAY (Màn Hình Loading)

```html
<div id="loadingOverlay" class="loading-overlay" style="display: none;">
    <div class="spinner"></div>
    <p id="loadingText">Processing...</p>
</div>
```

**Chức năng:**
- Hiển thị khi đang xử lý (build index, search, apply feedback)
- Chặn tương tác với UI trong lúc xử lý
- Hiển thị spinner animation

**Thiết kế:**
- **Background**: Trắng mờ (rgba(255,255,255,0.9)) với blur
- **Spinner**: Vòng tròn xoay, màu xanh nhạt (#a8d5e2)
- **Text**: Màu xám đậm (#2c3e50)
- **Position**: Fixed, full screen, z-index cao (1000)

**Khi nào hiển thị:**
- Build index
- Load index
- Search
- Apply feedback
- Reset feedback

---

## 5. 🔄 QUY TRÌNH SỬ DỤNG

### Bước 1: Build/Load Index
1. Nhập folder ảnh (hoặc dùng mặc định "images/")
2. Click "Build Index" → Nhập số lượng → Đợi
3. Hoặc click "Load Index" nếu đã có index

### Bước 2: Tìm Kiếm
1. Click "Select Query Image" → Chọn ảnh từ máy
2. Xem preview ảnh
3. Click "Search" → Đợi kết quả
4. Xem danh sách ảnh tương tự với similarity scores

### Bước 3: Relevance Feedback
1. Đánh dấu ảnh "Relevant" hoặc "Irrelevant" bằng checkbox
2. Click "Apply Feedback"
3. Xem kết quả mới được cải thiện
4. Lặp lại để cải thiện thêm

### Bước 4: Reset (Tùy chọn)
1. Click "Reset" để xóa tất cả feedback
2. Quay về query ban đầu

---

## 6. 🎨 MÀU SẮC CHÍNH

- **Background chính**: #f5f7fa (xám rất nhạt)
- **Container**: White (#ffffff)
- **Header gradient**: #a8d5e2 → #b8e0d2 (xanh pastel)
- **Primary button**: #a8d5e2 (xanh nhạt)
- **Success button**: #b8e0d2 (xanh lá nhạt)
- **Warning button**: #ffe4b5 (vàng nhạt)
- **Danger button**: #f5c2c2 (hồng nhạt)
- **Text chính**: #2c3e50 (xám đậm)
- **Text phụ**: #6b9bd1 (xanh nhẹ)
- **Border**: #e8ecef, #d4e4f0 (xám nhạt)

---

## 7. 📱 RESPONSIVE DESIGN

UI tự động điều chỉnh trên mobile:
- Grid columns giảm xuống (min 150px)
- Buttons xếp dọc
- Input full width
- Query section xếp dọc

---

## 8. 🔌 TƯƠNG TÁC VỚI BACKEND

Tất cả tương tác qua REST API:
- `GET /api/status` - Kiểm tra trạng thái
- `POST /api/build_index` - Build index
- `POST /api/load_index` - Load index
- `POST /api/search` - Tìm kiếm
- `POST /api/feedback` - Áp dụng feedback
- `POST /api/reset` - Reset feedback
- `GET /api/images/<path>` - Lấy ảnh

Tất cả đều sử dụng JSON và async/await trong JavaScript.

