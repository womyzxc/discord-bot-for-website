"use client";

export default function HeroSection() {
  return (
    <section className="relative pt-32 pb-16 px-4 overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-20 left-10 w-16 h-16 opacity-20 animate-float">
          <svg className="w-full h-full text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div className="absolute top-40 right-20 w-12 h-12 opacity-20 animate-float" style={{ animationDelay: '0.5s' }}>
          <svg className="w-full h-full text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <div className="absolute bottom-40 left-20 w-14 h-14 opacity-20 animate-float" style={{ animationDelay: '1s' }}>
          <svg className="w-full h-full text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="absolute bottom-20 right-10 w-16 h-16 opacity-20 animate-float" style={{ animationDelay: '1.5s' }}>
          <svg className="w-full h-full text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      <div className="max-w-5xl mx-auto text-center relative z-10">
        {/* Status badges */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <div className="flex items-center gap-2 bg-[#1a1a1b] rounded-full px-4 py-2 border border-yellow-500/30">
            <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
            <span className="text-yellow-500 text-sm font-medium">THREAT DETECTED</span>
          </div>
          <div className="flex items-center gap-2 bg-[#1a1a1b] rounded-full px-4 py-2 border border-green-500/30">
            <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="text-green-500 text-sm font-medium">PROTECTED</span>
          </div>
        </div>

        {/* Main title badges */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <span className="flex items-center gap-2 bg-green-900/30 text-green-400 px-3 py-1 rounded-full text-xs border border-green-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            ACTIVE
          </span>
          <span className="text-purple-400 font-orbitron font-bold text-sm tracking-wider">#1 DISCORD SECURITY BOT</span>
          <span className="flex items-center gap-2 bg-orange-900/30 text-orange-400 px-3 py-1 rounded-full text-xs border border-orange-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
            THREAT
          </span>
        </div>

        {/* Main Headline */}
        <h1 className="font-orbitron font-black text-5xl md:text-7xl lg:text-8xl mb-6">
          <span className="text-white glow-text-purple">ULTIMATE</span>
          <br />
          <span className="bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 bg-clip-text text-transparent">
            ANTI-NUKE
          </span>
          <br />
          <span className="text-white">PROTECTION</span>
        </h1>

        {/* Feature badges */}
        <div className="flex items-center justify-center gap-3 mb-8 flex-wrap">
          <span className="flex items-center gap-2 bg-[#1a1a1b] px-4 py-2 rounded-full border border-purple-500/30 text-sm text-gray-300">
            <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Instant Response
          </span>
          <span className="flex items-center gap-2 bg-[#1a1a1b] px-4 py-2 rounded-full border border-yellow-500/30 text-sm text-gray-300">
            <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            AI-Powered
          </span>
          <span className="flex items-center gap-2 bg-[#1a1a1b] px-4 py-2 rounded-full border border-cyan-500/30 text-sm text-gray-300">
            <svg className="w-4 h-4 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Military-Grade
          </span>
        </div>

        {/* Description */}
        <p className="text-gray-400 text-lg md:text-xl max-w-3xl mx-auto mb-10">
          Stop server destruction before it happens. Offcialx's advanced AI detects and neutralizes{" "}
          <span className="text-purple-400 font-semibold">nuke attempts</span>,{" "}
          <span className="text-cyan-400 font-semibold">mass raids</span>, and{" "}
          <span className="text-orange-400 font-semibold">coordinated attacks</span> in{" "}
          <span className="text-green-400 font-semibold">&lt;0.1</span> seconds.
        </p>

        {/* CTA Buttons */}
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <a
            href="/auth"
            className="group relative bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white px-8 py-4 rounded-xl transition-all font-orbitron font-bold text-sm tracking-wider flex items-center gap-3 glow-purple"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            DEPLOY PROTECTION
          </a>
          <a
            href="https://discord.com/api/oauth2/authorize?client_id=1338739893035204628&permissions=8&scope=bot%20applications.commands"
            target="_blank"
            rel="noopener noreferrer"
            className="group bg-[#1a1a1b] hover:bg-[#252527] text-white px-8 py-4 rounded-xl transition-all font-orbitron font-bold text-sm tracking-wider flex items-center gap-3 border border-purple-500/30"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z" />
            </svg>
            ADD TO SERVER
          </a>
        </div>
      </div>
    </section>
  );
}
