"use client";

/**
 * Main Application Dashboard
 * Combines Navbar, DocumentManager, ChatInterface, and AuthModal into a unified screen.
 */

import React, { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { DocumentManager } from "@/components/DocumentManager";
import { ChatInterface } from "@/components/ChatInterface";
import { AuthModal } from "@/components/AuthModal";

export default function DashboardPage() {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <Navbar onOpenAuthModal={() => setIsAuthModalOpen(true)} />

      {/* Main Two-Column Dashboard Content */}
      <main className="main-content">
        <div className="dashboard-grid">
          {/* Left Column: Knowledge Base & Uploads */}
          <DocumentManager
            selectedDocId={selectedDocId}
            onSelectDoc={(id) => setSelectedDocId(id)}
            onRequireAuth={() => setIsAuthModalOpen(true)}
          />

          {/* Right Column: AI RAG Chat & Citations */}
          <ChatInterface
            selectedDocId={selectedDocId}
            onClearDocFilter={() => setSelectedDocId(null)}
            onRequireAuth={() => setIsAuthModalOpen(true)}
          />
        </div>
      </main>

      {/* Authentication Popup Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
}
