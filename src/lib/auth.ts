import NextAuth from "next-auth";
import Discord from "next-auth/providers/discord";
import Google from "next-auth/providers/google";
import { createUser, getUserByProviderId, updateUserLogin } from "./db";

export const { handlers, signIn, signOut, auth } = NextAuth({
  secret: process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET,
  providers: [
    Discord({
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
    }),
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (!account) return false;

      try {
        // Check if user exists
        const dbUser = getUserByProviderId(account.provider, account.providerAccountId) as { id: number } | undefined;

        if (!dbUser) {
          // Create new user
          createUser({
            email: user.email || undefined,
            name: user.name || undefined,
            image: user.image || undefined,
            provider: account.provider,
            providerId: account.providerAccountId,
          });
        } else {
          // Update last login
          updateUserLogin(dbUser.id);
        }

        return true;
      } catch (error) {
        console.error("Error during sign in:", error);
        return true; // Still allow sign in even if DB fails
      }
    },
    async session({ session, token }) {
      if (session.user && token.sub) {
        (session.user as { id?: string }).id = token.sub;
      }
      return session;
    },
  },
  pages: {
    signIn: "/auth",
    error: "/auth/error",
  },
  trustHost: true,
});
