import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const screenshots = [
    {
        title: "客户画像与筛选规则自动生成",
        desc: "系统先整理产品、目标客户、负面筛选条件和竞争风险判断，后续搜索与评估都基于统一画像执行。",
        image: "/WechatIMG1056.png",
        tag: "智能分析"
    },
    {
        title: "Google Maps 发现 + 风险预筛",
        desc: "先发现真实企业，再快速过滤目录页、纯零售和疑似竞争对手，把深度洞察成本留给更值得跟进的公司。",
        image: "/WechatIMG1057.png",
        tag: "精准获客"
    },
    {
        title: "决策人、评分与海关证据同屏呈现",
        desc: "线索详情不只展示联系人，还会保留客户角色、风险标签、证据强度和可落地的海关/贸易记录来源。",
        image: "/WechatIMG1058.png",
        tag: "高效转化"
    }
]

export default function ProductShowcase() {
    return (
        <section id="showcase" className="py-24 px-4 sm:px-6 bg-background overflow-hidden">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-sm font-semibold tracking-widest uppercase text-muted-foreground mb-3">
                        界面预览
                    </h2>
                    <h3 className="text-3xl sm:text-5xl font-bold mb-4 text-foreground tracking-tight">
                        看得见的自动化，触手可及的订单
                    </h3>
                    <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                        不是为了炫技而堆砌 AI，而是把复杂的判断链路压缩成销售能直接使用的结果界面。
                        搜索、评估、证据、联系人与导出一屏打通。
                    </p>
                </div>

                <div className="space-y-24">
                    {screenshots.map((s, i) => (
                        <div
                            key={i}
                            className={`flex flex-col ${i % 2 === 1 ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-12 md:gap-20`}
                        >
                            <div className="flex-1 space-y-6">
                                <Badge variant="secondary" className="px-3 py-1">{s.tag}</Badge>
                                <h4 className="text-3xl font-bold text-foreground">{s.title}</h4>
                                <p className="text-muted-foreground text-lg leading-relaxed">
                                    {s.desc}
                                </p>
                                <div className="pt-4 flex gap-4">
                                    <div className="w-12 h-1 bg-primary rounded-full" />
                                </div>
                            </div>

                            <div className="flex-1 w-full relative">
                                {/* Window Frame Decoration */}
                                <Card className="overflow-hidden border-2 shadow-2xl rounded-xl group transition-all duration-500 hover:translate-y-[-4px]">
                                    <div className="bg-muted h-8 border-b flex items-center px-4 gap-1.5 backdrop-blur-sm">
                                        <div className="w-2.5 h-2.5 rounded-full bg-red-400/50" />
                                        <div className="w-2.5 h-2.5 rounded-full bg-amber-400/50" />
                                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/50" />
                                    </div>
                                    <div className="relative aspect-[16/10] overflow-hidden bg-zinc-900">
                                        <img
                                            src={s.image}
                                            alt={s.title}
                                            className="object-cover w-full h-full object-top transition-transform duration-700 group-hover:scale-105"
                                        />
                                    </div>
                                </Card>

                                {/* Decorative background element */}
                                <div className={`absolute -z-10 w-64 h-64 bg-primary/5 rounded-full blur-3xl -top-10 ${i % 2 === 1 ? '-left-10' : '-right-10'}`} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
