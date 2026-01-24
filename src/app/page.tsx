import Navigation from "@/components/Navigation";
import HeroSection from "@/components/HeroSection";
import StatsSection from "@/components/StatsSection";
import ThreatMonitor from "@/components/ThreatMonitor";
import SecurityArsenal from "@/components/SecurityArsenal";
import CommandCenter from "@/components/CommandCenter";
import Testimonials from "@/components/Testimonials";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen overflow-x-hidden">
      <Navigation />
      <HeroSection />
      <StatsSection />
      <ThreatMonitor />
      <SecurityArsenal />
      <CommandCenter />
      <Testimonials />
      <CTASection />
      <Footer />
    </main>
  );
}
