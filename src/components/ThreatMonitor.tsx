"use client";

export default function ThreatMonitor() {
  return (
    <section className="py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-white font-semibold">Live Threat Monitor</span>
            </div>
            <span className="text-gray-500 text-sm">Real-time Protection Status</span>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 bg-[#1a1a1b] rounded-full px-4 py-2 border border-green-500/30">
              <span className="text-gray-400 text-sm">Anti-Nuke Shield</span>
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              <span className="text-green-500 text-sm font-medium">ACTIVE</span>
            </div>

            <div className="flex items-center gap-2 bg-[#1a1a1b] rounded-full px-4 py-2 border border-yellow-500/30">
              <span className="text-gray-400 text-sm">Raid Detection</span>
              <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
              <span className="text-yellow-500 text-sm font-medium">SCANNING</span>
            </div>

            <div className="flex items-center gap-2 bg-[#1a1a1b] rounded-full px-4 py-2 border border-purple-500/30">
              <span className="text-gray-400 text-sm">AI Analysis</span>
              <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
              <span className="text-purple-500 text-sm font-medium">LEARNING</span>
            </div>
          </div>

          <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-800">
            <button className="text-gray-400 hover:text-white transition text-sm flex items-center gap-2">
              Explore Security Arsenal
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <div className="w-10 h-10 rounded-full bg-purple-900/30 border border-purple-500/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
