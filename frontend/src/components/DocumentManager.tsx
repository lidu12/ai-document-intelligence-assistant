"use client";

/**
 * Document Manager Component
 * Provides drag-and-drop file uploading, status monitoring, chunk stats,
 * and scoped document filtering for targeted RAG queries.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Filter,
  Loader2,
  RefreshCw,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { DocumentItem, documentsApi } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface DocumentManagerProps {
  selectedDocId: number | null;
  onSelectDoc: (docId: number | null) => void;
  onRequireAuth: () => void;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  selectedDocId,
  onSelectDoc,
  onRequireAuth,
}) => {
  const { isAuthenticated } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load documents from backend
  const fetchDocuments = useCallback(async () => {
    if (!isAuthenticated) {
      setDocuments([]);
      return;
    }
    setIsLoading(true);
    try {
      const response = await documentsApi.list();
      setDocuments(response.documents);
    } catch (err: any) {
      console.error("Failed to load documents:", err);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Handle file upload
  const handleUploadFile = async (file: File) => {
    if (!isAuthenticated) {
      onRequireAuth();
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);

    // Frontend validation checks
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "txt") {
      setUploadError("Only .pdf and .txt files are supported.");
      return;
    }

    const maxBytes = 10 * 1024 * 1024; // 10 MB
    if (file.size > maxBytes) {
      setUploadError("File size exceeds 10 MB limit.");
      return;
    }

    setIsUploading(true);
    try {
      const uploadedDoc = await documentsApi.upload(file);
      setUploadSuccess(`"${uploadedDoc.filename}" uploaded and ingested (${uploadedDoc.total_chunks} chunks).`);
      await fetchDocuments();
      // Auto-clear success message after 4s
      setTimeout(() => setUploadSuccess(null), 4000);
    } catch (err: any) {
      setUploadError(err?.message || "Failed to upload document.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Handle document deletion
  const handleDelete = async (e: React.MouseEvent, docId: number) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this document and all its vector embeddings?")) {
      return;
    }

    try {
      await documentsApi.delete(docId);
      if (selectedDocId === docId) {
        onSelectDoc(null);
      }
      await fetchDocuments();
    } catch (err: any) {
      alert(err?.message || "Failed to delete document.");
    }
  };

  // Drag & drop event handlers
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUploadFile(e.dataTransfer.files[0]);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="glass-card" style={{ display: "flex", flexDirection: "column", height: "100%", padding: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <FileText size={20} color="var(--primary)" />
          <h3 style={{ fontSize: "1.1rem" }}>Knowledge Base</h3>
          <span className="badge badge-info">{documents.length} Docs</span>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={isLoading}
          className="btn btn-ghost btn-icon"
          title="Refresh Documents"
        >
          <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => {
          if (!isAuthenticated) onRequireAuth();
          else fileInputRef.current?.click();
        }}
        style={{
          border: `2px dashed ${isDragging ? "var(--primary)" : "var(--border-subtle)"}`,
          borderRadius: "var(--radius-md)",
          padding: "20px",
          textAlign: "center",
          background: isDragging ? "rgba(99, 102, 241, 0.08)" : "rgba(13, 18, 29, 0.4)",
          cursor: "pointer",
          transition: "all var(--transition-smooth)",
          marginBottom: "16px",
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleUploadFile(e.target.files[0]);
            }
          }}
        />
        {isUploading ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
            <Loader2 size={28} className="animate-spin" color="var(--primary)" />
            <span style={{ fontSize: "0.85rem", color: "#a5b4fc", fontWeight: 500 }}>
              Extracting text & generating embeddings...
            </span>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
            <UploadCloud size={28} color="var(--text-muted)" />
            <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
              {isDragging ? "Drop file to ingest" : "Click or drag PDF / TXT here"}
            </span>
            <span style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>
              PDF or TXT (Max 10 MB)
            </span>
          </div>
        )}
      </div>

      {/* Status Banners */}
      {uploadError && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 12px",
            marginBottom: "12px",
            background: "rgba(244, 63, 94, 0.12)",
            border: "1px solid rgba(244, 63, 94, 0.25)",
            borderRadius: "var(--radius-sm)",
            color: "#fb7185",
            fontSize: "0.8rem",
          }}
        >
          <AlertCircle size={15} style={{ flexShrink: 0 }} />
          <span>{uploadError}</span>
        </div>
      )}

      {uploadSuccess && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 12px",
            marginBottom: "12px",
            background: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.25)",
            borderRadius: "var(--radius-sm)",
            color: "#34d399",
            fontSize: "0.8rem",
          }}
        >
          <CheckCircle2 size={15} style={{ flexShrink: 0 }} />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* Scoped Filter Notification Banner */}
      {selectedDocId && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 12px",
            marginBottom: "12px",
            background: "rgba(99, 102, 241, 0.12)",
            border: "1px solid rgba(99, 102, 241, 0.3)",
            borderRadius: "var(--radius-md)",
            fontSize: "0.775rem",
            color: "#c7d2fe",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Filter size={14} color="var(--primary)" />
            <span>Targeting 1 Document for RAG</span>
          </div>
          <button
            onClick={() => onSelectDoc(null)}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              fontSize: "0.75rem",
              textDecoration: "underline",
            }}
          >
            Clear Filter
          </button>
        </div>
      )}

      {/* Document List */}
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
        {documents.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "36px 12px",
              color: "var(--text-muted)",
              fontSize: "0.85rem",
            }}
          >
            {!isAuthenticated ? (
              <p>Sign in to upload and view your documents.</p>
            ) : (
              <p>No documents uploaded yet. Drag and drop a PDF or text file above to start querying.</p>
            )}
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            return (
              <div
                key={doc.id}
                onClick={() => onSelectDoc(isSelected ? null : doc.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "10px 12px",
                  borderRadius: "var(--radius-md)",
                  background: isSelected ? "rgba(99, 102, 241, 0.16)" : "rgba(255, 255, 255, 0.03)",
                  border: `1px solid ${isSelected ? "rgba(99, 102, 241, 0.5)" : "var(--border-subtle)"}`,
                  cursor: "pointer",
                  transition: "all var(--transition-fast)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "var(--radius-sm)",
                      background: doc.file_type.includes("pdf")
                        ? "rgba(244, 63, 94, 0.15)"
                        : "rgba(6, 182, 212, 0.15)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <FileText
                      size={17}
                      color={doc.file_type.includes("pdf") ? "#fb7185" : "#38bdf8"}
                    />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <p
                      style={{
                        fontSize: "0.85rem",
                        fontWeight: 600,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        maxWidth: "190px",
                        color: isSelected ? "#ffffff" : "var(--text-primary)",
                      }}
                    >
                      {doc.filename}
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "2px" }}>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                        {formatBytes(doc.file_size_bytes)}
                      </span>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>•</span>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                        {doc.total_chunks} Chunks
                      </span>
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span
                    className={`badge ${
                      doc.status === "ready"
                        ? "badge-success"
                        : doc.status === "processing"
                        ? "badge-warning"
                        : "badge-danger"
                    }`}
                    style={{ fontSize: "0.65rem" }}
                  >
                    {doc.status}
                  </span>
                  <button
                    onClick={(e) => handleDelete(e, doc.id)}
                    className="btn btn-ghost btn-icon"
                    title="Delete Document"
                    style={{ padding: "6px", color: "var(--text-muted)" }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
