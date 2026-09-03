"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { chat, ModelWarmingUpError } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatPanelProps {
  healthOk: boolean;
}

export default function ChatPanel({ healthOk }: ChatPanelProps) {
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
      const response = await chat(userMessage);
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
      {/* Header */}
      <div className="px-8 py-6 border-b border-rim bg-surface">
        <h1 className="text-2xl font-serif font-bold text-ink">Chat</h1>
        <p className="text-sm text-ink-subtle mt-1">
          {healthOk ? "Backend ready" : "Backend unavailable"}
        </p>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-auto p-8 space-y-6 max-w-2xl mx-auto w-full"
      >
        {messages.length === 0 && (
          <div className="text-center text-ink-subtle py-12">
            <p className="text-lg">Upload a PDF to start chatting</p>
            <p className="text-sm mt-2">
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
              className={`max-w-sm ${
                msg.role === "user"
                  ? "bg-ink text-white rounded-3xl rounded-br-lg"
                  : "bg-surface border border-rim rounded-3xl rounded-bl-lg"
              } px-4 py-3`}
            >
              <p className="text-sm leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-1 animate-fade-up">
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
          <div className="p-4 bg-amber/10 text-amber rounded-lg text-sm">
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
              disabled={loading || !healthOk}
              className="flex-1 px-4 py-2 rounded-lg border border-rim bg-bg-subtle text-ink placeholder-ink-subtle focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || !healthOk}
              className="px-4 py-2 rounded-lg bg-amber text-white hover:bg-amber-dark disabled:opacity-50 transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
