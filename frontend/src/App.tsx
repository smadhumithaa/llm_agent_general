import { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";
const uid = () => Math.random().toString(36).slice(2);

// ── Types ─────────────────────────────────────────────────────────────────────
type Step = { tool: string; input: string; observation: string };

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: Step[];
  timestamp: Date;
};

// ── Tool icons ────────────────────────────────────────────────────────────────
const TOOL_ICONS: Record<string, string> = {
  web_search: "🔍",
  get_weather: "🌤️",
  get_news: "📰",
  execute_python: "🐍",
  summarize_document: "📄",
};

// ── API ───────────────────────────────────────────────────────────────────────
async function askAgent(question: string, sessionId: string) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Subcomponents ─────────────────────────────────────────────────────────────

function ToolStep({ step, index }: { step: Step; index: number }) {
  const [open, setOpen] = useState(false);
  const icon = TOOL_ICONS[step.tool] || "🔧";
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden text-xs">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <span className="text-gray-400 font-mono">#{index + 1}</span>
        <span>{icon}</span>
        <span className="font-semibold text-gray-700">{step.tool}</span>
        <span className="text-gray-400 truncate flex-1">{String(step.input).slice(0, 60)}</span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-3 py-2 bg-white border-t border-gray-100 space-y-2">
          <div>
            <p className="text-gray-400 font-semibold uppercase tracking-wide text-[10px] mb-0.5">Input</p>
            <p className="text-gray-700 font-mono whitespace-pre-wrap break-all">{step.input}</p>
          </div>
          <div>
            <p className="text-gray-400 font-semibold uppercase tracking-wide text-[10px] mb-0.5">Observation</p>
            <p className="text-gray-600 whitespace-pre-wrap">{step.observation}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  const [showSteps, setShowSteps] = useState(false);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5`}>
      <div className={`max-w-[78%] ${isUser ? "order-2" : "order-1"}`}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow">
              A
            </div>
            <span className="text-xs text-gray-500 font-semibold">Aria</span>
            {msg.steps && msg.steps.length > 0 && (
              <button
                onClick={() => setShowSteps((v) => !v)}
                className="text-[10px] px-2 py-0.5 rounded-full bg-violet-50 border border-violet-200 text-violet-600 hover:bg-violet-100 transition-colors font-medium"
              >
                {showSteps ? "Hide" : "Show"} reasoning ({msg.steps.length} steps)
              </button>
            )}
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-indigo-600 text-white rounded-tr-sm shadow"
              : "bg-white border border-gray-200 text-gray-800 shadow-sm rounded-tl-sm"
          }`}
        >
          {msg.content}
        </div>

        {/* Tool reasoning chain */}
        {showSteps && msg.steps && msg.steps.length > 0 && (
          <div className="mt-2 space-y-1.5 border-l-2 border-violet-200 pl-3">
            <p className="text-[10px] text-violet-500 font-semibold uppercase tracking-wide">
              🧠 Agent Reasoning Chain
            </p>
            {msg.steps.map((step, i) => (
              <ToolStep key={i} step={step} index={i} />
            ))}
          </div>
        )}

        <p className="mt-1 text-xs text-gray-400 px-1">
          {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}

function SuggestedPrompts({ onSelect }: { onSelect: (q: string) => void }) {
  const examples = [
    "What's the weather in Mumbai?",
    "Search for the latest news on AI regulation",
    "Calculate the compound interest on $10,000 at 8% for 5 years",
    "Summarize the document I uploaded",
  ];
  return (
    <div className="flex flex-wrap gap-2 justify-center mt-4">
      {examples.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="text-xs px-3 py-1.5 rounded-full border border-gray-300 text-gray-600 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all"
        >
          {q}
        </button>
      ))}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [sessionId] = useState(uid);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (question?: string) => {
    const q = (question ?? input).trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { id: uid(), role: "user", content: q, timestamp: new Date() }]);
    setInput("");
    setLoading(true);

    try {
      const data = await askAgent(q, sessionId);
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: data.answer,
          steps: data.steps,
          timestamp: new Date(),
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "assistant", content: `❌ ${e.message}`, timestamp: new Date() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadStatus("");
    try {
      const data = await uploadFile(file);
      setUploadStatus(`✅ ${data.filename} uploaded`);
    } catch (e: any) {
      setUploadStatus(`❌ ${e.message}`);
    } finally {
      setUploading(false);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-indigo-50 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow">
            A
          </div>
          <div>
            <h1 className="font-bold text-gray-800">Aria</h1>
            <p className="text-xs text-gray-400">General Purpose AI Agent · Gemini 2.0 Flash</p>
          </div>
        </div>

        {/* Tool badges */}
        <div className="hidden md:flex items-center gap-1.5">
          {Object.entries(TOOL_ICONS).map(([name, icon]) => (
            <span key={name} className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-500 border">
              {icon} {name.replace("_", " ")}
            </span>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 md:px-20 py-6">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-3xl font-bold shadow-lg mb-4">
              A
            </div>
            <h2 className="text-xl font-bold text-gray-800">Hi, I'm Aria 👋</h2>
            <p className="text-gray-500 mt-2 max-w-md text-sm">
              I can search the web, check the weather, get news, run Python code, and summarize your documents. Ask me anything!
            </p>
            <SuggestedPrompts onSelect={(q) => handleSend(q)} />
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} msg={msg} />)
        )}

        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center gap-2 text-sm text-gray-500">
              <div className="flex gap-1">
                {[0, 150, 300].map((delay) => (
                  <div
                    key={delay}
                    className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
              <span className="text-xs">Thinking & using tools...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="bg-white border-t border-gray-200 px-4 md:px-20 py-4 shadow-lg">
        {/* Upload row */}
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 text-gray-500 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all disabled:opacity-50"
          >
            {uploading ? "⏳ Uploading..." : "📎 Upload doc"}
          </button>
          {uploadStatus && <span className="text-xs text-gray-500">{uploadStatus}</span>}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
          />
        </div>

        {/* Message input */}
        <div className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ask anything — I'll pick the right tools automatically..."
            rows={1}
            className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all"
            style={{ minHeight: "46px", maxHeight: "140px" }}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-200 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 text-sm font-semibold transition-colors"
          >
            {loading ? "⏳" : "→"}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-1.5 text-center">
          Enter to send · Shift+Enter for new line · Click "Show reasoning" to see how I think
        </p>
      </div>
    </div>
  );
}
