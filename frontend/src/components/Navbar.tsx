"use client";

/**
 * Top Navigation Header Component
 * Displays application branding, live RAG engine status, and user authentication actions.
 */

import React from "react";
import { Bot, LogIn, LogOut, Sparkles, User as UserIcon } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface NavbarProps {
  onOpenAuthModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenAuthModal }) => {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(7, 9, 14, 0.8)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        position: "sticky",
        top: 0,
        zIndex: 40,
        padding: "14px 24px",
      }}
    >
      <div
        style={{
          maxWidth: "1440px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Brand Logo & Title */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, var(--primary) 0%, var(--accent-violet) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 16px var(--primary-glow)",
            }}
          >
            <Bot size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontFamily: "Outfit", fontWeight: 700, fontSize: "1.15rem", letterSpacing: "-0.01em" }}>
                DocuMind <span className="gradient-text">AI</span>
              </span>
              <span className="badge badge-info" style={{ fontSize: "0.65rem", padding: "2px 7px" }}>
                RAG v1.0
              </span>
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "-2px" }}>
              Enterprise Document Intelligence Assistant
            </p>
          </div>
        </div>

        {/* Right Section: System Indicator & User Auth Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {/* Live RAG Engine Indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              background: "rgba(16, 185, 129, 0.08)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
              borderRadius: "var(--radius-full)",
              fontSize: "0.75rem",
              color: "#34d399",
              fontWeight: 500,
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "#10b981",
                boxShadow: "0 0 8px #10b981",
              }}
            />
            <span>Gemini RAG Active</span>
          </div>

          {/* Authentication Actions */}
          {isAuthenticated && user ? (
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "6px 12px",
                  background: "var(--bg-glass)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                }}
              >
                <div
                  style={{
                    width: "26px",
                    height: "26px",
                    borderRadius: "50%",
                    background: "rgba(99, 102, 241, 0.2)",
                    border: "1px solid rgba(99, 102, 241, 0.4)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <UserIcon size={14} color="#a5b4fc" />
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "0.825rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    {user.full_name || "User"}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                    {user.email}
                  </span>
                </div>
              </div>

              <button
                onClick={logout}
                className="btn btn-secondary btn-icon"
                title="Log Out"
                style={{ padding: "8px 12px", gap: "6px", fontSize: "0.825rem" }}
              >
                <LogOut size={15} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuthModal}
              className="btn btn-primary"
              style={{ padding: "8px 16px", fontSize: "0.85rem" }}
            >
              <LogIn size={16} />
              <span>Sign In / Register</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
