const steps = [
  {
    num: '01',
    title: '输入产品与目标市场',
    desc: '填入官网、产品资料、关键词和目标区域，系统先理解你卖什么、适合卖给谁、哪些公司应该排除。',
    detail: '这一层不是简单读文档，而是形成后续搜索、评估和风险判断都要复用的统一上下文。',
  },
  {
    num: '02',
    title: '建立 ICP 与筛选规则',
    desc: 'ReAct 推理智能体会把产品、行业、客户角色、负面条件和竞争风险整理成结构化画像，明确什么叫“真客户”。',
    detail: '系统后面用的关键词生成、Quick Gate 预筛、客户角色判断和最终评分，都基于这一步。',
  },
  {
    num: '03',
    title: 'Google Maps 企业发现',
    desc: '系统围绕 Google Maps 找到真实企业主体，优先拿到公司名称、地址、官网、电话、业务类型等基础信息。',
    detail: '这一步的目标不是搜尽可能多网页，而是先抓到尽可能真实的企业实体，减少目录页和噪音站点。',
  },
  {
    num: '04',
    title: 'Quick Gate 预筛 + 深度洞察',
    desc: '先过滤明显无关、目录页、纯零售和疑似竞争对手，再对保留候选补全决策人、邮箱、LinkedIn、客户角色和风险标签。',
    detail: '这样既能保住召回率，又能避免把大量“相关但不是真客户”的公司推进到销售列表。',
  },
  {
    num: '05',
    title: '证据整理与销售交付',
    desc: '如果公开海关/贸易记录存在，系统会整理成具体记录；最终结果会连同评分、联系人、风险和来源证据一起展示与导出。',
    detail: '你拿到的不只是 lead 名单，而是一份可解释、可复核、可直接分发给销售跟进的线索档案。',
  },

]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-4 sm:px-6 bg-muted/30 border-y">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-sm font-semibold tracking-widest uppercase text-muted-foreground mb-3">工作流解析</h2>
          <h3 className="text-3xl sm:text-4xl font-bold mb-4 text-foreground">机器为你代工的 5 个步骤</h3>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            从客户画像、企业发现到风险评估、联系人补全与证据整理，
            把原本分散的人工动作压缩成一条可持续复用的获客工作流。
          </p>
        </div>

        <div className="relative max-w-4xl mx-auto">
          {/* Vertical line indicator */}
          <div className="absolute left-[2.25rem] top-8 bottom-8 w-px bg-border hidden md:block" />

          <div className="space-y-12">
            {steps.map((step) => (
              <div key={step.num} className="flex flex-col md:flex-row gap-6 md:gap-12 relative group">
                <div className="flex-shrink-0 relative z-10 w-16 md:w-20">
                  <div className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-background border shadow-sm flex items-center justify-center text-xl md:text-2xl font-black text-muted-foreground/30 group-hover:text-primary group-hover:border-primary transition-colors">
                    {step.num}
                  </div>
                </div>
                <div className="flex-1 pt-2 md:pt-4">
                  <h4 className="font-bold text-xl mb-3 text-foreground">{step.title}</h4>
                  <p className="text-muted-foreground leading-relaxed mb-3">{step.desc}</p>
                  <p className="text-sm text-muted-foreground/80 bg-background/50 p-3 rounded-md border inline-block">
                    {step.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
