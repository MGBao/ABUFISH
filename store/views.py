import decimal
from datetime import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q, F, Avg, Count
from django.views.generic import ListView
from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from store.models import (
    Address, Cart, Category, Lastseen_Product, Notification, 
    Order, Product, Comment, Profile, ProductReview, Favorite, 
    Invoice, Voucher, UserVoucher, ChatMessage  
)
from .forms import RegistrationForm, AddressForm, CommentForm, ProfileForm, RatingForm


def home(request):
    user = request.user
    categories = Category.objects.filter(is_active=True, is_featured=True).order_by('-count')[:4]
    products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    products_popular = Product.objects.all().order_by('-count')[:8]
    all_categories = Category.objects.all()
    all_products = []
    for category in all_categories:
        items = Product.objects.filter(category=category)[:8]
        all_products.extend(list(items))
    if request.GET.get('gmail'):
        messages.success(request, "Đăng ký nhận thông báo thành công!")
    context = {'categories': categories, 'products': products, 'products_popular': products_popular, 'all_categories': all_categories, 'all_products': all_products}
    if user.is_authenticated:
        lastseen = Lastseen_Product.objects.filter(user=user).order_by('-created_at')[:4]
        context['lastseen_products'] = [i.product for i in lastseen]
    return render(request, 'store/index.html', context)

def detail(request, slug):
    user = request.user
    product = get_object_or_404(Product, slug=slug)
    Product.objects.filter(slug=slug).update(count=F('count') + 1)
    Category.objects.filter(title=product.category.title).update(count=F('count') + 1)
    related_products = Product.objects.exclude(id=product.id).filter(is_active=True, category=product.category)[:8]
    avg = ProductReview.objects.filter(product=product).aggregate(Avg('review_rating'))
    count_buy = Order.objects.filter(product=product, status='Delivered').count()
    checklike = Favorite.objects.filter(user=user, product=product) if user.is_authenticated else None
    if user.is_authenticated:
        Lastseen_Product.objects.filter(user=user, product=product).delete()
        Lastseen_Product.objects.create(user=user, product=product)
    if request.method == 'POST':
        if 'content' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                Comment.objects.create(product=product, user=user, commenter_name=user.username, comment_body=form.cleaned_data['content'])
                return redirect('store:product-detail', slug=product.slug)
        elif 'review_rating' in request.POST:
            form1 = RatingForm(request.POST)
            if form1.is_valid():
                ProductReview.objects.update_or_create(
                    user=user, product=product,
                    defaults={
                        'review_text': form1.cleaned_data['review_text'],
                        'review_rating': form1.cleaned_data['review_rating']
                    }
                )
                messages.success(request, "Đánh giá của bạn đã được ghi nhận!")
                return redirect('store:product-detail', slug=product.slug)
    context = {'product': product, 'related_products': related_products, 'avg': avg, 'checklike': checklike, 'count': count_buy, 'form': CommentForm(), 'form1': RatingForm()}
    return render(request, 'store/detail.html', context)

def all_categories(request):
    return render(request, 'store/categories.html', {'categories': Category.objects.filter(is_active=True)})

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category)
    filter_price = request.GET.get('filter_price', '')
    sorting = request.GET.get('sorting', '')
    price_map = {'1': (0, 100000), '2': (100000, 200000), '3': (200000, 400000), '4': (400000, 1000000), '5': (1000000, 99999999)}
    if filter_price in price_map:
        products = products.filter(price__gte=price_map[filter_price][0], price__lte=price_map[filter_price][1])
    if sorting == "high-low": products = products.order_by('-price')
    elif sorting == "low-high": products = products.order_by('price')
    elif sorting == "popularity": products = products.annotate(num_orders=Count('order')).order_by('-num_orders')
    paginator = Paginator(products, 9)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    context = {'category': category, 'products': page, 'all_categories': Category.objects.filter(is_active=True), 'all': products}
    return render(request, 'store/category_products.html', context)

@login_required
def cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    amount = sum(item.quantity * item.product.price for item in cart_items)
    shipping = decimal.Decimal(35000)
    code = request.GET.get('voucher')
    if code:
        v = Voucher.objects.filter(code=code, is_active=True).first()
        if v:
            uv, _ = UserVoucher.objects.get_or_create(user=user, voucher=v, defaults={'count': 0})
            if uv.count < 3:
                if v.type == 1: shipping = decimal.Decimal(0) if code != "ABUXINCHAO" else decimal.Decimal(5000)
                else: amount -= (amount * decimal.Decimal(v.discount)) if code != "ABUCAMON" else decimal.Decimal(v.discount)
                messages.success(request, "Áp dụng mã giảm giá thành công!")
            else: messages.error(request, "Mã này đã hết lượt dùng!")
        else: messages.error(request, "Mã không tồn tại!")
    return render(request, 'store/cart.html', {'cart_products': cart_items, 'amount': amount, 'shipping_amount': shipping, 'total_amount': amount + shipping, 'addresses': Address.objects.filter(user=user)})

@login_required
def checkout(request):
    addr_id = request.GET.get('address')
    if not addr_id:
        messages.error(request, "Vui lòng chọn địa chỉ!")
        return redirect('store:cart')
    
    user = request.user
    address = get_object_or_404(Address, id=addr_id)
    cart_items = Cart.objects.filter(user=user)
    total = request.GET.get('total_amount')
    
    # Tạo hóa đơn 
    invoice = Invoice.objects.create(user=user, price=decimal.Decimal(total))
    
    # Tạo từng món hàng 
    for item in cart_items:
        order = Order.objects.create(
            user=user, 
            address=address, 
            product=item.product, 
            quantity=item.quantity, 
            ordered_date=invoice.ordered_date
        )
        
    
        invoice.order.add(order) 
        item.delete()
        
    Notification.objects.create(user=user, content="Đặt hàng thành công!", type=0)
    return redirect('store:orders')

@login_required
def checkout_test(request):
    user = request.user
    tong = request.GET.get('total_amount', 0)
    if request.method == 'POST':
        loc = request.POST.get('locality'); cit = request.POST.get('city'); sta = request.POST.get('state')
        if loc and cit and sta:
            addr = Address.objects.create(user=user, locality=loc, city=cit, state=sta)
            inv = Invoice.objects.create(user=user, price=decimal.Decimal(float(tong)))
            for item in Cart.objects.filter(user=user):
                Order.objects.create(user=user, address=addr, product=item.product, quantity=item.quantity)
                item.delete()
            messages.success(request, "Đặt hàng thành công!")
            return redirect('store:orders')
    return render(request, 'store/checkout.html', {'cart': Cart.objects.filter(user=user), 'tong': tong})

def _handle_like(user, product):
    content = f"Bạn đã thích sản phẩm {product.title}"[:70]
    fav = Favorite.objects.filter(user=user, product=product)
    if fav.exists():
        fav.delete()
        Notification.objects.filter(user=user, slug=product.slug, type=1).delete()
        product.likes -= 1
        product.user_likes.remove(user)
    else:
        Favorite.objects.create(user=user, product=product)
        Notification.objects.create(user=user, slug=product.slug, content=content, type=1)
        product.likes += 1
        product.user_likes.add(user)
    product.save()

@login_required
def add_notifi_like_home(request):
    product = get_object_or_404(Product, id=request.GET.get('prod_id'))
    _handle_like(request.user, product)
    return redirect('store:home')

@login_required
def add_notifi_like_cp(request):
    product = get_object_or_404(Product, id=request.GET.get('prod_id'))
    _handle_like(request.user, product)
    return redirect('store:category-products', product.category.slug)

@login_required
def add_notifi_like_p(request):
    product = get_object_or_404(Product, id=request.GET.get('prod_id'))
    _handle_like(request.user, product)
    return redirect('store:product-detail', product.slug)

@login_required
def add_notifi_like_rp(request):
    product = get_object_or_404(Product, id=request.GET.get('related_prod_id'))
    _handle_like(request.user, product)
    return redirect('store:product-detail', product.slug)

class RegistrationView(View):
    def get(self, request): return render(request, 'account/register.html', {'form': RegistrationForm()})
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đăng ký thành công!")
            return redirect('store:login')
        return render(request, 'account/register.html', {'form': form})

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    form = ProfileForm(instance=request.user.profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid(): 
            form.save()
            messages.success(request, "Đã cập nhật profile!")
    return render(request, 'account/profile.html', {'orders': orders, 'form': form, 'addresses': Address.objects.filter(user=request.user)})

@method_decorator(login_required, name='dispatch')
class AddressView(View):
    def get(self, request): return render(request, 'account/add_address.html', {'form': AddressForm()})
    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()
            # Lưu SĐT vào profile nếu có
            phone = request.POST.get('phone', '')
            if phone:
                request.user.profile.phone = phone
                request.user.profile.save()
            return redirect('store:profile')
        return render(request, 'account/add_address.html', {'form': form})

@login_required
def remove_address(request, id):
    get_object_or_404(Address, user=request.user, id=id).delete()
    return redirect('store:profile')

@login_required
def add_to_cart(request):
    product = get_object_or_404(Product, id=request.GET.get('prod_id'))
    quantity = int(request.GET.get('quantity', 1))
    item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()
    return redirect('store:cart')

@login_required
def plus_cart(request, cart_id):
    item = get_object_or_404(Cart, id=cart_id, user=request.user)
    item.quantity += 1; item.save()
    return redirect('store:cart')

@login_required
def minus_cart(request, cart_id):
    item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if item.quantity > 1: item.quantity -= 1; item.save()
    else: item.delete()
    return redirect('store:cart')

@login_required
def remove_cart(request, cart_id):
    get_object_or_404(Cart, id=cart_id, user=request.user).delete()
    return redirect('store:cart')

@login_required
def orders(request):
    return render(request, 'store/orders.html', {'orders': Order.objects.filter(user=request.user).order_by('-ordered_date')})

@login_required
def like_products(request):
    return render(request, 'store/like_products.html', {'favorites': Favorite.objects.filter(user=request.user)})

@login_required
def remove_like(request, favorite_id):
    fav = get_object_or_404(Favorite, id=favorite_id, user=request.user)
    fav.product.likes -= 1; fav.product.user_likes.remove(request.user); fav.product.save()
    fav.delete()
    return redirect('store:like-products')

@login_required
def invoice(request):
    return render(request, 'store/invoice.html', {'billings': Invoice.objects.filter(user=request.user).order_by('-ordered_date')})

@login_required
def purchase_orders(request):
    return render(request, 'store/purchase_orders.html', {'orders': Order.objects.filter(user=request.user, status='Delivered')})

@login_required
def billing(request): return render(request, 'store/billing.html')

def shop(request): return render(request, 'store/shop.html')

def introduce(request): return render(request, 'store/introduce.html')

def test(request): return render(request, 'store/test.html')

class SearchView(ListView):
    model = Product
    template_name = 'store/search.html'
    context_object_name = 'all_search_results'
    def get_queryset(self):
        query = self.request.GET.get('query')
        return Product.objects.filter(Q(title__icontains=query) | Q(category__title__icontains=query)) if query else Product.objects.none()

# HỆ THỐNG CHAT
@csrf_exempt
@login_required
def send_message(request):
    if request.method == 'POST':
        try:
            user_msg = request.POST.get('message', '')
            if not user_msg:
                import json
                data = json.loads(request.body)
                user_msg = data.get('message', '')

            user_msg_lower = user_msg.lower()
            bot_reply = "Xin Chào ! Tui là AI Abufish. Bạn muốn hỏi về cá hay giá cả nè?"

            if any(kw in user_msg_lower for kw in ["giá", "nhiêu", "bao nhiêu", "mua"]):
                prods = Product.objects.filter(title__icontains=user_msg).distinct()
                if not prods:
                    words = user_msg.split()
                    for word in words:
                        if len(word) > 2:
                            prods = Product.objects.filter(title__icontains=word)
                            if prods:
                                break
                if prods:
                    bot_reply = "Hiện có: " + ", ".join([f"{p.title} ({int(p.price):,}đ)".replace(",", ".") for p in prods[:3]])
                else:
                    bot_reply = "Xin lỗi, tui không tìm thấy sản phẩm phù hợp. Có thể mô tả rõ hơn không?"

            elif any(kw in user_msg_lower for kw in ["hello", "chào", "xin chào", "hi"]):
                bot_reply = "Chào nhé! Chúc một ngày tốt lành. Tui có thể giúp gì ?"

            elif any(kw in user_msg_lower for kw in ["danh mục", "loại", "có gì", "bán gì"]):
                categories = Category.objects.filter(is_active=True)[:5]
                bot_reply = "Abufish có các danh mục: " + ", ".join([c.title for c in categories])

            elif any(kw in user_msg_lower for kw in ["cá", "fish"]):
                prods = Product.objects.filter(title__icontains=user_msg_lower).distinct()
                if not prods:
                    words = user_msg_lower.split()
                    for word in words:
                        if len(word) > 2:
                            prods = Product.objects.filter(title__icontains=word)
                            if prods:
                                break
                if prods:
                    bot_reply = "Tui tìm thấy: " + ", ".join([f"{p.title} ({int(p.price):,}đ)".replace(",", ".") for p in prods[:3]])
                else:
                    bot_reply = "Xin lỗi, tui không tìm thấy loại cá đó. Hãy thử tìm loại khác nhé!"

            ChatMessage.objects.create(user=request.user, message=user_msg, is_admin_reply=False)
            ChatMessage.objects.create(user=request.user, message=bot_reply, is_admin_reply=True)

            return JsonResponse({'status': 'success', 'reply': bot_reply})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def get_messages(request):
    messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')
    messages_list = [{
        'message': msg.message,
        'is_admin_reply': msg.is_admin_reply
    } for msg in messages]
    return JsonResponse({'messages': messages_list})