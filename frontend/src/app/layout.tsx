import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "DocuMind AI — Enterprise Document Intelligence & RAG Assistant",
  description:
    "Production-grade AI Document Intelligence Assistant powered by Google Gemini, PostgreSQL pgvector semantic search, and verified source citations.",
  keywords: [
    "RAG",
    "Document Intelligence",
    "FastAPI",
    "Gemini",
    "Vector Search",
    "pgvector",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
