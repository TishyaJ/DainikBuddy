import React, { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Send, ArrowLeft, Mic, Sparkles, RotateCcw, WifiOff } from "lucide-react";
import { api, streamChat } from "../lib/api";
import { useOffline } from "../context/OfflineContext";

const BUDDIES = {
  finance: {
    name: "Finance Buddy", emoji: "🦉", color: "finance",
    tag: "Savings. Budgeting. Smart choices.",
    prompts: ["How can I save more?", "Is this a good purchase?", "Help me stick to my budget", "Analyze my spending"],
  },
  wellness: {
    name: "Wellness Buddy", emoji: "☁️", color: "wellness",
    tag: "Here for your mind and body.",
    prompts: ["I'm feeling stressed", "Sleep tips for better rest", "Exam anxiety help", "Quick breathing exercise"],
  },
  discover: {
    name: "Discover Buddy", emoji: "🧭", color: "discover",
    tag: "Food, travel & student hacks.",
    prompts: ["Cheap food near me", "Best way to travel to college", "Student discounts", "Budget travel tips"],
  },
  helper: {
    name: "Helper Buddy", emoji: "✨", color: "helper",
    tag: "Cross-domain reasoning. One reply, full picture.",
    prompts: ["Plan tomorrow for me", "Where am I leaking money?", "Am I balanced this week?", "Help me focus better"],
  },
};

export default function BuddyChat() {
  const { buddy } = useParams();
  const meta = BUDDIES[buddy] || BUDDIES.helper;
  const nav = useNavigate();
  const { isOnline } = useOffline();
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    api.get(`/chat/${buddy}/history`).then((r) => setMsgs(r.data));
  }, [buddy]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const send = async (text) => {
    const t = (text ?? input).trim();
    if (!t || streaming) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: t, id: `u-${Date.now()}` }, { role: "assistant", content: "", id: `a-${Date.now()}`, streaming: true }]);
    setStreaming(true);
    try {
      await streamChat(buddy, t,
        (delta) => setMsgs((m) => {
          const next = [...m]; next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + delta }; return next;
        }),
        () => setStreaming(false),
      );
    } catch (e) {
      setMsgs((m) => { const next = [...m]; next[next.length - 1] = { ...next[next.length - 1], content: "Sorry, I had trouble connecting. Try again." }; return next; });
      setStreaming(false);
    }
  };

  const clear = async () => { await api.delete(`/chat/${buddy}/history`); setMsgs([]); };

  if (!isOnline) {
    return (
      <div data-domain={meta.color} className="flex-1 flex flex-col overflow-hidden bg-[#FAFAFA]">
        <div className="px-5 pt-6 pb-4 bdy-gradient text-white">
          <div className="flex items-center justify-between">
            <button onClick={() => nav("/chat")} data-testid="chat-back-btn" className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="text-center">
              <div className="text-2xl">{meta.emoji}</div>
              <div className="font-display font-bold text-base leading-tight">{meta.name}</div>
            </div>
            <div className="w-9" />
          </div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-5" data-testid="buddy-chat-offline-message">
          <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mb-4">
            <WifiOff className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="font-display font-bold text-lg text-slate-800">Chat requires internet</h2>
          <p className="text-sm text-slate-500 text-center mt-2 max-w-xs">
            AI chat features need an active internet connection. Your data is saved locally and will sync when you're back online.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div data-domain={meta.color} className="flex-1 flex flex-col overflow-hidden bg-[#FAFAFA]">
      <div className="px-5 pt-6 pb-4 bdy-gradient text-white">
        <div className="flex items-center justify-between">
          <button onClick={() => nav("/chat")} data-testid="chat-back-btn" className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="text-center">
            <div className="text-2xl">{meta.emoji}</div>
            <div className="font-display font-bold text-base leading-tight">{meta.name}</div>
            <div className="text-[10px] text-white/80">{meta.tag}</div>
          </div>
          <button onClick={clear} data-testid="chat-clear-btn" className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto scroll-area px-5 py-4 space-y-3" data-testid="chat-messages">
        {msgs.length === 0 && (
          <div className="text-center mt-4">
            <div className="text-5xl">{meta.emoji}</div>
            <p className="text-sm text-slate-600 mt-2">Hi Alex! How can I help today?</p>
          </div>
        )}
        {msgs.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] px-3.5 py-2.5 text-sm leading-relaxed ${m.role === "user"
              ? "bdy-bg text-white rounded-2xl rounded-tr-sm"
              : "bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-sm"
              }`}>
              {m.content || (m.streaming && <span className="inline-flex gap-1"><span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" /><span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" style={{ animationDelay: "150ms" }} /><span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" style={{ animationDelay: "300ms" }} /></span>)}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {msgs.length === 0 && (
        <div className="px-5 pb-2">
          <div className="text-[11px] font-semibold text-slate-500 mb-2">You can try asking:</div>
          <div className="flex flex-col gap-1.5">
            {meta.prompts.map((p) => (
              <button key={p} onClick={() => send(p)} data-testid={`prompt-${p.slice(0, 10)}`}
                className="text-left text-xs bg-white border border-slate-200 rounded-full px-3 py-2 text-slate-700 hover:bdy-soft">
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="border-t border-slate-200 bg-white px-3 py-3 flex items-center gap-2">
        <button data-testid="mic-btn" className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
          <Mic className="w-4 h-4" />
        </button>
        <input
          data-testid="chat-input" value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Type a message..."
          className="flex-1 bg-slate-100 rounded-full px-4 py-2.5 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[color:var(--bdy)]/30"
        />
        <button onClick={() => send()} disabled={streaming} data-testid="chat-send-btn"
          className="w-10 h-10 rounded-full bdy-bg text-white flex items-center justify-center disabled:opacity-50 active:scale-95">
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
