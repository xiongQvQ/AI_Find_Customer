import { ArrowRight, Play, Cpu, ShieldCheck, Globe, UserCheck } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function Hero() {
  return (
    <section className="relative pt-32 pb-24 px-4 sm:px-6 overflow-hidden bg-background">
      <div className="relative max-w-5xl mx-auto text-center">

        <Badge variant="secondary" className="mb-6 py-1.5 px-4 text-sm font-medium">
          <span className="flex h-2 w-2 rounded-full bg-primary mr-2"></span>
          AI Agent 驱动 · 线索可解释 · 本地私有
        </Badge>

        <h1 className="text-5xl sm:text-7xl font-bold tracking-tight leading-[1.1] mb-6 text-foreground">
          重新定义
          <br />
          <span className="text-primary">外贸客户开发效率</span>
        </h1>

        <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto mb-10 leading-relaxed">
          B2Binsights 不是一个只会“批量搜索”的 AI 工具，而是一套面向真实成交场景的 B2B 获客工作流。
          只需输入你的产品资料，系统会自动完成：<span className="text-foreground font-medium">客户画像建立、Google Maps 企业发现、线索评估、决策人补全、风险标记与海关记录整理。</span>
          <br className="hidden sm:block mt-2" />
          让销售看到的不再是“搜到很多公司”，而是“哪些是真客户、为什么值得跟、证据在哪里”。
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="h-12 px-8 text-base font-semibold w-full sm:w-auto">
            获取专业版授权 <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
          <Button size="lg" variant="outline" className="h-12 px-8 text-base font-semibold w-full sm:w-auto">
            <Play className="mr-2 w-4 h-4" /> 演示视频
          </Button>
        </div>

        {/* Stats / Trust Badges */}
        <div className="mt-20 pt-10 border-t grid grid-cols-2 md:grid-cols-5 gap-8 max-w-5xl mx-auto">
          {[
            { value: '5+1', label: '核心 AI 智能体', icon: Cpu },
            { value: '决策人', label: '深度挖掘', icon: UserCheck },
            { value: '100%', label: '本地运行/数据私有', icon: ShieldCheck },
            { value: 'Maps', label: '真实企业发现', icon: Globe },
            { value: '海关', label: '记录级证据', icon: ShieldCheck },
          ].map((s) => (
            <div key={s.label} className="flex flex-col items-center">
              <div className="text-3xl font-bold text-foreground mb-1">{s.value}</div>
              <div className="text-xs text-muted-foreground uppercase tracking-widest">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
