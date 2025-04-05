import NextAuth from "next-auth";
import GitHubProvider from "next-auth/providers/github";

// Configure NextAuth.js with GitHub OAuth credentials
const authOptions = {
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID as string, // Your GitHub OAuth Client ID from your GitHub App
      clientSecret: process.env.GITHUB_CLIENT_SECRET as string, // Your GitHub OAuth Client Secret
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET, // A secret for encrypting tokens and cookies
};

// NextAuth now expects you to export HTTP method handlers in the app router.
const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
