"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";

function ErrorContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  const errorMessages: Record<string, string> = {
    Configuration: "There is a problem with the server configuration. Please contact support.",
    AccessDenied: "You do not have permission to sign in.",
    Verification: "The verification token has expired or has already been used.",
    OAuthSignin: "Error in constructing an authorization URL.",
    OAuthCallback: "Error in handling the response from the OAuth provider.",
    OAuthCreateAccount: "Could not create OAuth provider user in the database.",
    EmailCreateAccount: "Could not create email provider user in the database.",
    Callback: "Error in the OAuth callback handler route.",
    OAuthAccountNotLinked: "Email on the account is already linked, but not with this OAuth account.",
    EmailSignin: "Sending the e-mail with the verification token failed.",
    CredentialsSignin: "The authorize callback returned null in the Credentials provider.",
    SessionRequired: "The content of this page requires you to be signed in at all times.",
    Default: "An unknown error occurred.",
  };

  const errorMessage = error ? errorMessages[error] || errorMessages.Default : errorMessages.Default;

  return (
    <main className="min-h-screen bg-[#040405] flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b] text-center">
          {/* Error Icon */}
          <div className="w-16 h-16 rounded-2xl bg-red-900/30 border border-red-500/30 flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>

          <h1 className="font-orbitron font-bold text-2xl text-white mb-4">
            Authentication Error
          </h1>

          {/* Error Details */}
          <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-xl">
            <p className="text-red-400 text-sm mb-2">
              <strong>Error:</strong> {error || "Unknown"}
            </p>
            <p className="text-gray-400 text-sm">
              {errorMessage}
            </p>
          </div>

          {/* Common Solutions */}
          {error === "OAuthCallback" && (
            <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-500/30 rounded-xl text-left">
              <p className="text-yellow-400 text-sm font-semibold mb-2">Possible Solution:</p>
              <p className="text-gray-400 text-xs">
                Make sure the OAuth2 redirect URI is configured in your Discord Developer Portal:
              </p>
              <code className="block text-xs text-cyan-400 bg-[#1a1a1b] p-2 rounded mt-2 break-all">
                {typeof window !== 'undefined' ? `${window.location.origin}/api/auth/callback/discord` : '/api/auth/callback/discord'}
              </code>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Link
              href="/auth"
              className="flex-1 bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl transition font-semibold text-sm"
            >
              Try Again
            </Link>
            <Link
              href="/"
              className="flex-1 bg-[#1a1a1b] hover:bg-[#252527] text-gray-300 px-4 py-3 rounded-xl transition font-semibold text-sm border border-purple-500/30"
            >
              Go Home
            </Link>
          </div>

          {/* Support Link */}
          <p className="mt-6 text-gray-500 text-xs">
            Need help?{" "}
            <a
              href="https://discord.gg/NXK5sFEJSy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              Join our Discord
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}

export default function AuthErrorPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-[#040405] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
      </main>
    }>
      <ErrorContent />
    </Suspense>
  );
}
