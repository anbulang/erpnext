# ERPNext 架构文档

本目录包含 ERPNext 系统的架构图和技术文档。

## 📁 目录结构

```
docs/
├── README.md                   # 本文件
├── architecture/               # 架构图
│   ├── overall-architecture.*  # 整体架构（4层模型）
│   ├── tech-stack.*           # 技术栈
│   └── controller-inheritance.* # 控制器继承链
├── workflows/                  # 业务流程图
│   ├── pos-workflow.*         # POS收银流程
│   └── wholesale-flow.*       # B2B批发流程
├── data-model/                 # 数据模型
│   └── data-relationships.*   # DocType关系图
└── _src/                       # 源文件
    ├── *.mmd                  # Mermaid源码
    └── puppeteer-config.json  # 渲染配置
```

## 🎨 架构图

### 整体架构 (overall-architecture)

展示 ERPNext 的 4 层技术架构：
- **前端层**: POS 界面、Desk UI、门户网站
- **应用层**: ERPNext 业务模块（POS、库存、销售等）
- **框架层**: Frappe Framework（ORM、权限、API）
- **数据层**: MariaDB、Redis

### 技术栈 (tech-stack)

展示完整的技术栈及依赖关系：
- 前端：Vue.js、Frappe UI
- 后端：Python、Frappe Framework、ERPNext
- 数据：MariaDB、Redis
- 构建：Node.js、npm

### 控制器继承链 (controller-inheritance)

展示 ERPNext 核心控制器的继承层次：
```
Document (Frappe 基类)
  └─ StatusUpdater (状态管理)
      └─ TransactionBase (交易基础)
          └─ AccountsController (会计分录)
              └─ StockController (库存分录)
                  ├─ SellingController (销售逻辑)
                  │   └─ POSInvoice (POS特定)
                  └─ BuyingController (采购逻辑)
```

## 🔄 业务流程图

### POS 收银流程 (pos-workflow)

展示完整的 POS 收银流程：
1. **开班** (POS Opening Entry)
2. **收银** (POS Invoice)
   - 扫码/添加商品
   - 计算税费和总价
   - 选择支付方式
   - 提交（自动生成库存分录和会计分录）
3. **结班** (POS Closing Entry)

### B2B 批发流程 (wholesale-flow)

展示食品原料批发的标准业务流程：
```
报价单 → 销售订单 → 送货单 → 销售发票 → 收款
(Quotation) (Sales Order) (Delivery Note) (Sales Invoice) (Payment)
```

包括：
- 批次选择（FEFO - 先过期先出）
- 账期管理（月结 30/60 天）
- 信用额度控制

## 📊 数据模型

### DocType 关系图 (data-relationships)

展示核心 DocType 之间的关系：
- Company → Warehouse → Bin (库存余额)
- Item → Item Price (价格)
- Item → Batch (批次，含保质期)
- Customer → POS Invoice → POS Invoice Item
- POS Invoice → Stock Ledger Entry (库存分录)
- POS Invoice → GL Entry (会计分录)

## 🛠️ 如何更新图表

所有图表由 Mermaid 图表语言生成。要更新：

1. 编辑源文件：`docs/_src/*.mmd`
2. 重新渲染：
   ```bash
   cd /home/user/erpnext/docs/_src
   npx -y @mermaid-js/mermaid-cli \
     -i your-diagram.mmd \
     -o ../category/your-diagram.svg \
     -t default \
     -b white \
     -p puppeteer-config.json
   ```

或使用批量渲染脚本（如果已创建）。

## 📚 相关文档

- [ERPNext 门店系统学习指南](../ERPNEXT_门店系统学习指南.md)
- [门店系统架构图](../门店系统架构图.md)
- [食品批发系统快速上线指南](../食品批发系统快速上线指南.md)

## 🔗 外部资源

- [ERPNext 官方文档](https://docs.erpnext.com/)
- [Frappe Framework 文档](https://frappeframework.com/docs)
- [Mermaid 图表语法](https://mermaid.js.org/)

---

**生成时间**: 2026-06-24
**工具**: claude-mermaid (Mermaid CLI)
