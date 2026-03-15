import { useState } from 'react'
import { Menu, X, Zap } from 'lucide-react'
import { Button } from "@/components/ui/button"

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 group cursor-pointer">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
            <Zap className="w-5 h-5 fill-current" />
          </div>
          <span className="font-bold text-lg tracking-tight text-foreground">B2Binsights</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
          <a href="#features" className="hover:text-foreground transition-colors">功能特性</a>
          <a href="#how-it-works" className="hover:text-foreground transition-colors">工作原理</a>
          <a href="#pricing" className="hover:text-foreground transition-colors">定价方案</a>
          <a href="#faq" className="hover:text-foreground transition-colors">服务支持</a>
        </div>

        <div className="hidden md:flex items-center gap-4">
          <Button asChild size="sm">
            <a href="#pricing">获取授权</a>
          </Button>
        </div>

        <button className="md:hidden p-2 text-muted-foreground hover:text-foreground transition-colors" onClick={() => setOpen(!open)}>
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t bg-background px-6 py-4 flex flex-col gap-4 text-sm font-medium">
          <a href="#features" className="text-muted-foreground hover:text-foreground" onClick={() => setOpen(false)}>功能特性</a>
          <a href="#how-it-works" className="text-muted-foreground hover:text-foreground" onClick={() => setOpen(false)}>工作原理</a>
          <a href="#pricing" className="text-muted-foreground hover:text-foreground" onClick={() => setOpen(false)}>定价方案</a>
          <a href="#faq" className="text-muted-foreground hover:text-foreground" onClick={() => setOpen(false)}>服务支持</a>
          <Button asChild className="w-full mt-2" onClick={() => setOpen(false)}>
            <a href="#pricing">立即获取授权</a>
          </Button>
        </div>
      )}
    </nav>
  )
}
