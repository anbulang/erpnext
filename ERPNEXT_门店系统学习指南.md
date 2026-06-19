# ERPNext 门店系统 - 由浅入深学习指南

> 从零基础到精通 ERPNext POS 系统，应用于自己的门店业务

---

## 📚 目录

1. [第一层：核心概念入门](#第一层核心概念入门)
2. [第二层：Frappe 框架基础](#第二层frappe-框架基础)
3. [第三层：门店核心模块](#第三层门店核心模块)
4. [第四层：业务流程深入](#第四层业务流程深入)
5. [第五层：定制化开发](#第五层定制化开发)
6. [实战项目：构建自己的门店系统](#实战项目构建自己的门店系统)

---

## 第一层：核心概念入门

### 1.1 ERPNext 是什么？

**三句话理解 ERPNext：**
1. ERPNext **不是独立软件**，而是一个运行在 **Frappe Framework** 上的"应用（App）"
2. 它像一个"**业务积木盒**"，由 521 个 DocType（业务对象）组成
3. 门店系统只需要其中的 **10-15 个核心 DocType**

### 1.2 关键术语速查表

| 术语 | 含义 | 类比 |
|------|------|------|
| **DocType** | 业务对象定义 | 类似数据库表 + 业务逻辑类 |
| **Doc / Document** | DocType 的实例 | 类似一条数据记录 |
| **Controller** | 服务端业务逻辑 | Django 的 Model + View |
| **Hooks** | 应用与框架的接口 | WordPress 的插件钩子 |
| **bench** | 开发/运维命令行工具 | npm/composer/artisan 的组合 |
| **POS** | Point of Sale（销售点） | 收银系统 |
| **Item** | 商品/产品 | 你门店卖的东西 |
| **Stock Entry** | 库存变动单 | 入库/出库/调拨 |

### 1.3 架构三层模型

```
┌─────────────────────────────────────────┐
│     你的门店定制层 (Custom App)          │  ← 第五层：你的代码
├─────────────────────────────────────────┤
│     ERPNext 应用层 (本仓库)              │  ← 第三层：业务模块
├─────────────────────────────────────────┤
│     Frappe Framework                     │  ← 第二层：框架基础
├─────────────────────────────────────────┤
│     MariaDB + Redis + Node.js            │  ← 第一层：基础设施
└─────────────────────────────────────────┘
```

---

## 第二层：Frappe 框架基础

### 2.1 必须理解的框架概念

#### 2.1.1 DocType = Schema + Logic + UI

每个 DocType 都是一个**目录**，包含：

```
erpnext/accounts/doctype/pos_invoice/
├── pos_invoice.json          # 数据结构定义（字段、权限、索引）
├── pos_invoice.py            # 服务端业务逻辑（Python）
├── pos_invoice.js            # 客户端脚本（表单行为）
├── pos_invoice_dashboard.py # 仪表盘配置
├── test_pos_invoice.py       # 单元测试
└── regional/                 # 区域化逻辑（如税务）
```

**关键文件说明：**

**`.json` 文件** - 定义字段结构：
```json
{
  "fields": [
    {
      "fieldname": "customer",
      "fieldtype": "Link",
      "label": "客户",
      "options": "Customer",
      "reqd": 1
    },
    {
      "fieldname": "grand_total",
      "fieldtype": "Currency",
      "label": "总金额",
      "read_only": 1
    }
  ]
}
```

**`.py` 文件** - 定义业务逻辑：
```python
class POSInvoice(SalesInvoice):
    def validate(self):
        # 保存前校验
        super().validate()
        self.validate_pos_payments()
    
    def on_submit(self):
        # 提交后处理（更新库存、会计分录）
        super().on_submit()
        self.update_stock_ledger()
```

**`.js` 文件** - 定义前端行为：
```javascript
frappe.ui.form.on('POS Invoice', {
    refresh: function(frm) {
        // 表单刷新时的逻辑
        frm.add_custom_button('打印收据', function() {
            frm.print_doc();
        });
    },
    
    customer: function(frm) {
        // 客户选择后自动填充信息
        frappe.call({
            method: 'get_customer_info',
            args: {customer: frm.doc.customer},
            callback: function(r) {
                frm.set_value('customer_name', r.message.name);
            }
        });
    }
});
```

#### 2.1.2 生命周期钩子（核心机制）

每个文档都有固定的生命周期，可以在关键节点插入逻辑：

```python
class MyDocType(Document):
    def validate(self):
        """保存前校验（草稿/提交前都会触发）"""
        if self.qty < 0:
            frappe.throw("数量不能为负")
    
    def before_save(self):
        """即将保存到数据库"""
        self.total = self.qty * self.rate
    
    def after_insert(self):
        """首次插入数据库后"""
        self.send_notification()
    
    def on_submit(self):
        """提交后（不可再编辑）"""
        self.update_stock()
        self.make_gl_entries()
    
    def on_cancel(self):
        """取消后（反操作）"""
        self.reverse_stock()
        self.reverse_gl_entries()
    
    def on_trash(self):
        """删除前"""
        if self.docstatus == 1:
            frappe.throw("不能删除已提交的单据")
```

**状态流转图：**
```
创建 → validate() → before_save() → after_insert() → 草稿状态
      ↓
      提交 → validate() → before_submit() → on_submit() → 已提交状态
      ↓
      取消 → on_cancel() → 已取消状态
      ↓
      删除 → on_trash() → 已删除
```

#### 2.1.3 核心 API 速查

```python
# ========== 数据库操作 ==========
# 创建新文档
doc = frappe.new_doc("Item")
doc.item_code = "ITEM-001"
doc.item_name = "可乐"
doc.insert()  # 保存草稿
doc.submit()  # 提交

# 读取文档
doc = frappe.get_doc("Item", "ITEM-001")
doc.standard_rate = 5.0
doc.save()

# 查询列表
items = frappe.get_all(
    "Item",
    filters={"item_group": "饮料"},
    fields=["name", "item_name", "standard_rate"],
    limit=20
)

# 原生 SQL（少用）
frappe.db.sql("""
    SELECT item_code, SUM(actual_qty) 
    FROM `tabBin` 
    WHERE warehouse='主仓'
    GROUP BY item_code
""", as_dict=True)

# ========== 权限检查 ==========
if frappe.has_permission("POS Invoice", "write"):
    doc.save()

# ========== 异常处理 ==========
frappe.throw("库存不足")  # 抛出红色错误
frappe.msgprint("操作成功")  # 蓝色提示

# ========== 后台任务 ==========
frappe.enqueue(
    method="my_app.tasks.send_email",
    queue='long',
    timeout=300,
    customer=doc.customer
)

# ========== 缓存 ==========
value = frappe.cache().get_value("key")
frappe.cache().set_value("key", value, expires_in_sec=3600)
```

### 2.2 hooks.py - 应用的总配置文件

`erpnext/hooks.py` 是 ERPNext 与 Frappe 的**唯一契约**，理解它就理解了整个应用的结构：

```python
# ========== 基本信息 ==========
app_name = "erpnext"
app_title = "ERPNext"

# ========== 前端资源 ==========
app_include_js = "erpnext.bundle.js"  # 全局 JS
app_include_css = "erpnext.bundle.css"

# ========== 文档事件钩子 ==========
doc_events = {
    # 所有 DocType 都触发
    "*": {
        "validate": [
            "erpnext.support.doctype.service_level_agreement.service_level_agreement.apply"
        ]
    },
    
    # 特定 DocType
    "Stock Entry": {
        "on_submit": "erpnext.stock.doctype.material_request.material_request.update_completed_qty",
        "on_cancel": "erpnext.stock.doctype.material_request.material_request.update_completed_qty"
    },
    
    # 销售发票提交后的区域化处理
    "Sales Invoice": {
        "on_submit": ["erpnext.regional.italy.utils.sales_invoice_on_submit"]
    }
}

# ========== 定时任务 ==========
scheduler_events = {
    "hourly": [
        "erpnext.projects.doctype.project.project.hourly_reminder"
    ],
    "daily_maintenance": [
        "erpnext.stock.reorder_item.reorder_item",  # 自动补货
        "erpnext.assets.doctype.asset.depreciation.post_depreciation_entries"  # 资产折旧
    ]
}

# ========== 门户路由 ==========
website_route_rules = [
    {"from_route": "/orders", "to_route": "Sales Order"},
    {"from_route": "/invoices", "to_route": "Sales Invoice"}
]

# ========== 启动钩子 ==========
after_install = "erpnext.setup.install.after_install"
boot_session = "erpnext.startup.boot.boot_session"
```

---

## 第三层：门店核心模块

### 3.1 门店系统需要的 DocType 地图

```
门店业务流程               对应 DocType                    路径
─────────────────────────────────────────────────────────────
【基础设置】
├─ 商品管理               Item                          stock/doctype/item/
├─ 商品分类               Item Group                    setup/doctype/item_group/
├─ 计量单位               UOM                           setup/doctype/uom/
├─ 仓库                   Warehouse                     stock/doctype/warehouse/
├─ 客户                   Customer                      selling/doctype/customer/
├─ 供应商                 Supplier                      buying/doctype/supplier/
└─ 价格表                 Price List                    stock/doctype/price_list/

【POS 收银】
├─ POS 配置               POS Profile                   accounts/doctype/pos_profile/
├─ 班次开始               POS Opening Entry             accounts/doctype/pos_opening_entry/
├─ 收银单                 POS Invoice                   accounts/doctype/pos_invoice/
└─ 班次结束               POS Closing Entry             accounts/doctype/pos_closing_entry/

【库存管理】
├─ 采购订单               Purchase Order                buying/doctype/purchase_order/
├─ 采购收货               Purchase Receipt              stock/doctype/purchase_receipt/
├─ 库存调整               Stock Entry                   stock/doctype/stock_entry/
├─ 库存余额               Bin                           stock/doctype/bin/
├─ 序列号                 Serial No                     stock/doctype/serial_no/
└─ 批次                   Batch                         stock/doctype/batch/

【财务】
├─ 销售发票               Sales Invoice                 accounts/doctype/sales_invoice/
├─ 支付条目               Payment Entry                 accounts/doctype/payment_entry/
└─ 总账分录               GL Entry                      accounts/doctype/gl_entry/
```

### 3.2 核心模块详解

#### 3.2.1 Item（商品）- 一切的基础

**关键字段：**
```python
# erpnext/stock/doctype/item/item.json (简化)
{
    "item_code": "COLA-500",           # 商品编码
    "item_name": "可口可乐 500ml",      # 商品名称
    "item_group": "饮料",              # 分类
    "stock_uom": "瓶",                 # 库存单位
    "is_stock_item": 1,                # 是否库存商品
    "has_serial_no": 0,                # 是否序列号管理
    "has_batch_no": 1,                 # 是否批次管理
    "valuation_method": "FIFO",        # 计价方式
    "standard_rate": 5.0,              # 标准售价
    "barcodes": [                      # 条形码（可多个）
        {"barcode": "6901234567890"}
    ],
    "item_defaults": [                 # 默认设置
        {
            "company": "我的门店",
            "default_warehouse": "主仓",
            "expense_account": "销售成本 - MD",
            "income_account": "销售收入 - MD"
        }
    ]
}
```

**常用方法：**
```python
# erpnext/stock/doctype/item/item.py
class Item(Document):
    def validate(self):
        # 自动生成商品编码
        if not self.item_code:
            self.item_code = make_autoname(self.naming_series)
        
        # 校验条形码唯一性
        self.validate_barcode()
        
        # 检查是否变更了关键字段
        if self.has_value_changed("is_stock_item"):
            self.validate_stock_exists()
    
    def on_trash(self):
        # 删除前检查是否有交易记录
        if self.check_if_sle_exists():
            frappe.throw("此商品已有出入库记录，不能删除")
```

**实战示例 - 批量导入商品：**
```python
# 从 Excel 导入商品
import frappe

def import_items_from_excel(file_path):
    import pandas as pd
    df = pd.read_excel(file_path)
    
    for index, row in df.iterrows():
        if frappe.db.exists("Item", row['商品编码']):
            continue  # 跳过已存在的
        
        item = frappe.new_doc("Item")
        item.item_code = row['商品编码']
        item.item_name = row['商品名称']
        item.item_group = row['分类']
        item.stock_uom = row['单位']
        item.standard_rate = row['售价']
        item.is_stock_item = 1
        
        # 添加条形码
        item.append("barcodes", {
            "barcode": row['条形码']
        })
        
        # 设置默认仓库
        item.append("item_defaults", {
            "company": "我的门店",
            "default_warehouse": "主仓"
        })
        
        item.insert()
        frappe.db.commit()
        print(f"导入成功: {item.item_code}")
```

#### 3.2.2 POS Profile（收银配置）- 收银系统的大脑

**用途：** 定义每个收银台的行为规则

**核心配置：**
```python
{
    "name": "门店1-收银台1",
    "company": "我的门店",
    "warehouse": "门店1-主仓",            # 默认仓库
    "customer": "散客",                   # 默认客户
    "selling_price_list": "零售价",       # 价格表
    
    # 支付方式
    "payments": [
        {"mode_of_payment": "现金", "default": 1},
        {"mode_of_payment": "微信支付"},
        {"mode_of_payment": "支付宝"}
    ],
    
    # 行为控制
    "update_stock": 1,                    # 自动更新库存
    "validate_stock_on_save": 1,          # 保存时校验库存
    "allow_rate_change": 1,               # 允许改价
    "allow_discount_change": 1,           # 允许改折扣
    "print_receipt_on_order_complete": 1, # 完成后打印小票
    "hide_unavailable_items": 1,          # 隐藏缺货商品
    
    # 适用范围
    "applicable_for_users": [             # 只有这些用户能用
        {"user": "cashier1@mystore.com"}
    ],
    "item_groups": [                      # 只能卖这些分类
        {"item_group": "饮料"},
        {"item_group": "零食"}
    ]
}
```

#### 3.2.3 POS Invoice（收银单）- 收银的核心

**继承链：** `POSInvoice → SalesInvoice → SellingController → StockController → AccountsController`

这意味着它自动拥有：
- **AccountsController**：自动生成会计分录
- **StockController**：自动生成库存分录
- **SellingController**：销售逻辑（折扣、税费）

**核心字段：**
```python
{
    "customer": "C-001",
    "posting_date": "2026-06-19",
    "pos_profile": "门店1-收银台1",
    
    # 商品明细
    "items": [
        {
            "item_code": "COLA-500",
            "item_name": "可口可乐 500ml",
            "qty": 2,
            "rate": 5.0,
            "amount": 10.0,
            "warehouse": "门店1-主仓"
        }
    ],
    
    # 支付明细
    "payments": [
        {
            "mode_of_payment": "微信支付",
            "amount": 10.0,
            "account": "微信支付 - MD"
        }
    ],
    
    "grand_total": 10.0,
    "paid_amount": 10.0,
    "change_amount": 0.0,
    "is_pos": 1,
    "update_stock": 1
}
```

**关键方法：**
```python
# erpnext/accounts/doctype/pos_invoice/pos_invoice.py
class POSInvoice(SalesInvoice):
    def validate(self):
        super().validate()  # 调用父类的所有校验
        
        # POS 特有校验
        self.validate_pos_payments()  # 检查支付金额
        self.validate_stock_availability()  # 检查库存
        self.validate_pos_return()  # 退货逻辑
    
    def on_submit(self):
        # 父类已处理：库存分录 + 会计分录
        super().on_submit()
        
        # POS 特有逻辑
        if self.redeem_loyalty_points:
            self.redeem_loyalty_program()  # 积分兑换
        
        if self.coupon_code:
            self.apply_coupon_code()  # 优惠券核销
```

**实战示例 - 前端创建收银单：**
```javascript
// point_of_sale.js (简化版)
frappe.ui.form.on('POS Invoice', {
    // 扫描条形码
    scan_barcode: function(frm, cdt, cdn) {
        frappe.call({
            method: 'erpnext.selling.page.point_of_sale.point_of_sale.search_by_term',
            args: {
                search_term: frm.doc.scan_barcode,
                warehouse: frm.doc.set_warehouse,
                price_list: frm.doc.selling_price_list
            },
            callback: function(r) {
                if (r.message && r.message.items.length > 0) {
                    add_item_to_cart(frm, r.message.items[0]);
                }
            }
        });
    },
    
    // 结账
    checkout: function(frm) {
        // 校验支付金额
        if (frm.doc.paid_amount < frm.doc.grand_total) {
            frappe.msgprint('支付金额不足');
            return;
        }
        
        // 提交单据
        frm.save('Submit').then(() => {
            // 打印小票
            frm.print_doc();
            
            // 重置表单，开始下一单
            frm.reload_doc();
        });
    }
});

function add_item_to_cart(frm, item) {
    let existing_item = frm.doc.items.find(d => d.item_code === item.item_code);
    
    if (existing_item) {
        // 已存在，数量 +1
        frappe.model.set_value(existing_item.doctype, existing_item.name, 
                               'qty', existing_item.qty + 1);
    } else {
        // 新增行
        let row = frm.add_child('items');
        row.item_code = item.item_code;
        row.item_name = item.item_name;
        row.qty = 1;
        row.rate = item.price_list_rate;
    }
    
    frm.refresh_field('items');
    frm.script_manager.trigger('calculate_taxes_and_totals');
}
```

#### 3.2.4 Stock Entry（库存调整）- 入库/出库/调拨

**核心业务类型：**
```python
STOCK_ENTRY_TYPES = [
    "Material Receipt",      # 物料入库（采购入库、退货入库）
    "Material Issue",        # 物料出库（生产领料、报损）
    "Material Transfer",     # 仓库间调拨
    "Manufacture",           # 生产入库
    "Repack",               # 重新打包
    "Send to Subcontractor" # 发给外协商
]
```

**字段结构：**
```python
{
    "stock_entry_type": "Material Receipt",  # 入库
    "posting_date": "2026-06-19",
    "company": "我的门店",
    
    # 明细行
    "items": [
        {
            "item_code": "COLA-500",
            "qty": 100,              # 数量
            "basic_rate": 3.0,       # 成本价
            "t_warehouse": "门店1-主仓",  # 目标仓库（入库）
            "s_warehouse": None,     # 源仓库（出库时用）
            "batch_no": "BATCH-001", # 批次号
            "serial_no": None        # 序列号（回车分隔）
        }
    ]
}
```

**实战示例 - 采购入库：**
```python
def create_purchase_receipt(purchase_order):
    """根据采购订单创建入库单"""
    doc = frappe.new_doc("Stock Entry")
    doc.stock_entry_type = "Material Receipt"
    doc.company = purchase_order.company
    
    for po_item in purchase_order.items:
        doc.append("items", {
            "item_code": po_item.item_code,
            "qty": po_item.qty,
            "basic_rate": po_item.rate,
            "t_warehouse": po_item.warehouse,
            "purchase_order": purchase_order.name,
            "purchase_order_item": po_item.name
        })
    
    doc.insert()
    doc.submit()  # 提交后自动更新库存
    return doc
```

---

## 第四层：业务流程深入

### 4.1 完整收银流程（含底层机制）

```
┌──────────────────────────────────────────────────────────────┐
│ 1. 开班（POS Opening Entry）                                  │
├──────────────────────────────────────────────────────────────┤
│  收银员登录 → 点击"开始营业" → 填写备用金                      │
│  操作：                                                       │
│    opening = frappe.new_doc("POS Opening Entry")             │
│    opening.pos_profile = "门店1-收银台1"                     │
│    opening.balance_details = [                               │
│        {"mode_of_payment": "现金", "opening_amount": 500}   │
│    ]                                                         │
│    opening.submit()                                          │
└──────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. 收银（POS Invoice）                                        │
├──────────────────────────────────────────────────────────────┤
│  扫码 → 添加商品 → 选支付方式 → 结账                          │
│                                                              │
│  【扫码触发】                                                 │
│  前端：point_of_sale.js 调用                                  │
│    → search_by_term(barcode)                                 │
│    → scan_barcode() 匹配条形码                               │
│    → 返回商品信息 + 价格 + 库存                              │
│                                                              │
│  【添加到购物车】                                             │
│  前端：pos_item_cart.js                                       │
│    → add_child('items') 添加行                               │
│    → calculate_taxes_and_totals() 计算总价                   │
│                                                              │
│  【提交单据】                                                 │
│  后端：POSInvoice.on_submit()                                │
│    ├─ 调用 SalesInvoice.on_submit()                         │
│    │   ├─ 调用 StockController.on_submit()                  │
│    │   │   └─ make_stock_ledger_entry()  【库存分录】       │
│    │   └─ 调用 AccountsController.on_submit()               │
│    │       └─ make_gl_entries()  【会计分录】               │
│    └─ 处理积分/优惠券                                        │
└──────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. 结班（POS Closing Entry）                                  │
├──────────────────────────────────────────────────────────────┤
│  点击"结束营业" → 自动汇总今日交易 → 核对现金                  │
│  操作：                                                       │
│    closing = frappe.new_doc("POS Closing Entry")            │
│    closing.pos_opening_entry = opening.name                  │
│    closing.get_invoices()  # 拉取今日所有单据                │
│    closing.set_difference()  # 计算长短款                    │
│    closing.submit()                                          │
│                                                              │
│  生成报表：                                                   │
│    - 销售额汇总（按支付方式）                                 │
│    - 商品销售明细                                             │
│    - 税金汇总                                                 │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 控制器继承链 - 自动化的秘密

**问题：** 为什么 `POSInvoice.submit()` 会自动更新库存和账目？

**答案：** 多层继承链 + 模板方法模式

```python
# 继承链：
POSInvoice → SalesInvoice → SellingController → StockController → AccountsController

# ========== AccountsController（最底层）==========
# erpnext/controllers/accounts_controller.py
class AccountsController(TransactionBase):
    def on_submit(self):
        # 所有财务单据都会生成会计分录
        self.make_gl_entries()
    
    def make_gl_entries(self):
        """生成会计分录（借贷必相等）"""
        gl_entries = []
        
        # 借：应收账款（或现金）
        gl_entries.append({
            "account": self.debit_to,
            "debit": self.grand_total,
            "party_type": "Customer",
            "party": self.customer
        })
        
        # 贷：销售收入
        for item in self.items:
            gl_entries.append({
                "account": item.income_account,
                "credit": item.amount
            })
        
        # 贷：销项税
        for tax in self.taxes:
            gl_entries.append({
                "account": tax.account_head,
                "credit": tax.tax_amount
            })
        
        make_gl_entries(gl_entries)

# ========== StockController ==========
# erpnext/controllers/stock_controller.py
class StockController(AccountsController):
    def on_submit(self):
        # 先调用父类（生成会计分录）
        super().on_submit()
        
        # 然后生成库存分录
        if self.update_stock:
            self.update_stock_ledger()
    
    def update_stock_ledger(self):
        """生成库存分录（Stock Ledger Entry）"""
        sle_list = []
        
        for item in self.items:
            sle_list.append({
                "item_code": item.item_code,
                "warehouse": item.warehouse,
                "actual_qty": -item.qty,  # 负数 = 出库
                "posting_date": self.posting_date,
                "voucher_type": self.doctype,
                "voucher_no": self.name
            })
        
        make_stock_ledger_entries(sle_list)

# ========== SellingController ==========
# erpnext/controllers/selling_controller.py
class SellingController(StockController):
    def validate(self):
        super().validate()
        
        # 销售特有逻辑
        self.calculate_taxes_and_totals()
        self.calculate_commission()
        self.set_missing_lead_customer_details()

# ========== POSInvoice ==========
# erpnext/accounts/doctype/pos_invoice/pos_invoice.py
class POSInvoice(SalesInvoice):
    def validate(self):
        super().validate()
        # 只需要写 POS 特有的逻辑
        self.validate_pos_payments()
    
    def on_submit(self):
        super().on_submit()
        # 父类已经处理了库存和会计，这里只处理积分
        if self.redeem_loyalty_points:
            self.redeem_loyalty_program()
```

**流程图：**
```
用户调用：pos_invoice.submit()
    ↓
POSInvoice.on_submit()
    ├─ 处理积分
    └─ super().on_submit()  ← 调用父类
        ↓
    SalesInvoice.on_submit()
        ├─ 更新客户未结款
        └─ super().on_submit()  ← 继续调用父类
            ↓
        StockController.on_submit()
            ├─ update_stock_ledger()  【生成库存分录】
            └─ super().on_submit()
                ↓
            AccountsController.on_submit()
                └─ make_gl_entries()  【生成会计分录】
```

### 4.3 实战案例：商品促销打折

**需求：** 买二送一，第三件免费

**实现方式 1：前端脚本（简单场景）**
```javascript
// pos_invoice.js
frappe.ui.form.on('POS Invoice Item', {
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // 每买 3 件，总价按 2 件计算
        if (row.qty >= 3 && row.item_code === 'PROMO-ITEM') {
            let free_qty = Math.floor(row.qty / 3);
            let paid_qty = row.qty - free_qty;
            
            frappe.model.set_value(cdt, cdn, 'rate', 
                (row.price_list_rate * paid_qty) / row.qty);
        }
    }
});
```

**实现方式 2：后端 Pricing Rule（推荐）**
```python
# 创建 Pricing Rule
def setup_buy_2_get_1_free():
    rule = frappe.new_doc("Pricing Rule")
    rule.title = "买二送一"
    rule.apply_on = "Item Code"
    rule.items = [{"item_code": "PROMO-ITEM"}]
    
    # 规则类型
    rule.price_or_product_discount = "Product"
    rule.same_item = 1
    rule.free_item = "PROMO-ITEM"
    
    # 条件：每买 2 件
    rule.min_qty = 2
    rule.free_qty = 1
    rule.free_item_qty_based_on = "Quantity"
    
    # 适用范围
    rule.valid_from = "2026-06-01"
    rule.valid_upto = "2026-06-30"
    rule.company = "我的门店"
    
    rule.insert()
```

**工作原理：** 
- 添加商品时，系统自动检查 Pricing Rule
- 调用 `erpnext.stock.get_item_details.apply_pricing_rule()`
- 自动添加赠品行（`is_free_item = 1`）

---

## 第五层：定制化开发

### 5.1 创建自己的 Custom App

**为什么需要 Custom App？**
- 不直接修改 ERPNext 源码（方便升级）
- 隔离你的业务逻辑
- 可复用到多个站点

**创建步骤：**
```bash
# 1. 创建新应用
cd ~/frappe-bench
bench new-app my_store

# 2. 安装到站点
bench --site mystore.localhost install-app my_store

# 3. 目录结构
my_store/
├── my_store/
│   ├── hooks.py              # 应用配置
│   ├── my_store_module/      # 你的模块
│   │   └── doctype/
│   │       └── store_config/  # 自定义 DocType
│   ├── public/               # 前端资源
│   ├── templates/            # 网页模板
│   └── api.py                # API 接口
├── setup.py
└── requirements.txt
```

### 5.2 常见定制场景

#### 场景 1：扩展 POS Invoice 添加会员卡字段

**方法 1：Custom Field（无需代码）**
```python
# 通过界面：Customize Form → POS Invoice → Add Custom Field
# 或者通过脚本：
frappe.get_doc({
    "doctype": "Custom Field",
    "dt": "POS Invoice",
    "fieldname": "membership_card",
    "label": "会员卡号",
    "fieldtype": "Data",
    "insert_after": "customer"
}).insert()
```

**方法 2：在 Custom App 中用 Property Setter**
```python
# my_store/hooks.py
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["dt", "in", ["POS Invoice", "Customer"]]]
    }
]

# my_store/my_store_module/doctype/store_config/store_config.py
def setup_custom_fields():
    custom_fields = {
        "POS Invoice": [
            {
                "fieldname": "membership_card",
                "label": "会员卡号",
                "fieldtype": "Link",
                "options": "Membership Card",
                "insert_after": "customer"
            },
            {
                "fieldname": "member_discount",
                "label": "会员折扣",
                "fieldtype": "Percent",
                "read_only": 1,
                "insert_after": "membership_card"
            }
        ]
    }
    
    create_custom_fields(custom_fields)
```

#### 场景 2：会员卡自动折扣

**后端钩子：**
```python
# my_store/hooks.py
doc_events = {
    "POS Invoice": {
        "validate": "my_store.api.apply_membership_discount"
    }
}

# my_store/api.py
import frappe

def apply_membership_discount(doc, method):
    """会员卡自动打折"""
    if not doc.membership_card:
        return
    
    # 获取会员等级
    card = frappe.get_doc("Membership Card", doc.membership_card)
    discount = card.discount_percentage
    
    if discount > 0:
        # 应用折扣
        doc.additional_discount_percentage = discount
        doc.member_discount = discount
        
        # 重新计算总价
        doc.calculate_taxes_and_totals()
```

**前端自动填充：**
```javascript
// my_store/public/js/pos_invoice.js
frappe.ui.form.on('POS Invoice', {
    customer: function(frm) {
        // 客户选择后自动获取会员卡
        frappe.call({
            method: 'my_store.api.get_customer_membership',
            args: {customer: frm.doc.customer},
            callback: function(r) {
                if (r.message) {
                    frm.set_value('membership_card', r.message.card_number);
                }
            }
        });
    }
});
```

#### 场景 3：自定义报表 - 每日销售汇总

```python
# my_store/my_store_module/report/daily_sales_summary/daily_sales_summary.py

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    
    return columns, data, None, chart

def get_columns():
    return [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("商品"), "fieldname": "item", "fieldtype": "Link", 
         "options": "Item", "width": 150},
        {"label": _("销量"), "fieldname": "qty", "fieldtype": "Int", "width": 80},
        {"label": _("销售额"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("利润"), "fieldname": "profit", "fieldtype": "Currency", "width": 120}
    ]

def get_data(filters):
    return frappe.db.sql("""
        SELECT 
            pi.posting_date as date,
            pii.item_code as item,
            SUM(pii.qty) as qty,
            SUM(pii.amount) as amount,
            SUM(pii.amount - pii.qty * i.valuation_rate) as profit
        FROM 
            `tabPOS Invoice` pi
        INNER JOIN 
            `tabPOS Invoice Item` pii ON pii.parent = pi.name
        INNER JOIN
            `tabItem` i ON i.name = pii.item_code
        WHERE 
            pi.docstatus = 1
            AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY 
            pi.posting_date, pii.item_code
        ORDER BY 
            pi.posting_date DESC, amount DESC
    """, filters, as_dict=1)

def get_chart(data):
    """生成图表"""
    dates = list(set([d['date'] for d in data]))
    amounts = [sum([d['amount'] for d in data if d['date'] == date]) for date in dates]
    
    return {
        "data": {
            "labels": dates,
            "datasets": [{"name": "销售额", "values": amounts}]
        },
        "type": "line"
    }
```

**对应的 JSON 配置：**
```json
// daily_sales_summary.json
{
    "name": "Daily Sales Summary",
    "report_name": "每日销售汇总",
    "ref_doctype": "POS Invoice",
    "report_type": "Script Report",
    "is_standard": "No",
    "module": "My Store Module"
}
```

#### 场景 4：微信小程序对接

**创建 API 端点：**
```python
# my_store/api.py

@frappe.whitelist(allow_guest=True)
def get_product_list(category=None, search=None):
    """小程序获取商品列表"""
    filters = {"disabled": 0, "is_sales_item": 1}
    
    if category:
        filters["item_group"] = category
    
    if search:
        items = frappe.db.sql("""
            SELECT name, item_name, image, standard_rate, description
            FROM `tabItem`
            WHERE disabled = 0 
              AND is_sales_item = 1
              AND (item_name LIKE %(search)s OR item_code LIKE %(search)s)
        """, {"search": f"%{search}%"}, as_dict=1)
    else:
        items = frappe.get_all("Item", filters=filters, 
                               fields=["name", "item_name", "image", "standard_rate"])
    
    # 获取库存
    for item in items:
        item['stock'] = get_stock_balance(item.name, "门店1-主仓")
    
    return items

@frappe.whitelist()
def create_online_order(items, customer_mobile):
    """小程序下单"""
    # 查找或创建客户
    customer = frappe.db.get_value("Customer", {"mobile_no": customer_mobile})
    if not customer:
        customer_doc = frappe.new_doc("Customer")
        customer_doc.customer_name = customer_mobile
        customer_doc.mobile_no = customer_mobile
        customer_doc.insert(ignore_permissions=True)
        customer = customer_doc.name
    
    # 创建销售订单
    order = frappe.new_doc("Sales Order")
    order.customer = customer
    order.delivery_date = frappe.utils.add_days(frappe.utils.today(), 1)
    
    for item in items:
        order.append("items", {
            "item_code": item['item_code'],
            "qty": item['qty'],
            "rate": item['rate']
        })
    
    order.insert(ignore_permissions=True)
    order.submit()
    
    return {"order_id": order.name, "grand_total": order.grand_total}

def get_stock_balance(item_code, warehouse):
    """获取库存余额"""
    from erpnext.stock.utils import get_stock_balance
    return get_stock_balance(item_code, warehouse)
```

**小程序调用：**
```javascript
// 微信小程序端
wx.request({
    url: 'https://mystore.com/api/method/my_store.api.get_product_list',
    data: {category: '饮料'},
    success: function(res) {
        console.log(res.data.message);  // 商品列表
    }
});
```

---

## 实战项目：构建自己的门店系统

### 项目 1：便利店系统（7天完成）

**Day 1-2：基础配置**
```yaml
任务清单:
  - [ ] 安装 ERPNext（Docker / bench）
  - [ ] 创建公司：我的便利店
  - [ ] 设置仓库：主仓、次仓
  - [ ] 配置会计科目
  - [ ] 创建价格表：零售价、会员价
  - [ ] 导入商品（100-200 SKU）
  - [ ] 设置条形码
```

**Day 3-4：POS 配置**
```yaml
任务清单:
  - [ ] 创建 POS Profile：收银台1、收银台2
  - [ ] 配置支付方式：现金、微信、支付宝、刷卡
  - [ ] 设置默认客户：散客
  - [ ] 配置小票打印格式
  - [ ] 测试完整收银流程（开班→收银→结班）
  - [ ] 配置商品分组（快速选择）
```

**Day 5-6：库存管理**
```yaml
任务清单:
  - [ ] 创建供应商：可口可乐公司、康师傅等
  - [ ] 创建采购订单
  - [ ] 采购入库（Stock Entry）
  - [ ] 设置库存预警（Reorder Level）
  - [ ] 盘点流程（Stock Reconciliation）
  - [ ] 报损流程（Material Issue）
```

**Day 7：报表与优化**
```yaml
任务清单:
  - [ ] 每日销售汇总报表
  - [ ] 畅销商品排行
  - [ ] 库存周转率
  - [ ] 收银员业绩统计
  - [ ] 备份方案
```

### 项目 2：奶茶店系统（进阶）

**特殊需求：**
1. **组合商品（BOM）** - 一杯奶茶由多种原料组成
2. **规格选择** - 大杯/中杯/小杯，冰/热
3. **加料** - 珍珠、椰果、布丁（加价）
4. **会员充值** - 储值卡

**实现方案：**

**1. BOM（物料清单）**
```python
# 奶茶 BOM 配置
bom = frappe.new_doc("BOM")
bom.item = "珍珠奶茶-中杯"
bom.quantity = 1

# 原料明细
bom.append("items", {
    "item_code": "红茶",
    "qty": 0.05,  # kg
    "rate": 80
})
bom.append("items", {
    "item_code": "牛奶",
    "qty": 0.3,   # L
    "rate": 10
})
bom.append("items", {
    "item_code": "珍珠",
    "qty": 0.05,  # kg
    "rate": 20
})
bom.append("items", {
    "item_code": "一次性杯子-中杯",
    "qty": 1,
    "rate": 0.5
})

bom.insert()
bom.submit()
```

**2. 商品变体（Variants）**
```python
# 创建模板商品
template = frappe.new_doc("Item")
template.item_code = "珍珠奶茶-T"
template.item_name = "珍珠奶茶"
template.has_variants = 1

# 定义属性
template.append("attributes", {"attribute": "杯型"})
template.append("attributes", {"attribute": "温度"})
template.insert()

# 创建属性值
frappe.get_doc({
    "doctype": "Item Attribute",
    "attribute_name": "杯型",
    "item_attribute_values": [
        {"attribute_value": "大杯", "abbr": "L"},
        {"attribute_value": "中杯", "abbr": "M"},
        {"attribute_value": "小杯", "abbr": "S"}
    ]
}).insert()

# 自动生成变体（大杯-冰、大杯-热、中杯-冰...）
from erpnext.controllers.item_variant import create_variant
create_variant("珍珠奶茶-T", {"杯型": "大杯", "温度": "冰"})
```

**3. 加料逻辑（Product Bundle）**
```python
# 创建 Product Bundle
bundle = frappe.new_doc("Product Bundle")
bundle.new_item_code = "珍珠奶茶-中杯-加珍珠"
bundle.parent_item = "珍珠奶茶-中杯"

bundle.append("items", {
    "item_code": "珍珠奶茶-中杯",
    "qty": 1
})
bundle.append("items", {
    "item_code": "珍珠（加料）",
    "qty": 1,
    "rate": 2  # 加料费
})

bundle.insert()
```

**4. 会员储值卡**
```python
# 自定义 DocType: Membership Card
{
    "doctype": "Membership Card",
    "fields": [
        {"fieldname": "card_number", "fieldtype": "Data", "unique": 1},
        {"fieldname": "customer", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "balance", "fieldtype": "Currency"},
        {"fieldname": "discount_percentage", "fieldtype": "Percent"}
    ]
}

# 充值 API
@frappe.whitelist()
def recharge_card(card_number, amount):
    card = frappe.get_doc("Membership Card", card_number)
    card.balance += amount
    card.save()
    
    # 记录流水
    frappe.get_doc({
        "doctype": "Card Transaction",
        "card_number": card_number,
        "type": "Recharge",
        "amount": amount
    }).insert()
    
    return card.balance

# POS 支付时扣款
# 在 POS Invoice 的 validate 钩子中
def validate_membership_payment(doc, method):
    for payment in doc.payments:
        if payment.mode_of_payment == "会员卡":
            card = frappe.get_doc("Membership Card", doc.membership_card)
            if card.balance < payment.amount:
                frappe.throw("余额不足")
            
            card.balance -= payment.amount
            card.save()
```

---

## 学习资源与最佳实践

### 必读文档
1. **Frappe Framework 文档**: https://frappeframework.com/docs
2. **ERPNext 用户手册**: https://docs.erpnext.com
3. **Frappe School**: https://school.frappe.io
4. **源码导读**: 直接读 `erpnext/` 源码，从 hooks.py 开始

### 关键文件清单（按优先级）

```
必读（入门）:
├─ erpnext/hooks.py                          # 应用总配置
├─ erpnext/accounts/doctype/pos_profile/     # POS 配置
├─ erpnext/accounts/doctype/pos_invoice/     # 收银单
├─ erpnext/stock/doctype/item/               # 商品
├─ erpnext/stock/doctype/stock_entry/        # 库存调整
└─ erpnext/selling/page/point_of_sale/       # POS 界面

进阶（深入）:
├─ erpnext/controllers/                      # 控制器基类
│   ├─ accounts_controller.py                # 会计逻辑
│   ├─ stock_controller.py                   # 库存逻辑
│   └─ taxes_and_totals.py                   # 税费计算
├─ erpnext/stock/stock_ledger.py             # 库存分录引擎
├─ erpnext/accounts/general_ledger.py        # 会计分录引擎
└─ frappe/model/document.py                  # 框架基类（最底层）

高级（定制）:
├─ erpnext/setup/install.py                  # 安装逻辑
├─ erpnext/patches/                          # 数据迁移脚本
└─ erpnext/regional/                         # 本地化示例
```

### 开发环境搭建

```bash
# 方法 1：Docker（推荐新手）
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d

# 方法 2：本地 bench（推荐开发）
# 安装依赖
sudo apt install -y python3-dev python3-pip redis-server mariadb-server

# 安装 bench
pip3 install frappe-bench

# 初始化
bench init frappe-bench --frappe-branch version-16
cd frappe-bench

# 创建站点
bench new-site mystore.localhost
bench --site mystore.localhost install-app erpnext

# 启动
bench start

# 访问：http://mystore.localhost:8000
# 用户名：Administrator  密码：（创建站点时设置）
```

### 调试技巧

```python
# 1. 打印调试
frappe.log_error(title="调试信息", message=frappe.as_json(doc.as_dict()))

# 2. 断点调试（VSCode）
import pdb; pdb.set_trace()

# 3. SQL 日志
frappe.db.sql_list(query, debug=True)

# 4. 前端 console
console.log(cur_frm.doc);  // 当前表单数据
console.log(locals);       // 所有本地数据

# 5. bench 命令
bench --site mystore.localhost console  # 进入 Python shell
bench --site mystore.localhost mariadb  # 进入数据库
bench --site mystore.localhost clear-cache  # 清缓存
```

### 常见陷阱

```python
# ❌ 错误 1：修改后不生效
# 原因：Frappe 有多层缓存
# 解决：
bench --site mystore.localhost clear-cache
bench restart

# ❌ 错误 2：直接修改 erpnext 源码
# 原因：升级时会丢失
# 解决：创建 Custom App 或用 Custom Field

# ❌ 错误 3：循环导入
# 原因：在文件顶部 import，模块间相互依赖
# 解决：在函数内部 import
def my_function():
    from erpnext.stock.utils import get_stock_balance  # ✅

# ❌ 错误 4：忘记 commit
# 原因：Frappe 不自动提交事务
# 解决：
doc.insert()
frappe.db.commit()  # 必须手动提交

# ❌ 错误 5：权限问题
# 原因：没有给角色授权
# 解决：Setup → Role Permissions Manager
```

---

## 下一步行动计划

### 第 1 周：熟悉环境
- [ ] 搭建开发环境
- [ ] 创建测试站点
- [ ] 导入 50 个测试商品
- [ ] 完成一笔完整的 POS 交易
- [ ] 阅读 `hooks.py` 和 `pos_invoice.py`

### 第 2 周：深入模块
- [ ] 研究 Item DocType 的所有字段
- [ ] 理解 Stock Ledger Entry 的生成逻辑
- [ ] 追踪一笔销售的会计分录
- [ ] 画出控制器继承链
- [ ] 写一个简单的 Custom Field

### 第 3 周：定制开发
- [ ] 创建自己的 Custom App
- [ ] 添加会员卡功能
- [ ] 写一个销售报表
- [ ] 对接一个外部 API

### 第 4 周：生产部署
- [ ] 导入真实商品数据
- [ ] 配置真实仓库和账户
- [ ] 培训收银员
- [ ] 监控性能和日志
- [ ] 制定备份方案

---

## 快速参考卡片

### DocType 生命周期
```
创建 → validate → before_save → after_insert → 草稿
提交 → validate → before_submit → on_submit → 已提交
取消 → on_cancel → 已取消
删除 → on_trash → 已删除
```

### Frappe API 速查
```python
# 文档操作
frappe.new_doc(doctype)
frappe.get_doc(doctype, name)
frappe.get_all(doctype, filters, fields)
frappe.db.get_value(doctype, name, fieldname)
frappe.db.set_value(doctype, name, fieldname, value)
frappe.delete_doc(doctype, name)

# 消息
frappe.msgprint(msg)
frappe.throw(msg)
frappe.log_error(title, message)

# 用户/权限
frappe.session.user
frappe.has_permission(doctype, ptype)

# 工具
frappe.utils.today()
frappe.utils.now()
frappe.utils.flt(value)
frappe.utils.cint(value)
```

### bench 命令速查
```bash
bench start                    # 启动开发服务器
bench new-site <site>          # 创建站点
bench new-app <app>            # 创建应用
bench get-app <app>            # 拉取应用
bench install-app <app>        # 安装应用
bench migrate                  # 数据库迁移
bench clear-cache              # 清缓存
bench console                  # Python shell
bench mariadb                  # 进入数据库
```

---

**祝学习顺利！有问题随时查阅源码，代码是最好的文档。**
