import { Check, Building2, type LucideIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface Plan {
  icon: LucideIcon
  name: string
  desc: string
  features: string[]
  cta: string
  highlight: boolean
}

const plans: Plan[] = [
  {
    icon: Building2,
    name: '商务咨询',
    desc: '针对你的团队规模、使用场景和部署要求，由客户经理提供 1 对 1 方案说明与授权建议。',
    features: [
      '根据团队人数推荐授权方式',
      '说明核心能力与适用边界',
      '支持批量授权与定制咨询',
      '提供部署、安装与使用指导',
      '解答数据安全与交付问题',
    ],
    cta: '联系客户经理',
    highlight: true,
  },
]

interface PricingProps {
  onContact: () => void
}

export default function Pricing({ onContact }: PricingProps) {
  return (
    <section id="pricing" className="py-24 px-4 sm:px-6 bg-muted/30">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">联系客户经理获取方案</h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            当前页面不展示价格。根据你的团队规模和业务需求，客户经理会提供对应的授权方案与使用建议。
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative overflow-hidden transition-all duration-300 ${plan.highlight ? 'border-primary ring-1 ring-primary shadow-md' : 'shadow-sm'
                }`}
            >
              {plan.highlight && (
                <div className="absolute top-0 right-0">
                  <Badge className="rounded-none rounded-bl-lg px-4 py-1 font-semibold shadow-none">
                    推荐选择
                  </Badge>
                </div>
              )}
              <CardHeader className="p-8 pb-4">
                <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mb-6">
                  <plan.icon className="w-6 h-6 text-foreground" />
                </div>
                <CardTitle className="text-xl mb-2">{plan.name}</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  {plan.desc}
                </CardDescription>
              </CardHeader>

              <CardContent className="p-8 pt-0">
                <Button
                  onClick={onContact}
                  variant={plan.highlight ? "default" : "outline"}
                  className="w-full h-12 mb-8 text-base font-semibold"
                >
                  {plan.cta}
                </Button>

                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4 border-b pb-2">
                  核心权益
                </div>
                <ul className="space-y-4">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-3 text-sm text-foreground">
                      <div className="mt-0.5 flex-shrink-0">
                        <Check className="w-4 h-4 text-primary" />
                      </div>
                      {f}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-16 text-center text-sm text-muted-foreground">
          支持微信沟通 · 可提供完整安装说明、使用指导与结果交付建议
        </div>
      </div>
    </section>
  )
}
