import { Zap, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t bg-background py-16 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 md:gap-8 mb-12">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
                <Zap className="w-5 h-5 fill-current" />
              </div>
              <span className="font-bold tracking-tight text-foreground text-lg">B2Binsights</span>
            </div>
            <p className="text-muted-foreground text-sm max-w-sm leading-relaxed">
              面向真实成交场景的 B2B 获客智能体。让 AI 帮你完成企业发现、客户评估、决策人补全、风险判断与证据整理，把销售时间留给真正值得跟进的客户。
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">产品</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li><a href="#features" className="hover:text-primary transition-colors">核心功能</a></li>
              <li><a href="#how-it-works" className="hover:text-primary transition-colors">工作原理</a></li>
              <li><a href="#pricing" className="hover:text-primary transition-colors">价格方案</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">支持与联系</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li><a href="#faq" className="hover:text-primary transition-colors">常见问题</a></li>
              <li>
                <a href="mailto:info@b2binsights.io" className="flex items-center gap-2 hover:text-primary transition-colors">
                  <Mail className="w-4 h-4" /> info@b2binsights.io
                </a>
              </li>

            </ul>
          </div>
        </div>

        <div className="pt-8 border-t flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p>© {new Date().getFullYear()} B2Binsights. 保留所有权利。</p>
          <div className="flex items-center gap-4">
            <span>本地运行</span>
            <span>数据私有</span>
            <span>买断制授权</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
