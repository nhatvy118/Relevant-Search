# Hướng Dẫn Chi Tiết - Hệ Thống Tìm Kiếm Ảnh với Relevance Feedback

## 📋 Tổng Quan Dự Án

Đây là hệ thống **Image Retrieval với Relevance Feedback** sử dụng phương pháp **Rocchio**. Hệ thống hỗ trợ 2 phương pháp tìm kiếm:

1. **Traditional Method**: Sử dụng đặc trưng thị giác (màu sắc, cường độ, texture)
2. **Text-based (CLIP) Method**: Sử dụng CLIP model để tìm kiếm bằng text hoặc ảnh

---

## 🏗️ Cấu Trúc Source Code

### 1. **app.py** - Flask Web Server (File chính)

Đây là file backend chính, cung cấp REST API cho frontend:

**Chức năng chính:**
- **`/api/status`**: Kiểm tra trạng thái index (có index chưa, số lượng ảnh)
- **`/api/build_index`**: Xây dựng index từ folder ảnh (hỗ trợ cả 2 phương pháp)
- **`/api/load_index`**: Load index đã có sẵn từ file `.pkl`
- **`/api/search`**: Thực hiện tìm kiếm ảnh
  - Traditional: query bằng ảnh upload hoặc file path
  - CLIP: query bằng text, ảnh upload, hoặc file path
- **`/api/feedback`**: Áp dụng relevance feedback (đánh dấu relevant/irrelevant)
- **`/api/reset`**: Reset feedback về trạng thái ban đầu
- **`/api/list_images`**: Liệt kê ảnh có sẵn để chọn làm query
- **`/api/images/<filename>`**: Serve ảnh để hiển thị trên frontend

**Cấu trúc:**
- Sử dụng Flask với CORS để frontend có thể gọi API
- Quản lý 2 global indexer: `traditional_indexer` và `text_indexer`
- Quản lý 2 global retrieval: `traditional_retrieval` và `text_retrieval`

### 2. **build_index.py** - Script Build Traditional Index

Script độc lập để build Traditional index từ command line (không cần GUI):

**Cách sử dụng:**
```bash
python build_index.py --folder <đường_dẫn_folder_ảnh> [--max-images N] [--output file.pkl] [--force]
```

**Tham số:**
- `--folder`: Đường dẫn đến folder chứa ảnh (bắt buộc)
- `--max-images`: Số lượng ảnh tối đa để index (mặc định: tất cả)
- `--output`: Tên file index output (mặc định: `image_index.pkl`)
- `--force`: Force rebuild ngay cả khi index đã tồn tại

**Ví dụ:**
```bash
python build_index.py --folder images --max-images 1000 --output image_index.pkl
```

### 3. **build_index_clip.py** - Script Build CLIP Index

Script độc lập để build CLIP index từ command line (không cần GUI):

**Cách sử dụng:**
```bash
python build_index_clip.py --folder <đường_dẫn_folder_ảnh> [--max-images N] [--output file.pkl] [--force]
```

**Tham số:**
- `--folder`: Đường dẫn đến folder chứa ảnh (bắt buộc)
- `--max-images`: Số lượng ảnh tối đa để index (mặc định: tất cả)
- `--output`: Tên file index output (mặc định: `text_index.pkl`)
- `--force`: Force rebuild ngay cả khi index đã tồn tại

**Ví dụ:**
```bash
python build_index_clip.py --folder images --max-images 1000 --output text_index.pkl
```

**Lưu ý:** CLIP index mất nhiều thời gian hơn Traditional vì cần load CLIP model và xử lý từng ảnh.

### 4. **traditional/** - Phương Pháp Traditional

#### **feature_extractor.py**
- Trích xuất đặc trưng thị giác từ ảnh (màu sắc, histogram, texture)
- Sử dụng OpenCV và NumPy

#### **indexer.py** (`ImageIndexer`)
- Quản lý index: build, save, load
- Lưu features và image paths vào file `.pkl`
- Hỗ trợ rebuild index

#### **retrieval.py** (`TraditionalImageRetrieval`)
- Thực hiện tìm kiếm dựa trên đặc trưng thị giác
- **Implement Rocchio Method**:
  ```
  q_new = α·q_original + (β/|Dr|)·Σ(dj ∈ Dr) - (γ/|Dn|)·Σ(dj ∈ Dn)
  ```
  - `α = 1.0`: Trọng số cho query gốc
  - `β = 0.75`: Trọng số cho relevant images
  - `γ = 0.25`: Trọng số cho irrelevant images
- Hỗ trợ relevance feedback: đánh dấu relevant/irrelevant

### 5. **clip/** - Phương Pháp CLIP

#### **extractor.py** (`CLIPExtractor`)
- Sử dụng CLIP model (OpenAI) để trích xuất embeddings
- Hỗ trợ cả text và image embeddings

#### **indexer.py** (`TextIndexer`)
- Tương tự `ImageIndexer` nhưng dùng CLIP embeddings
- Lưu vào `text_index.pkl`

#### **retrieval.py** (`TextRetrieval`)
- Tìm kiếm dựa trên CLIP embeddings
- Hỗ trợ query bằng:
  - **Text**: "a red car", "beautiful sunset"
  - **Image**: Upload ảnh hoặc chọn từ dataset
- Cũng implement Rocchio method với relevance feedback
- **Đặc biệt**: Hỗ trợ text feedback (mô tả bằng text thay vì chỉ đánh dấu ảnh)

### 6. **static/** - Frontend Files

- **index.html**: Giao diện web
- **app.js**: JavaScript xử lý tương tác với API
- **style.css**: Styling

---

## 🚀 Hướng Dẫn Chạy Ứng Dụng

### Bước 1: Kích hoạt Virtual Environment

```bash
# Di chuyển vào thư mục project
cd /Users/pila_vyhuynh/Uni/IR/Project

# Kích hoạt virtual environment
source venv/bin/activate
```

### Bước 2: Cài Đặt Dependencies

**⚠️ Lưu ý quan trọng về Dependency Conflict:**

Có conflict giữa `torch`, `torchvision` và `clip-by-openai`:
- `clip-by-openai` yêu cầu `torch==1.7.1` (version cũ)
- Nhưng `torchvision 0.23.0` yêu cầu `torch==2.8.0`
- CLIP model thực tế hoạt động tốt với torch 2.8.0, chỉ là dependency declaration cũ

**Cách 1: Sử dụng script tự động (Khuyến nghị)**
```bash
# Chạy script cài đặt tự động
./install.sh
```

**Cách 2: Cài đặt thủ công**
```bash
# 1. Cài đặt các packages cơ bản
pip install numpy>=1.24.0 opencv-python>=4.8.0 Pillow>=10.0.0 scipy>=1.13.0 scikit-learn>=1.3.0 Flask>=2.3.0 flask-cors>=4.0.0

# 2. Cài đặt torch và torchvision với version tương thích
pip install torch==2.8.0 torchvision==0.23.0

# 3. Cài đặt clip-by-openai với --no-deps để bỏ qua dependency check
pip install clip-by-openai --no-deps
```

**Cách 3: Cài đặt từ requirements.txt (sẽ gặp lỗi)**
```bash
# KHÔNG khuyến nghị - sẽ gặp lỗi dependency conflict
pip install -r requirements.txt
```

**Dependencies chính:**
- `numpy`: Xử lý mảng số
- `opencv-python`: Xử lý ảnh
- `Pillow`: Thao tác ảnh
- `scikit-learn`: Machine learning utilities
- `Flask`: Web framework
- `flask-cors`: CORS support
- `torch`, `torchvision`: PyTorch cho CLIP
- `clip-by-openai`: CLIP model

### Bước 3: Chuẩn Bị Dữ Liệu

Đảm bảo bạn có folder chứa ảnh (ví dụ: `images/`). Folder này đã có sẵn với 44,441 ảnh.

### Bước 4: Build Index (Tùy chọn)

**Cách 1: Build từ Command Line (không cần GUI)**

**Traditional Method:**
```bash
# Build index cho Traditional method
python build_index.py --folder images --max-images 1000 --output image_index.pkl

# Hoặc build tất cả ảnh (có thể mất nhiều thời gian)
python build_index.py --folder images --output image_index.pkl

# Force rebuild nếu index đã tồn tại
python build_index.py --folder images --output image_index.pkl --force
```

**CLIP Method:**
```bash
# Build index cho CLIP method (text-based retrieval)
python build_index_clip.py --folder images --max-images 1000 --output text_index.pkl

# Hoặc build tất cả ảnh (sẽ mất nhiều thời gian hơn Traditional)
python build_index_clip.py --folder images --output text_index.pkl

# Force rebuild nếu index đã tồn tại
python build_index_clip.py --folder images --output text_index.pkl --force
```

**Lưu ý:**
- CLIP index mất nhiều thời gian hơn Traditional (cần load CLIP model và xử lý từng ảnh)
- Index đã có sẵn: `image_index.pkl` (Traditional) và `text_index.pkl` (CLIP)
- Nếu đã có index, có thể bỏ qua bước này

**Cách 2: Build từ Web Interface**
- Chạy web server (bước 5)
- Mở trình duyệt và build index từ giao diện
- Có thể chọn method: Traditional hoặc Text (CLIP)

### Bước 5: Chạy Web Server

```bash
# Chạy server mặc định (port 5000)
python app.py

# Hoặc chỉ định port khác
python app.py 8080
```

**Output:**
```
Starting Image Retrieval Server...
Open your browser and go to: http://localhost:5000
```

### Bước 6: Sử Dụng Web Interface

1. **Mở trình duyệt**: Truy cập `http://localhost:5000`

2. **Chọn phương pháp**: Traditional hoặc Text (CLIP)

3. **Build/Load Index**:
   - Nếu chưa có index: Nhập folder ảnh → Click "Build Index"
   - Nếu đã có index: Click "Load Index"

4. **Tìm kiếm**:
   - **Traditional**: Upload ảnh query hoặc chọn ảnh từ dataset
   - **CLIP**: Nhập text query, upload ảnh, hoặc chọn ảnh từ dataset

5. **Relevance Feedback**:
   - Đánh dấu ảnh **relevant** (✓) hoặc **irrelevant** (✗)
   - Click "Apply Feedback" để cải thiện kết quả
   - Click "Reset" để xóa feedback

---

## 📝 Workflow Chi Tiết

### Traditional Method Workflow:

1. **Build Index**:
   ```
   ImageIndexer.build_index() 
   → FeatureExtractor.extract_features_from_folder()
   → Lưu features vào image_index.pkl
   ```

2. **Search**:
   ```
   Upload query image 
   → FeatureExtractor.extract_features()
   → TraditionalImageRetrieval.initial_query_from_features()
   → Tính cosine similarity với tất cả ảnh
   → Trả về top-k kết quả
   ```

3. **Relevance Feedback**:
   ```
   Đánh dấu relevant/irrelevant
   → TraditionalImageRetrieval.add_feedback()
   → TraditionalImageRetrieval.reformulate_query() (Rocchio)
   → Search lại với query mới
   ```

### CLIP Method Workflow:

1. **Build Index**:
   ```
   TextIndexer.build_index()
   → CLIPExtractor.extract_image_features()
   → Lưu CLIP embeddings vào text_index.pkl
   ```

2. **Search**:
   ```
   Text query hoặc Image query
   → CLIPExtractor.encode_text() hoặc encode_image()
   → TextRetrieval.initial_query_from_text/image()
   → Tính cosine similarity
   → Trả về top-k kết quả
   ```

3. **Relevance Feedback**:
   ```
   Đánh dấu ảnh + Text feedback (tùy chọn)
   → TextRetrieval.add_feedback() + add_text_feedback()
   → TextRetrieval.reformulate_query() (Rocchio)
   → Search lại
   ```

---

## 🔧 Cấu Hình và Tùy Chỉnh

### Thay Đổi Rocchio Parameters:

Trong `traditional/retrieval.py` hoặc `clip/retrieval.py`:
```python
self.alpha = 1.0   # Trọng số query gốc
self.beta = 0.75   # Trọng số relevant images
self.gamma = 0.25  # Trọng số irrelevant images
```

### Thay Đổi Số Lượng Kết Quả:

Trong API call, thêm parameter:
```json
{
  "top_k": 30  // Mặc định là 20
}
```

### Thay Đổi Folder Ảnh:

Trong `app.py`, sửa:
```python
IMAGES_FOLDER = 'images'  # Đổi thành folder của bạn
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **Lần đầu build index**: Có thể mất nhiều thời gian (đặc biệt với CLIP)
2. **Memory**: CLIP model cần nhiều RAM hơn Traditional method
3. **Index files**: 
   - `image_index.pkl`: Traditional index (chỉ query bằng ảnh)
   - `text_index.pkl`: CLIP index (query bằng text hoặc ảnh)
   - Có thể xóa và rebuild nếu cần
4. **Port conflict**: Nếu port 5000 bị chiếm, server sẽ tự động tìm port khác

### 📝 Giải Thích Tên File Index

**Tại sao Traditional là `image_index.pkl` còn CLIP là `text_index.pkl`?**

- **`image_index.pkl` (Traditional)**: 
  - Chỉ có thể query bằng **ảnh** (image-to-image search)
  - Sử dụng visual features: màu sắc, histogram, texture
  - → Tên phản ánh: chỉ làm việc với ảnh

- **`text_index.pkl` (CLIP)**: 
  - **Tính năng chính**: Query bằng **text** (text-to-image search)
  - Ví dụ: "a red car", "beautiful sunset"
  - Ngoài ra cũng hỗ trợ query bằng ảnh
  - → Tên phản ánh: khả năng query bằng text (tính năng đặc biệt)

**Lưu ý**: Cả hai đều index ảnh, chỉ khác cách extract features và cách query. Xem chi tiết trong `GIAI_THICH_TEN_FILE.md`

---

## 🐛 Troubleshooting

**Lỗi: "ResolutionImpossible" hoặc "dependency conflict"**
- **Nguyên nhân**: Conflict giữa `torch`, `torchvision` và `clip-by-openai`
- **Giải pháp**: 
  ```bash
  # Cài đặt theo thứ tự:
  pip install torch==2.8.0 torchvision==0.23.0
  pip install clip-by-openai --no-deps
  ```
  Hoặc sử dụng script: `./install.sh`

**Lỗi: "Index file not found"**
- Giải pháp: Build index trước (bước 4)

**Lỗi: "Module not found"**
- Giải pháp: Cài đặt dependencies theo hướng dẫn ở Bước 2

**Lỗi: "Port already in use"**
- Giải pháp: Server sẽ tự động tìm port khác, hoặc kill process đang dùng port đó

**CLIP model download chậm**
- Lần đầu sử dụng CLIP, model sẽ được download tự động (có thể mất vài phút)

---

## 📚 Tài Liệu Tham Khảo

- Rocchio Method: Xem slide bài giảng
- CLIP Paper: "Learning Transferable Visual Models From Natural Language Supervision"
- Flask Documentation: https://flask.palletsprojects.com/

