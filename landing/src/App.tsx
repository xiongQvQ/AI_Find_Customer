import { useState } from 'react'
import './App.css'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import ProductShowcase from './components/ProductShowcase'
import PainPoints from './components/PainPoints'
import Features from './components/Features'
import HowItWorks from './components/HowItWorks'
import Pricing from './components/Pricing'
import FAQ from './components/FAQ'
import Footer from './components/Footer'
import WechatPayment from './components/WechatPayment'

function App() {
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false)

  const handleContact = () => {
    setIsPaymentModalOpen(true)
  }

  return (
    <div className="min-h-screen bg-background font-sans antialiased text-foreground">
      <Navbar />
      <main>
        <Hero />
        <ProductShowcase />
        <PainPoints />
        <Features />
        <HowItWorks />
        <Pricing onContact={handleContact} />
        <FAQ />
      </main>
      <Footer />

      <WechatPayment
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
      />
    </div>
  )
}

export default App
