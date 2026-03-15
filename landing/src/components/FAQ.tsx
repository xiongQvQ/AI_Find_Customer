import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const faqs = [
  {
    q: 'B2Binsights 需要联网运行吗？',
    a: '软件本体本地运行，不依赖我们的服务器。但在执行企业发现、官网解析、决策人挖掘和公开贸易数据查询时，需要调用你自己的 LLM API 和搜索 API。这些都是你可控的第三方能力，数据主流程仍在本地完成。',
  },
  {
    q: '我需要自己准备 API Key 吗？',
    a: '是的。至少需要一个 LLM API Key 和一个搜索 API Key。系统不锁定供应商，你可以根据预算选择更强推理模型或更低成本模型。重点不是堆模型，而是让模型在你已经定义好的评估、联系人、风险和证据工作流里发挥作用。',
  },
  {
    q: '支持哪些操作系统？',
    a: '目前优先支持 Windows 系统（提供 .exe 安装包），适配 Windows 10 及以上版本。macOS 版本正在内部适配中，敬请期待。',
  },
  {
    q: '一次能找多少条线索？',
    a: '取决于你设置的目标数量、目标市场、搜索 API 配额和筛选条件。和传统批量抓取不同，B2Binsights 会先去噪再深挖，所以你拿到的不是单纯“搜到多少公司”，而是带公司信息、客户角色、风险标签、决策人、联系方式和证据来源的可用线索。',
  },
  {
    q: '授权码如何使用？',
    a: '购买后我们会通过邮件发送授权码。在软件首次启动时输入授权码激活，年度授权到期后需续费，终身授权不需要。',
  },
  {
    q: '可以退款吗？',
    a: '由于软件产品的特殊性，授权处理后暂不支持无理由退款。为了确保符合您的需求，我们提供免费的功能测试服务，请扫描定价下方的微信联系客户经理为您安排测试。',
  },
  {
    q: '和人工找客户相比有什么优势？',
    a: '人工最大的问题不是找不到公司，而是很难持续完成“发现、判断、查官网、找决策人、辨别竞争对手、整理证据”这整套动作。B2Binsights 把这条链路做成自动化流程，销售看到的是更接近成交判断的线索，而不是一堆还要二次筛选的网页结果。',
  },
  {
    q: '决策人挖掘功能是怎么工作的？',
    a: '系统会优先访问官网，再结合搜索结果补全管理层、采购、销售负责人等关键角色。输出不仅包含姓名和职位，还会保留邮箱、LinkedIn 和来源页面；如果只能推断邮箱，也会明确标记为 inferred，避免把猜测当成事实。',
  },
  {
    q: '为什么它比普通“搜公司”工具更靠谱？',
    a: '因为它不把“行业相关”直接当成“目标客户”。系统会先做 Quick Gate 预筛，再做深度评估，区分真实客户、疑似竞争对手、目录页、纯零售公司和低质量候选。最后还会给出 customer role、competitor risk、evidence strength 和 risk flags，帮助团队复核。',
  },
  {
    q: '海关数据会展示什么？',
    a: '如果公开贸易数据库里能找到具体记录，系统会展示对应的来源、时间、贸易方向、相关国家、HS 线索、产品线索和来源链接。如果没有找到正向证据，就不会伪装成“有海关数据”，只会明确标记为 No data found。',
  },
  {
    q: '是否支持团队多人使用？',
    a: '年度授权支持 1 台设备，终身授权支持 2 台设备。如果团队有更多设备需求，请联系我们询问团队授权方案。',
  },
]

export default function FAQ() {
  return (
    <section id="faq" className="py-24 px-4 sm:px-6 bg-background">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-sm font-semibold tracking-widest uppercase text-muted-foreground mb-3">支持与解答</h2>
          <h3 className="text-3xl sm:text-4xl font-bold mb-4 text-foreground">常见问题</h3>
          <p className="text-muted-foreground text-lg">还有其他疑问？欢迎发邮件联系我们团队。</p>
        </div>

        <Accordion type="single" collapsible className="w-full">
          {faqs.map((faq, i) => (
            <AccordionItem key={i} value={`item-${i}`} className="border-b border-border">
              <AccordionTrigger className="text-left font-medium text-foreground py-5 hover:text-primary transition-colors">
                {faq.q}
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground leading-relaxed">
                {faq.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}
