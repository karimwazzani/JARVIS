"use server";

import "server-only";

import { createClient } from "@supabase/supabase-js";

type TransactionRow = {
  tipo: "gasto" | "ingreso";
  monto: number | string;
  fecha: string;
};

type LogRow = {
  id?: number;
  evento: string;
  fecha: string;
};

type ProposalRow = {
  id: number;
  descripcion: string;
  accion_tecnica: string | null;
  fecha_creacion: string;
};

type CalendarRow = {
  titulo: string;
  fecha_hora: string;
  ubicacion: string | null;
};

type PreferenceRow = {
  valor: string;
};

type ConversationRow = {
  id: number;
  chat_id: string;
  rol: string;
  contenido: string;
  fecha?: string;
};

type MemoryRow = {
  id?: number;
  categoria: string;
  dato: string;
  fecha_registro: string;
};

type TaskRow = {
  id: number;
  chat_id: string;
  titulo: string;
  descripcion: string | null;
  estado: string;
  fecha_creacion: string;
};

function getSupabaseAdmin() {
  const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;

  if (!url || !key) {
    throw new Error("Missing Supabase server environment variables.");
  }

  return createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

function startOfCurrentMonthUtc() {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
}

function startOfTrailingWeekUtc() {
  const now = new Date();
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  start.setUTCDate(start.getUTCDate() - 6);
  return start;
}

function formatDayLabel(dateString: string) {
  return new Date(dateString).toLocaleDateString("es-AR", {
    weekday: "short",
    timeZone: "UTC",
  });
}

function formatRelative(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function labelFromRoute(route: string) {
  return route
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function parseAgentRun(evento: string) {
  if (!evento.startsWith("[AGENT_RUN]")) return null;
  const jsonPart = evento.replace("[AGENT_RUN]", "").trim();
  try {
    return JSON.parse(jsonPart) as {
      route: string;
      status: string;
      requires_confirmation: boolean;
      user_message: string;
      response_preview: string;
      metadata?: Record<string, string>;
    };
  } catch {
    return null;
  }
}

export type FinanceChartPoint = {
  name: string;
  income: number;
  expense: number;
};

export type AgentRunEntry = {
  route: string;
  label: string;
  status: string;
  requiresConfirmation: boolean;
  userMessage: string;
  responsePreview: string;
  timestamp: string;
};

export type AgentMemoryEntry = {
  route: string;
  category: string;
  content: string;
  timestamp: string;
};

export type AgentConversationEntry = {
  id: number;
  chatId: string;
  role: string;
  content: string;
  timestamp?: string;
};

export type AgentSummary = {
  route: string;
  label: string;
  totalRuns: number;
  latestStatus: string;
  latestAt: string | null;
  latestPrompt: string;
  latestResponse: string;
  memoryItems: AgentMemoryEntry[];
  recentRuns: AgentRunEntry[];
};

export type ProposalEntry = {
  id: number;
  descripcion: string;
  tecnica: string | null;
  fecha: string;
};

export type CalendarEntry = {
  titulo: string;
  fecha: string;
  ubicacion: string | null;
};

export type TaskEntry = {
  id: number;
  titulo: string;
  descripcion: string | null;
  estado: string;
  fecha: string;
};

export type DashboardSnapshot = {
  totalBalance: number;
  mtdExpense: number;
  chartData: FinanceChartPoint[];
  systemMode: string;
  totalAgentRuns: number;
  uniqueChats: number;
  pendingTasks: number;
  pendingApprovals: number;
  logs: { evento: string; fecha: string }[];
  proposals: ProposalEntry[];
  calendar: CalendarEntry[];
  tasks: TaskEntry[];
  conversations: AgentConversationEntry[];
  agentRuns: AgentRunEntry[];
  agentSummaries: AgentSummary[];
};

export async function getDashboardSnapshot(): Promise<DashboardSnapshot> {
  try {
    const supabase = getSupabaseAdmin();
    const monthStart = startOfCurrentMonthUtc().toISOString();
    const weekStart = startOfTrailingWeekUtc();
    const todayEnd = new Date(weekStart);
    todayEnd.setUTCDate(todayEnd.getUTCDate() + 6);
    todayEnd.setUTCHours(23, 59, 59, 999);

    const [
      transactionsResult,
      monthTransactionsResult,
      weekTransactionsResult,
      logsResult,
      propuestasResult,
      calendarResult,
      modeResult,
      conversationsResult,
      memoriesResult,
      tasksResult,
    ] = await Promise.all([
      supabase.from("transacciones").select("tipo,monto,fecha").order("fecha", { ascending: true }),
      supabase.from("transacciones").select("tipo,monto,fecha").gte("fecha", monthStart),
      supabase
        .from("transacciones")
        .select("tipo,monto,fecha")
        .gte("fecha", weekStart.toISOString())
        .lte("fecha", todayEnd.toISOString())
        .order("fecha", { ascending: true }),
      supabase.from("log_eventos").select("id,evento,fecha").order("fecha", { ascending: false }).limit(60),
      supabase
        .from("propuestas_automatizacion")
        .select("id,descripcion,accion_tecnica,fecha_creacion")
        .eq("estado", "pendiente")
        .order("fecha_creacion", { ascending: false })
        .limit(10),
      supabase
        .from("eventos_calendario")
        .select("titulo,fecha_hora,ubicacion")
        .gte("fecha_hora", new Date().toISOString())
        .order("fecha_hora", { ascending: true })
        .limit(5),
      supabase
        .from("preferencias_usuario")
        .select("valor")
        .eq("clave", "modo_sistema")
        .order("fecha_actualizacion", { ascending: false })
        .limit(1),
      supabase.from("conversaciones").select("id,chat_id,rol,contenido,fecha").order("id", { ascending: false }).limit(30),
      supabase.from("memorias").select("categoria,dato,fecha_registro").like("categoria", "agent::%").order("fecha_registro", { ascending: false }).limit(30),
      supabase.from("tareas").select("id,chat_id,titulo,descripcion,estado,fecha_creacion").order("fecha_creacion", { ascending: false }).limit(10),
    ]);

    const errors = [
      transactionsResult.error,
      monthTransactionsResult.error,
      weekTransactionsResult.error,
      logsResult.error,
      propuestasResult.error,
      calendarResult.error,
      modeResult.error,
      conversationsResult.error,
      memoriesResult.error,
      tasksResult.error,
    ].filter(Boolean);

    if (errors.length > 0) throw errors[0];

    const allTransactions = (transactionsResult.data || []) as TransactionRow[];
    const monthTransactions = (monthTransactionsResult.data || []) as TransactionRow[];
    const weekTransactions = (weekTransactionsResult.data || []) as TransactionRow[];
    const logs = (logsResult.data || []) as LogRow[];
    const conversations = (conversationsResult.data || []) as ConversationRow[];
    const memories = (memoriesResult.data || []) as MemoryRow[];
    const tasks = (tasksResult.data || []) as TaskRow[];

    const totals = allTransactions.reduce(
      (acc, row) => {
        const amount = Number(row.monto) || 0;
        if (row.tipo === "ingreso") acc.income += amount;
        if (row.tipo === "gasto") acc.expense += amount;
        return acc;
      },
      { income: 0, expense: 0 },
    );

    const mtdExpense = monthTransactions.reduce((sum, row) => {
      const amount = Number(row.monto) || 0;
      return row.tipo === "gasto" ? sum + amount : sum;
    }, 0);

    const dailyMap = new Map<string, FinanceChartPoint>();
    for (let index = 0; index < 7; index += 1) {
      const date = new Date(weekStart);
      date.setUTCDate(weekStart.getUTCDate() + index);
      const key = date.toISOString().slice(0, 10);
      dailyMap.set(key, {
        name: formatDayLabel(date.toISOString()),
        income: 0,
        expense: 0,
      });
    }

    for (const row of weekTransactions) {
      const key = new Date(row.fecha).toISOString().slice(0, 10);
      const bucket = dailyMap.get(key);
      if (!bucket) continue;
      const amount = Number(row.monto) || 0;
      if (row.tipo === "ingreso") bucket.income += amount;
      if (row.tipo === "gasto") bucket.expense += amount;
    }

    const agentRuns = logs
      .map((row) => {
        const parsed = parseAgentRun(row.evento);
        if (!parsed) return null;
        return {
          route: parsed.route,
          label: labelFromRoute(parsed.route),
          status: parsed.status,
          requiresConfirmation: parsed.requires_confirmation,
          userMessage: parsed.user_message,
          responsePreview: parsed.response_preview,
          timestamp: row.fecha,
        } satisfies AgentRunEntry;
      })
      .filter((row): row is AgentRunEntry => Boolean(row));

    const memoryByRoute = new Map<string, AgentMemoryEntry[]>();
    for (const row of memories) {
      const parts = row.categoria.split("::");
      const route = parts[1] || "jarvis_orchestrator";
      const category = parts[2] || "memory";
      const current = memoryByRoute.get(route) || [];
      current.push({
        route,
        category,
        content: row.dato,
        timestamp: row.fecha_registro,
      });
      memoryByRoute.set(route, current);
    }

    const grouped = new Map<string, AgentSummary>();
    for (const run of agentRuns) {
      const current = grouped.get(run.route) || {
        route: run.route,
        label: run.label,
        totalRuns: 0,
        latestStatus: run.status,
        latestAt: run.timestamp,
        latestPrompt: run.userMessage,
        latestResponse: run.responsePreview,
        memoryItems: memoryByRoute.get(run.route) || [],
        recentRuns: [],
      };
      current.totalRuns += 1;
      if (!current.latestAt || new Date(run.timestamp) > new Date(current.latestAt)) {
        current.latestAt = run.timestamp;
        current.latestStatus = run.status;
        current.latestPrompt = run.userMessage;
        current.latestResponse = run.responsePreview;
      }
      if (current.recentRuns.length < 4) {
        current.recentRuns.push(run);
      }
      grouped.set(run.route, current);
    }

    for (const [route, memoryItems] of memoryByRoute.entries()) {
      if (!grouped.has(route)) {
        grouped.set(route, {
          route,
          label: labelFromRoute(route),
          totalRuns: 0,
          latestStatus: "idle",
          latestAt: memoryItems[0]?.timestamp || null,
          latestPrompt: "",
          latestResponse: "",
          memoryItems,
          recentRuns: [],
        });
      }
    }

    const uniqueChats = new Set(conversations.map((row) => row.chat_id)).size;
    const pendingTasks = tasks.filter((task) => task.estado === "pendiente").length;
    const pendingApprovals = (propuestasResult.data || []).length;

    return {
      totalBalance: totals.income - totals.expense,
      mtdExpense,
      chartData: Array.from(dailyMap.values()),
      systemMode: ((modeResult.data || []) as PreferenceRow[])[0]?.valor || "Estándar",
      totalAgentRuns: agentRuns.length,
      uniqueChats,
      pendingTasks,
      pendingApprovals,
      logs: logs
        .filter((row) => !row.evento.startsWith("[AGENT_RUN]"))
        .slice(0, 12)
        .map((row) => ({ evento: row.evento, fecha: row.fecha })),
      proposals: ((propuestasResult.data || []) as ProposalRow[]).map((row) => ({
        id: row.id,
        descripcion: row.descripcion,
        tecnica: row.accion_tecnica,
        fecha: row.fecha_creacion,
      })),
      calendar: ((calendarResult.data || []) as CalendarRow[]).map((row) => ({
        titulo: row.titulo,
        fecha: row.fecha_hora,
        ubicacion: row.ubicacion,
      })),
      tasks: tasks.map((task) => ({
        id: task.id,
        titulo: task.titulo,
        descripcion: task.descripcion,
        estado: task.estado,
        fecha: task.fecha_creacion,
      })),
      conversations: conversations.map((row) => ({
        id: row.id,
        chatId: row.chat_id,
        role: row.rol,
        content: row.contenido,
        timestamp: row.fecha,
      })),
      agentRuns,
      agentSummaries: Array.from(grouped.values()).sort((a, b) => {
        const aTime = a.latestAt ? new Date(a.latestAt).getTime() : 0;
        const bTime = b.latestAt ? new Date(b.latestAt).getTime() : 0;
        return bTime - aTime;
      }),
    };
  } catch (error) {
    console.error("Failed to build dashboard snapshot:", error);
    return {
      totalBalance: 0,
      mtdExpense: 0,
      chartData: [
        { name: "lun", income: 0, expense: 0 },
        { name: "mar", income: 0, expense: 0 },
        { name: "mie", income: 0, expense: 0 },
        { name: "jue", income: 0, expense: 0 },
        { name: "vie", income: 0, expense: 0 },
        { name: "sab", income: 0, expense: 0 },
        { name: "dom", income: 0, expense: 0 },
      ],
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
  }
}

export async function clearAllLogs() {
  try {
    const supabase = getSupabaseAdmin();
    const { error } = await supabase.from("log_eventos").delete().neq("id", 0);
    if (error) throw error;
    return { success: true };
  } catch {
    return { success: false };
  }
}

export async function addQuickTransaction(
  monto: number,
  descripcion: string,
  tipo: "gasto" | "ingreso" = "gasto",
) {
  try {
    const supabase = getSupabaseAdmin();
    const { error } = await supabase.from("transacciones").insert({
      tipo,
      monto,
      descripcion,
      fecha: new Date().toISOString(),
    });
    if (error) throw error;
    return { success: true };
  } catch {
    return { success: false };
  }
}

export async function setSystemMode(modo: string) {
  try {
    const supabase = getSupabaseAdmin();
    const { error: deleteError } = await supabase
      .from("preferencias_usuario")
      .delete()
      .eq("clave", "modo_sistema");
    if (deleteError) throw deleteError;

    const { error: insertError } = await supabase.from("preferencias_usuario").insert({
      chat_id: "general",
      clave: "modo_sistema",
      valor: modo,
      fecha_actualizacion: new Date().toISOString(),
    });
    if (insertError) throw insertError;

    const { error: logError } = await supabase.from("log_eventos").insert({
      chat_id: "system",
      evento: `Cambio de modo a: ${modo}`,
      fecha: new Date().toISOString(),
    });
    if (logError) throw logError;

    return { success: true };
  } catch (e) {
    console.error("Error setting mode:", e);
    return { success: false };
  }
}

export async function sendWebPanelMessage(message: string, chatId = "web-panel") {
  try {
    const backendUrl = process.env.NEXT_PUBLIC_JARVIS_BACKEND_URL || "https://jarvis-backend-7hh7.onrender.com";
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chatId, message }),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      chatId: data.chatId as string,
      response: data.response as string,
    };
  } catch (error) {
    console.error("Error sending web panel message:", error);
    return {
      success: false,
      chatId,
      response: "No pude comunicarme con Jarvis desde el panel web.",
    };
  }
}
