import { useEffect, useRef, useState } from "react";
import { MessageCircle, Send, X } from "lucide-react";
import { api } from "../api";
import type { ChatMessage } from "../types";

interface Props {
  loanId: number | null;
}

function genSessionId(): string {
  return `s_${Math.random().toString(36).slice(2, 10)}_${Date.now()}`;
}

export default function ChatWidget({ loanId }: Props) {
  const [open, setOpen] = useState(false);
  const [sessionId] = useState<string>(() => genSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, open]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await api.ask({
        query: text,
        session_id: sessionId,
        loan_id: loanId,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong contacting the assistant.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <>
      {/* Floating action button */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close assistant" : "Open assistant"}
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 text-white shadow-lg transition hover:scale-105 hover:bg-slate-800"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-30 flex h-[32rem] w-[22rem] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3">
            <div>
              <div className="text-sm font-semibold text-slate-900">
                FlowFund Assistant
              </div>
              <div className="text-xs text-slate-500">
                {loanId ? `Context: Loan #${loanId}` : "General mode"}
              </div>
            </div>
          </div>

          <div
            ref={scrollRef}
            className="flex-1 space-y-3 overflow-y-auto p-4 text-sm"
          >
            {messages.length === 0 && (
              <div className="mt-8 text-center text-xs text-slate-400">
                Ask me anything about loans, finance, or this product.
                <div className="mt-3 space-y-1">
                  <Suggestion
                    text="How does daily auto-debit work?"
                    onClick={setInput}
                  />
                  <Suggestion
                    text="What is flat interest vs reducing balance?"
                    onClick={setInput}
                  />
                  <Suggestion
                    text="Why do I need a wallet buffer?"
                    onClick={setInput}
                  />
                  <Suggestion
                    text="Can I repay my loan early?"
                    onClick={setInput}
                  />
                  <Suggestion
                    text="What are my rights as a borrower?"
                    onClick={setInput}
                  />
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div
                key={i}
                className={m.role === "user" ? "flex justify-end" : ""}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 leading-relaxed ${
                    m.role === "user"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-900"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>
                </div>
              </div>
            ))}

            {sending && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-slate-100 px-3 py-2 text-slate-500">
                  <span className="inline-block animate-pulse">thinking...</span>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-slate-200 p-3">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="Ask a question..."
                disabled={sending}
                className="flex-1 rounded-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none placeholder:text-slate-400 focus:border-slate-500"
              />
              <button
                onClick={send}
                disabled={sending || !input.trim()}
                className="rounded-full bg-slate-900 p-2 text-white disabled:opacity-40"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Suggestion({
  text,
  onClick,
}: {
  text: string;
  onClick: (t: string) => void;
}) {
  return (
    <button
      onClick={() => onClick(text)}
      className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-left text-xs text-slate-700 hover:border-slate-400"
    >
      {text}
    </button>
  );
}
