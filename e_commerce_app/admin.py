from django.contrib import admin
from .models import Product, Order, OrderItem, Category
from django.utils.html import format_html

# Custom Product Admin with image preview
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'image_tag')
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover;" />', obj.image.url)
        return "(No Image)"
    image_tag.short_description = 'Image Preview'

admin.site.register(Product, ProductAdmin)

# Inline Order Items inside Orders
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Custom Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'phone', 'address', 'created_at')
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(Category)
