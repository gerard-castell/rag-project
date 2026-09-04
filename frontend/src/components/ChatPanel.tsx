"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, Send } from "lucide-react";
import { chat, ModelWarmingUpError } from "@/lib/api";
import { Doc } from "./AppShell";
import PageHeader from "./PageHeader";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatPanelProps {
  healthOk: boolean;
  activeDoc: Doc | null;
}

export default function ChatPanel({ healthOk, activeDoc }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warmingUp, setWarmingUp] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);
    setError(null);
    setWarmingUp(false);

    try {
      const response = await chat(userMessage, activeDoc?.doc_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.response },
      ]);
    } catch (err) {
      if (err instanceof ModelWarmingUpError) {
        setWarmingUp(true);
      } else {
        setError(
          err instanceof Error
            ? err.message
            : "Chat failed. Ensure documents are uploaded and the backend is running."
        );
      }
      setMessages((prev) => prev.slice(0, -1)); // Remove user message on error
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader
        icon={MessageSquare}
        title="Chat"
        subtitle={
          activeDoc ? `Chatting with: ${activeDoc.source}` : "All documents"
        }
      />

      {/* Messages */}
      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        className="flex-1 overflow-auto p-8 space-y-6 max-w-2xl mx-auto w-full"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center text-center py-16">
            <div className="w-16 h-16 rounded-full bg-amber-soft flex items-center justify-center mb-4">
              <MessageSquare className="w-7 h-7 text-amber-dark" strokeWidth={1.5} />
            </div>
            <p className="text-ink font-medium">Upload a PDF to start chatting</p>
            <p className="text-sm text-ink-subtle mt-1">
              Ask questions about your documents and get grounded answers
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`animate-fade-up ${
              msg.role === "user" ? "flex justify-end" : ""
            }`}
          >
            <div
              className={`max-w-sm px-4 py-3 ${
                msg.role === "user"
                  ? "bg-ink text-white rounded-3xl rounded-br-lg shadow-[var(--shadow-card)]"
                  : "bg-surface border border-rim rounded-3xl rounded-bl-lg shadow-[var(--shadow-card)]"
              }`}
            >
              <p className="text-sm leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div
            className="flex gap-1 px-4 py-3 w-fit rounded-3xl rounded-bl-lg bg-surface border border-rim animate-fade-up"
            aria-label="Assistant is typing"
          >
            <div
              className="w-2 h-2 rounded-full bg-amber animate-bounce-dot"
              style={{ animationDelay: "0s" }}
            />
            <div
              className="w-2 h-2 rounded-full bg-amber animate-bounce-dot"
              style={{ animationDelay: "0.2s" }}
            />
            <div
              className="w-2 h-2 rounded-full bg-amber animate-bounce-dot"
              style={{ animationDelay: "0.4s" }}
            />
          </div>
        )}

        {warmingUp && (
          <div className="p-4 bg-amber-soft text-amber-dark rounded-lg text-sm">
            The model is warming up after being idle (cold start can take up
            to two minutes). Please retry in a moment.
          </div>
        )}

        {error && (
          <div className="p-4 bg-danger-soft text-danger rounded-lg text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-8 py-6 border-t border-rim bg-surface">
        <div className="max-w-2xl mx-auto">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question..."
              aria-label="Chat message"
              disabled={loading || !healthOk}
              className="flex-1 px-4 py-2.5 rounded-full border border-rim bg-bg-subtle text-ink placeholder-ink-subtle focus:outline-none focus:ring-2 focus:ring-amber focus:border-transparent disabled:opacity-50 transition-shadow"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || !healthOk}
              aria-label="Send message"
              className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-amber text-white shadow-[var(--shadow-card)] hover:bg-amber-dark hover:shadow-[var(--shadow-card-hover)] active:scale-95 disabled:opacity-50 disabled:shadow-none disabled:active:scale-100 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-dark"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
