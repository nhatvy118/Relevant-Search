# Image Retrieval with Relevance Feedback

Hệ thống tìm kiếm ảnh với Relevance Feedback sử dụng phương pháp Rocchio - Web Interface

## Cài đặt

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

## Chạy ứng dụng

```bash
# Chạy web server
python app.py
```

Sau đó mở trình duyệt và truy cập URL được hiển thị (mặc định: http://localhost:5000)

## Sử dụng

1. **Build/Load Index**: Nhập folder ảnh và click "Build Index" hoặc "Load Index"
2. **Tìm kiếm**: Upload query image và click "Search"
3. **Relevance Feedback**: Đánh dấu ảnh relevant/irrelevant và click "Apply Feedback"
4. **Reset**: Click "Reset" để xóa feedback

## Cấu trúc Project

- `app.py` - Flask web server
- `feature_extractor.py` - Extract features từ ảnh
- `indexer.py` - Index và quản lý features
- `retrieval.py` - Hệ thống tìm kiếm với Rocchio method
- `build_index.py` - Script build index từ command line
- `static/` - Frontend files (HTML, CSS, JavaScript)

## Phương pháp

Sử dụng **Rocchio Method**:
```
q_new = α·q_original + (β/|Dr|)·Σ(dj ∈ Dr) - (γ/|Dn|)·Σ(dj ∈ Dn)
```

Với: α=1.0, β=0.75, γ=0.25

Xem chi tiết trong file `HUONG_DAN_CHAY.md`

