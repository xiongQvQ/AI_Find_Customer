import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface WechatPaymentProps {
    isOpen: boolean
    onClose: () => void
}

export default function WechatPayment({ isOpen, onClose }: WechatPaymentProps) {
    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-md pt-10 text-center">
                <DialogHeader>
                    <div className="mx-auto mb-2 text-xs font-semibold text-primary uppercase tracking-wider">
                        联系客户经理
                    </div>
                    <DialogTitle className="text-2xl font-bold mb-2 text-center">扫码添加微信</DialogTitle>
                    <DialogDescription className="text-center text-sm mb-4">
                        添加客户经理微信并备注 "B2Binsights"，我们会尽快与你沟通授权方案。
                    </DialogDescription>
                </DialogHeader>

                <div className="flex justify-center my-6">
                    <div className="w-64 h-64 rounded-xl overflow-hidden border bg-white p-2 shadow-sm">
                        <img
                            src="/WechatIMG1064.jpeg"
                            alt="Wechat QR Code"
                            className="w-full h-full object-contain"
                        />
                    </div>
                </div>

                <div className="flex flex-col gap-3">
                    <DialogClose asChild>
                        <Button variant="outline" className="w-full h-11">
                            我已知晓
                        </Button>
                    </DialogClose>
                </div>
            </DialogContent>
        </Dialog>
    )
}
