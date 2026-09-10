from django.contrib import admin
from .models import (
    TransactionCategory, Transaction, FeeStructure, Invoice, Payment,
    ItemCategory, InventoryItem, StockMovement,
)


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']
    list_filter = ['type']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'date', 'student', 'staff', 'recorded_by']
    list_filter = ['category', 'date']
    search_fields = ['description']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['school_class', 'academic_year', 'semester', 'amount']
    list_filter = ['academic_year', 'semester', 'school_class']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_structure', 'amount_due', 'due_date']
    list_filter = ['fee_structure']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount_paid', 'date_paid', 'recorded_by']
    list_filter = ['date_paid']
@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'reorder_level']
    list_filter = ['category']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['item', 'movement_type', 'quantity', 'date', 'recorded_by']
    list_filter = ['movement_type', 'date']
    