import { useState } from 'react'
import {
  BFTheme,
  BrandLockup,
  Button,
  Card,
  Notice,
  ProcessSteps,
  Progress,
  StatusTag,
  Tabs,
} from '@bflabs/ui'

const DEMO_HOST = 'your-site.com'

const axes = [
  {
    id: 'discoverable',
    index: '01',
    score: 75,
    label: '可发现',
    description: '公开入口能找到，正文对爬虫仍偏薄。',
    tone: 'progress' as const,
    tag: 'partial',
  },
  {
    id: 'understandable',
    index: '02',
    score: 33,
    label: '可理解',
    description: '购买事实缺少稳定答案页。',
    tone: 'accent' as const,
    tag: 'weak',
  },
  {
    id: 'actionable',
    index: '03',
    score: 0,
    label: '可操作',
    description: '尚无 MCP / 工具契约。',
    tone: 'accent' as const,
    tag: 'fail',
  },
]

const findings = [
  { id: 'D-HTML', title: '原始 HTML 缺少可用正文', owner: 'geo-optimize' },
  { id: 'U-INTENTS', title: '高意图问题没有答案入口', owner: 'geo-optimize' },
  { id: 'A-TOOLS', title: '公开工具与 schema 不可发现', owner: 'webmcp-enable' },
]

const deliverySteps = [
  { id: 'baseline', label: '基线', description: '锁定接手前证据', state: 'complete' as const },
  { id: 'fix', label: '修复', description: '落地可验证改动', state: 'complete' as const },
  { id: 'verify', label: '验收', description: '复测与抽样回执', state: 'active' as const },
  { id: 'trend', label: '趋势', description: '周期对比与续修', state: 'queued' as const },
]

export default function App() {
  const [url, setUrl] = useState('')
  const [screen, setScreen] = useState('diagnose')
  const [activeStep, setActiveStep] = useState('verify')
  const [scannedHost, setScannedHost] = useState(DEMO_HOST)
  const [showMore, setShowMore] = useState(false)

  const startScan = () => {
    const cleaned = url
      .trim()
      .replace(/^https?:\/\//i, '')
      .replace(/\/.*$/, '')
    setScannedHost(cleaned || DEMO_HOST)
    setShowMore(false)
    setScreen('report')
  }

  return (
    <BFTheme className="ar-shell">
      <header className="ar-header">
        <BrandLockup tagline="Agent Readiness" />
      </header>

      <main className="ar-main">
        {screen === 'diagnose' ? (
          <DiagnoseScreen
            url={url}
            onUrlChange={setUrl}
            onScan={startScan}
          />
        ) : (
          <div className="ar-after">
            <Tabs
              label="结果"
              value={screen}
              onValueChange={setScreen}
              items={[
                {
                  value: 'report',
                  label: '报告',
                  content: (
                    <ReportScreen
                      host={scannedHost}
                      showMore={showMore}
                      onToggleMore={() => setShowMore((v) => !v)}
                      onRescan={() => setScreen('diagnose')}
                      onPaid={() => setScreen('delivery')}
                    />
                  ),
                },
                {
                  value: 'delivery',
                  label: '交付示例',
                  content: (
                    <DeliveryScreen
                      host={scannedHost}
                      activeStep={activeStep}
                      onStepChange={setActiveStep}
                    />
                  ),
                },
              ]}
            />
          </div>
        )}
      </main>
    </BFTheme>
  )
}

function DiagnoseScreen({
  url,
  onUrlChange,
  onScan,
}: {
  url: string
  onUrlChange: (value: string) => void
  onScan: () => void
}) {
  return (
    <section className="ar-landing">
      <div className="ar-landing__center">
        <h1 className="ar-landing__title">
          你的网站，AI 读得懂吗？
        </h1>
        <p className="ar-landing__sub">
          免费检查可发现、可理解、可操作。不承诺排名，只给证据。
        </p>

        <form
          className="ar-search"
          onSubmit={(event) => {
            event.preventDefault()
            onScan()
          }}
        >
          <div className="ar-search__field">
            <span className="ar-search__prefix">https://</span>
            <input
              value={url}
              placeholder={DEMO_HOST}
              onChange={(event) => onUrlChange(event.target.value)}
              autoComplete="url"
              inputMode="url"
              aria-label="网站域名"
              autoFocus
            />
          </div>
          <Button type="submit" variant="primary" size="lg">
            检查
          </Button>
        </form>

        <p className="ar-landing__line">
          30 秒出报告 · 公开页面 only · 零登录
        </p>
      </div>
    </section>
  )
}

function ReportScreen({
  host,
  showMore,
  onToggleMore,
  onRescan,
  onPaid,
}: {
  host: string
  showMore: boolean
  onToggleMore: () => void
  onRescan: () => void
  onPaid: () => void
}) {
  return (
    <section className="ar-result">
      <div className="ar-result__head">
        <div>
          <StatusTag tone="success">完成</StatusTag>
          <h2 className="ar-result__host">{host}</h2>
        </div>
        <Button variant="quiet" size="sm" onClick={onRescan}>
          检查其他站
        </Button>
      </div>

      <div className="ar-scores">
        {axes.map((axis) => (
          <article className="ar-score" key={axis.id}>
            <div className="ar-score__meta">
              <span>{axis.label}</span>
              <StatusTag tone={axis.tone} showDot={false}>
                {axis.tag}
              </StatusTag>
            </div>
            <p className="ar-score__num">
              {axis.score}
              <small>/100</small>
            </p>
            <Progress value={axis.score} showValue={false} />
            <p className="ar-score__desc">{axis.description}</p>
          </article>
        ))}
      </div>

      <ul className="ar-gaps">
        {findings.map((item) => (
          <li key={item.id}>
            <code>{item.id}</code>
            <span>{item.title}</span>
          </li>
        ))}
      </ul>

      <div className="ar-result__foot">
        <Button variant="secondary" size="sm" onClick={onToggleMore}>
          {showMore ? '收起' : '如何改进'}
        </Button>
        <span className="ar-fine">可见度与业务结果默认未测量</span>
      </div>

      {showMore ? (
        <div className="ar-more">
          <Card
            index="Free"
            title="开源 Skill"
            description="把报告交给自己的 Agent，本地修、可验证。"
          >
            <p className="ar-more__list">geo-optimize · webmcp-enable</p>
            <Button variant="secondary" size="sm" trailingIcon>
              GitHub
            </Button>
          </Card>
          <Card
            tone="dark"
            index="Paid"
            title="BFLabs 交付"
            description="分阶段实施与复测，用 Before/After 证明变化。"
          >
            <Button variant="accent" size="sm" trailingIcon onClick={onPaid}>
              看交付示例
            </Button>
          </Card>
        </div>
      ) : null}
    </section>
  )
}

function DeliveryScreen({
  host,
  activeStep,
  onStepChange,
}: {
  host: string
  activeStep: string
  onStepChange: (value: string) => void
}) {
  return (
    <section className="ar-result ar-result--delivery">
      <div className="ar-result__head">
        <div>
          <StatusTag tone="progress">验收中</StatusTag>
          <h2 className="ar-result__host">{host}</h2>
          <p className="ar-fine">付费示例：阶段清楚，变化可见</p>
        </div>
      </div>

      <ProcessSteps
        items={deliverySteps}
        value={activeStep}
        onValueChange={onStepChange}
      />

      <div className="ar-delta">
        <Card tone="dark">
          <p className="ar-delta__kicker">本周 Δ</p>
          <p className="ar-delta__num">
            33<span>→</span>78
          </p>
          <p className="ar-fine ar-fine--on-dark">可理解 +45 · 关闭 4/7 缺口</p>
          <Progress value={78} label="可理解" />
        </Card>
        <div className="ar-ba">
          <Card index="Before" title="几乎读不到">
            <p className="ar-fine">HTML 约 38 字 · 无答案页</p>
          </Card>
          <Card tone="accent" index="After" title="事实可核对">
            <p className="ar-fine">SSR 正文 · 答案页 · 接入路径</p>
          </Card>
        </div>
      </div>

      <Notice
        title="没有 Before / After，就不算完成本阶段"
        description="下一阶段只修仍开放的项。"
      />
    </section>
  )
}
