# BFLabs Agent Readiness · Brand Spec
> 采集日期：2026-08-07  
> 视觉真源：https://github.com/Sunnyender-org/bflabs-ui (`5499778`)  
> 包：`@bflabs/ui@0.1.0`

## 核心资产

### Logo
- 官方：`@bflabs/ui` → `BrandMark` / `BrandLockup`（`bf-mark.svg` 1200×700）
- 禁止重画、拉伸、改色

### Token（来自 `packages/ui/src/styles/tokens.css`）
- Charcoal `#111417`
- Warm White `#FAF8F5`
- BF Orange `#FF6A33`
- Steel `#6B7177` / Silver / Soft Tone / Sand
- Signal Blue `#4C7FAF`
- Display：Space Grotesk
- Body：Inter + Noto Sans SC
- Radius：control 2px / surface 4px（偏方）

### 气质
Useful · Real · Applied · Reliable · Forward-moving

### 禁区（与 bflabs-ui 一致）
- 大面积装饰渐变 / 软气泡 / 过多 pill
- 神秘总分盖过三轴
- readiness 画成 ranking/收入保证

## 产品结构
```
免费诊断站 → 免费 Skill → 付费阶段交付（基线/修复/验收/趋势）
```

## 前端组件映射（实现时必须用官方组件）

| 产品区 | @bflabs/ui |
|---|---|
| 顶栏品牌 | `BrandLockup` |
| 屏切换 | `Tabs` |
| 主标题 | `KineticHeading` / `SectionHeading` |
| 诊断提交 | `Button` primary + accent |
| 三轴 / Skill / Before-After | `Card` (+ tone dark/accent) |
| 分数进度 | `Progress` |
| 状态 | `StatusTag` |
| 付费四阶段 | `ProcessSteps` |
| 边界提示 | `Notice` |
| 入场 | `Reveal` |
| 主题壳 | `BFTheme` |

## 设计原型
- 可运行：`designs/bflabs-ui-agent-readiness/`
- 预览图：`designs/bflabs-ui-agent-readiness/preview/*.png`
