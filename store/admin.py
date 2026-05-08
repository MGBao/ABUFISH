from django.contrib import admin
from .models import (
    Address, Category, Favorite, Invoice, Lastseen_Product, 
    Notification, Product, Cart, Order, Comment, Profile, 
    ProductReview, UserVoucher, Voucher, ChatMessage  
)



class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'locality', 'city', 'state')
    list_filter = ('city', 'state')
    list_per_page = 10
    search_fields = ('locality', 'city', 'state')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category_image', 'is_active', 'is_featured', 'updated_at')
    list_editable = ('slug', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured')
    list_per_page = 10
    search_fields = ('title', 'description')
    prepopulated_fields = {"slug": ("title", )}

class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'product_image', 'is_active', 'is_featured', 'updated_at')
    list_editable = ('slug', 'category', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured')
    list_per_page = 10
    search_fields = ('title', 'category__title', 'short_description')
    prepopulated_fields = {"slug": ("title", )}

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    list_editable = ('quantity',)
    list_filter = ('created_at',)
    list_per_page = 20
    search_fields = ('user', 'product')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'status', 'ordered_date')
    list_editable = ('quantity', 'status')
    list_filter = ('status', 'ordered_date')
    list_per_page = 20
    search_fields = ('user', 'product')

# --- PHẦN QUẢN LÝ CHAT BOX MỚI ---

class ChatMessageAdmin(admin.ModelAdmin):
    # Hiển thị thông tin ra danh sách để ông dễ nhìn
    list_display = ('user', 'short_message', 'is_admin_reply', 'created_at')
    # Bộ lọc bên phải: giúp ông lọc nhanh tin nhắn chưa trả lời (is_admin_reply = False)
    list_filter = ('is_admin_reply', 'user', 'created_at')
    # Tìm kiếm theo tên khách hoặc nội dung
    search_fields = ('user__username', 'message')
    # Sắp xếp tin mới nhất lên đầu
    ordering = ('-created_at',)

    # Hàm hiển thị nội dung ngắn để không bị vỡ giao diện bảng
    def short_message(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message
    short_message.short_description = "Nội dung tin nhắn"



admin.site.register(Address, AddressAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin) 

admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(Profile)
admin.site.register(ProductReview)
admin.site.register(Favorite)
admin.site.register(Voucher)
admin.site.register(UserVoucher)
admin.site.register(Invoice)
admin.site.register(Lastseen_Product)