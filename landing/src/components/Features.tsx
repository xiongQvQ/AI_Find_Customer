import { Brain, Search, Globe, Shield, Zap, BarChart3, Languages, Users } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

const features = [
  {
    icon: Brain,
    title: '双层评估，先筛后挖',
    desc: '先用高召回 Quick Gate 排除明显无关、目录页与疑似竞争对手，再对保留候选做深度洞察，兼顾线索质量与覆盖率。',
  },
  {
    icon: Search,
    title: 'Google Maps 驱动获客发现',
    desc: '围绕 Google Maps 结果做企业发现与去重，优先拿到真实公司名称、地址、官网、电话和业务类型，减少无效网页噪音。',
  },
  {
    icon: Users,
    title: '决策人和联系方式深挖',
    desc: '自动补全 CEO、采购、销售负责人等关键角色，提取姓名、职位、邮箱、LinkedIn，并结合官网与搜索结果做交叉验证。',
  },
  {
    icon: Globe,
    title: '企业画像自动成型',
    desc: '支持官网、关键词和资料输入，自动抽取产品、行业、目标客户画像和负面筛选条件，为后续搜索和评估提供统一上下文。',
  },
  {
    icon: Zap,
    title: '自适应关键词循环',
    desc: '系统会根据每轮线索效果自动调整关键词，不只追求搜索量，而是持续提高匹配度、联系人质量和结果可用性。',
  },
  {
    icon: BarChart3,
    title: '海关记录与证据链展示',
    desc: '当公开贸易数据存在时，系统会展示具体海关/贸易记录，包括时间、方向、国家、HS 线索、产品线索和来源链接，而不只是一句总结。',
  },
  {
    icon: Shield,
    title: '风险标签与客户角色判断',
    desc: '每条线索都会保留 customer role、competitor risk、evidence strength 与 risk flags，方便销售快速识别真实客户、可疑竞争对手和低质量结果。',
  },
  {
    icon: Languages,
    title: '本地运行，可解释可导出',
    desc: '从搜索进度、线索评分到证据来源、CSV 导出，整条链路都可追溯，适合团队内复核、分发和二次跟进。',
  },
]

export default function Features() {
  return (
    <section id="features" className="py-24 px-4 sm:px-6 bg-background">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div className="max-w-2xl">
            <h2 className="text-sm font-semibold tracking-widest uppercase text-muted-foreground mb-3">
              核心优势
            </h2>
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
              全托管式 AI 工作流
            </p>
          </div>
          <p className="text-muted-foreground max-w-sm text-sm">
            不只是帮你搜公司，而是把“发现、评估、联系人挖掘、风险判断、海关证据整理”做成一条能交付销售使用的流程。
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f) => (
            <Card key={f.title} className="border bg-card shadow-sm">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <f.icon className="w-5 h-5 text-primary" />
                  </div>
                </div>
                <CardTitle className="text-lg font-semibold">
                  {f.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm leading-relaxed">
                  {f.desc}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
