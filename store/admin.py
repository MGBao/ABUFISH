from django.contrib import admin
from django.db import models
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from django.utils.html import format_html
from .models import (
    Address, Category, Favorite, Invoice, Lastseen_Product,
    Notification, Product, Cart, Order, Comment, Profile,
    ProductReview, UserVoucher, Voucher, ChatMessage, PaymentSummary
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
    change_list_template = 'admin/cart_by_user.html'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from .models import Cart
        from django.contrib.auth.models import User

        carts = Cart.objects.all().order_by('user')
        users = User.objects.filter(cart__isnull=False).distinct()

        data = []
        for user in users:
            user_carts = carts.filter(user=user)
            total = sum(item.quantity * item.product.price for item in user_carts)
            data.append({
                'user': user,
                'carts': user_carts,
                'total': total
            })

        extra_context = extra_context or {}
        extra_context['data'] = data
        return super().changelist_view(request, extra_context=extra_context)

# --- ORDER ADMIN (cập nhật, có badge nguồn tiền) ---
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'payment_badge', 'status', 'ordered_date')
    list_editable = ('quantity', 'status')
    list_filter = ('status', 'payment_method', 'ordered_date')
    list_per_page = 20
    search_fields = ('user__username', 'product__title')
    def has_delete_permission(self, request, obj=None):
        return False
    def payment_badge(self, obj):
        colors = {
            'cod':    ('#e8f5e9', '#2e7d32', '🚚 COD'),
            'paypal': ('#e3f2fd', '#1565c0', '💳 PayPal'),
            'momo':   ('#fce4ec', '#880e4f', '📱 MoMo'),
            'vnpay':  ('#fff8e1', '#e65100', '🏦 VNPay'),
        }
        bg, color, label = colors.get(obj.payment_method, ('#f5f5f5', '#555', obj.payment_method))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;'
            'border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
            bg, color, label
        )
    payment_badge.short_description = "Nguồn tiền"

# --- CHAT BOX ---
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_message', 'is_admin_reply', 'created_at')
    list_filter = ('is_admin_reply', 'user', 'created_at')
    search_fields = ('user__username', 'message')
    ordering = ('-created_at',)

    def short_message(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message
    short_message.short_description = "Nội dung tin nhắn"

# --- THỐNG KÊ NGUỒN TIỀN ---
class PaymentSummaryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/payment_summary.html'

    def changelist_view(self, request, extra_context=None):
        summary = (
            Order.objects
            .filter(status='Delivered')
            .values('payment_method')
            .annotate(
                total_orders=Count('id'),
                total_revenue=Coalesce(
                    Sum(
                        models.F('quantity') * models.F('product__price'),
                        output_field=DecimalField()
                    ),
                    0,
                    output_field=DecimalField()
                )
            )
            .order_by('-total_revenue')
        )

        grand_total = Order.objects.filter(status='Delivered').aggregate(
            total=Coalesce(
                Sum(
                    models.F('quantity') * models.F('product__price'),
                    output_field=DecimalField()
                ),
                0,
                output_field=DecimalField()
            )
        )['total']

        extra_context = extra_context or {}
        extra_context['summary'] = summary
        extra_context['grand_total'] = grand_total
        return super().changelist_view(request, extra_context=extra_context)


# --- ĐĂNG KÝ ---
admin.site.register(Address, AddressAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(PaymentSummary, PaymentSummaryAdmin)

class CommentAdmin(admin.ModelAdmin):
    change_list_template = 'admin/comment_by_product.html'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from .models import Comment, Product

        products = Product.objects.filter(comments__isnull=False).distinct()

        data = []
        for product in products:
            comments = Comment.objects.filter(product=product).order_by('-date_added')
            data.append({
                'product': product,
                'comments': comments,
            })

        extra_context = extra_context or {}
        extra_context['data'] = data
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Comment, CommentAdmin)
admin.site.register(Notification)
admin.site.register(Profile)
admin.site.register(ProductReview)
admin.site.register(Favorite)
admin.site.register(Voucher)
admin.site.register(UserVoucher)
class InvoiceAdmin(admin.ModelAdmin):
    change_list_template = 'admin/invoice_by_user.html'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from .models import Invoice
        from django.contrib.auth.models import User

        invoices = Invoice.objects.all().order_by('-ordered_date')

        users = User.objects.filter(invoice__in=invoices).distinct()
        data = []
        for user in users:
            data.append({
                'user': user,
                'invoices': invoices.filter(user=user)
            })

        extra_context = extra_context or {}
        extra_context['data'] = data
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Invoice, InvoiceAdmin)
class LastseenProductAdmin(admin.ModelAdmin):
    change_list_template = 'admin/lastseen_by_user.html'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from .models import Lastseen_Product
        from django.contrib.auth.models import User

        users = User.objects.filter(
            lastseen_product__isnull=False
        ).distinct()

        data = []
        for user in users:
            products = Lastseen_Product.objects.filter(
                user=user
            ).order_by('-created_at')
            data.append({
                'user': user,
                'products': products
            })

        extra_context = extra_context or {}
        extra_context['data'] = data
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Lastseen_Product, LastseenProductAdmin)