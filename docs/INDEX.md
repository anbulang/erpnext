# ERPNext 架构文档 - 图表索引

> 快速导航到所有架构图和流程图

## ⭐ 新版专业图表 (推荐)

**深色主题 · 交互式 · 一键导出 PNG/PDF**

| 图表 | 描述 | 文件 |
|------|------|------|
| **整体架构** | 4层技术架构：前端→应用→框架→数据 | [HTML](diagrams/01-overall-architecture.html) 🔥 |
| **控制器继承** | Document→StatusUpdater→...→POSInvoice | [HTML](diagrams/02-controller-inheritance.html) 🔥 |
| **POS收银流程** | 开班→收银→库存会计分录→结班 | [HTML](diagrams/03-pos-workflow.html) 🔥 |

> 💡 **使用方法**: 在浏览器中打开 HTML 文件，点击右上角 `⋯` 可导出为 PNG 或 PDF

---

## 📋 原版 Mermaid 图表

### 🏗️ 架构图 (Architecture)

| 图表 | 描述 | 文件 |
|------|------|------|
| **整体架构** | 4层技术架构：前端→应用→框架→数据 | [SVG](architecture/overall-architecture.svg) \| [PNG](architecture/overall-architecture.png) |
| **技术栈** | 完整技术栈及依赖关系 | [SVG](architecture/tech-stack.svg) \| [PNG](architecture/tech-stack.png) |
| **控制器继承** | Document→StatusUpdater→...→POSInvoice | [SVG](architecture/controller-inheritance.svg) \| [PNG](architecture/controller-inheritance.png) |

### 🔄 业务流程 (Workflows)

| 图表 | 描述 | 文件 |
|------|------|------|
| **POS收银流程** | 开班→收银→库存会计分录→结班 | [SVG](workflows/pos-workflow.svg) \| [PNG](workflows/pos-workflow.png) |
| **B2B批发流程** | 报价单→订单→送货→开票→收款 | [SVG](workflows/wholesale-flow.svg) \| [PNG](workflows/wholesale-flow.png) |

### 📊 数据模型 (Data Model)

| 图表 | 描述 | 文件 |
|------|------|------|
| **DocType关系** | 核心业务对象关系图 | [SVG](data-model/data-relationships.svg) \| [PNG](data-model/data-relationships.png) |

---

## 🎯 按场景查看

### 我是新手，想理解 ERPNext 整体架构
1. 先看 [整体架构](diagrams/01-overall-architecture.html) 🔥 - 了解 4 层模型
2. 再看 [技术栈](architecture/tech-stack.svg) - 了解用了哪些技术
3. 然后看 [控制器继承](diagrams/02-controller-inheritance.html) 🔥 - 理解代码组织方式

### 我要实现零售门店POS系统
1. 看 [POS收银流程](diagrams/03-pos-workflow.html) 🔥 - 理解完整收银流程
2. 看 [DocType关系](data-model/data-relationships.svg) - 理解数据模型
3. 参考 [门店系统学习指南](../ERPNEXT_门店系统学习指南.md)

### 我要实现食品批发系统
1. 看 [B2B批发流程](workflows/wholesale-flow.svg) - 理解业务流程
2. 看 [DocType关系](data-model/data-relationships.svg) - 理解数据结构
3. 参考 [食品批发系统快速上线指南](../食品批发系统快速上线指南.md)

### 我要定制开发
1. 看 [控制器继承](architecture/controller-inheritance.svg) - 理解继承链
2. 看 [整体架构](architecture/overall-architecture.svg) - 理解框架结构
3. 参考 [学习指南第五层：定制化开发](../ERPNEXT_门店系统学习指南.md#第五层定制化开发)

---

## 🔧 技术细节

### 图表生成工具
- **语言**: Mermaid 图表语法
- **渲染器**: @mermaid-js/mermaid-cli (puppeteer + Chromium)
- **字体**: WenQuanYi Zen Hei (文泉驿正黑，支持中文)
- **格式**: SVG (矢量图，无损缩放) + PNG (位图，兼容性好)

### 源文件位置
所有 Mermaid 源文件位于 `_src/` 目录：
- `_src/*.mmd` - Mermaid 图表源码
- `_src/puppeteer-config.json` - 渲染配置
- `_src/render-all.sh` - 批量渲染脚本

### 如何更新图表
```bash
# 1. 编辑源文件
vi docs/_src/overall-architecture.mmd

# 2. 重新渲染（单个）
cd docs/_src
npx -y @mermaid-js/mermaid-cli \
  -i overall-architecture.mmd \
  -o ../architecture/overall-architecture.svg \
  -t default -b white -p puppeteer-config.json

# 3. 或批量渲染（所有）
bash render-all.sh
```

---

## 📖 相关文档

- [README](README.md) - 文档说明
- [ERPNext 门店系统学习指南](../ERPNEXT_门店系统学习指南.md) - 完整学习路径
- [门店系统架构图](../门店系统架构图.md) - 文本版架构说明
- [食品批发系统快速上线指南](../食品批发系统快速上线指南.md) - B2B场景

---

**最后更新**: 2026-06-24  
**生成工具**: Mermaid CLI + Workflow
