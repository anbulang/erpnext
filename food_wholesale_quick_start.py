"""
食品原料批发系统 - 快速启动脚本
===================================

这是一个专门为食品原料批发定制的快速启动脚本
与零售门店系统的主要区别:
1. 不使用 POS 模块
2. 核心是 B2B 账期管理
3. 强调批次和保质期管理
4. 业务流程: 报价单 → 销售订单 → 送货单 → 销售发票

运行方式:
bench --site your_site.localhost console
>>> exec(open('food_wholesale_quick_start.py').read())
>>> quick_start()
"""

import frappe
import pandas as pd
from frappe.utils import today, add_days, get_first_day, get_last_day, nowtime
import random

# ========== 1. 基础数据初始化 ==========

def init_base_data():
    """初始化基础数据（客户分组、价格表、支付条款）"""
    print("🚀 开始初始化食品批发系统...\n")

    print("Step 1: 创建客户分组...")
    # 客户分组
    customer_groups = [
        ("餐饮客户", "适用于餐厅、酒店等", 5),
        ("烘焙客户", "适用于面包店、蛋糕店", 8),
        ("VIP 客户", "长期合作大客户", 12)
    ]

    for group, desc, discount in customer_groups:
        if not frappe.db.exists("Customer Group", group):
            cg = frappe.new_doc("Customer Group")
            cg.customer_group_name = group
            cg.parent_customer_group = "所有客户分组"
            cg.insert()
            print(f"  ✓ {group} (默认折扣 {discount}%)")

    print("\nStep 2: 创建价格表...")
    # 价格表
    price_lists = [
        "标准售价",
        "餐饮客户价",
        "烘焙客户价",
        "VIP 客户价"
    ]

    for pl in price_lists:
        if not frappe.db.exists("Price List", pl):
            price_list = frappe.new_doc("Price List")
            price_list.price_list_name = pl
            price_list.selling = 1
            price_list.currency = "CNY"
            price_list.insert()
            print(f"  ✓ {pl}")

    print("\nStep 3: 创建支付条款...")
    # 支付条款
    payment_terms = [
        ("月结 30 天", 30),
        ("月结 60 天", 60),
        ("现结", 0)
    ]

    for name, days in payment_terms:
        if not frappe.db.exists("Payment Terms Template", name):
            ptt = frappe.new_doc("Payment Terms Template")
            ptt.template_name = name
            ptt.append("terms", {
                "invoice_portion": 100,
                "credit_days": days
            })
            ptt.insert()
            print(f"  ✓ {name}")

    frappe.db.commit()
    print("\n✅ 基础数据初始化完成\n")


def create_sample_items():
    """创建示例食品原料商品"""

    print("Step 4: 创建示例商品...\n")

    # 商品数据: (编码, 名称, 分类, 单位, 售价, 成本, 保质期天数)
    sample_items = [
        # 面粉类
        ("FLOUR-HIGH-25", "高筋面粉 25kg", "面粉类", "袋", 180.00, 160.00, 180),
        ("FLOUR-LOW-25", "低筋面粉 25kg", "面粉类", "袋", 170.00, 150.00, 180),
        ("FLOUR-MID-25", "中筋面粉 25kg", "面粉类", "袋", 175.00, 155.00, 180),

        # 糖类
        ("SUGAR-WHITE-50", "白砂糖 50kg", "糖类", "袋", 280.00, 250.00, 365),
        ("SUGAR-BROWN-50", "红糖 50kg", "糖类", "袋", 320.00, 280.00, 365),
        ("SYRUP-HONEY-5", "蜂蜜糖浆 5kg", "糖类", "桶", 180.00, 150.00, 365),

        # 乳制品
        ("BUTTER-ANCHOR-1", "安佳黄油 1kg", "乳制品", "盒", 68.00, 55.00, 365),
        ("CREAM-FRESH-1", "鲜奶油 1L", "乳制品", "盒", 48.00, 38.00, 30),
        ("MILK-POWDER-25", "全脂奶粉 25kg", "乳制品", "袋", 680.00, 580.00, 365),

        # 蛋类
        ("EGG-FRESH-30", "鲜鸡蛋 30枚", "蛋类", "托", 25.00, 20.00, 15),
        ("EGG-DUCK-30", "鸭蛋 30枚", "蛋类", "托", 35.00, 28.00, 15),

        # 油脂类
        ("OIL-SOYBEAN-5L", "大豆油 5L", "油脂类", "桶", 65.00, 52.00, 365),
        ("OIL-CORN-5L", "玉米油 5L", "油脂类", "桶", 75.00, 60.00, 365),

        # 添加剂
        ("YEAST-DRY-500G", "干酵母 500g", "添加剂", "袋", 28.00, 22.00, 180),
        ("BAKING-POWDER-1KG", "泡打粉 1kg", "添加剂", "袋", 35.00, 28.00, 365),
    ]

    created_count = 0

    for code, name, group, uom, sell_price, cost, shelf_life in sample_items:
        # 先创建商品分类
        if not frappe.db.exists("Item Group", group):
            ig = frappe.new_doc("Item Group")
            ig.item_group_name = group
            ig.parent_item_group = "所有商品分组"
            ig.insert()
            print(f"  ✓ 创建分类: {group}")

        # 创建商品
        if frappe.db.exists("Item", code):
            continue

        item = frappe.new_doc("Item")
        item.item_code = code
        item.item_name = name
        item.item_group = group
        item.stock_uom = uom
        item.standard_rate = sell_price
        item.valuation_rate = cost

        # 库存和销售设置
        item.is_stock_item = 1
        item.is_sales_item = 1
        item.is_purchase_item = 1

        # 批次和保质期管理（食品必须）
        item.has_batch_no = 1
        item.create_new_batch = 1
        item.batch_number_series = f"BATCH-{code[:4]}-.####"
        item.has_expiry_date = 1
        item.shelf_life_in_days = shelf_life

        # 默认设置（需要根据实际公司名称修改）
        # item.append("item_defaults", {
        #     "company": "你的公司",
        #     "default_warehouse": "主仓库"
        # })

        item.insert()
        created_count += 1
        print(f"  ✓ {code} - {name}")

    frappe.db.commit()
    print(f"\n✅ 成功创建 {created_count} 个商品\n")


def set_customer_prices():
    """批量设置客户专属价格"""

    print("Step 5: 设置客户价格...\n")

    # 获取所有商品
    items = frappe.get_all("Item",
                          filters={"is_sales_item": 1},
                          fields=["name", "standard_rate"])

    if not items:
        print("  ⚠️  没有商品，跳过价格设置")
        return

    # 价格策略（基于标准价的折扣）
    price_rules = {
        "餐饮客户价": 0.95,  # 95折
        "烘焙客户价": 0.92,  # 92折
        "VIP 客户价": 0.88   # 88折
    }

    created_count = 0

    for price_list, discount_factor in price_rules.items():
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
            price.price_list_rate = item.standard_rate * discount_factor
            price.selling = 1
            price.insert()
            created_count += 1

        print(f"  ✓ {price_list}: {len(items)} 个商品")

    frappe.db.commit()
    print(f"\n✅ 成功设置 {created_count} 个价格\n")


def create_sample_customers():
    """创建示例客户"""

    print("Step 6: 创建示例客户...\n")

    # 客户数据: (名称, 分组, 价格表, 信用额度, 联系人, 电话)
    sample_customers = [
        ("张三面包店", "烘焙客户", "烘焙客户价", 50000, "张三", "13800138000"),
        ("李四餐厅", "餐饮客户", "餐饮客户价", 30000, "李四", "13900139000"),
        ("王五酒店", "餐饮客户", "餐饮客户价", 80000, "王五", "13700137000"),
        ("赵六蛋糕店", "烘焙客户", "烘焙客户价", 40000, "赵六", "13600136000"),
        ("钱七食品厂", "VIP 客户", "VIP 客户价", 200000, "钱七", "13500135000"),
    ]

    created_count = 0

    for name, group, price_list, credit_limit, contact_name, mobile in sample_customers:
        if frappe.db.exists("Customer", name):
            continue

        # 创建客户
        cust = frappe.new_doc("Customer")
        cust.customer_name = name
        cust.customer_type = "Company"
        cust.customer_group = group
        cust.territory = "所有地区"
        cust.default_price_list = price_list
        cust.payment_terms = "月结 30 天"

        # 信用额度
        # cust.append("credit_limits", {
        #     "company": "你的公司",
        #     "credit_limit": credit_limit
        # })

        cust.insert()
        created_count += 1
        print(f"  ✓ {name} ({group}, 额度: ¥{credit_limit:,.0f})")

        # 创建联系人
        contact = frappe.new_doc("Contact")
        contact.first_name = contact_name
        contact.append("links", {
            "link_doctype": "Customer",
            "link_name": name
        })
        contact.append("phone_nos", {
            "phone": mobile,
            "is_primary_mobile_no": 1
        })
        contact.insert()

    frappe.db.commit()
    print(f"\n✅ 成功创建 {created_count} 个客户\n")


# ========== 2. 业务流程演示 ==========

def demo_sales_flow():
    """演示完整销售流程"""

    print("🎬 演示销售流程...\n")

    # 检查是否有客户和商品
    customers = frappe.get_all("Customer", limit=1)
    items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=3)

    if not customers:
        print("  ⚠️  没有客户，跳过流程演示")
        return

    if not items:
        print("  ⚠️  没有商品，跳过流程演示")
        return

    customer_name = customers[0].name

    print(f"Step 1: 创建报价单（客户: {customer_name}）")

    # 1. 创建报价单
    quot = frappe.new_doc("Quotation")
    quot.party_name = customer_name
    quot.quotation_to = "Customer"
    quot.transaction_date = today()
    quot.valid_till = add_days(today(), 7)

    # 获取客户默认价格表
    customer = frappe.get_doc("Customer", customer_name)
    quot.selling_price_list = customer.default_price_list or "标准售价"

    # 添加商品
    for item in items[:2]:  # 只添加前2个商品
        # 获取价格
        price = frappe.db.get_value("Item Price", {
            "item_code": item.name,
            "price_list": quot.selling_price_list
        }, "price_list_rate")

        if not price:
            price = frappe.db.get_value("Item", item.name, "standard_rate")

        quot.append("items", {
            "item_code": item.name,
            "qty": random.randint(5, 20),
            "rate": price
        })

    quot.insert()
    print(f"  ✓ 报价单: {quot.name}")
    print(f"    金额: ¥{quot.grand_total:,.2f}")

    print(f"\nStep 2: 报价单 → 销售订单")

    # 2. 转销售订单
    from frappe.model.mapper import get_mapped_doc

    so = get_mapped_doc("Quotation", quot.name, {
        "Quotation": {
            "doctype": "Sales Order",
            "field_map": {
                "party_name": "customer"
            }
        },
        "Quotation Item": {
            "doctype": "Sales Order Item"
        }
    })

    so.delivery_date = add_days(today(), 3)
    so.insert()
    so.submit()

    print(f"  ✓ 销售订单: {so.name}")
    print(f"    交货日期: {so.delivery_date}")

    print("\n✅ 销售流程演示完成")
    print("\n💡 下一步可以在界面操作:")
    print("   1. 销售订单 → Make → Delivery Note (送货单)")
    print("   2. 送货单 → Make → Sales Invoice (销售发票)")
    print("   3. 销售发票 → Make → Payment Entry (收款)")


# ========== 3. 数据导入函数 ==========

def import_items_from_excel(file_path):
    """从 Excel 批量导入商品

    Excel 列: item_code, item_name, item_group, stock_uom,
             standard_rate, valuation_rate, shelf_life_days
    """

    df = pd.read_excel(file_path)
    created_count = 0

    print(f"开始从 {file_path} 导入商品...\n")

    for _, row in df.iterrows():
        # 创建分类
        if pd.notna(row['item_group']) and not frappe.db.exists("Item Group", row['item_group']):
            ig = frappe.new_doc("Item Group")
            ig.item_group_name = row['item_group']
            ig.parent_item_group = "所有商品分组"
            ig.insert()

        # 跳过已存在的商品
        if frappe.db.exists("Item", row['item_code']):
            continue

        item = frappe.new_doc("Item")
        item.item_code = row['item_code']
        item.item_name = row['item_name']
        item.item_group = row['item_group']
        item.stock_uom = row['stock_uom']
        item.standard_rate = row.get('standard_rate', 0)
        item.valuation_rate = row.get('valuation_rate', 0)

        item.is_stock_item = 1
        item.is_sales_item = 1
        item.is_purchase_item = 1

        # 批次和保质期
        item.has_batch_no = 1
        item.create_new_batch = 1
        item.batch_number_series = f"BATCH-{row['item_code'][:4]}-.####"

        if pd.notna(row.get('shelf_life_days')):
            item.has_expiry_date = 1
            item.shelf_life_in_days = int(row['shelf_life_days'])

        item.insert()
        created_count += 1
        print(f"✓ {row['item_code']} - {row['item_name']}")

    frappe.db.commit()
    print(f"\n✅ 成功导入 {created_count} 个商品")


def import_customers_from_excel(file_path):
    """从 Excel 批量导入客户

    Excel 列: customer_name, customer_group, payment_terms,
             credit_limit, contact_person, mobile_no
    """

    df = pd.read_excel(file_path)
    created_count = 0

    print(f"开始从 {file_path} 导入客户...\n")

    for _, row in df.iterrows():
        if frappe.db.exists("Customer", row['customer_name']):
            continue

        cust = frappe.new_doc("Customer")
        cust.customer_name = row['customer_name']
        cust.customer_type = "Company"
        cust.customer_group = row.get('customer_group', '所有客户分组')
        cust.territory = "所有地区"
        cust.payment_terms = row.get('payment_terms', '月结 30 天')

        # 根据客户分组设置默认价格表
        if row.get('customer_group') == '烘焙客户':
            cust.default_price_list = '烘焙客户价'
        elif row.get('customer_group') == '餐饮客户':
            cust.default_price_list = '餐饮客户价'
        elif row.get('customer_group') == 'VIP 客户':
            cust.default_price_list = 'VIP 客户价'

        cust.insert()
        created_count += 1
        print(f"✓ {row['customer_name']}")

    frappe.db.commit()
    print(f"\n✅ 成功导入 {created_count} 个客户")


# ========== 4. 报表和工具函数 ==========

def get_expiring_items(days=30):
    """临期商品预警"""

    alert_date = add_days(today(), days)

    result = frappe.db.sql("""
        SELECT
            b.item,
            i.item_name,
            b.batch_id,
            b.expiry_date,
            DATEDIFF(b.expiry_date, CURDATE()) as days_to_expire,
            b.batch_qty as qty
        FROM
            `tabBatch` b
        INNER JOIN
            `tabItem` i ON b.item = i.name
        WHERE
            b.expiry_date <= %(alert_date)s
            AND b.expiry_date >= CURDATE()
            AND b.batch_qty > 0
        ORDER BY
            b.expiry_date ASC
    """, {"alert_date": alert_date}, as_dict=1)

    if not result:
        print(f"✅ 没有 {days} 天内过期的商品")
        return []

    print(f"\n⚠️  临期商品预警（{days} 天内过期）")
    print("=" * 90)
    print(f"{'商品':<25} {'批次号':<18} {'过期日期':<12} {'剩余天数':>8} {'库存':>8}")
    print("-" * 90)

    for item in result:
        print(f"{item.item_name:<25} {item.batch_id:<18} {item.expiry_date} "
              f"{item.days_to_expire:>8} {item.qty:>8.0f}")

    print("=" * 90)
    return result


def get_customer_outstanding():
    """客户欠款汇总"""

    result = frappe.db.sql("""
        SELECT
            si.customer,
            c.customer_name,
            c.customer_group,
            SUM(si.outstanding_amount) as outstanding,
            COUNT(*) as invoice_count,
            MIN(si.posting_date) as earliest_invoice
        FROM
            `tabSales Invoice` si
        INNER JOIN
            `tabCustomer` c ON si.customer = c.name
        WHERE
            si.docstatus = 1
            AND si.outstanding_amount > 0
        GROUP BY
            si.customer
        ORDER BY
            outstanding DESC
    """, as_dict=1)

    if not result:
        print("✅ 所有客户已结清欠款")
        return []

    print("\n📋 客户欠款汇总")
    print("=" * 100)
    print(f"{'客户':<30} {'分组':<15} {'欠款金额':>15} {'发票数':>8} {'最早发票日期':<12}")
    print("-" * 100)

    total_outstanding = 0

    for row in result:
        print(f"{row.customer_name:<30} {row.customer_group:<15} "
              f"¥{row.outstanding:>14.2f} {row.invoice_count:>8} {row.earliest_invoice}")
        total_outstanding += row.outstanding

    print("-" * 100)
    print(f"{'合计':<30} {'':<15} ¥{total_outstanding:>14.2f}")
    print("=" * 100)

    return result


def monthly_sales_summary(month=None):
    """月度销售汇总"""

    if not month:
        month = today()[:7]  # "2026-06"

    start_date = get_first_day(month)
    end_date = get_last_day(month)

    result = frappe.db.sql("""
        SELECT
            si.customer,
            COUNT(DISTINCT si.name) as invoice_count,
            SUM(si.grand_total) as total_sales,
            SUM(si.outstanding_amount) as outstanding
        FROM
            `tabSales Invoice` si
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(start)s AND %(end)s
        GROUP BY
            si.customer
        ORDER BY
            total_sales DESC
    """, {"start": start_date, "end": end_date}, as_dict=1)

    if not result:
        print(f"⚠️  {month} 无销售数据")
        return []

    print(f"\n📊 {month} 销售汇总")
    print("=" * 90)
    print(f"{'客户':<30} {'发票数':>8} {'销售额':>15} {'未收款':>15}")
    print("-" * 90)

    total_sales = 0
    total_outstanding = 0

    for row in result:
        print(f"{row.customer:<30} {row.invoice_count:>8} "
              f"¥{row.total_sales:>14.2f} ¥{row.outstanding:>14.2f}")
        total_sales += row.total_sales
        total_outstanding += row.outstanding

    print("-" * 90)
    print(f"{'合计':<30} {'':<8} ¥{total_sales:>14.2f} ¥{total_outstanding:>14.2f}")
    print("=" * 90)

    return result


# ========== 主函数 ==========

def quick_start():
    """一键快速启动"""

    print("\n" + "="*70)
    print("  🥖 食品原料批发系统 - 快速启动")
    print("="*70 + "\n")

    init_base_data()
    create_sample_items()
    set_customer_prices()
    create_sample_customers()
    demo_sales_flow()

    print("\n" + "="*70)
    print("  🎉 系统初始化完成！")
    print("="*70 + "\n")

    print("下一步操作:")
    print("─" * 70)
    print("📥 数据导入:")
    print("  • import_items_from_excel('商品列表.xlsx')")
    print("  • import_customers_from_excel('客户列表.xlsx')")
    print("")
    print("📊 查看报表:")
    print("  • get_expiring_items(30)          # 临期商品预警")
    print("  • get_customer_outstanding()      # 客户欠款汇总")
    print("  • monthly_sales_summary('2026-06') # 月度销售")
    print("")
    print("💡 业务操作:")
    print("  • 在界面中: Selling → Quotation → New")
    print("  • 报价单 → Make → Sales Order")
    print("  • 销售订单 → Make → Delivery Note")
    print("  • 送货单 → Make → Sales Invoice")
    print("─" * 70)


# ========== 入口 ==========

if __name__ == "__main__":
    print(__doc__)
    print("\n使用 quick_start() 一键初始化系统")
