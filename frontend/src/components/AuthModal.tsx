"use client";

/**
 * Authentication Modal Component
 * Provides glassmorphic tabbed interface for User Login and Registration with real-time validation.
 */

import React, { useState } from "react";
import { AlertCircle, Lock, Mail, Sparkles, User as UserIcon, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { login, register } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [fullName, setFullName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (isRegisterMode) {
        if (!email || !password) {
          throw new Error("Email and password are required.");
        }
        if (password.length < 8) {
          throw new Error("Password must be at least 8 characters long.");
        }
        await register(email, password, fullName || undefined);
      } else {
        if (!email || !password) {
          throw new Error("Please enter your email and password.");
        }
        await login(email, password);
      }
      onClose();
      // Reset form fields
      setEmail("");
      setPassword("");
      setFullName("");
    } catch (err: any) {
      setError(err?.message || "Authentication failed. Please check your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchTab = (toRegister: boolean) => {
    setIsRegisterMode(toRegister);
    setError(null);
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="glass-card"
        style={{
          width: "100%",
          maxWidth: "440px",
          padding: "28px",
          background: "rgba(13, 18, 30, 0.95)",
          border: "1px solid rgba(99, 102, 241, 0.25)",
          boxShadow: "0 24px 48px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(99, 102, 241, 0.2)",
          position: "relative",
          animation: "fadeIn 0.2s ease-out",
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="btn btn-ghost btn-icon"
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            color: "var(--text-muted)",
          }}
        >
          <X size={20} />
        </button>

        {/* Header Icon & Title */}
        <div style={{ textAlign: "center", marginBottom: "22px" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              margin: "0 auto 12px",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, var(--primary) 0%, var(--accent-violet) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 20px var(--primary-glow)",
            }}
          >
            <Sparkles size={24} color="#ffffff" />
          </div>
          <h2 style={{ fontSize: "1.4rem", marginBottom: "4px" }}>
            {isRegisterMode ? "Create Account" : "Welcome Back"}
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {isRegisterMode
              ? "Register to upload documents and query with AI"
              : "Sign in to access your documents and chat history"}
          </p>
        </div>

        {/* Tab Toggle */}
        <div
          style={{
            display: "flex",
            background: "rgba(255, 255, 255, 0.04)",
            padding: "4px",
            borderRadius: "var(--radius-md)",
            marginBottom: "20px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <button
            type="button"
            onClick={() => switchTab(false)}
            style={{
              flex: 1,
              padding: "8px",
              borderRadius: "var(--radius-sm)",
              border: "none",
              background: !isRegisterMode ? "var(--primary)" : "transparent",
              color: !isRegisterMode ? "#ffffff" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all var(--transition-fast)",
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => switchTab(true)}
            style={{
              flex: 1,
              padding: "8px",
              borderRadius: "var(--radius-sm)",
              border: "none",
              background: isRegisterMode ? "var(--primary)" : "transparent",
              color: isRegisterMode ? "#ffffff" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all var(--transition-fast)",
            }}
          >
            Register
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 14px",
              marginBottom: "16px",
              background: "rgba(244, 63, 94, 0.12)",
              border: "1px solid rgba(244, 63, 94, 0.3)",
              borderRadius: "var(--radius-md)",
              color: "#fb7185",
              fontSize: "0.825rem",
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Form Fields */}
        <form onSubmit={handleSubmit}>
          {isRegisterMode && (
            <div className="input-group">
              <label className="input-label">Full Name</label>
              <div style={{ position: "relative" }}>
                <UserIcon
                  size={17}
                  style={{
                    position: "absolute",
                    left: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-muted)",
                  }}
                />
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. Jane Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={{ paddingLeft: "38px" }}
                />
              </div>
            </div>
          )}

          <div className="input-group">
            <label className="input-label">Email Address</label>
            <div style={{ position: "relative" }}>
              <Mail
                size={17}
                style={{
                  position: "absolute",
                  left: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--text-muted)",
                }}
              />
              <input
                type="email"
                required
                className="input-field"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ paddingLeft: "38px" }}
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Password</label>
            <div style={{ position: "relative" }}>
              <Lock
                size={17}
                style={{
                  position: "absolute",
                  left: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--text-muted)",
                }}
              />
              <input
                type="password"
                required
                className="input-field"
                placeholder={isRegisterMode ? "Min. 8 characters" : "Enter password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: "38px" }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "8px", padding: "12px" }}
          >
            {isSubmitting ? (
              <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{
                    width: "16px",
                    height: "16px",
                    border: "2px solid #ffffff",
                    borderTopColor: "transparent",
                    borderRadius: "50%",
                    display: "inline-block",
                  }}
                  className="animate-spin"
                />
                Processing...
              </span>
            ) : isRegisterMode ? (
              "Create Account"
            ) : (
              "Sign In"
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
