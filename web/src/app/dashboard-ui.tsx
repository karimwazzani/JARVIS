"use client";

import Link from "next/link";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowLeft,
  Bot,
  Brain,
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

type WorkspaceView = "chat" | "memory" | "runs";

type AgentMeta = {
  title: string;
  blurb: string;
  accent: "cyan" | "orange";
  icon: LucideIcon;
};

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export const AGENT_META: Record<string, AgentMeta> = {
  jarvis_orchestrator: {
    title: "Jarvis Orchestrator",
    blurb: "Recibe el pedido, decide quien entra y arma la salida final.",
    accent: "cyan",
    icon: Brain,
  },
  memory_keeper: {
    title: "Memory Keeper",
    blurb: "Ordena memoria, contexto y continuidad entre turnos.",
    accent: "cyan",
    icon: Database,
  },
  research: {
    title: "Research",
    blurb: "Investiga mercado, competencia, ideas y fuentes.",
    accent: "orange",
    icon: Sparkles,
  },
  coder: {
    title: "Coder",
    blurb: "Piensa producto, arreglos, features y arquitectura.",
    accent: "cyan",
    icon: Cpu,
  },
  content_strategist: {
    title: "Content Strategist",
    blurb: "Propone estrategia, hooks, series y contenido.",
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
    blurb: "Revisa riesgos, pruebas y calidad del sistema.",
    accent: "orange",
    icon: Activity,
  },
  finance_ops: {
    title: "Finance Ops",
    blurb: "Sigue gastos, ingresos y estado operativo.",
    accent: "orange",
    icon: Wallet,
  },
};

const MODE_OPTIONS = ["Estandar", "Centinela", "Relax", "Ejecutor"];

const EMPTY_SNAPSHOT: DashboardSnapshot = {
  totalBalance: 0,
  mtdExpense: 0,
  chartData: [],
  systemMode: "Estandar",
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

function labelFromRoute(route: string) {
  return route
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function buildAgentChatId(route: string) {
  return `web-panel:${route}`;
}

function getAgentMeta(route: string): AgentMeta {
  return (
    AGENT_META[route] || {
      title: labelFromRoute(route),
      blurb: "Ruta disponible en el sistema Jarvis.",
      accent: "cyan",
      icon: Cpu,
    }
  );
}

function buildFallbackAgent(route: string): AgentSummary {
  return {
    route,
    label: labelFromRoute(route),
    totalRuns: 0,
    latestStatus: "idle",
    latestAt: null,
    latestPrompt: "",
    latestResponse: "",
    memoryItems: [],
    recentRuns: [],
  };
}

function useDashboardSnapshot() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot>(EMPTY_SNAPSHOT);

  useEffect(() => {
    const load = async () => {
      const data = await getDashboardSnapshot();
      setSnapshot(data);
    };

    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  return { snapshot, setSnapshot };
}

function TopShell({
  title,
  subtitle,
  currentPath,
  children,
  systemMode,
  onModeChange,
}: {
  title: string;
  subtitle: string;
  currentPath: "overview" | "agent" | "system";
  children: React.ReactNode;
  systemMode: string;
  onModeChange: (mode: string) => void;
}) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[var(--color-jarvis-bg)] p-4 md:p-5">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-4">
        <header className="glass-panel neon-border rounded-2xl px-5 py-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl border border-[var(--color-jarvis-cyan)]/20 bg-[var(--color-jarvis-cyan)]/10 p-3">
                <Bot className="text-[var(--color-jarvis-cyan)]" size={24} />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] uppercase tracking-[0.32em] text-[var(--color-jarvis-muted)]">Jarvis Control Deck</p>
                <h1 className="text-2xl font-semibold text-white">{title}</h1>
                <p className="mt-1 text-sm text-[var(--color-jarvis-muted)]">{subtitle}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <NavLink href="/" active={currentPath === "overview"}>
                Overview
              </NavLink>
              <NavLink href="/sistema" active={currentPath === "system"}>
                Sistema
              </NavLink>
              <MetricBadge label="Hora" value={time.toLocaleTimeString("es-AR", { hour12: false })} />
              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Modo</p>
                <select
                  value={systemMode}
                  onChange={(event) => onModeChange(event.target.value)}
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

        {children}
      </div>
    </div>
  );
}

export function OverviewDashboardPage() {
  const { snapshot, setSnapshot } = useDashboardSnapshot();

  const handleModeChange = async (mode: string) => {
    const result = await setSystemMode(mode);
    if (result.success) {
      setSnapshot((prev) => ({ ...prev, systemMode: mode }));
    }
  };

  return (
    <TopShell
      title="Centro de control"
      subtitle="Vista general para entrar rapido a cada agente y al estado global del sistema."
      currentPath="overview"
      systemMode={snapshot.systemMode}
      onModeChange={handleModeChange}
    >
      <section className="grid grid-cols-2 gap-3 xl:grid-cols-5">
        <StatTile label="Agentes" value={String(snapshot.agentSummaries.length || 0)} icon={Cpu} accent="cyan" />
        <StatTile label="Runs" value={String(snapshot.totalAgentRuns)} icon={Activity} accent="cyan" />
        <StatTile label="Chats" value={String(snapshot.uniqueChats)} icon={MessageSquare} accent="orange" />
        <StatTile label="Pendientes" value={String(snapshot.pendingTasks)} icon={Clock3} accent="orange" />
        <StatTile
          label="Balance"
          value={`$${snapshot.totalBalance.toLocaleString("es-AR", { maximumFractionDigits: 0 })}`}
          icon={Wallet}
          accent="cyan"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="glass-panel rounded-2xl p-4">
          <SectionTitle icon={Cpu} title="Agentes disponibles" />
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {snapshot.agentSummaries.map((agent) => {
              const meta = getAgentMeta(agent.route);
              const Icon = meta.icon;
              return (
                <Link
                  key={agent.route}
                  href={`/agentes/${agent.route}`}
                  className="rounded-2xl border border-white/8 bg-black/10 p-4 transition hover:border-white/16 hover:bg-white/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg border border-white/10 bg-black/20 p-2">
                        <Icon
                          size={18}
                          className={meta.accent === "cyan" ? "text-[var(--color-jarvis-cyan)]" : "text-[var(--color-jarvis-orange)]"}
                        />
                      </div>
                      <div>
                        <p className="text-base font-semibold text-white">{meta.title}</p>
                        <p className="mt-1 text-sm text-[var(--color-jarvis-muted)]">{meta.blurb}</p>
                      </div>
                    </div>
                    <ChevronRight size={18} className="shrink-0 text-[var(--color-jarvis-muted)]" />
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-2">
                    <MiniStat label="Runs" value={String(agent.totalRuns)} />
                    <MiniStat label="Memorias" value={String(agent.memoryItems.length)} />
                    <MiniStat label="Estado" value={agent.latestStatus} />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-4">
          <SectionTitle icon={Activity} title="Ultimos movimientos" />
          <div className="mt-4 space-y-3">
            {snapshot.agentRuns.slice(0, 6).map((run, index) => (
              <div key={`${run.timestamp}-${index}`} className="rounded-xl border border-white/8 bg-black/10 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-white">{getAgentMeta(run.route).title}</p>
                  <StatusPill status={run.status} compact />
                </div>
                <p className="mt-2 text-xs text-[var(--color-jarvis-muted)]">{run.userMessage}</p>
                <p className="mt-2 line-clamp-3 text-sm text-gray-300">{run.responsePreview}</p>
              </div>
            ))}
            {snapshot.agentRuns.length === 0 ? <EmptyState text="Todavia no hay actividad reciente." /> : null}
          </div>
        </div>
      </section>
    </TopShell>
  );
}

export function AgentWorkspacePage({ route }: { route: string }) {
  const { snapshot, setSnapshot } = useDashboardSnapshot();
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>("chat");
  const [message, setMessage] = useState("");
  const [chatFeed, setChatFeed] = useState<ChatBubble[]>([]);
  const [sending, setSending] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const selectedAgent = useMemo(() => {
    return snapshot.agentSummaries.find((item) => item.route === route) || buildFallbackAgent(route);
  }, [snapshot.agentSummaries, route]);

  const agentMeta = getAgentMeta(route);
  const agentChatId = buildAgentChatId(route);

  useEffect(() => {
    const recognitionSupported =
      typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
    setVoiceSupported(recognitionSupported);
  }, []);

  useEffect(() => {
    const scopedFeed = snapshot.conversations
      .filter((row) => row.chatId === agentChatId)
      .slice(0, 20)
      .reverse()
      .map((row) => ({
        role: row.role as "user" | "assistant",
        content: row.content,
        timestamp: row.timestamp || "",
      }));
    setChatFeed(scopedFeed);
  }, [snapshot.conversations, agentChatId]);

  const handleModeChange = async (mode: string) => {
    const result = await setSystemMode(mode);
    if (result.success) {
      setSnapshot((prev) => ({ ...prev, systemMode: mode }));
    }
  };

  const submitMessage = async (content: string) => {
    if (!content.trim()) return;

    const trimmed = content.trim();
    setChatFeed((prev) => [
      ...prev,
      { role: "user", content: trimmed, timestamp: new Date().toISOString() },
    ]);
    setSending(true);
    setMessage("");

    const result = await sendWebPanelMessage(trimmed, agentChatId, route);

    setChatFeed((prev) => [
      ...prev,
      { role: "assistant", content: result.response, timestamp: new Date().toISOString() },
    ]);
    setSending(false);

    const data = await getDashboardSnapshot();
    setSnapshot(data);
  };

  const toggleVoiceInput = () => {
    const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!RecognitionCtor) return;

    if (recognitionRef.current && listening) {
      recognitionRef.current.stop();
      return;
    }

    const recognition = new RecognitionCtor();
    recognitionRef.current = recognition;
    recognition.lang = "es-AR";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };
    recognition.onerror = () => {
      setListening(false);
      recognitionRef.current = null;
    };
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .flatMap((result) => Array.from(result))
        .map((part) => part.transcript)
        .join(" ")
        .trim();
      if (transcript) {
        void submitMessage(transcript);
      }
    };

    recognition.start();
  };

  return (
    <TopShell
      title={agentMeta.title}
      subtitle={agentMeta.blurb}
      currentPath="agent"
      systemMode={snapshot.systemMode}
      onModeChange={handleModeChange}
    >
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-gray-300 transition hover:bg-white/5"
        >
          <ArrowLeft size={16} />
          Volver
        </Link>
        <Link
          href="/sistema"
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-gray-300 transition hover:bg-white/5"
        >
          Ver sistema
        </Link>
      </div>

      <section className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="glass-panel rounded-2xl p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 pb-4">
            <div className="flex items-center gap-2">
              <agentMeta.icon
                size={18}
                className={agentMeta.accent === "cyan" ? "text-[var(--color-jarvis-cyan)]" : "text-[var(--color-jarvis-orange)]"}
              />
              <h2 className="text-xl font-semibold text-white">{agentMeta.title}</h2>
              <StatusPill status={selectedAgent.latestStatus} />
            </div>

            <div className="flex flex-wrap gap-2">
              <ViewTab label="Chat" active={workspaceView === "chat"} onClick={() => setWorkspaceView("chat")} />
              <ViewTab label="Memoria" active={workspaceView === "memory"} onClick={() => setWorkspaceView("memory")} />
              <ViewTab label="Runs" active={workspaceView === "runs"} onClick={() => setWorkspaceView("runs")} />
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <MiniStat label="Ultima actividad" value={selectedAgent.latestAt ? formatTimeCompact(selectedAgent.latestAt) : "sin datos"} />
            <MiniStat label="Runs" value={String(selectedAgent.totalRuns)} />
            <MiniStat label="Memorias" value={String(selectedAgent.memoryItems.length)} />
            <MiniStat label="Chat actual" value={route} />
          </div>

          {workspaceView === "chat" ? (
            <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
              <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">Canal directo</p>
                    <p className="mt-1 text-sm text-white">Le hablas directo a {agentMeta.title}</p>
                  </div>
                  <button
                    onClick={toggleVoiceInput}
                    disabled={!voiceSupported}
                    className={cn(
                      "inline-flex h-11 items-center gap-2 rounded-xl border px-4 text-sm font-medium transition",
                      listening
                        ? "border-[var(--color-jarvis-orange)]/40 bg-[var(--color-jarvis-orange)]/15 text-[var(--color-jarvis-orange)]"
                        : "border-white/10 bg-black/20 text-white hover:bg-white/5",
                      !voiceSupported && "opacity-40",
                    )}
                  >
                    {listening ? <MicOff size={16} /> : <Mic size={16} />}
                    {listening ? "Escuchando..." : "Activar microfono"}
                  </button>
                </div>

                <div className="mt-4 h-[420px] overflow-y-auto rounded-2xl border border-white/8 bg-[var(--color-jarvis-surface)]/40 p-4 custom-scrollbar">
                  <div className="space-y-3">
                    {chatFeed.length > 0 ? (
                      chatFeed.map((item, index) => (
                        <div key={`${item.timestamp}-${index}`} className={cn("flex", item.role === "user" ? "justify-end" : "justify-start")}>
                          <div
                            className={cn(
                              "max-w-[80%] rounded-2xl border px-4 py-3 text-sm leading-relaxed",
                              item.role === "user"
                                ? "border-[var(--color-jarvis-cyan)]/20 bg-[var(--color-jarvis-cyan)]/12 text-white"
                                : "border-white/10 bg-white/5 text-gray-200",
                            )}
                          >
                            {item.content}
                          </div>
                        </div>
                      ))
                    ) : (
                      <EmptyState text="Todavia no hay mensajes en este canal. Podes escribir o activar el microfono." />
                    )}
                    {sending ? (
                      <div className="flex justify-start">
                        <div className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-gray-300">
                          <span className="inline-flex items-center gap-2">
                            <LoaderCircle className="animate-spin" size={14} />
                            Jarvis esta pensando...
                          </span>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_160px]">
                  <textarea
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    placeholder={`Escribile a ${agentMeta.title}...`}
                    className="min-h-[120px] resize-none rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--color-jarvis-muted)]"
                  />
                  <button
                    onClick={() => void submitMessage(message)}
                    disabled={sending || !message.trim()}
                    className="rounded-2xl bg-[var(--color-jarvis-cyan)]/15 px-4 py-3 text-sm font-medium text-[var(--color-jarvis-cyan)] transition hover:bg-[var(--color-jarvis-cyan)]/20 disabled:opacity-40"
                  >
                    Enviar
                  </button>
                </div>
              </div>

              <div className="grid gap-4">
                <SideBlock title="Ultimo pedido" content={selectedAgent.latestPrompt || "Sin pedido reciente para este agente."} />
                <SideBlock title="Ultima respuesta" content={selectedAgent.latestResponse || "Sin respuesta visible todavia."} scrollable />
              </div>
            </div>
          ) : null}

          {workspaceView === "memory" ? (
            <div className="mt-4 h-[620px] overflow-y-auto rounded-2xl border border-white/8 bg-black/10 p-4 custom-scrollbar">
              <div className="space-y-3">
                {selectedAgent.memoryItems.length ? (
                  selectedAgent.memoryItems.map((item, index) => (
                    <div key={`${item.timestamp}-${index}`} className="rounded-xl border border-white/8 bg-white/4 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-cyan)]">{item.category}</span>
                        <span className="text-[10px] text-[var(--color-jarvis-muted)]">{formatTimeCompact(item.timestamp)}</span>
                      </div>
                      <p className="mt-2 text-sm text-gray-300">{item.content}</p>
                    </div>
                  ))
                ) : (
                  <EmptyState text="Este agente todavia no dejo memoria visible." />
                )}
              </div>
            </div>
          ) : null}

          {workspaceView === "runs" ? (
            <div className="mt-4 h-[620px] overflow-y-auto rounded-2xl border border-white/8 bg-black/10 p-4 custom-scrollbar">
              <div className="space-y-3">
                {selectedAgent.recentRuns.length ? (
                  selectedAgent.recentRuns.map((run, index) => (
                    <div key={`${run.timestamp}-${index}`} className="rounded-xl border border-white/8 bg-white/4 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-white">{agentMeta.title}</p>
                        <StatusPill status={run.status} compact />
                      </div>
                      <p className="mt-2 text-xs text-[var(--color-jarvis-muted)]">{run.userMessage}</p>
                      <p className="mt-2 text-sm text-gray-300">{run.responsePreview}</p>
                    </div>
                  ))
                ) : (
                  <EmptyState text="Todavia no hay runs recientes para este agente." />
                )}
              </div>
            </div>
          ) : null}
        </div>

        <div className="grid content-start gap-4">
          <SummaryList
            title="Navegacion rapida"
            items={Object.keys(AGENT_META).map((agentRoute) => `${getAgentMeta(agentRoute).title} -> /agentes/${agentRoute}`)}
            empty="Sin rutas cargadas."
          />
          <SummaryList
            title="Conversacion global"
            items={snapshot.conversations
              .filter((item: AgentConversationEntry) => item.chatId !== agentChatId)
              .slice(0, 6)
              .map((item: AgentConversationEntry) => `${item.role}: ${item.content}`)}
            empty="No hay conversacion global reciente."
          />
        </div>
      </section>
    </TopShell>
  );
}

export function SystemOperationsPage() {
  const { snapshot, setSnapshot } = useDashboardSnapshot();
  const [chartsReady, setChartsReady] = useState(false);

  useEffect(() => {
    setChartsReady(true);
  }, []);

  const handleModeChange = async (mode: string) => {
    const result = await setSystemMode(mode);
    if (result.success) {
      setSnapshot((prev) => ({ ...prev, systemMode: mode }));
    }
  };

  const handleQuickTransaction = async (tipo: "gasto" | "ingreso") => {
    const amountText = prompt(tipo === "gasto" ? "Monto del gasto:" : "Monto del ingreso:");
    if (!amountText) return;
    const description = prompt("Descripcion:");
    if (!description) return;
    const result = await addQuickTransaction(Number(amountText), description, tipo);
    if (result.success) {
      const data = await getDashboardSnapshot();
      setSnapshot(data);
    }
  };

  const handleClearLogs = async () => {
    if (!confirm("Limpiar los logs visibles del panel?")) return;
    const result = await clearAllLogs();
    if (result.success) {
      const data = await getDashboardSnapshot();
      setSnapshot(data);
    }
  };

  return (
    <TopShell
      title="Sistema y operaciones"
      subtitle="Vista dedicada para finanzas, tareas, calendario, aprobaciones y logs."
      currentPath="system"
      systemMode={snapshot.systemMode}
      onModeChange={handleModeChange}
    >
      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <div className="glass-panel rounded-2xl p-4">
          <SectionTitle icon={Wallet} title="Finanzas" />
          <div className="mt-4 rounded-2xl border border-white/8 bg-black/10 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
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
            <div className="mt-4 h-44">
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
        </div>

        <div className="glass-panel rounded-2xl p-4">
          <SectionTitle icon={Clock3} title="Tareas y agenda" />
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <SummaryList
              title="Tareas"
              items={snapshot.tasks.map((task) => `${task.titulo}${task.descripcion ? ` - ${task.descripcion}` : ""}`)}
              empty="No hay tareas visibles."
            />
            <SummaryList
              title="Calendario"
              items={snapshot.calendar.map((item) => `${formatTimeCompact(item.fecha)} - ${item.titulo}`)}
              empty="No hay eventos proximos."
            />
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="glass-panel rounded-2xl p-4">
          <div className="flex items-center justify-between gap-3">
            <SectionTitle icon={Shield} title="Aprobaciones" />
          </div>
          <div className="mt-4">
            <SummaryList
              title="Pendientes"
              items={snapshot.proposals.map((item) => item.descripcion)}
              empty="No hay aprobaciones pendientes."
            />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-4">
          <div className="flex items-center justify-between gap-3">
            <SectionTitle icon={Database} title="Logs del sistema" />
            <button onClick={() => void handleClearLogs()} className="text-xs text-[var(--color-jarvis-orange)] hover:underline">
              limpiar
            </button>
          </div>
          <div className="mt-4 h-[360px] overflow-y-auto custom-scrollbar">
            <div className="space-y-2">
              {snapshot.logs.slice(0, 12).map((log, index) => (
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
      </section>
    </TopShell>
  );
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className={cn(
        "rounded-xl border px-4 py-2 text-sm transition",
        active
          ? "border-[var(--color-jarvis-cyan)]/30 bg-[var(--color-jarvis-cyan)]/12 text-[var(--color-jarvis-cyan)]"
          : "border-white/10 bg-black/20 text-gray-300 hover:bg-white/5",
      )}
    >
      {children}
    </Link>
  );
}

function SectionTitle({ icon: Icon, title }: { icon: LucideIcon; title: string }) {
  return (
    <div className="flex items-center gap-2">
      <Icon size={16} className="text-[var(--color-jarvis-cyan)]" />
      <h2 className="text-sm font-mono uppercase tracking-[0.28em] text-white">{title}</h2>
    </div>
  );
}

function ViewTab({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-xl border px-3 py-2 text-sm transition",
        active
          ? "border-[var(--color-jarvis-cyan)]/30 bg-[var(--color-jarvis-cyan)]/12 text-[var(--color-jarvis-cyan)]"
          : "border-white/10 bg-black/20 text-gray-300 hover:bg-white/5",
      )}
    >
      {label}
    </button>
  );
}

function MetricBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-right">
      <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">{label}</p>
      <p className="font-mono text-lg text-white">{value}</p>
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

function SideBlock({ title, content, scrollable = false }: { title: string; content: string; scrollable?: boolean }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
      <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--color-jarvis-muted)]">{title}</p>
      <div className={cn("mt-3 text-sm leading-relaxed text-gray-300", scrollable && "max-h-[260px] overflow-y-auto pr-1 custom-scrollbar")}>
        {content}
      </div>
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
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 uppercase tracking-[0.2em]",
        compact ? "text-[9px]" : "text-[10px]",
        tone,
      )}
    >
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
      <div className="mt-3 max-h-[280px] space-y-2 overflow-y-auto pr-1 custom-scrollbar">
        {items.length > 0 ? (
          items.slice(0, 8).map((item, index) => (
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
