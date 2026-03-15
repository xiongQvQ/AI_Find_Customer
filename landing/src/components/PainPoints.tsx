import { AlertCircle, Clock, Search, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const painPoints = [
    {
        icon: Clock,
        title: '效率极低',
        description: '每天花费 4-6 小时手动在 Google、LinkedIn 和各大 B2B 平台翻找线索。',
    },
    {
        icon: Search,
        title: '石沉大海',
        description: '辛苦找到的往往是 generic 邮箱（info/sales），永远联系不到真正的决策者。',
    },
    {
        icon: TrendingDown,
        title: '获客成本高',
        description: '购买现成的线索库不仅昂贵，而且数据往往已经过时，转化率极低。',
    },
    {
        icon: AlertCircle,
        title: '缺乏专业性',
        description: '无法快速调研每一个潜在客户的背景，导致发出的开发信千篇一律。',
    },
]

export default function PainPoints() {
    return (
        <section className="py-24 px-4 sm:px-6 bg-muted/30">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-sm font-semibold tracking-widest uppercase text-muted-foreground mb-3">
                        为什么选择 B2Binsights
                    </h2>
                    <p className="text-3xl sm:text-4xl font-bold mb-4 text-foreground">
                        传统外贸获客的时代已经过去
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {painPoints.map((point) => (
                        <Card key={point.title} className="bg-card border-none shadow-sm">
                            <CardHeader className="pb-4">
                                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                                    <point.icon className="w-5 h-5 text-primary" />
                                </div>
                                <CardTitle className="text-xl font-bold">{point.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-muted-foreground leading-relaxed text-sm">
                                    {point.description}
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                <div className="mt-16 p-6 rounded-xl bg-primary/5 border border-primary/10 text-center max-w-3xl mx-auto">
                    <p className="text-foreground text-base mb-0">
                        <strong>B2Binsights</strong> 正是为此而生。它不是一个简单的抓取工具，而是一套把<strong>发现、评估、联系人挖掘、风险判断与证据整理</strong>打通的获客工作流。
                    </p>
                </div>
            </div>
        </section>
    )
}
