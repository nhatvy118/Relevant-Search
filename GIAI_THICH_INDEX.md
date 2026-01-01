# Giải Thích: Build Index vs Load Index

## 🔨 BUILD INDEX (Xây dựng Index)

### Chức năng:
**Build Index** là quá trình **extract features** từ tất cả ảnh trong folder và **lưu vào file** để dùng sau.

### Quy trình:

1. **Đọc tất cả ảnh** trong folder (ví dụ: `images/`)
2. **Extract features** từ mỗi ảnh:
   - Color histogram (RGB) - 96 features (32 bins × 3 channels)
   - Intensity histogram (grayscale) - 32 features
   - Texture features (gradient-based) - 4 features
   - **Tổng cộng: ~132 features/ảnh**

3. **Lưu vào file** `image_index.pkl`:
   - Danh sách đường dẫn ảnh
   - Ma trận features (N × 132) với N = số lượng ảnh

### Khi nào dùng:
- ✅ **Lần đầu tiên** sử dụng hệ thống
- ✅ **Thêm ảnh mới** vào folder
- ✅ **Muốn rebuild** index từ đầu

### Thời gian:
- ⏱️ **Chậm**: Phải xử lý từng ảnh
- Ví dụ: 5000 ảnh có thể mất **5-10 phút** tùy máy

### Kết quả:
- Tạo file `image_index.pkl` trong thư mục project
- File này chứa tất cả features đã extract

---

## 📂 LOAD INDEX (Tải Index)

### Chức năng:
**Load Index** là quá trình **đọc file index đã có sẵn** từ đĩa, không cần extract lại.

### Quy trình:

1. **Kiểm tra** file `image_index.pkl` có tồn tại không
2. **Đọc file** từ đĩa (rất nhanh)
3. **Load vào memory**:
   - Danh sách đường dẫn ảnh
   - Ma trận features

### Khi nào dùng:
- ✅ **Đã build index trước đó**
- ✅ **Khởi động lại** ứng dụng
- ✅ **Muốn dùng nhanh** không cần rebuild

### Thời gian:
- ⚡ **Rất nhanh**: Chỉ đọc file
- Thường mất **< 1 giây** ngay cả với 10,000+ ảnh

### Kết quả:
- Load index vào memory
- Sẵn sàng để tìm kiếm ngay

---

## 📊 So Sánh

| Tiêu chí | Build Index | Load Index |
|----------|-------------|------------|
| **Tốc độ** | ⏱️ Chậm (5-10 phút) | ⚡ Rất nhanh (< 1 giây) |
| **Xử lý** | Extract features từ ảnh | Chỉ đọc file |
| **Khi dùng** | Lần đầu, thêm ảnh mới | Đã có index sẵn |
| **Kết quả** | Tạo file `.pkl` | Load từ file `.pkl` |
| **Tài nguyên** | CPU cao (xử lý ảnh) | I/O đĩa (đọc file) |

---

## 💡 Ví Dụ Thực Tế

### Scenario 1: Lần đầu sử dụng
```
1. Bạn có folder "images/" với 5000 ảnh
2. Click "Build Index"
3. Hệ thống extract features từ 5000 ảnh (mất ~5 phút)
4. Lưu vào "image_index.pkl"
5. ✅ Sẵn sàng tìm kiếm
```

### Scenario 2: Lần sau sử dụng
```
1. Mở lại ứng dụng
2. Click "Load Index"
3. Hệ thống đọc "image_index.pkl" (mất < 1 giây)
4. ✅ Sẵn sàng tìm kiếm ngay
```

### Scenario 3: Thêm ảnh mới
```
1. Thêm 100 ảnh mới vào folder "images/"
2. Click "Build Index" (force rebuild)
3. Hệ thống extract lại từ 5100 ảnh
4. Lưu index mới
5. ✅ Index đã cập nhật
```

---

## 🎯 Tóm Tắt

- **Build Index** = Xây dựng index mới (chậm, nhưng cần thiết lần đầu)
- **Load Index** = Dùng index đã có (nhanh, tiện lợi)

**Quy trình khuyến nghị:**
1. Lần đầu: **Build Index** (1 lần)
2. Các lần sau: **Load Index** (nhanh hơn nhiều)
3. Khi thêm ảnh: **Build Index** lại (force rebuild)

---

## 📁 File Index

File `image_index.pkl` chứa:
```python
{
    'image_paths': [
        'images/1.jpg',
        'images/2.jpg',
        ...
    ],
    'features': numpy array (N × 132)
    # N = số lượng ảnh
    # 132 = số features mỗi ảnh
}
```

File này có thể **rất lớn**:
- 5000 ảnh × 132 features × 8 bytes ≈ **5-10 MB**
- 10,000 ảnh ≈ **10-20 MB**

