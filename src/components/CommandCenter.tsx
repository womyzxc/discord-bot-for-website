"use client";

const features = [
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    title: "Immersive Interface",
    description: "Game-like UI with smooth animations, interactive elements, and intuitive navigation that makes security management enjoyable.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: "Real-time Visualization",
    description: "Live threat maps, animated charts, and dynamic dashboards that turn complex security data into engaging visuals.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    ),
    title: "Achievement System",
    description: "Unlock badges, level up your security score, and compete with other servers through our gamified progression system.",
  },
];

export default function CommandCenter() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 bg-purple-900/30 px-4 py-2 rounded-full border border-purple-500/30 text-purple-400 text-sm mb-4">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
            Interactive Experience
          </span>
          <h2 className="font-orbitron font-bold text-3xl md:text-5xl text-white mb-4">
            Gamified <span className="text-purple-500">Command Center</span>
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Transform security management into an engaging experience with our game-inspired dashboard that makes protecting your server rewarding and intuitive
          </p>
        </div>

        {/* Content */}
        <div className="grid md:grid-cols-2 gap-8 items-center">
          {/* Dashboard Preview */}
          <div className="relative">
            <div className="absolute -top-4 right-4 flex items-center gap-2 bg-[#1a1a1b] px-3 py-1.5 rounded-full border border-green-500/30 z-10">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-green-400 text-xs">Live Dashboard</span>
            </div>
            <div className="gradient-border rounded-2xl overflow-hidden">
              <img
                src="https://ext.same-assets.com/1028511663/1672369699.jpeg"
                alt="Dashboard Preview"
                className="w-full h-auto opacity-80"
              />
              <div className="absolute bottom-4 left-4 bg-[#0a0a0b]/90 backdrop-blur-sm px-4 py-2 rounded-lg border border-purple-500/30">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <div>
                    <p className="text-white text-sm font-semibold">Real-time Analytics</p>
                    <p className="text-gray-400 text-xs">Live threat monitoring</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features list */}
          <div className="space-y-4">
            {features.map((feature, index) => (
              <div
                key={index}
                className="gradient-border rounded-xl p-5 bg-[#0a0a0b] hover:bg-[#0f0f10] transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-purple-900/30 border border-purple-500/30 flex items-center justify-center text-purple-400 flex-shrink-0">
                    {feature.icon}
                  </div>
                  <div>
                    <h4 className="font-orbitron font-semibold text-white mb-2">
                      {feature.title}
                    </h4>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {/* CTA button */}
            <button className="w-full mt-6 flex items-center justify-center gap-2 bg-[#1a1a1b] hover:bg-[#252527] text-white px-6 py-4 rounded-xl transition border border-purple-500/30">
              <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              Try Interactive Demo
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse ml-2"></span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
