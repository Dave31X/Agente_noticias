import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  ChevronLeft,
  Menu,
  MessageSquare,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Send,
  Sparkles,
  Trash2,
  Wifi,
  WifiOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn, shortTitle } from "@/lib/utils";

type Role = "user" | "assistant";
type ChatState = "idle" | "thinking" | "typing" | "error";

type Message = {
  id: string;
  role: Role;
  content: string;
  createdAt: number;
};

type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
};

type Status = {
  ok: boolean;
  llm: string;
  documents: number;
  latest: string | null;
  vectorstore: boolean;
};

const STORAGE_KEY = "newsagent.conversations.v1";
const API_BASE = import.meta.env.VITE_NEWSAGENT_API ?? "";

function id() {
  return crypto.randomUUID();
}

function emptyConversation(): Conversation {
  return {
    id: id(),
    title: "Nueva conversación",
    messages: [],
    updatedAt: Date.now(),
  };
}

function readStoredConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    return Array.isArray(parsed) && parsed.length ? parsed : [emptyConversation()];
  } catch {
    return [emptyConversation()];
  }
}

async function parseSseResponse(
  response: Response,
  onEvent: (event: string, data: Record<string, unknown>) => void,
) {
  if (!response.body) throw new Error("El navegador no entregó un stream de respuesta.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const block of events) {
      const event = block.match(/^event:\s*(.+)$/m)?.[1]?.trim() ?? "message";
      const dataRaw = block.match(/^data:\s*(.+)$/m)?.[1]?.trim() ?? "{}";
      onEvent(event, JSON.parse(dataRaw));
    }
  }
}

function TypingIndicator({ state }: { state: ChatState }) {
  const label = state === "thinking" ? "Consultando corpus y web" : "Redactando compendio";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto flex w-full max-w-3xl items-center gap-3 px-4 py-3 text-sm text-muted-foreground"
    >
      <div className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-muted">
        <Bot className="h-4 w-4" />
      </div>
      <span>{label}</span>
      <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
      <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
      <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
    </motion.div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className={cn("mx-auto flex w-full max-w-3xl gap-3 px-4 py-4", isUser && "justify-end")}
    >
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-muted">
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
      )}
      <div
        className={cn(
          "min-w-0 rounded-2xl text-[15px] leading-7 shadow-sm",
          isUser
            ? "max-w-[82%] bg-primary px-4 py-3 text-primary-foreground"
            : "w-full border border-border bg-card/70 px-5 py-4 text-foreground",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <ReactMarkdown
            className="message-prose"
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </motion.article>
  );
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(readStoredConversations);
  const [activeId, setActiveId] = useState(conversations[0]?.id);
  const [input, setInput] = useState("");
  const [chatState, setChatState] = useState<ChatState>("idle");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [allowWeb, setAllowWeb] = useState(true);
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const shouldStickRef = useRef(true);

  const active = useMemo(
    () => conversations.find((conversation) => conversation.id === activeId) ?? conversations[0],
    [activeId, conversations],
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    fetch(`${API_BASE}/api/status`)
      .then((response) => response.json())
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    if (shouldStickRef.current) {
      endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [active?.messages, chatState]);

  function updateActive(mutator: (conversation: Conversation) => Conversation) {
    setConversations((current) =>
      current.map((conversation) => (conversation.id === active.id ? mutator(conversation) : conversation)),
    );
  }

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    shouldStickRef.current = distance < 180;
  }

  function newChat() {
    const next = emptyConversation();
    setConversations((current) => [next, ...current]);
    setActiveId(next.id);
    setInput("");
    setError(null);
    setChatState("idle");
    setMobileSidebar(false);
  }

  function removeConversation(conversationId: string) {
    setConversations((current) => {
      const remaining = current.filter((conversation) => conversation.id !== conversationId);
      const next = remaining.length ? remaining : [emptyConversation()];
      if (conversationId === activeId) setActiveId(next[0].id);
      return next;
    });
  }

  async function submitMessage(event?: FormEvent) {
    event?.preventDefault();
    const message = input.trim();
    if (!message || chatState === "thinking" || chatState === "typing") return;

    const userMessage: Message = { id: id(), role: "user", content: message, createdAt: Date.now() };
    const assistantId = id();
    const assistantMessage: Message = { id: assistantId, role: "assistant", content: "", createdAt: Date.now() };

    shouldStickRef.current = true;
    setInput("");
    setError(null);
    setChatState("thinking");
    updateActive((conversation) => ({
      ...conversation,
      title: conversation.messages.length ? conversation.title : shortTitle(message),
      messages: [...conversation.messages, userMessage, assistantMessage],
      updatedAt: Date.now(),
    }));

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, allowWeb }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error ?? `Error HTTP ${response.status}`);
      }

      await parseSseResponse(response, (eventName, data) => {
        if (eventName === "status") {
          setChatState(data.state === "typing" ? "typing" : "thinking");
        }
        if (eventName === "token") {
          const token = String(data.token ?? "");
          updateActive((conversation) => ({
            ...conversation,
            messages: conversation.messages.map((item) =>
              item.id === assistantId ? { ...item, content: item.content + token } : item,
            ),
            updatedAt: Date.now(),
          }));
        }
        if (eventName === "error") {
          throw new Error(String(data.error ?? "Error generando respuesta"));
        }
        if (eventName === "done") {
          setChatState("idle");
        }
      });
      setChatState("idle");
    } catch (exc) {
      const messageError = exc instanceof Error ? exc.message : "Error desconocido";
      setError(messageError);
      setChatState("error");
      updateActive((conversation) => ({
        ...conversation,
        messages: conversation.messages.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                content:
                  "No pude completar la respuesta. Revisa que la API esté encendida y que las claves del modelo estén disponibles.",
              }
            : item,
        ),
      }));
    }
  }

  const sidebar = (
    <aside className="flex h-full flex-col border-r border-border bg-card/70">
      <div className="flex h-16 items-center gap-3 border-b border-border px-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">NewsAgent</p>
          <p className="truncate text-xs text-muted-foreground">Radar politico</p>
        </div>
        <Button className="ml-auto md:hidden" variant="ghost" size="icon" onClick={() => setMobileSidebar(false)}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>

      <div className="p-3">
        <Button className="w-full justify-start" variant="subtle" onClick={newChat}>
          <Plus className="h-4 w-4" />
          Nuevo chat
        </Button>
      </div>

      <div className="flex items-center gap-2 px-4 pb-2 text-xs text-muted-foreground">
        <Search className="h-3.5 w-3.5" />
        Historial local
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        <AnimatePresence initial={false}>
          {conversations.map((conversation) => (
            <motion.div
              key={conversation.id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="group mb-1 flex items-center gap-1"
            >
              <button
                className={cn(
                  "flex min-w-0 flex-1 items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition-colors",
                  conversation.id === active.id
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                )}
                onClick={() => {
                  setActiveId(conversation.id);
                  setMobileSidebar(false);
                }}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <span className="truncate">{conversation.title}</span>
              </button>
              <Button
                className="opacity-0 transition-opacity group-hover:opacity-100"
                variant="ghost"
                size="icon"
                onClick={() => removeConversation(conversation.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </motion.div>
          ))}
        </AnimatePresence>
      </nav>

      <div className="border-t border-border p-3">
        <label className="flex cursor-pointer items-center justify-between rounded-xl bg-muted/50 px-3 py-2 text-sm">
          <span className="text-muted-foreground">Complementar con web</span>
          <input
            checked={allowWeb}
            onChange={(event) => setAllowWeb(event.target.checked)}
            type="checkbox"
            className="h-4 w-4 accent-blue-500"
          />
        </label>
      </div>
    </aside>
  );

  return (
    <div className="h-full overflow-hidden bg-background">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_50%_-10%,rgba(59,130,246,.16),transparent_32%)]" />
      <div className="relative flex h-full">
        <AnimatePresence initial={false}>
          {sidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 304, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="hidden h-full shrink-0 overflow-hidden md:block"
            >
              {sidebar}
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {mobileSidebar && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/60 md:hidden"
              onClick={() => setMobileSidebar(false)}
            >
              <motion.div
                initial={{ x: -320 }}
                animate={{ x: 0 }}
                exit={{ x: -320 }}
                transition={{ duration: 0.22 }}
                className="h-full w-[304px]"
                onClick={(event) => event.stopPropagation()}
              >
                {sidebar}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <main className="flex min-w-0 flex-1 flex-col">
          <header className="glass-panel z-20 flex h-16 items-center gap-3 border-b border-border px-3 md:px-5">
            <Button className="md:hidden" variant="ghost" size="icon" onClick={() => setMobileSidebar(true)}>
              <Menu className="h-5 w-5" />
            </Button>
            <Button
              className="hidden md:inline-flex"
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen((value) => !value)}
            >
              {sidebarOpen ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeftOpen className="h-5 w-5" />}
            </Button>

            <div className="min-w-0 flex-1">
              <h1 className="truncate text-sm font-semibold md:text-base">{active.title}</h1>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {status?.ok ? <Wifi className="h-3.5 w-3.5 text-emerald-400" /> : <WifiOff className="h-3.5 w-3.5" />}
                <span className="truncate">
                  {status ? `${status.llm} · ${status.documents.toLocaleString("es-CO")} docs` : "Conectando API"}
                </span>
              </div>
            </div>

            <div className="hidden items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-1.5 text-xs text-muted-foreground sm:flex">
              {status?.vectorstore ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <AlertCircle className="h-3.5 w-3.5" />}
              <span>{status?.latest ?? "sin fecha"}</span>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-muted/40">
              <Moon className="h-4 w-4 text-muted-foreground" />
            </div>
          </header>

          <section ref={scrollRef} onScroll={handleScroll} className="min-h-0 flex-1 overflow-y-auto">
            {active.messages.length === 0 ? (
              <div className="mx-auto flex min-h-full max-w-3xl flex-col justify-center px-5 py-12">
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="text-center">
                  <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-glow">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <h2 className="text-3xl font-semibold tracking-tight md:text-5xl">Pregunta sin ruido.</h2>
                  <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
                    NewsAgent sintetiza el corpus local y la web reciente en respuestas neutrales, compactas y faciles de leer.
                  </p>
                  <div className="mt-8 grid gap-3 md:grid-cols-2">
                    {[
                      "¿Qué está pasando con las elecciones presidenciales en Colombia?",
                      "Hazme un compendio sencillo de candidatos y temas de campaña.",
                      "¿Qué dicen las encuestas y qué límites tienen?",
                      "Sepárame hechos, interpretaciones e implicaciones.",
                    ].map((prompt) => (
                      <button
                        key={prompt}
                        className="rounded-2xl border border-border bg-card/60 p-4 text-left text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground"
                        onClick={() => setInput(prompt)}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </motion.div>
              </div>
            ) : (
              <div className="pb-36 pt-4">
                <AnimatePresence initial={false}>
                  {active.messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                </AnimatePresence>
                {(chatState === "thinking" || chatState === "typing") && <TypingIndicator state={chatState} />}
                {error && (
                  <div className="mx-auto max-w-3xl px-4 py-3">
                    <div className="rounded-2xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-red-200">
                      {error}
                    </div>
                  </div>
                )}
                <div ref={endRef} />
              </div>
            )}
          </section>

          <div className="glass-panel z-20 border-t border-border px-3 py-3 md:px-6">
            <form onSubmit={submitMessage} className="mx-auto max-w-3xl">
              <div className="flex items-end gap-2 rounded-3xl border border-border bg-card/85 p-2 shadow-glow">
                <Textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      void submitMessage();
                    }
                  }}
                  placeholder="Pregunta sobre politica colombiana..."
                  rows={1}
                  className="max-h-44 border-0 bg-transparent shadow-none focus-visible:ring-0"
                  disabled={chatState === "thinking" || chatState === "typing"}
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={!input.trim() || chatState === "thinking" || chatState === "typing"}
                  className="mb-0.5 shrink-0 rounded-2xl"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="mt-2 text-center text-[11px] text-muted-foreground">
                Enter para enviar · Shift Enter para nueva linea · historial guardado en este navegador
              </p>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
