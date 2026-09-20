"use client";

/**
 * AI Chat & RAG Interface Component
 * Provides multi-turn conversation stream, document-scoped queries,
 * interactive source citation inspection cards, and quick prompt starters.
 */

import React, { useEffect, useRef, useState } from "react";
import {
  Bot,
  ChevronDown,
  ChevronUp,
  FileText,
  Filter,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  User as UserIcon,
} from "lucide-react";
import { ChatMessage, SourceCitation, chatApi } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface ChatInterfaceProps {
  selectedDocId: number | null;
  onClearDocFilter: () => void;
  onRequireAuth: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  selectedDocId,
  onClearDocFilter,
  onRequireAuth,
}) => {
  const { isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expandedCitationIndex, setExpandedCitationIndex] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Handle sending a question to the RAG pipeline
  const handleSendMessage = async (customQuery?: string) => {
    const queryToSend = customQuery || inputQuery;
    if (!queryToSend.trim() || isLoading) return;

    if (!isAuthenticated) {
      onRequireAuth();
      return;
    }

    setInputQuery("");
    const userMsg: ChatMessage = {
      id: Date.now(),
      conversation_id: currentConversationId || 0,
      role: "user",
      content: queryToSend.trim(),
      sources_meta: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await chatApi.query({
        query: queryToSend.trim(),
        conversation_id: currentConversationId,
        document_id: selectedDocId,
      });

      setCurrentConversationId(response.conversation_id);

      const aiMsg: ChatMessage = {
        id: Date.now() + 1,
        conversation_id: response.conversation_id,
        role: "assistant",
        content: response.answer,
        sources_meta: response.sources && response.sources.length > 0 ? response.sources : null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        conversation_id: currentConversationId || 0,
        role: "assistant",
        content: `Error: ${err?.message || "Failed to generate answer. Please verify your Gemini API key and try again."}`,
        sources_meta: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Start new chat session
  const handleNewChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleCitation = (key: string) => {
    setExpandedCitationIndex((prev) => (prev === key ? null : key));
  };

  const quickPrompts = [
    "Summarize the main points in my uploaded documents.",
    "What are the key technical concepts described in the files?",
    "Extract any important dates, obligations, or actions required.",
  ];

  return (
    <div className="glass-card" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Chat Top Bar */}
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "rgba(13, 18, 29, 0.4)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "var(--radius-sm)",
              background: "rgba(99, 102, 241, 0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Sparkles size={18} color="var(--primary)" />
          </div>
          <div>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>RAG Intelligence Chat</h3>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Grounded on Vector Embeddings with Source Citations
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {selectedDocId && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                background: "rgba(99, 102, 241, 0.15)",
                border: "1px solid rgba(99, 102, 241, 0.3)",
                borderRadius: "var(--radius-full)",
                fontSize: "0.75rem",
                color: "#c7d2fe",
              }}
            >
              <Filter size={12} />
              <span>Doc #{selectedDocId} Filter</span>
              <button
                onClick={onClearDocFilter}
                style={{ background: "none", border: "none", color: "#a5b4fc", cursor: "pointer", marginLeft: "4px" }}
              >
                ×
              </button>
            </div>
          )}

          <button onClick={handleNewChat} className="btn btn-secondary" style={{ padding: "6px 12px", fontSize: "0.8rem" }}>
            <Plus size={14} />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div
            style={{
              margin: "auto 0",
              textAlign: "center",
              padding: "40px 20px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                background: "rgba(99, 102, 241, 0.12)",
                border: "1px solid rgba(99, 102, 241, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "16px",
                boxShadow: "0 0 24px var(--primary-glow)",
              }}
            >
              <Bot size={30} color="var(--primary)" />
            </div>
            <h3 style={{ fontSize: "1.3rem", marginBottom: "8px" }}>
              Ask anything about your documents
            </h3>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", maxWidth: "480px", marginBottom: "28px" }}>
              Every answer is synthesized using semantic vector similarity search and citing the exact pages of your uploaded files.
            </p>

            {/* Quick Starters */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%", maxWidth: "480px" }}>
              {quickPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(prompt)}
                  className="btn btn-secondary"
                  style={{
                    textAlign: "left",
                    justifyContent: "flex-start",
                    padding: "10px 14px",
                    fontSize: "0.85rem",
                    borderRadius: "var(--radius-md)",
                    background: "rgba(255, 255, 255, 0.02)",
                  }}
                >
                  <MessageSquare size={14} color="var(--primary)" style={{ flexShrink: 0 }} />
                  <span>{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, msgIdx) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={msg.id || msgIdx}
                className={`message-bubble ${isUser ? "message-user" : "message-ai"}`}
              >
                {/* Header with avatar */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    marginBottom: "6px",
                    fontSize: "0.75rem",
                    color: isUser ? "#c7d2fe" : "var(--text-muted)",
                    fontWeight: 600,
                  }}
                >
                  {isUser ? <UserIcon size={14} /> : <Bot size={14} color="var(--primary)" />}
                  <span>{isUser ? "You" : "DocuMind Intelligence"}</span>
                </div>

                {/* Message Body */}
                <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {msg.content}
                </div>

                {/* Source Citations Box */}
                {!isUser && msg.sources_meta && msg.sources_meta.length > 0 && (
                  <div className="citation-box">
                    <div className="citation-header">
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <FileText size={14} />
                        <span>Sources & Citations ({msg.sources_meta.length})</span>
                      </div>
                      <span className="badge badge-info" style={{ fontSize: "0.65rem" }}>
                        Verified Chunks
                      </span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
                      {msg.sources_meta.map((source: SourceCitation, cIdx: number) => {
                        const key = `${msg.id}-${cIdx}`;
                        const isExpanded = expandedCitationIndex === key;
                        const matchPct = Math.round(source.similarity_score * 100);

                        return (
                          <div
                            key={cIdx}
                            style={{
                              background: "rgba(255, 255, 255, 0.03)",
                              border: "1px solid var(--border-subtle)",
                              borderRadius: "var(--radius-sm)",
                              padding: "8px 10px",
                              cursor: "pointer",
                            }}
                            onClick={() => toggleCitation(key)}
                          >
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                                  [{cIdx + 1}] {source.filename}
                                </span>
                                <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                                  (Page {source.page_number}, Chunk #{source.chunk_index + 1})
                                </span>
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                <span style={{ fontSize: "0.725rem", color: "#34d399", fontWeight: 600 }}>
                                  {matchPct}% Match
                                </span>
                                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                              </div>
                            </div>

                            {/* Similarity Score Visual Meter */}
                            <div className="similarity-bar">
                              <div className="similarity-fill" style={{ width: `${matchPct}%` }} />
                            </div>

                            {/* Expandable Chunk Content Snippet */}
                            {isExpanded && (
                              <p
                                style={{
                                  marginTop: "8px",
                                  padding: "8px",
                                  background: "rgba(0, 0, 0, 0.3)",
                                  borderRadius: "var(--radius-sm)",
                                  fontSize: "0.775rem",
                                  color: "var(--text-secondary)",
                                  fontStyle: "italic",
                                  lineHeight: 1.5,
                                }}
                              >
                                &ldquo;{source.snippet}&rdquo;
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Loading / Typing Indicator */}
        {isLoading && (
          <div className="message-bubble message-ai" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Sparkles size={16} className="animate-spin" color="var(--primary)" />
            <span style={{ fontSize: "0.85rem", color: "#a5b4fc" }}>
              Retrieving relevant vector chunks & generating answer...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div
        style={{
          padding: "16px 20px",
          borderTop: "1px solid var(--border-subtle)",
          background: "rgba(13, 18, 29, 0.8)",
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          style={{ display: "flex", gap: "10px", alignItems: "flex-end" }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              !isAuthenticated
                ? "Sign in to ask questions about your documents..."
                : selectedDocId
                ? `Ask a question about document #${selectedDocId}...`
                : "Ask a question about your uploaded documents..."
            }
            className="input-field"
            style={{
              resize: "none",
              minHeight: "44px",
              maxHeight: "120px",
              paddingTop: "10px",
            }}
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="btn btn-primary btn-icon"
            style={{ width: "44px", height: "44px", flexShrink: 0 }}
            title="Send Question"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
