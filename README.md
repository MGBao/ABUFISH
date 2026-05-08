
# Đề tài website bán cá cảnh trực tuyến

## Ngôn ngữ lập trình
* [Django - Python](https://https://www.djangoproject.com//)
* HTML/CSS
* Javascript

### Các phần mềm cần cài trước trong máy


  pip install django

  pip install pillow


   ```
2. Chạy chương trình 
   
   Window
   ```
   python manage.py runserver
   ```
 
3. Tạo tài khoản admin để truy cập site của admin

     Window
     ```
   python manage.py createsuperuser
   ```
 
   ```
4. Truy cập trang web

    Đường dẫn để sử dụng với user
     ```
    http://127.0.0.1:8000/
    ```
    Đường dẫn vào site admin để quản lý dữ liệu (dùng tài khoản admin để đăng nhập)
     ```
   http://127.0.0.1:8000/admin
   ```



## Chức năng của trang web
* Xem sản phẩm theo độ phổ biến, danh mục, xem gần đây
* Hiện chi tiết các thông số SP
* Thêm SP vào giỏ và đặt SP
* Thông báo like SP và đặt hàng, thêm hàng
* Nhận xét và Đánh giá SP
* Lọc SP theo giá và sắp xếp theo độ phổ biến, giá từ thấp đến cao và ngược lại
* Tìm kiếm sản phẩm theo tên và danh mục
* Hiển thị sản phẩm yêu thích, đơn hàng, hoá đơn và đơn đã mua.
### Người dùng
* Đăng kí tài khoản, đổi mật khẩu dễ dàng
* Người dùng có thể xem sản phẩm, mua sản phẩm
* Lưu hóa đơn mua hàng, sản phẩm từng mua
* Đánh giá sản phẩm
* Sửa đổi thông tin của người dùng
* Lưu sản phẩm được xem gần đây
* Tìm kiếm sản phẩm theo tên hoặc danh mục
### Sản phẩm
* Lưu thông tin cơ bản sản phẩm
* Thống kê lượt xem sản phẩm
* Thống kê đánh giá sản phẩm
