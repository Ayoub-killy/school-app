from django.urls import path
from . import views
from . import dept_views as views_dept

app_name = 'resources'

urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('fee-structures/', views.feestructure_list, name='feestructure_list'),
    path('fee-structures/add/', views.feestructure_create, name='feestructure_create'),
    path('fee-structures/<int:pk>/edit/', views.feestructure_update, name='feestructure_update'),
    path('fee-structures/<int:pk>/delete/', views.feestructure_delete, name='feestructure_delete'),
    path('fee-structures/<int:pk>/generate-invoices/', views.generate_invoices, name='generate_invoices'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('item-categories/', views.itemcategory_list, name='itemcategory_list'),
    path('item-categories/add/', views.itemcategory_create, name='itemcategory_create'),
    path('item-categories/<int:pk>/edit/', views.itemcategory_update, name='itemcategory_update'),
    path('item-categories/<int:pk>/delete/', views.itemcategory_delete, name='itemcategory_delete'),
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_create, name='item_create'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('department/', views_dept.department_dashboard, name='department_dashboard'),
    path('department/demands/', views_dept.demand_list, name='demand_list'),
    path('department/demands/<int:pk>/delete/', views_dept.demand_delete, name='demand_delete'),
    path('department/inventory/', views_dept.department_inventory_list, name='department_inventory_list'),
    path('department/transactions/', views_dept.department_transaction_list, name='department_transaction_list'),
    path('department/report/generate/', views_dept.department_report_generate, name='department_report_generate'),
    path('reports/', views_dept.head_reports_list, name='head_reports_list'),
    path('department-comparison/', views.department_comparison, name='department_comparison'),
]
