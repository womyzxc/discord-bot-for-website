"use client";

const ShieldIcon = () => (
  <svg className="w-full h-full text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const LockIcon = () => (
  <svg className="w-full h-full text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
  </svg>
);

const BrainIcon = () => (
  <svg className="w-full h-full text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-full h-full text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
  </svg>
);

const BellIcon = () => (
  <svg className="w-full h-full text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
);

const TrophyIcon = () => (
  <svg className="w-full h-full text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const iconComponents: { [key: number]: () => JSX.Element } = {
  0: ShieldIcon,
  1: LockIcon,
  2: BrainIcon,
  3: UserIcon,
  4: BellIcon,
  5: TrophyIcon,
};

const features = [
  {
    number: "#1",
    title: "Advanced Anti-Raid",
    description: "AI-powered detection system that identifies coordinated attacks in real-time. Automatically triggers lockdown protocols and prevents mass disruption with machine learning algorithms.",
    stats: [
      { value: "99.9%", label: "Accuracy" },
      { value: "<1s", label: "Response" },
      { value: "24/7", label: "Active" },
    ],
    accent: "purple",
    align: "left",
  },
  {
    number: "#2",
    title: "Anti-Nuke Protection",
    description: "Comprehensive server protection that monitors role permissions, channel modifications, and admin actions. Instantly reverts malicious changes and preserves your server structure.",
    stats: [
      { value: "100%", label: "Accuracy" },
      { value: "<0.1s", label: "Response" },
      { value: "24/7", label: "Active" },
    ],
    accent: "purple",
    align: "right",
  },
  {
    number: "#3",
    title: "Smart Auto-Moderation",
    description: "Intelligent content filtering powered by natural language processing. Detects spam, inappropriate content, and malicious links with contextual understanding.",
    stats: [
      { value: "98.5%", label: "Accuracy" },
      { value: "<2s", label: "Response" },
      { value: "24/7", label: "Active" },
    ],
    accent: "purple",
    align: "left",
  },
  {
    number: "#4",
    title: "Welcome System",
    description: "Create memorable first impressions with customizable welcome messages, role assignments, and interactive onboarding experiences that engage new members.",
    stats: [
      { value: "100%", label: "Accuracy" },
      { value: "Instant", label: "Response" },
      { value: "24/7", label: "Active" },
    ],
    accent: "purple",
    align: "right",
  },
  {
    number: "#5",
    title: "Real-time Alerts",
    description: "Instant notifications about suspicious activity, raids, and security threats delivered through Discord webhooks and dashboard alerts for immediate response.",
    stats: [
      { value: "99.8%", label: "Accuracy" },
      { value: "<0.1s", label: "Response" },
      { value: "24/7", label: "Active" },
    ],
    accent: "purple",
    align: "left",
  },
  {
    number: "#6",
    title: "XP & Leveling",
    description: "Gamify your security with XP for actions, server levels, and achievements for reaching security milestones. Motivate your community through interactive progression.",
    stats: [
      { value: "100%", label: "Accuracy" },
      { value: "Instant", label: "Response" },
      { value: "24/7", label: "Active" },
    ],
    accent: "purple",
    align: "right",
  },
];

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const isRight = feature.align === "right";
  const IconComponent = iconComponents[index];

  return (
    <div className={`flex flex-col ${isRight ? "md:flex-row-reverse" : "md:flex-row"} items-center gap-8 md:gap-16`}>
      {/* Content */}
      <div className="flex-1 max-w-md">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-purple-900/30 border border-purple-500/30 flex items-center justify-center p-2.5">
            <IconComponent />
          </div>
          <span className="text-purple-400 text-sm font-medium bg-purple-900/30 px-3 py-1 rounded-full border border-purple-500/30">
            Feature {feature.number}
          </span>
        </div>

        <h3 className="font-orbitron font-bold text-2xl md:text-3xl text-white mb-4">
          {feature.title}
        </h3>

        <p className="text-gray-400 mb-6 leading-relaxed">
          {feature.description}
        </p>

        {/* Stats */}
        <div className="flex items-center gap-6 mb-4">
          {feature.stats.map((stat, idx) => (
            <div key={idx} className="text-center">
              <p className="font-orbitron font-bold text-xl text-purple-400">{stat.value}</p>
              <p className="text-xs text-gray-500">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Live badge */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span className="text-green-400 text-sm">Live & Active</span>
        </div>
      </div>

      {/* Icon visual */}
      <div className="flex-1 flex justify-center">
        <div className="relative">
          <div className="w-32 h-32 md:w-40 md:h-40 rounded-full bg-purple-900/20 border border-purple-500/30 flex items-center justify-center p-8">
            <IconComponent />
          </div>
          {/* Decorative elements */}
          <div className="absolute -top-4 -right-4 w-8 h-8 rounded-full bg-purple-900/30 border border-purple-500/30"></div>
          <div className="absolute -bottom-2 -left-6 w-6 h-6 rounded-full bg-purple-900/30 border border-purple-500/30"></div>
        </div>
      </div>
    </div>
  );
}

export default function SecurityArsenal() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 bg-purple-900/30 px-4 py-2 rounded-full border border-purple-500/30 text-purple-400 text-sm mb-4">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Advanced Protection
          </span>
          <h2 className="font-orbitron font-bold text-3xl md:text-5xl text-white mb-4">
            Security <span className="text-purple-500">Arsenal</span>
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Cutting-edge protection powered by AI and machine learning to keep your Discord server safe from all threats
          </p>
        </div>

        {/* Features */}
        <div className="space-y-20">
          {features.map((feature, index) => (
            <FeatureCard key={index} feature={feature} index={index} />
          ))}
        </div>

        {/* Bottom badge */}
        <div className="text-center mt-16">
          <span className="inline-flex items-center gap-2 bg-[#1a1a1b] px-6 py-3 rounded-full border border-purple-500/30 text-gray-300">
            <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            All features work together seamlessly
          </span>
        </div>
      </div>
    </section>
  );
}
