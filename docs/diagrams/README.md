# 专业架构图表

深色主题、交互式、高质量的 ERPNext 架构图表。

## 📊 图表列表

| 文件 | 描述 |
|------|------|
| [01-overall-architecture.html](01-overall-architecture.html) | ERPNext 整体架构 (4层模型) |
| [02-controller-inheritance.html](02-controller-inheritance.html) | 控制器继承层次 |
| [03-pos-workflow.html](03-pos-workflow.html) | POS 收银完整流程 |

## 🚀 使用方法

### 查看图表

直接在浏览器中打开 HTML 文件即可查看：

```bash
# 方法 1: 使用默认浏览器
open docs/diagrams/01-overall-architecture.html

# 方法 2: 指定浏览器
google-chrome docs/diagrams/01-overall-architecture.html
firefox docs/diagrams/01-overall-architecture.html
```

或者直接双击 HTML 文件。

### 导出图片

每个图表右上角都有 `⋯` 按钮，点击后可以：

- **📋 Copy** - 复制为高清 PNG 到剪贴板 (2倍分辨率)
- **🖼️ PNG** - 下载为高清 PNG 图片文件
- **📄 PDF** - 导出为 PDF 文档 (适合打印)

> 导出的图片自动包含 32px 边距，无需手动裁剪。

## 🎨 设计特性

### 视觉设计

- **深色主题** - 专业的深色背景 (`#020617`)
- **网格背景** - 微妙的 40px 网格辅助视觉对齐
- **JetBrains Mono 字体** - 等宽编程字体，技术感强
- **颜色编码** - 不同组件类型使用语义化配色

### 颜色语义

| 组件类型 | 颜色 | 描述 |
|---------|------|------|
| Frontend | Cyan (`#22d3ee`) | 前端界面和客户端 |
| Backend | Emerald (`#34d399`) | 后端服务和 API |
| Database | Violet (`#a78bfa`) | 数据库和存储 |
| Framework | Amber (`#fbbf24`) | 框架层组件 |
| Security | Rose (`#fb7185`) | 安全和认证 |

### 技术实现

- **自包含 HTML** - 所有样式和脚本内联，无外部依赖
- **Google Fonts** - 在线加载 JetBrains Mono 字体
- **html2canvas** - 高质量 Canvas 渲染导出
- **jsPDF** - PDF 生成支持

## 📐 架构说明

### 01-overall-architecture.html

展示 ERPNext 的 4 层架构：

1. **前端层** - POS UI、Desk、Portal、Mobile App
2. **应用层** - 21 个业务模块 (POS、库存、销售、财务...)
3. **框架层** - Frappe Framework (ORM、API、权限、任务)
4. **数据层** - MariaDB、Redis、文件存储

### 02-controller-inheritance.html

完整的控制器继承链：

```
Document (Frappe)
  └─ StatusUpdater
      └─ TransactionBase
          └─ AccountsController (会计分录)
              └─ StockController (库存分录)
                  ├─ SellingController → POS Invoice, Sales Order...
                  └─ BuyingController → Purchase Order...
```

### 03-pos-workflow.html

POS 完整业务流程：

1. **开班** - POS Opening Entry
2. **收银** - POS Invoice (扫码、支付、打印)
3. **自动分录生成** - Stock Ledger Entry + GL Entry
4. **结班** - POS Closing Entry (核对金额)

## 🔧 生成工具

这些图表基于 [Cocoon AI architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) 模板生成。

### 模板特性

- MIT 开源许可
- 无需安装，浏览器直接打开
- 内置导出功能 (PNG/PDF)
- 响应式设计，支持移动端

## 📖 相关文档

- [图表索引](../INDEX.md) - 所有图表导航
- [Mermaid 图表](../_src/) - 原版 Mermaid 源文件
- [学习指南](../../ERPNEXT_门店系统学习指南.md) - 完整学习路径
- [快速上线指南](../../食品批发系统快速上线指南.md) - B2B 场景

---

**生成时间**: 2026-06-25  
**工具**: Cocoon AI architecture-diagram-generator  
**许可**: MIT License
