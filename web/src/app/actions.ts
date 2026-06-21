"use server";

import "server-only";

import { createClient } from "@supabase/supabase-js";

type TransactionRow = {
  tipo: "gasto" | "ingreso";
  monto: number | string;
  fecha: string;
};

type LogRow = {
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
  return new Date(dateString).toLocaleDateString("en-US", {
    weekday: "short",
    timeZone: "UTC",
  });
}

export type FinanceChartPoint = {
  name: string;
  income: number;
  expense: number;
};

export type LogEntry = {
  evento: string;
  fecha: string;
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

export type WeatherData = {
  temp: string;
  cond: string;
  humidity: string;
  wind: string;
};

export async function getFinancialData() {
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
    ] = await Promise.all([
      supabase.from("transacciones").select("tipo,monto,fecha").order("fecha", { ascending: true }),
      supabase.from("transacciones").select("tipo,monto,fecha").gte("fecha", monthStart),
      supabase
        .from("transacciones")
        .select("tipo,monto,fecha")
        .gte("fecha", weekStart.toISOString())
        .lte("fecha", todayEnd.toISOString())
        .order("fecha", { ascending: true }),
      supabase.from("log_eventos").select("evento,fecha").order("fecha", { ascending: false }).limit(10),
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
    ]);

    const errors = [
      transactionsResult.error,
      monthTransactionsResult.error,
      weekTransactionsResult.error,
      logsResult.error,
      propuestasResult.error,
      calendarResult.error,
    ].filter(Boolean);

    if (errors.length > 0) {
      throw errors[0];
    }

    const allTransactions = (transactionsResult.data || []) as TransactionRow[];
    const monthTransactions = (monthTransactionsResult.data || []) as TransactionRow[];
    const weekTransactions = (weekTransactionsResult.data || []) as TransactionRow[];

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

    return {
      totalBalance: totals.income - totals.expense,
      mtdExpense,
      chartData: Array.from(dailyMap.values()),
      logs: ((logsResult.data || []) as LogRow[]).map((row) => ({
        evento: row.evento,
        fecha: row.fecha,
      })),
      propuestas: ((propuestasResult.data || []) as ProposalRow[]).map((row) => ({
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
    };
  } catch (error) {
    console.error("Failed to fetch database data:", error);
    return {
      totalBalance: 0,
      mtdExpense: 0,
      logs: [],
      propuestas: [],
      calendar: [],
      chartData: [
        { name: "Mon", income: 0, expense: 0 },
        { name: "Tue", income: 0, expense: 0 },
        { name: "Wed", income: 0, expense: 0 },
        { name: "Thu", income: 0, expense: 0 },
        { name: "Fri", income: 0, expense: 0 },
        { name: "Sat", income: 0, expense: 0 },
        { name: "Sun", income: 0, expense: 0 },
      ],
    };
  }
}

export async function getWeatherData() {
  try {
    const res = await fetch("https://wttr.in/Buenos%20Aires?format=%t|%C|%h|%w");
    if (res.ok) {
      const txt = await res.text();
      const [temp, cond, humidity, wind] = txt.split("|");
      return { temp, cond, humidity, wind };
    }
  } catch {
    return { temp: "--", cond: "No disponible", humidity: "--", wind: "--" };
  }
  return { temp: "--", cond: "No disponible", humidity: "--", wind: "--" };
}

export async function updatePropuestaStatus(id: number, status: "aprobada" | "rechazada") {
  try {
    const supabase = getSupabaseAdmin();
    const { error } = await supabase
      .from("propuestas_automatizacion")
      .update({ estado: status })
      .eq("id", id);

    if (error) throw error;
    return { success: true };
  } catch (e) {
    console.error("Error updating proposal:", e);
    return { success: false };
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

export async function getSystemStatus() {
  try {
    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("preferencias_usuario")
      .select("valor")
      .eq("clave", "modo_sistema")
      .order("fecha_actualizacion", { ascending: false })
      .limit(1);

    if (error) throw error;
    return ((data || []) as PreferenceRow[])[0]?.valor || "Estándar";
  } catch {
    return "Estándar";
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
