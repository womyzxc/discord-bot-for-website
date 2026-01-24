"use client";

import Link from "next/link";
import { useState } from "react";
import { useSession } from "next-auth/react";

export default function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { data: session, status } = useSession();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#040405]/80 backdrop-blur-md border-b border-purple-900/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg overflow-hidden">
              <img
                src="/logo.jpg"
                alt="Offcialx Logo"
                className="w-full h-full object-cover"
              />
            </div>
            <span className="font-orbitron font-bold text-white text-xl">Offcialx</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-purple-400 hover:text-purple-300 transition font-medium text-sm">
              Home
            </Link>
            <Link href="/documentation" className="text-gray-400 hover:text-white transition font-medium text-sm">
              Documentation
            </Link>
            <Link href="/themes" className="text-gray-400 hover:text-white transition font-medium text-sm">
              Themes
            </Link>
            <Link href="/status" className="text-gray-400 hover:text-white transition font-medium text-sm">
              Status
            </Link>
            <a href="https://discord.gg/NXK5sFEJSy" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition font-medium text-sm">
              Support
            </a>
          </div>

          {/* Right side */}
          <div className="hidden md:flex items-center gap-4">
            {/* Theme Toggle */}
            <div className="flex items-center gap-2 bg-[#1a1a1b] rounded-full px-3 py-1.5 border border-purple-900/30">
              <span className="text-xs text-gray-400">Offcialx</span>
              <span className="text-xs text-purple-400">Default</span>
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                <div className="w-2 h-2 rounded-full bg-cyan-500"></div>
              </div>
            </div>

            {/* Customize Button */}
            <button className="flex items-center gap-2 text-gray-400 hover:text-white transition text-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Customize
            </button>

            {/* Auth Button */}
            {status === "loading" ? (
              <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
            ) : session?.user ? (
              <Link
                href="/dashboard"
                className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg transition font-medium text-sm flex items-center gap-2"
              >
                {session.user.image ? (
                  <img src={session.user.image} alt="" className="w-5 h-5 rounded-full" />
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                )}
                Dashboard
              </Link>
            ) : (
              <Link
                href="/auth"
                className="bg-[#5865F2] hover:bg-[#4752C4] text-white px-4 py-2 rounded-lg transition font-medium text-sm flex items-center gap-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z" />
                </svg>
                Login with Discord
              </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-white"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-[#0a0a0b] border-t border-purple-900/20">
          <div className="px-4 py-4 space-y-3">
            <Link href="/" className="block text-purple-400 font-medium">Home</Link>
            <Link href="/documentation" className="block text-gray-400">Documentation</Link>
            <Link href="/themes" className="block text-gray-400">Themes</Link>
            <Link href="/status" className="block text-gray-400">Status</Link>
            <a href="https://discord.gg/NXK5sFEJSy" target="_blank" rel="noopener noreferrer" className="block text-gray-400">Support</a>
            {session?.user ? (
              <Link
                href="/dashboard"
                className="block bg-purple-600 text-white px-4 py-2 rounded-lg text-center"
              >
                Dashboard
              </Link>
            ) : (
              <Link
                href="/auth"
                className="block bg-[#5865F2] text-white px-4 py-2 rounded-lg text-center"
              >
                Login with Discord
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
