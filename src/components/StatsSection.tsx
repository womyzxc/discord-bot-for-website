"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface AnimatedCounterProps {
  end: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}

function AnimatedCounter({ end, duration = 2000, prefix = "", suffix = "", className = "" }: AnimatedCounterProps) {
  const [count, setCount] = useState(0);
  const [hasStarted, setHasStarted] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const prevEndRef = useRef(end);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasStarted) {
          setHasStarted(true);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [hasStarted]);

  useEffect(() => {
    if (!hasStarted || end === 0) return;

    const startValue = prevEndRef.current !== end ? count : 0;
    prevEndRef.current = end;

    let startTime: number | null = null;
    let animationFrame: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);

      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(startValue + (end - startValue) * easeOutQuart));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrame);
  }, [end, duration, hasStarted]);

  return (
    <span ref={ref} className={className}>
      {prefix}{count.toLocaleString()}{suffix}
    </span>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  sublabel: string;
  color: string;
  borderColor: string;
  glowColor: string;
}

function StatCard({ icon, label, value, prefix = "", suffix = "", sublabel, color, borderColor, glowColor }: StatCardProps) {
  return (
    <div
      className={`relative rounded-2xl p-6 text-center bg-[#0a0a0b] border ${borderColor} transition-all duration-300 hover:scale-105 group overflow-hidden`}
    >
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-300 ${glowColor} blur-xl`} />

      <div className="relative z-10">
        <div className="flex justify-center mb-3">
          {icon}
        </div>
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2 font-medium">{label}</p>
        <p className={`font-orbitron font-black text-3xl md:text-4xl ${color} mb-1`}>
          <AnimatedCounter end={value} prefix={prefix} suffix={suffix} duration={2500} />
        </p>
        <p className="text-xs text-gray-500">{sublabel}</p>
      </div>
    </div>
  );
}

interface BotStats {
  totalServers: number;
  totalUsers: number;
  averageLatency: number;
  uptime: number;
  threatsBlocked: number;
}

export default function StatsSection() {
  const [stats, setStats] = useState<BotStats>({
    threatsBlocked: 0,
    totalServers: 0,
    averageLatency: 45,
    uptime: 99,
    totalUsers: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  const fetchBotStats = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/stats");
      const data = await response.json();

      if (data.success && data.stats) {
        setStats({
          totalServers: data.stats.totalServers || 0,
          totalUsers: data.stats.totalUsers || 0,
          averageLatency: data.stats.averageLatency || 45,
          uptime: data.stats.uptime || 99,
          threatsBlocked: data.stats.threatsBlocked || 0,
        });
      }
      setIsLoading(false);
    } catch (err) {
      console.log("Using default stats");
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBotStats();
    const interval = setInterval(fetchBotStats, 30000);
    return () => clearInterval(interval);
  }, [fetchBotStats]);

  return (
    <section className="py-12 px-4 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-900/5 to-transparent pointer-events-none" />

      <div className="max-w-5xl mx-auto relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          <StatCard
            icon={
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            }
            label="THREATS BLOCKED"
            value={stats.threatsBlocked}
            suffix="+"
            sublabel="This Month"
            color="text-red-500"
            borderColor="border-red-500/20 hover:border-red-500/40"
            glowColor="bg-red-500"
          />

          <StatCard
            icon={
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
            label="SERVERS PROTECTED"
            value={stats.totalServers}
            suffix="+"
            sublabel="Active Now"
            color="text-green-500"
            borderColor="border-green-500/20 hover:border-green-500/40"
            glowColor="bg-green-500"
          />

          <StatCard
            icon={
              <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            label="RESPONSE TIME"
            value={5}
            prefix="<0."
            suffix="s"
            sublabel="Average"
            color="text-purple-500"
            borderColor="border-purple-500/20 hover:border-purple-500/40"
            glowColor="bg-purple-500"
          />

          <StatCard
            icon={
              <svg className="w-8 h-8 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            label="SUCCESS RATE"
            value={stats.uptime}
            suffix="%"
            sublabel="Accuracy"
            color="text-cyan-500"
            borderColor="border-cyan-500/20 hover:border-cyan-500/40"
            glowColor="bg-cyan-500"
          />
        </div>
      </div>
    </section>
  );
}
