"""
ERPNext 门店系统 - 实战代码示例集
=================================

这是一个可以直接在 bench console 中运行的代码集合
运行方式: bench --site mystore.localhost console
然后复制粘贴下面的代码

目录:
1. 基础数据初始化
2. 商品管理
3. POS 收银
4. 库存管理
5. 报表查询
6. 会员系统
7. 批量操作
8. 调试工具
"""

import frappe
from frappe.utils import today, now, flt, cint, add_days
import random
from datetime import datetime, timedelta


# ================== 1. 基础数据初始化 ==================

def init_store_data():
    """一键初始化门店基础数据"""

    # 1.1 创建仓库
    if not frappe.db.exists("Warehouse", "门店1-主仓"):
        warehouse = frappe.new_doc("Warehouse")
        warehouse.warehouse_name = "门店1-主仓"
        warehouse.parent_warehouse = "所有仓库 - MD"  # MD = 公司缩写
        warehouse.company = "我的门店"
        warehouse.insert()
        print(f"✓ 创建仓库: {warehouse.name}")

    # 1.2 创建客户分组
    for group_name in ["散客", "会员", "VIP会员"]:
        if not frappe.db.exists("Customer Group", group_name):
            group = frappe.new_doc("Customer Group")
            group.customer_group_name = group_name
            group.parent_customer_group = "所有客户分组"
            group.insert()
            print(f"✓ 创建客户分组: {group_name}")

    # 1.3 创建默认客户（散客）
    if not frappe.db.exists("Customer", "散客"):
        customer = frappe.new_doc("Customer")
        customer.customer_name = "散客"
        customer.customer_type = "Individual"
        customer.customer_group = "散客"
        customer.territory = "所有地区"
        customer.insert()
        print(f"✓ 创建默认客户: 散客")

    # 1.4 创建商品分类
    item_groups = {
        "饮料": ["碳酸饮料", "果汁", "茶饮", "矿泉水"],
        "零食": ["膨化食品", "糖果", "饼干"],
        "日用品": ["洗护用品", "纸品"]
    }

    for parent, children in item_groups.items():
        if not frappe.db.exists("Item Group", parent):
            group = frappe.new_doc("Item Group")
            group.item_group_name = parent
            group.parent_item_group = "所有商品分组"
            group.is_group = 1
            group.insert()
            print(f"✓ 创建分类: {parent}")

        for child in children:
            if not frappe.db.exists("Item Group", child):
                subgroup = frappe.new_doc("Item Group")
                subgroup.item_group_name = child
                subgroup.parent_item_group = parent
                subgroup.insert()
                print(f"  ✓ 创建子分类: {child}")

    # 1.5 创建支付方式
    payment_modes = [
        ("现金", "Cash", "现金 - MD"),
        ("微信支付", "Bank", "微信支付 - MD"),
        ("支付宝", "Bank", "支付宝 - MD"),
        ("刷卡", "Bank", "银行存款 - MD")
    ]

    for mode_name, mode_type, account in payment_modes:
        if not frappe.db.exists("Mode of Payment", mode_name):
            mode = frappe.new_doc("Mode of Payment")
            mode.mode_of_payment = mode_name
            mode.type = mode_type
            mode.append("accounts", {
                "company": "我的门店",
                "default_account": account
            })
            mode.insert()
            print(f"✓ 创建支付方式: {mode_name}")

    print("\n✅ 基础数据初始化完成！")


def create_pos_profile():
    """创建 POS 配置"""

    if frappe.db.exists("POS Profile", "门店1-收银台1"):
        print("POS Profile 已存在")
        return

    pos = frappe.new_doc("POS Profile")
    pos.name = "门店1-收银台1"
    pos.company = "我的门店"
    pos.warehouse = "门店1-主仓"
    pos.customer = "散客"
    pos.selling_price_list = "标准售价"

    # 支付方式
    for mode in ["现金", "微信支付", "支付宝", "刷卡"]:
        pos.append("payments", {
            "mode_of_payment": mode,
            "default": 1 if mode == "现金" else 0
        })

    # 行为设置
    pos.update_stock = 1
    pos.validate_stock_on_save = 1
    pos.allow_rate_change = 1
    pos.allow_discount_change = 1
    pos.print_receipt_on_order_complete = 1
    pos.hide_unavailable_items = 1

    # 适用用户
    pos.append("applicable_for_users", {
        "user": frappe.session.user
    })

    pos.insert()
    print(f"✅ 创建 POS Profile: {pos.name}")


# ================== 2. 商品管理 ==================

def create_sample_items():
    """批量创建示例商品"""

    items_data = [
        # (编码, 名称, 分类, 单位, 售价, 成本, 条形码)
        ("COLA-500", "可口可乐 500ml", "碳酸饮料", "瓶", 5.0, 3.0, "6901234567890"),
        ("SPRITE-500", "雪碧 500ml", "碳酸饮料", "瓶", 5.0, 3.0, "6901234567891"),
        ("PEPSI-500", "百事可乐 500ml", "碳酸饮料", "瓶", 4.5, 2.8, "6901234567892"),
        ("JUICE-ORANGE", "鲜橙多 450ml", "果汁", "瓶", 6.0, 3.5, "6901234567893"),
        ("WATER-550", "农夫山泉 550ml", "矿泉水", "瓶", 2.0, 1.2, "6901234567894"),
        ("CHIPS-LAY", "乐事薯片 70g", "膨化食品", "包", 8.0, 5.0, "6901234567895"),
        ("CHIPS-PRINGLES", "品客薯片 110g", "膨化食品", "罐", 12.0, 7.5, "6901234567896"),
        ("CANDY-MIX", "大白兔奶糖 200g", "糖果", "袋", 15.0, 9.0, "6901234567897"),
        ("COOKIE-OREO", "奥利奥饼干 116g", "饼干", "包", 10.0, 6.0, "6901234567898"),
        ("TISSUE-BOX", "清风抽纸 3层", "纸品", "盒", 18.0, 12.0, "6901234567899"),
    ]

    created = 0
    for item_code, item_name, item_group, uom, rate, cost, barcode in items_data:
        if frappe.db.exists("Item", item_code):
            continue

        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = item_name
        item.item_group = item_group
        item.stock_uom = uom
        item.standard_rate = rate
        item.valuation_rate = cost
        item.is_stock_item = 1
        item.is_sales_item = 1
        item.opening_stock = 100  # 初始库存
        item.valuation_rate = cost

        # 添加条形码
        item.append("barcodes", {"barcode": barcode})

        # 默认设置
        item.append("item_defaults", {
            "company": "我的门店",
            "default_warehouse": "门店1-主仓",
            "expense_account": "销售成本 - MD",
            "income_account": "销售收入 - MD"
        })

        item.insert()
        created += 1
        print(f"✓ 创建商品: {item_code} - {item_name}")

    print(f"\n✅ 成功创建 {created} 个商品")


def import_items_from_excel(file_path):
    """从 Excel 批量导入商品

    Excel 格式:
    商品编码 | 商品名称 | 分类 | 单位 | 售价 | 成本 | 条形码
    """
    import pandas as pd

    df = pd.read_excel(file_path)
    created = 0

    for _, row in df.iterrows():
        if frappe.db.exists("Item", row['商品编码']):
            continue

        item = frappe.new_doc("Item")
        item.item_code = row['商品编码']
        item.item_name = row['商品名称']
        item.item_group = row['分类']
        item.stock_uom = row['单位']
        item.standard_rate = row['售价']
        item.is_stock_item = 1

        if pd.notna(row['条形码']):
            item.append("barcodes", {"barcode": str(row['条形码'])})

        item.append("item_defaults", {
            "company": "我的门店",
            "default_warehouse": "门店1-主仓"
        })

        item.insert()
        created += 1

    frappe.db.commit()
    print(f"✅ 导入 {created} 个商品")


def set_item_prices(price_list="标准售价"):
    """批量设置商品价格"""

    items = frappe.get_all("Item",
                          filters={"is_sales_item": 1},
                          fields=["name", "standard_rate"])

    for item in items:
        # 检查是否已有价格
        if frappe.db.exists("Item Price", {
            "item_code": item.name,
            "price_list": price_list
        }):
            continue

        price = frappe.new_doc("Item Price")
        price.item_code = item.name
        price.price_list = price_list
        price.price_list_rate = item.standard_rate
        price.selling = 1
        price.insert()
        print(f"✓ 设置价格: {item.name} = {item.standard_rate}")

    print("✅ 价格设置完成")


# ================== 3. POS 收银 ==================

def create_pos_opening():
    """开班"""

    # 检查是否已有开班单
    existing = frappe.db.get_all("POS Opening Entry",
                                 filters={
                                     "user": frappe.session.user,
                                     "docstatus": 1,
                                     "pos_closing_entry": ["in", ["", None]]
                                 })
    if existing:
        print(f"⚠️  已有未结班次: {existing[0].name}")
        return existing[0].name

    opening = frappe.new_doc("POS Opening Entry")
    opening.period_start_date = now()
    opening.posting_date = today()
    opening.user = frappe.session.user
    opening.pos_profile = "门店1-收银台1"
    opening.company = "我的门店"

    # 备用金
    opening.append("balance_details", {
        "mode_of_payment": "现金",
        "opening_amount": 500.00
    })

    opening.insert()
    opening.submit()

    print(f"✅ 开班成功: {opening.name}")
    print(f"   时间: {opening.period_start_date}")
    print(f"   备用金: ¥{opening.balance_details[0].opening_amount}")
    return opening.name


def create_pos_invoice_simple(items_list, payment_mode="现金"):
    """快速创建收银单

    Args:
        items_list: [(item_code, qty), ...]
        payment_mode: 支付方式

    Example:
        create_pos_invoice_simple([
            ("COLA-500", 2),
            ("CHIPS-LAY", 1)
        ])
    """

    invoice = frappe.new_doc("POS Invoice")
    invoice.customer = "散客"
    invoice.posting_date = today()
    invoice.posting_time = now()
    invoice.pos_profile = "门店1-收银台1"
    invoice.company = "我的门店"
    invoice.debit_to = "应收账款 - MD"
    invoice.is_pos = 1
    invoice.update_stock = 1

    # 添加商品
    for item_code, qty in items_list:
        item_doc = frappe.get_doc("Item", item_code)
        invoice.append("items", {
            "item_code": item_code,
            "item_name": item_doc.item_name,
            "qty": qty,
            "rate": item_doc.standard_rate,
            "warehouse": "门店1-主仓"
        })

    # 计算总价
    invoice.calculate_taxes_and_totals()

    # 添加支付
    invoice.append("payments", {
        "mode_of_payment": payment_mode,
        "amount": invoice.grand_total,
        "account": frappe.db.get_value("Mode of Payment Account",
                                       {"parent": payment_mode,
                                        "company": "我的门店"},
                                       "default_account")
    })

    invoice.insert()
    invoice.submit()

    print(f"✅ 收银成功: {invoice.name}")
    print(f"   商品数: {len(invoice.items)}")
    print(f"   总金额: ¥{invoice.grand_total}")
    print(f"   支付: {payment_mode}")
    return invoice.name


def simulate_daily_sales(num_transactions=20):
    """模拟一天的销售数据"""

    # 先开班
    opening = create_pos_opening()

    # 可用商品
    items = frappe.get_all("Item",
                          filters={"is_sales_item": 1, "disabled": 0},
                          pluck="name")

    # 支付方式
    payment_modes = ["现金", "微信支付", "支付宝", "刷卡"]

    created_invoices = []

    for i in range(num_transactions):
        # 随机选择 1-5 个商品
        num_items = random.randint(1, 5)
        items_list = [
            (random.choice(items), random.randint(1, 3))
            for _ in range(num_items)
        ]

        # 随机支付方式
        payment = random.choice(payment_modes)

        try:
            invoice_name = create_pos_invoice_simple(items_list, payment)
            created_invoices.append(invoice_name)
            print(f"  [{i+1}/{num_transactions}] {invoice_name}")
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    print(f"\n✅ 模拟完成: 成功创建 {len(created_invoices)} 笔交易")
    return created_invoices


def create_pos_closing():
    """结班"""

    # 查找未结班次
    opening = frappe.db.get_value("POS Opening Entry",
                                 filters={
                                     "user": frappe.session.user,
                                     "docstatus": 1,
                                     "pos_closing_entry": ["in", ["", None]]
                                 })

    if not opening:
        print("⚠️  没有未结班次")
        return

    closing = frappe.new_doc("POS Closing Entry")
    closing.pos_opening_entry = opening
    closing.period_end_date = now()
    closing.posting_date = today()
    closing.user = frappe.session.user
    closing.pos_profile = "门店1-收银台1"
    closing.company = "我的门店"

    # 自动拉取交易数据
    closing.get_payment_reconciliation_details()
    closing.set_pos_invoices()

    closing.insert()
    closing.submit()

    print(f"✅ 结班成功: {closing.name}")
    print(f"   开班: {closing.pos_opening_entry}")
    print(f"   交易笔数: {len(closing.pos_transactions)}")
    print(f"   总销售额: ¥{closing.grand_total}")

    # 打印分支付方式汇总
    print("\n支付方式汇总:")
    for payment in closing.payment_reconciliation:
        print(f"   {payment.mode_of_payment}: ¥{payment.closing_amount}")

    return closing.name


# ================== 4. 库存管理 ==================

def create_stock_entry_receipt(item_code, qty, rate):
    """采购入库

    Args:
        item_code: 商品编码
        qty: 数量
        rate: 成本单价
    """

    entry = frappe.new_doc("Stock Entry")
    entry.stock_entry_type = "Material Receipt"
    entry.company = "我的门店"
    entry.posting_date = today()

    entry.append("items", {
        "item_code": item_code,
        "qty": qty,
        "basic_rate": rate,
        "t_warehouse": "门店1-主仓",  # 目标仓库
        "cost_center": "主营 - MD"
    })

    entry.insert()
    entry.submit()

    print(f"✅ 入库成功: {entry.name}")
    print(f"   商品: {item_code}")
    print(f"   数量: {qty}")
    print(f"   单价: ¥{rate}")
    return entry.name


def create_stock_entry_issue(item_code, qty, reason="报损"):
    """库存出库（报损/赠送等）"""

    entry = frappe.new_doc("Stock Entry")
    entry.stock_entry_type = "Material Issue"
    entry.company = "我的门店"
    entry.posting_date = today()

    entry.append("items", {
        "item_code": item_code,
        "qty": qty,
        "s_warehouse": "门店1-主仓",  # 源仓库
        "cost_center": "主营 - MD"
    })

    entry.insert()
    entry.submit()

    print(f"✅ {reason}成功: {entry.name}")
    print(f"   商品: {item_code}")
    print(f"   数量: {qty}")
    return entry.name


def get_stock_balance(item_code, warehouse="门店1-主仓"):
    """查询库存余额"""

    from erpnext.stock.utils import get_stock_balance

    qty = get_stock_balance(item_code, warehouse)

    print(f"商品: {item_code}")
    print(f"仓库: {warehouse}")
    print(f"库存: {qty}")
    return qty


def stock_reconciliation(items_dict):
    """库存盘点

    Args:
        items_dict: {item_code: actual_qty, ...}

    Example:
        stock_reconciliation({
            "COLA-500": 95,
            "CHIPS-LAY": 48
        })
    """

    recon = frappe.new_doc("Stock Reconciliation")
    recon.company = "我的门店"
    recon.posting_date = today()
    recon.posting_time = now()
    recon.purpose = "Stock Reconciliation"

    for item_code, actual_qty in items_dict.items():
        item = frappe.get_doc("Item", item_code)
        recon.append("items", {
            "item_code": item_code,
            "warehouse": "门店1-主仓",
            "qty": actual_qty,
            "valuation_rate": item.valuation_rate
        })

    recon.insert()
    recon.submit()

    print(f"✅ 盘点完成: {recon.name}")
    print(f"   盘点商品数: {len(items_dict)}")
    return recon.name


# ================== 5. 报表查询 ==================

def get_daily_sales_summary(date=None):
    """每日销售汇总"""

    if not date:
        date = today()

    result = frappe.db.sql("""
        SELECT
            pi.posting_date AS 日期,
            COUNT(DISTINCT pi.name) AS 交易笔数,
            SUM(pi.grand_total) AS 销售额,
            SUM(pi.grand_total - pi.total_taxes_and_charges) AS 净销售额,
            SUM(pi.total_taxes_and_charges) AS 税金,
            AVG(pi.grand_total) AS 平均客单价
        FROM
            `tabPOS Invoice` pi
        WHERE
            pi.docstatus = 1
            AND pi.posting_date = %(date)s
    """, {"date": date}, as_dict=1)

    if result:
        print(f"\n📊 {date} 销售汇总")
        print("=" * 50)
        for key, value in result[0].items():
            if key == "日期":
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value:.2f}")
    else:
        print(f"⚠️  {date} 无销售数据")

    return result


def get_top_selling_items(start_date=None, end_date=None, limit=10):
    """畅销商品排行"""

    if not start_date:
        start_date = add_days(today(), -30)
    if not end_date:
        end_date = today()

    result = frappe.db.sql("""
        SELECT
            pii.item_code AS 商品编码,
            pii.item_name AS 商品名称,
            SUM(pii.qty) AS 销量,
            SUM(pii.amount) AS 销售额,
            COUNT(DISTINCT pi.name) AS 订单数,
            AVG(pii.rate) AS 平均售价
        FROM
            `tabPOS Invoice Item` pii
        INNER JOIN
            `tabPOS Invoice` pi ON pii.parent = pi.name
        WHERE
            pi.docstatus = 1
            AND pi.posting_date BETWEEN %(start)s AND %(end)s
        GROUP BY
            pii.item_code
        ORDER BY
            销量 DESC
        LIMIT %(limit)s
    """, {"start": start_date, "end": end_date, "limit": limit}, as_dict=1)

    print(f"\n📊 畅销商品排行 ({start_date} ~ {end_date})")
    print("=" * 80)
    print(f"{'排名':<4} {'商品名称':<20} {'销量':>8} {'销售额':>12} {'订单数':>8}")
    print("-" * 80)

    for i, item in enumerate(result, 1):
        print(f"{i:<4} {item['商品名称']:<20} {item['销量']:>8.0f} "
              f"{item['销售额']:>12.2f} {item['订单数']:>8}")

    return result


def get_payment_method_summary(date=None):
    """支付方式汇总"""

    if not date:
        date = today()

    result = frappe.db.sql("""
        SELECT
            sip.mode_of_payment AS 支付方式,
            COUNT(DISTINCT pi.name) AS 笔数,
            SUM(sip.amount) AS 金额
        FROM
            `tabSales Invoice Payment` sip
        INNER JOIN
            `tabPOS Invoice` pi ON sip.parent = pi.name
        WHERE
            pi.docstatus = 1
            AND pi.posting_date = %(date)s
        GROUP BY
            sip.mode_of_payment
        ORDER BY
            金额 DESC
    """, {"date": date}, as_dict=1)

    print(f"\n📊 {date} 支付方式汇总")
    print("=" * 50)
    total = 0
    for row in result:
        print(f"{row['支付方式']:<15} 笔数: {row['笔数']:>5}  金额: ¥{row['金额']:>10.2f}")
        total += row['金额']
    print("-" * 50)
    print(f"{'合计':<15} {'':>11} ¥{total:>10.2f}")

    return result


def get_stock_alert(threshold=10):
    """库存预警"""

    result = frappe.db.sql("""
        SELECT
            b.item_code AS 商品编码,
            i.item_name AS 商品名称,
            b.actual_qty AS 库存,
            i.standard_rate AS 售价
        FROM
            `tabBin` b
        INNER JOIN
            `tabItem` i ON b.item_code = i.name
        WHERE
            b.warehouse = '门店1-主仓'
            AND b.actual_qty < %(threshold)s
            AND i.is_sales_item = 1
            AND i.disabled = 0
        ORDER BY
            b.actual_qty ASC
    """, {"threshold": threshold}, as_dict=1)

    print(f"\n⚠️  库存预警 (少于 {threshold} 件)")
    print("=" * 60)
    print(f"{'商品名称':<25} {'库存':>8} {'售价':>10}")
    print("-" * 60)

    for item in result:
        print(f"{item['商品名称']:<25} {item['库存']:>8.0f} ¥{item['售价']:>9.2f}")

    return result


# ================== 6. 会员系统（自定义功能示例）==================

def create_membership_card_doctype():
    """创建会员卡 DocType（仅示例结构，实际需在界面创建）"""

    # 这是代码创建 DocType 的方式（不推荐，应该用界面）
    # 这里仅作为学习参考

    if frappe.db.exists("DocType", "Membership Card"):
        print("Membership Card 已存在")
        return

    doctype = frappe.new_doc("DocType")
    doctype.name = "Membership Card"
    doctype.module = "Selling"
    doctype.custom = 1
    doctype.autoname = "field:card_number"
    doctype.naming_rule = "By fieldname"

    # 字段定义
    fields = [
        {"fieldname": "card_number", "label": "卡号", "fieldtype": "Data",
         "unique": 1, "reqd": 1},
        {"fieldname": "customer", "label": "客户", "fieldtype": "Link",
         "options": "Customer", "reqd": 1},
        {"fieldname": "customer_name", "label": "客户名称", "fieldtype": "Data",
         "fetch_from": "customer.customer_name", "read_only": 1},
        {"fieldname": "sb1", "fieldtype": "Section Break", "label": "余额信息"},
        {"fieldname": "balance", "label": "余额", "fieldtype": "Currency",
         "default": "0"},
        {"fieldname": "total_recharged", "label": "累计充值", "fieldtype": "Currency",
         "default": "0", "read_only": 1},
        {"fieldname": "cb1", "fieldtype": "Column Break"},
        {"fieldname": "discount_percentage", "label": "折扣率(%)",
         "fieldtype": "Percent", "default": "0"},
        {"fieldname": "card_level", "label": "卡等级", "fieldtype": "Select",
         "options": "\n普通卡\n银卡\n金卡\nVIP卡"},
    ]

    for i, field in enumerate(fields):
        field["idx"] = i + 1
        doctype.append("fields", field)

    # 权限
    doctype.append("permissions", {
        "role": "Sales User",
        "read": 1, "write": 1, "create": 1
    })

    doctype.insert()
    print("✅ 创建 Membership Card DocType")


def create_membership_card(customer, card_number, initial_balance=0):
    """创建会员卡"""

    card = frappe.new_doc("Membership Card")
    card.card_number = card_number
    card.customer = customer
    card.balance = initial_balance
    card.total_recharged = initial_balance
    card.card_level = "普通卡"
    card.discount_percentage = 5  # 5% 折扣

    card.insert()
    print(f"✅ 创建会员卡: {card_number}")
    print(f"   客户: {customer}")
    print(f"   余额: ¥{initial_balance}")
    return card.name


def recharge_card(card_number, amount):
    """会员卡充值"""

    card = frappe.get_doc("Membership Card", card_number)
    card.balance += amount
    card.total_recharged += amount

    # 根据累计充值调整等级
    if card.total_recharged >= 10000:
        card.card_level = "VIP卡"
        card.discount_percentage = 15
    elif card.total_recharged >= 5000:
        card.card_level = "金卡"
        card.discount_percentage = 12
    elif card.total_recharged >= 2000:
        card.card_level = "银卡"
        card.discount_percentage = 8

    card.save()

    print(f"✅ 充值成功")
    print(f"   卡号: {card_number}")
    print(f"   充值金额: ¥{amount}")
    print(f"   当前余额: ¥{card.balance}")
    print(f"   卡等级: {card.card_level} (折扣 {card.discount_percentage}%)")

    # 记录流水
    transaction = frappe.new_doc("Card Transaction")  # 需要先创建这个 DocType
    transaction.card_number = card_number
    transaction.transaction_type = "充值"
    transaction.amount = amount
    transaction.balance_after = card.balance
    transaction.insert()

    return card.balance


# ================== 7. 批量操作 ==================

def batch_update_item_prices(factor=1.1):
    """批量调整价格（如全部商品涨价 10%）"""

    items = frappe.get_all("Item Price",
                          filters={"price_list": "标准售价"},
                          fields=["name", "item_code", "price_list_rate"])

    updated = 0
    for item in items:
        new_rate = item.price_list_rate * factor
        frappe.db.set_value("Item Price", item.name, "price_list_rate", new_rate)
        print(f"✓ {item.item_code}: {item.price_list_rate:.2f} → {new_rate:.2f}")
        updated += 1

    frappe.db.commit()
    print(f"\n✅ 更新 {updated} 个商品价格")


def bulk_stock_in(items_list):
    """批量入库

    Args:
        items_list: [(item_code, qty, rate), ...]
    """

    entry = frappe.new_doc("Stock Entry")
    entry.stock_entry_type = "Material Receipt"
    entry.company = "我的门店"
    entry.posting_date = today()

    for item_code, qty, rate in items_list:
        entry.append("items", {
            "item_code": item_code,
            "qty": qty,
            "basic_rate": rate,
            "t_warehouse": "门店1-主仓",
            "cost_center": "主营 - MD"
        })

    entry.insert()
    entry.submit()

    print(f"✅ 批量入库成功: {entry.name}")
    print(f"   商品数: {len(items_list)}")
    return entry.name


# ================== 8. 调试工具 ==================

def check_accounting_entries(invoice_name):
    """检查单据的会计分录"""

    gl_entries = frappe.get_all("GL Entry",
                               filters={"voucher_no": invoice_name},
                               fields=["account", "debit", "credit", "posting_date"])

    print(f"\n📒 {invoice_name} 的会计分录:")
    print("=" * 70)
    print(f"{'科目':<30} {'借方':>15} {'贷方':>15}")
    print("-" * 70)

    total_debit = 0
    total_credit = 0

    for entry in gl_entries:
        print(f"{entry.account:<30} {entry.debit:>15.2f} {entry.credit:>15.2f}")
        total_debit += entry.debit
        total_credit += entry.credit

    print("-" * 70)
    print(f"{'合计':<30} {total_debit:>15.2f} {total_credit:>15.2f}")

    if abs(total_debit - total_credit) < 0.01:
        print("✅ 借贷平衡")
    else:
        print(f"❌ 不平衡! 差额: {total_debit - total_credit:.2f}")

    return gl_entries


def check_stock_ledger(item_code, warehouse="门店1-主仓", limit=20):
    """查看商品的库存流水"""

    entries = frappe.get_all("Stock Ledger Entry",
                            filters={"item_code": item_code, "warehouse": warehouse},
                            fields=["posting_date", "posting_time", "voucher_type",
                                   "voucher_no", "actual_qty", "qty_after_transaction"],
                            order_by="posting_date DESC, posting_time DESC",
                            limit=limit)

    print(f"\n📦 {item_code} @ {warehouse} 库存流水")
    print("=" * 100)
    print(f"{'日期':<12} {'单据类型':<20} {'单据编号':<25} {'变动':>8} {'结存':>8}")
    print("-" * 100)

    for entry in entries:
        print(f"{entry.posting_date} {entry.voucher_type:<20} "
              f"{entry.voucher_no:<25} {entry.actual_qty:>8.0f} "
              f"{entry.qty_after_transaction:>8.0f}")

    return entries


def performance_test():
    """性能测试 - 创建 100 笔销售单"""

    import time

    items = frappe.get_all("Item",
                          filters={"is_sales_item": 1},
                          limit=10,
                          pluck="name")

    start_time = time.time()

    for i in range(100):
        item_code = random.choice(items)
        create_pos_invoice_simple([(item_code, 1)], "现金")

    elapsed = time.time() - start_time

    print(f"\n⏱️  性能测试结果:")
    print(f"   创建 100 笔销售单")
    print(f"   耗时: {elapsed:.2f} 秒")
    print(f"   平均: {elapsed/100:.3f} 秒/笔")


# ================== 快速启动函数 ==================

def quick_start():
    """一键初始化整个门店系统"""

    print("🚀 开始初始化门店系统...\n")

    print("Step 1: 初始化基础数据...")
    init_store_data()

    print("\nStep 2: 创建示例商品...")
    create_sample_items()

    print("\nStep 3: 设置商品价格...")
    set_item_prices()

    print("\nStep 4: 创建 POS 配置...")
    create_pos_profile()

    print("\n" + "="*60)
    print("✅ 门店系统初始化完成！")
    print("="*60)
    print("\n下一步可以:")
    print("1. 开班: create_pos_opening()")
    print("2. 收银: create_pos_invoice_simple([('COLA-500', 2)])")
    print("3. 模拟销售: simulate_daily_sales(20)")
    print("4. 结班: create_pos_closing()")
    print("5. 查看报表: get_daily_sales_summary()")


# ================== 主函数示例 ==================

if __name__ == "__main__":
    """
    在 bench console 中使用:

    >>> exec(open('门店系统实战代码.py').read())
    >>> quick_start()  # 一键初始化

    或者单独调用某个函数:
    >>> create_pos_opening()
    >>> create_pos_invoice_simple([("COLA-500", 2), ("CHIPS-LAY", 1)])
    >>> get_daily_sales_summary()
    """

    print(__doc__)
    print("\n使用 quick_start() 开始体验完整流程")
