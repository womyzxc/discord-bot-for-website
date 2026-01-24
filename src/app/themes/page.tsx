"use client";

import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { useState } from "react";

const themes = [
  {
    id: "default",
    name: "Default",
    description: "The classic Offcialx purple theme",
    colors: {
      primary: "#9333ea",
      secondary: "#581c87",
      accent: "#a855f7",
    },
    gradient: "from-purple-600 to-purple-900",
    popular: true,
  },
  {
    id: "cyber-green",
    name: "Cyber Green",
    description: "A futuristic green hacker aesthetic",
    colors: {
      primary: "#22c55e",
      secondary: "#14532d",
      accent: "#4ade80",
    },
    gradient: "from-green-500 to-green-900",
    popular: false,
  },
  {
    id: "neon-blue",
    name: "Neon Blue",
    description: "Cool blue vibes for your server",
    colors: {
      primary: "#3b82f6",
      secondary: "#1e3a8a",
      accent: "#60a5fa",
    },
    gradient: "from-blue-500 to-blue-900",
    popular: false,
  },
  {
    id: "crimson",
    name: "Crimson",
    description: "Bold red for maximum impact",
    colors: {
      primary: "#ef4444",
      secondary: "#7f1d1d",
      accent: "#f87171",
    },
    gradient: "from-red-500 to-red-900",
    popular: false,
  },
  {
    id: "sunset",
    name: "Sunset",
    description: "Warm orange and pink gradients",
    colors: {
      primary: "#f97316",
      secondary: "#9a3412",
      accent: "#fb923c",
    },
    gradient: "from-orange-500 to-pink-600",
    popular: true,
  },
  {
    id: "midnight",
    name: "Midnight",
    description: "Deep dark theme with subtle accents",
    colors: {
      primary: "#6366f1",
      secondary: "#312e81",
      accent: "#818cf8",
    },
    gradient: "from-indigo-500 to-slate-900",
    popular: false,
  },
];

const previewElements = [
  { label: "Threats Blocked", value: "136,997+", color: "text-red-500" },
  { label: "Servers Protected", value: "13,000+", color: "text-green-500" },
  { label: "Response Time", value: "<0.5s", color: "primary" },
];

export default function ThemesPage() {
  const [selectedTheme, setSelectedTheme] = useState("default");
  const currentTheme = themes.find((t) => t.id === selectedTheme) || themes[0];

  return (
    <main className="min-h-screen">
      <Navigation />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <span className="inline-flex items-center gap-2 bg-purple-900/30 px-4 py-2 rounded-full border border-purple-500/30 text-purple-400 text-sm mb-6">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            Customization
          </span>
          <h1 className="font-orbitron font-bold text-4xl md:text-6xl text-white mb-6">
            Customize Your <span className="text-purple-500">Experience</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Choose from our collection of carefully crafted themes to match your server's personality.
          </p>
        </div>
      </section>

      {/* Theme Selection */}
      <section className="py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {themes.map((theme) => (
              <button
                key={theme.id}
                onClick={() => setSelectedTheme(theme.id)}
                className={`gradient-border rounded-2xl p-6 bg-[#0a0a0b] text-left transition-all ${
                  selectedTheme === theme.id
                    ? "ring-2 ring-purple-500 scale-[1.02]"
                    : "hover:bg-[#0f0f10]"
                }`}
              >
                {/* Theme Preview Bar */}
                <div className={`h-24 rounded-xl bg-gradient-to-r ${theme.gradient} mb-4 relative overflow-hidden`}>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex gap-2">
                      <div
                        className="w-8 h-8 rounded-full border-2 border-white/30"
                        style={{ backgroundColor: theme.colors.primary }}
                      />
                      <div
                        className="w-8 h-8 rounded-full border-2 border-white/30"
                        style={{ backgroundColor: theme.colors.secondary }}
                      />
                      <div
                        className="w-8 h-8 rounded-full border-2 border-white/30"
                        style={{ backgroundColor: theme.colors.accent }}
                      />
                    </div>
                  </div>
                  {theme.popular && (
                    <span className="absolute top-2 right-2 bg-yellow-500 text-black text-xs font-bold px-2 py-1 rounded-full">
                      Popular
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-orbitron font-bold text-lg text-white">{theme.name}</h3>
                  {selectedTheme === theme.id && (
                    <span className="flex items-center gap-1 text-green-400 text-sm">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Selected
                    </span>
                  )}
                </div>
                <p className="text-gray-400 text-sm">{theme.description}</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Live Preview */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="font-orbitron font-bold text-2xl text-white mb-2">Live Preview</h2>
            <p className="text-gray-400">See how your selected theme looks in action</p>
          </div>

          <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b]">
            {/* Preview Header */}
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-gray-800">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: currentTheme.colors.primary }}
                >
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <span className="font-orbitron font-bold text-white text-xl">Offcialx</span>
              </div>
              <div
                className="px-4 py-2 rounded-lg text-white text-sm font-medium"
                style={{ backgroundColor: currentTheme.colors.primary }}
              >
                {currentTheme.name} Theme
              </div>
            </div>

            {/* Preview Stats */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              {previewElements.map((el, idx) => (
                <div
                  key={idx}
                  className="rounded-xl p-4 text-center"
                  style={{ backgroundColor: `${currentTheme.colors.secondary}40` }}
                >
                  <p className="text-xs text-gray-400 mb-1">{el.label}</p>
                  <p
                    className="font-orbitron font-bold text-xl"
                    style={{ color: idx === 2 ? currentTheme.colors.primary : undefined }}
                  >
                    <span className={idx !== 2 ? el.color : ""}>{el.value}</span>
                  </p>
                </div>
              ))}
            </div>

            {/* Preview Button */}
            <div className="flex justify-center">
              <button
                className="px-8 py-3 rounded-xl text-white font-orbitron font-bold transition-all hover:opacity-90"
                style={{ backgroundColor: currentTheme.colors.primary }}
              >
                Deploy Protection
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Apply Theme CTA */}
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b]">
            <h3 className="font-orbitron font-bold text-2xl text-white mb-4">Ready to Apply Your Theme?</h3>
            <p className="text-gray-400 mb-6">
              Login to the dashboard to save your theme preferences and customize your bot experience.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <a
                href="/auth"
                className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-6 py-3 rounded-xl transition font-semibold"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                Login to Dashboard
              </a>
              <a
                href="https://discord.gg/NXK5sFEJSy"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-[#1a1a1b] hover:bg-[#252527] text-white px-6 py-3 rounded-xl transition border border-purple-500/30"
              >
                Need Help?
              </a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
