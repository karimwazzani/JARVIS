"use client";

import React, { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  Activity,
  Bot,
  Brain,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Cpu,
  Database,
  LoaderCircle,
  MessageSquare,
  Mic,
  MicOff,
  Shield,
  Sparkles,
  Wallet,
  Waves,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis } from "recharts";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

import {
  addQuickTransaction,
  clearAllLogs,
  getDashboardSnapshot,
  sendWebPanelMessage,
  setSystemMode,
  type AgentConversationEntry,
  type AgentSummary,
  type DashboardSnapshot,
  type FinanceChartPoint,
} from "./actions";

declare global {
  interface Window {
    webkitSpeechRecognition?: new () => SpeechRecognition;
    SpeechRecognition?: new () => SpeechRecognition;
  }
}

type SpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  start: () => void;
  stop: () => void;
};

type ChatBubble = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

const AGENT_META: Record<
  string,
  {
    title: string;
    blurb: string;
    accent: "cyan" | "orange";
    icon: LucideIcon;
  }
> = {
  jarvis_orchestrator: {
    title: "Jarvis Orchestrator",
    blurb: "Decide qué agente entra y arma la respuesta final.",
    accent: "cyan",
    icon: Brain,
  },
  memory_keeper: {
    title: "Memory Keeper",
    blurb: "Ordena memoria, contexto y estado útil para cada turno.",
    accent: "cyan",
    icon: Database,
  },
  research: {
    title: "Research",
    blurb: "Investiga mercado, competencia y fuentes.",
    accent: "orange",
    icon: Sparkles,
  },
  coder: {
    title: "Coder",
    blurb: "Piensa producto, bugs, features y arquitectura.",
    accent: "cyan",
    icon: Cpu,
  },
  content_strategist: {
    title: "Content Strategist",
    blurb: "Propone ideas, hooks, series y estrategia de contenido.",
    accent: "orange",
    icon: Waves,
  },
  devops_deploy: {
    title: "DevOps Deploy",
    blurb: "Maneja deploys, entornos e infraestructura.",
    accent: "cyan",
    icon: Shield,
  },
  qa_tester: {
    title: "QA Tester",
    blurb: "Valida comportamientos, pruebas y riesgos.",
    accent: "orange",
    icon: CheckCircle2,
  },
  finance_ops: {
    title: "Finance Ops",
    blurb: "Sigue gastos, ingresos y salud financiera.",
    accent: "orange",
    icon: Wallet,
  },
};

const MODE_OPTIONS = ["Estándar", "Centinela", "Relax", "Ejecutor", "Fiesta"];

const EMPTY_SNAPSHOT: DashboardSnapshot = {
  totalBalance: 0,
  mtdExpense: 0,
  chartData: [],
  systemMode: "Estándar",
  totalAgentRuns: 0,
  uniqueChats: 0,
  pendingTasks: 0,
  pendingApprovals: 0,
  logs: [],
  proposals: [],
  calendar: [],
  tasks: [],
  conversations: [],
  agentRuns: [],
  agentSummaries: [],
};

export default function Dashboard() {
  const chartsReady = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
  const [time, setTime] = useState(new Date());
  const [snapshot, setSnapshot] = useState<DashboardSnapshot>(EMPTY_SNAPSHOT);
  const [selectedRoute, setSelectedRoute] = useState("jarvis_orchestrator");
  const [message, setMessage] = useState("");
  const [chatFeed, setChatFeed] = useState<ChatBubble[]>([]);
  const [sending, setSending] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const recognitionSupported = typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
    setVoiceSupported(recognitionSupported);
  }, []);

  useEffect(() => {
    const load = async () => {
      const data = await getDashboardSnapshot();
      setSnapshot(data);
      if (data.agentSummaries.length > 0 && !data.agentSummaries.some((item) => item.route === selectedRoute)) {
        setSelectedRoute(data.agentSummaries[0].route);
      }

      const webConversations = data.conversations
        .filter((row) => row.chatId === "web-panel")
        .slice(0, 12)
        .reverse()
        .map((row) => ({
          role: row.role as "user" | "assistant",
          content: row.content,
          timestamp: row.timestamp || "",
        }));
      setChatFeed(webConversations);
    };

    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [selectedRoute]);

  const selectedAgent = useMemo(() => {
    return snapshot.agentSummaries.find((item) => item.route === selectedRoute) || null;
  }, [snapshot.agentSummaries, selectedRoute]);

  const handleModeChange = async (mode: string) => {
    const result = await setSystemMode(mode);
    if (result.success) {
      setSnapshot((prev) => ({ ...prev, systemMode: mode }));
    }
  };

  const handleQuickTransaction = async (tipo: "gasto" | "ingreso") => {
    const amountText = prompt(tipo === "gasto" ? "Monto del gasto:" : "Monto del ingreso:");
    if (!amountText) return;
    const description = prompt("Descripción:");
    if (!description) return;
    const result = await addQuickTransaction(Number(amountText), description, tipo);
    if (result.success) {
      const data = await getDashboardSnapshot();
      setSnapshot(data);
    }
  };

  const handleClearLogs = async () => {
    if (!confirm("¿Limpiar los logs visibles del panel?")) return;
    const result = await clearAllLogs();
    if (result.success) {
      const data = await getDashboardSnapshot();
      setSnapshot(data);
    }
  };

  const submitMessage = async (content: string) => {
    if (!content.trim()) return;

    const userBubble: ChatBubble = {
      role: "user",
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };
    setChatFeed((prev) => [...prev, userBubble]);
    setSending(true);
    setMessage("");

    const result = await sendWebPanelMessage(content.trim(), "web-panel");

    setChatFeed((prev) => [
      ...prev,
      {
        role: "assistant",
        content: result.response,
        timestamp: new Date().toISOString(),
      },
    ]);
    setSending(false);

    const data = await getDashboardSnapshot();
    setSnapshot(data);
    if (data.agentSummaries.length > 0) {
      setSelectedRoute(data.agentSummaries[0].route);
    }
  };

  const toggleVoiceInput = () => {
    const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!RecognitionCtor) return;

    if (listening) {
      setListening(false);
      return;
    }

    const recognition = new RecognitionCtor();
    recognition.lang = "es-AR";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .flatMap((result) => Array.from(result))
        .map((part) => part.transcript)
        .join(" ")
        .trim();
      if (transcript) {
        setMessage(transcript);
        void submitMessage(transcript);
      }
    };

    recognition.start();
  };

  return (
    <div className="min-h-screen p-4 md:p-6 selection:bg-[var(--color-jarvis-cyan)] selection:text-black">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-4">
        <header className="glass-panel neon-border rounded-2xl px-5 py-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl border border-[var(--color-jarvis-cyan)]/20 bg-[var(--color-jarvis-cyan)]/10 p-3">
                <Bot className="text-[var(--color-jarvis-cyan)]" size={26} />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.32em] text-[var(--color-jarvis-muted)]">Jarvis Control Deck</p>
                <h1 className="text-2xl font-semibold text-white">Panel operativo por agente</h1>
                <p className="mt-1 max-w-2xl text-sm text-[var(--color-jarvis-muted)]">
                  Acá ves qué agente trabajó, qué guardó, qué tareas están pendientes y además podés hablarle a Jarvis por texto o voz.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-right">
                <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Hora local</p>
                <p className="font-mono text-lg text-white">{time.toLocaleTimeString("es-AR", { hour12: false })}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Modo</p>
                <select
                  value={snapshot.systemMode}
                  onChange={(event) => handleModeChange(event.target.value)}
                  className="bg-transparent text-sm text-white outline-none"
                >
                  {MODE_OPTIONS.map((mode) => (
                    <option key={mode} value={mode} className="bg-slate-950">
                      {mode}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </header>

        <section className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          <StatTile label="Agentes activos" value={String(snapshot.agentSummaries.length || 0)} icon={Cpu} accent="cyan" />
          <StatTile label="Runs registrados" value={String(snapshot.totalAgentRuns)} icon={Activity} accent="cyan" />
          <StatTile label="Chats únicos" value={String(snapshot.uniqueChats)} icon={MessageSquare} accent="orange" />
          <StatTile label="Tareas pendientes" value={String(snapshot.pendingTasks)} icon={Clock3} accent="orange" />
          <StatTile
            label="Balance"
            value={`$${snapshot.totalBalance.toLocaleString("es-AR", { maximumFractionDigits: 0 })}`}
            icon={Wallet}
            accent="cyan"
          />
        </section>

        <main className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)_380px]">
          <aside className="glass-panel rounded-2xl p-4">
            <SectionTitle icon={Cpu} title="Mapa de agentes" />
            <div className="mt-4 space-y-2">
              {snapshot.agentSummaries.map((agent) => {
                const meta = AGENT_META[agent.route];
                const accent = meta?.accent || "cyan";
                const Icon = meta?.icon || Cpu;
                return (
                  <button
                    key={agent.route}
                    onClick={() => setSelectedRoute(agent.route)}
                    className={cn(
                      "w-full rounded-xl border p-3 text-left transition-colors",
                      selectedRoute === agent.route
                        ? accent === "cyan"
                          ? "border-[var(--color-jarvis-cyan)]/50 bg-[var(--color-jarvis-cyan)]/10"
                          : "border-[var(--color-jarvis-orange)]/50 bg-[var(--color-jarvis-orange)]/10"
                        : "border-white/8 bg-black/10 hover:bg-white/5",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-3">
                        <div className="rounded-lg border border-white/10 bg-black/20 p-2">
                          <Icon
                            size={16}
                            className={accent === "cyan" ? "text-[var(--color-jarvis-cyan)]" : "text-[var(--color-jarvis-orange)]"}
                          />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-white">{meta?.title || agent.label}</p>
                          <p className="mt-1 text-xs text-[var(--color-jarvis-muted)]">{agent.totalRuns} runs</p>
                        </div>
                      </div>
                      <ChevronRight size={16} className="mt-1 text-[var(--color-jarvis-muted)]" />
                    </div>
                    <p className="mt-3 line-clamp-2 text-xs text-[var(--color-jarvis-muted)]">
                      {meta?.blurb || "Ruta disponible en el sistema."}
                    </p>
                  </button>
                );
              })}
            </div>

            <div className="mt-6 rounded-xl border border-white/8 bg-black/10 p-3">
              <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Qué haría después</p>
              <ul className="mt-3 space-y-2 text-sm text-gray-300">
                <li>1. Afinar el router con clasificación real, no sólo keywords.</li>
                <li>2. Darle herramientas concretas a cada agente.</li>
                <li>3. Mostrar trazas, memoria y aprobaciones en tiempo real.</li>
              </ul>
            </div>
          </aside>

          <section className="flex flex-col gap-4">
            <div className="glass-panel rounded-2xl p-4">
              <SectionTitle icon={selectedAgent ? (AGENT_META[selectedAgent.route]?.icon || Brain) : Brain} title="Detalle del agente" />
              {selectedAgent ? (
                <div className="mt-4 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
                  <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xl font-semibold text-white">
                          {AGENT_META[selectedAgent.route]?.title || selectedAgent.label}
                        </p>
                        <p className="mt-1 text-sm text-[var(--color-jarvis-muted)]">
                          {AGENT_META[selectedAgent.route]?.blurb || "Ruta activa dentro del sistema Jarvis."}
                        </p>
                      </div>
                      <StatusPill status={selectedAgent.latestStatus} />
                    </div>

                    <div className="mt-4 grid gap-3 md:grid-cols-3">
                      <MiniStat label="Última actividad" value={selectedAgent.latestAt ? formatTimeCompact(selectedAgent.latestAt) : "sin datos"} />
                      <MiniStat label="Runs del agente" value={String(selectedAgent.totalRuns)} />
                      <MiniStat label="Memorias visibles" value={String(selectedAgent.memoryItems.length)} />
                    </div>

                    <div className="mt-4 grid gap-3">
                      <InfoBlock title="Último pedido" content={selectedAgent.latestPrompt || "Todavía no recibió un pedido claro."} />
                      <InfoBlock title="Última respuesta" content={selectedAgent.latestResponse || "Todavía no produjo una salida visible."} />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                    <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Memoria operativa</p>
                    <div className="mt-3 space-y-3">
                      {selectedAgent.memoryItems.length > 0 ? (
                        selectedAgent.memoryItems.slice(0, 4).map((item, index) => (
                          <div key={`${item.timestamp}-${index}`} className="rounded-xl border border-white/8 bg-white/3 p-3">
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-cyan)]">
                                {item.category}
                              </span>
                              <span className="text-[10px] text-[var(--color-jarvis-muted)]">{formatTimeCompact(item.timestamp)}</span>
                            </div>
                            <p className="mt-2 text-sm text-gray-300">{item.content}</p>
                          </div>
                        ))
                      ) : (
                        <EmptyState text="Este agente todavía no dejó memoria visible." />
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <EmptyState text="Todavía no hay agentes con actividad suficiente para mostrar." />
              )}
            </div>

            <div className="grid gap-4 xl:grid-cols-[1fr_0.95fr]">
              <div className="glass-panel rounded-2xl p-4">
                <SectionTitle icon={MessageSquare} title="Chat web con Jarvis" />
                <div className="mt-4 flex h-[440px] flex-col rounded-2xl border border-white/8 bg-black/15">
                  <div className="flex-1 space-y-3 overflow-y-auto p-4 custom-scrollbar">
                    {chatFeed.length > 0 ? (
                      chatFeed.map((item, index) => (
                        <div key={`${item.timestamp}-${index}`} className={cn("flex", item.role === "user" ? "justify-end" : "justify-start")}>
                          <div
                            className={cn(
                              "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                              item.role === "user"
                                ? "bg-[var(--color-jarvis-cyan)]/15 text-white border border-[var(--color-jarvis-cyan)]/20"
                                : "bg-white/6 text-gray-200 border border-white/10",
                            )}
                          >
                            <p>{item.content}</p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <EmptyState text="Todavía no le hablaste desde el panel. Escribile acá abajo o usá el micrófono." />
                    )}
                    {sending ? (
                      <div className="flex justify-start">
                        <div className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-gray-300">
                          <span className="inline-flex items-center gap-2">
                            <LoaderCircle className="animate-spin" size={14} />
                            Jarvis está pensando...
                          </span>
                        </div>
                      </div>
                    ) : null}
                  </div>

                  <div className="border-t border-white/8 p-4">
                    <div className="flex gap-3">
                      <textarea
                        value={message}
                        onChange={(event) => setMessage(event.target.value)}
                        placeholder="Escribile a Jarvis desde la web..."
                        className="min-h-[92px] flex-1 resize-none rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--color-jarvis-muted)]"
                      />
                      <div className="flex w-[120px] flex-col gap-3">
                        <button
                          onClick={() => void submitMessage(message)}
                          disabled={sending || !message.trim()}
                          className="flex h-11 items-center justify-center rounded-xl bg-[var(--color-jarvis-cyan)]/15 text-sm font-medium text-[var(--color-jarvis-cyan)] transition hover:bg-[var(--color-jarvis-cyan)]/20 disabled:opacity-40"
                        >
                          Enviar
                        </button>
                        <button
                          onClick={toggleVoiceInput}
                          disabled={!voiceSupported}
                          className={cn(
                            "flex h-11 items-center justify-center rounded-xl border text-sm font-medium transition",
                            listening
                              ? "border-[var(--color-jarvis-orange)]/40 bg-[var(--color-jarvis-orange)]/15 text-[var(--color-jarvis-orange)]"
                              : "border-white/10 bg-black/20 text-white hover:bg-white/5",
                            !voiceSupported && "opacity-40",
                          )}
                        >
                          <span className="inline-flex items-center gap-2">
                            {listening ? <MicOff size={16} /> : <Mic size={16} />}
                            {listening ? "Escuchando" : "Micrófono"}
                          </span>
                        </button>
                      </div>
                    </div>
                    <p className="mt-3 text-xs text-[var(--color-jarvis-muted)]">
                      El micrófono usa el reconocimiento de voz del navegador. Si tu browser no lo soporta, seguís teniendo el chat escrito.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-4">
                <div className="glass-panel rounded-2xl p-4">
                  <SectionTitle icon={Activity} title="Rutas recientes" />
                  <div className="mt-4 space-y-3">
                    {snapshot.agentRuns.slice(0, 6).map((run, index) => (
                      <div key={`${run.timestamp}-${index}`} className="rounded-xl border border-white/8 bg-black/10 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-semibold text-white">{AGENT_META[run.route]?.title || run.label}</p>
                          <StatusPill status={run.status} compact />
                        </div>
                        <p className="mt-2 text-xs text-[var(--color-jarvis-muted)]">{run.userMessage}</p>
                        <p className="mt-2 line-clamp-3 text-sm text-gray-300">{run.responsePreview}</p>
                      </div>
                    ))}
                    {snapshot.agentRuns.length === 0 ? <EmptyState text="Todavía no hay runs de agentes para mostrar." /> : null}
                  </div>
                </div>

                <div className="glass-panel rounded-2xl p-4">
                  <SectionTitle icon={Wallet} title="Finanzas y tareas" />
                  <div className="mt-4 grid gap-4">
                    <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Balance total</p>
                          <p className="mt-1 text-2xl font-semibold text-white">
                            ${snapshot.totalBalance.toLocaleString("es-AR", { maximumFractionDigits: 0 })}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <ActionButton label="Ingreso" onClick={() => void handleQuickTransaction("ingreso")} accent="cyan" />
                          <ActionButton label="Gasto" onClick={() => void handleQuickTransaction("gasto")} accent="orange" />
                        </div>
                      </div>
                      <div className="mt-4 h-36">
                        {chartsReady ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={snapshot.chartData}>
                              <defs>
                                <linearGradient id="financeGradient" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="var(--color-jarvis-cyan)" stopOpacity={0.3} />
                                  <stop offset="95%" stopColor="var(--color-jarvis-cyan)" stopOpacity={0} />
                                </linearGradient>
                              </defs>
                              <XAxis dataKey="name" stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} />
                              <RechartsTooltip
                                contentStyle={{
                                  backgroundColor: "rgba(2, 6, 23, 0.95)",
                                  border: "1px solid rgba(255,255,255,0.08)",
                                  borderRadius: 12,
                                }}
                              />
                              <Area type="monotone" dataKey="income" stroke="var(--color-jarvis-cyan)" fill="url(#financeGradient)" strokeWidth={2} />
                              <Area type="monotone" dataKey="expense" stroke="var(--color-jarvis-orange)" fillOpacity={0} strokeWidth={2} />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : null}
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                        <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Tareas abiertas</p>
                        <div className="mt-3 space-y-2">
                          {snapshot.tasks.slice(0, 4).map((task) => (
                            <div key={task.id} className="rounded-xl border border-white/8 bg-white/3 p-3">
                              <p className="text-sm font-medium text-white">{task.titulo}</p>
                              <p className="mt-1 text-xs text-[var(--color-jarvis-muted)]">{task.descripcion || "Sin descripción."}</p>
                            </div>
                          ))}
                          {snapshot.tasks.length === 0 ? <EmptyState text="No hay tareas visibles." /> : null}
                        </div>
                      </div>

                      <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Logs del sistema</p>
                          <button onClick={() => void handleClearLogs()} className="text-xs text-[var(--color-jarvis-orange)] hover:underline">
                            limpiar
                          </button>
                        </div>
                        <div className="mt-3 space-y-2">
                          {snapshot.logs.slice(0, 5).map((log, index) => (
                            <div key={`${log.fecha}-${index}`} className="rounded-xl border border-white/8 bg-white/3 p-3">
                              <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-cyan)]">
                                {formatTimeCompact(log.fecha)}
                              </p>
                              <p className="mt-1 text-sm text-gray-300">{log.evento}</p>
                            </div>
                          ))}
                          {snapshot.logs.length === 0 ? <EmptyState text="No hay logs generales para mostrar." /> : null}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <aside className="glass-panel rounded-2xl p-4">
            <SectionTitle icon={Database} title="Resumen global" />
            <div className="mt-4 grid gap-4">
              <SummaryList
                title="Calendario"
                items={snapshot.calendar.map((item) => `${formatTimeCompact(item.fecha)} · ${item.titulo}`)}
                empty="No hay eventos próximos."
              />
              <SummaryList
                title="Aprobaciones"
                items={snapshot.proposals.map((item) => item.descripcion)}
                empty="No hay propuestas pendientes."
              />
              <SummaryList
                title="Conversación reciente"
                items={snapshot.conversations.slice(0, 6).map((item: AgentConversationEntry) => `${item.role}: ${item.content}`)}
                empty="No hay conversación reciente."
              />
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
}

function SectionTitle({ icon: Icon, title }: { icon: LucideIcon; title: string }) {
  return (
    <div className="flex items-center gap-2 border-b border-white/8 pb-3">
      <Icon size={16} className="text-[var(--color-jarvis-cyan)]" />
      <h2 className="text-sm font-mono uppercase tracking-[0.28em] text-white">{title}</h2>
    </div>
  );
}

function StatTile({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  accent: "cyan" | "orange";
}) {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">{label}</p>
          <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/20 p-3">
          <Icon size={18} className={accent === "cyan" ? "text-[var(--color-jarvis-cyan)]" : "text-[var(--color-jarvis-orange)]"} />
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/3 p-3">
      <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">{label}</p>
      <p className="mt-1 text-sm font-medium text-white">{value}</p>
    </div>
  );
}

function InfoBlock({ title, content }: { title: string; content: string }) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/3 p-3">
      <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">{title}</p>
      <p className="mt-2 text-sm text-gray-300">{content}</p>
    </div>
  );
}

function StatusPill({ status, compact = false }: { status: string; compact?: boolean }) {
  const normalized = status.toLowerCase();
  const tone =
    normalized === "completed" || normalized === "live" || normalized === "online"
      ? "text-[var(--color-jarvis-cyan)] bg-[var(--color-jarvis-cyan)]/10 border-[var(--color-jarvis-cyan)]/20"
      : normalized.includes("await") || normalized.includes("pending")
        ? "text-[var(--color-jarvis-orange)] bg-[var(--color-jarvis-orange)]/10 border-[var(--color-jarvis-orange)]/20"
        : "text-gray-300 bg-white/5 border-white/10";

  return (
    <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 uppercase tracking-[0.2em]", compact ? "text-[9px]" : "text-[10px]", tone)}>
      {status}
    </span>
  );
}

function ActionButton({
  label,
  onClick,
  accent,
}: {
  label: string;
  onClick: () => void;
  accent: "cyan" | "orange";
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-xl border px-3 py-2 text-xs font-medium transition",
        accent === "cyan"
          ? "border-[var(--color-jarvis-cyan)]/20 bg-[var(--color-jarvis-cyan)]/10 text-[var(--color-jarvis-cyan)] hover:bg-[var(--color-jarvis-cyan)]/15"
          : "border-[var(--color-jarvis-orange)]/20 bg-[var(--color-jarvis-orange)]/10 text-[var(--color-jarvis-orange)] hover:bg-[var(--color-jarvis-orange)]/15",
      )}
    >
      {label}
    </button>
  );
}

function SummaryList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
      <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">{title}</p>
      <div className="mt-3 space-y-2">
        {items.length > 0 ? (
          items.slice(0, 5).map((item, index) => (
            <div key={`${title}-${index}`} className="rounded-xl border border-white/8 bg-white/3 p-3 text-sm text-gray-300">
              {item}
            </div>
          ))
        ) : (
          <EmptyState text={empty} />
        )}
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-white/10 bg-black/10 px-4 py-5 text-center text-sm text-[var(--color-jarvis-muted)]">
      {text}
    </div>
  );
}

function formatTimeCompact(value: string) {
  return new Date(value).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
