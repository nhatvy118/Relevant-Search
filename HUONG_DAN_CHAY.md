# Hướng Dẫn Chạy Frontend

## Bước 1: Kích hoạt Virtual Environment

```bash
source venv/bin/activate
```

## Bước 2: Cài đặt Flask (nếu chưa có)

```bash
pip install Flask flask-cors
```

Hoặc cài tất cả dependencies:
```bash
pip install -r requirements.txt
```

## Bước 3: Chạy Server

```bash
python app.py
```

Server sẽ tự động:
- Tìm port khả dụng (mặc định 5000, nếu bị chiếm sẽ tìm port khác)
- Hiển thị URL để truy cập

Ví dụ output:
```
Starting Image Retrieval Server...
Open your browser and go to: http://localhost:5000
 * Running on http://0.0.0.0:5000
```

## Bước 4: Mở Trình Duyệt

Mở trình duyệt (Chrome, Firefox, Safari, Edge...) và truy cập URL được hiển thị:
- **http://localhost:5000** (hoặc port khác nếu 5000 bị chiếm)

## Sử dụng Frontend

1. **Build/Load Index**: 
   - Nhập folder ảnh (mặc định: `images/`)
   - Click "Build Index" hoặc "Load Index"

2. **Tìm kiếm**:
   - Click "Select Query Image" để chọn ảnh từ máy tính
   - Click "Search"

3. **Relevance Feedback**:
   - Đánh dấu ảnh "Relevant" hoặc "Irrelevant"
   - Click "Apply Feedback" để cải thiện kết quả

4. **Reset**: Click "Reset" để xóa feedback

## Lưu ý

- Giữ terminal chạy server mở trong khi sử dụng
- Để dừng server: Nhấn `Ctrl + C` trong terminal
- Nếu port 5000 bị chiếm, server sẽ tự động dùng port khác (5001, 5002, ...)

## Troubleshooting

**Lỗi "ModuleNotFoundError: No module named 'flask'"**
→ Chạy: `pip install Flask flask-cors`

**Lỗi "Port already in use"**
→ Server sẽ tự động tìm port khác, hoặc chỉ định port: `python app.py 8080`

**Không mở được trang web**
→ Kiểm tra URL đúng chưa, và server đã chạy chưa

