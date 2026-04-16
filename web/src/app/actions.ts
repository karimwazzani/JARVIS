"use server";

import postgres from 'postgres';

const sql = postgres(process.env.DATABASE_URL || '', { ssl: 'require' });

export async function getFinancialData() {
  try {
    // 1. Get total balance
    const balanceResult = await sql`
      SELECT 
        SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) as total_ingresos,
        SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) as total_gastos
      FROM transacciones
    `;
    
    const ingresos = balanceResult[0]?.total_ingresos || 0;
    const gastos = balanceResult[0]?.total_gastos || 0;
    const totalBalance = ingresos - gastos;

    // 2. Get M.T.D Expense (Month to Date)
    const mtdResult = await sql`
      SELECT SUM(monto) as mtd_gasto
      FROM transacciones 
      WHERE tipo = 'gasto' AND date_trunc('month', fecha) = date_trunc('month', CURRENT_DATE)
    `;
    const mtdExpense = mtdResult[0]?.mtd_gasto || 0;

    // 3. Get Last 7 days data for chart
    const chartResult = await sql`
      WITH RECURSIVE days AS (
          SELECT current_date - 6 AS d
          UNION ALL
          SELECT d + 1 FROM days WHERE d < current_date
      )
      SELECT 
          to_char(days.d, 'Dy') as name,
          COALESCE(SUM(CASE WHEN t.tipo = 'ingreso' THEN t.monto ELSE 0 END), 0) as income,
          COALESCE(SUM(CASE WHEN t.tipo = 'gasto' THEN t.monto ELSE 0 END), 0) as expense
      FROM days
      LEFT JOIN transacciones t ON date_trunc('day', t.fecha)::date = days.d
      GROUP BY days.d
      ORDER BY days.d;
    `;
    
    const chartData = chartResult.map(row => ({
      name: row.name,
      income: Number(row.income),
      expense: Number(row.expense)
    }));

    // 4. Obtener Telemetría (Últimos 10 eventos)
    const logsResult = await sql`
      SELECT evento, fecha
      FROM log_eventos
      ORDER BY fecha DESC
      LIMIT 10
    `;

    // 5. Obtener Propuestas de Automatización pendientes
    const propuestasResult = await sql`
      SELECT id, descripcion, accion_tecnica, fecha_creacion
      FROM propuestas_automatizacion
      WHERE estado = 'pendiente'
      ORDER BY fecha_creacion DESC
      LIMIT 10
    `;

    // 6. Obtener próximos eventos de calendario
    const calendarResult = await sql`
      SELECT titulo, fecha_hora, ubicacion
      FROM eventos_calendario
      WHERE fecha_hora >= NOW()
      ORDER BY fecha_hora ASC
      LIMIT 5
    `;

    return {
      totalBalance,
      mtdExpense,
      chartData,
      logs: logsResult.map(l => ({ evento: l.evento, fecha: l.fecha.toISOString() })),
      propuestas: propuestasResult.map(p => ({ 
        id: p.id,
        descripcion: p.descripcion, 
        tecnica: p.accion_tecnica, 
        fecha: p.fecha_creacion.toISOString() 
      })),
      calendar: calendarResult.map(e => ({
        titulo: e.titulo,
        fecha: e.fecha_hora.toISOString(),
        ubicacion: e.ubicacion
      }))
    };
  } catch (error) {
    console.error("Failed to fetch database data:", error);
    // Return empty fallback info if connection fails
    return {
      totalBalance: 0,
      mtdExpense: 0,
      logs: [],
      propuestas: [],
      chartData: [
        { name: 'Mon', income: 0, expense: 0 },
        { name: 'Tue', income: 0, expense: 0 },
        { name: 'Wed', income: 0, expense: 0 },
        { name: 'Thu', income: 0, expense: 0 },
        { name: 'Fri', income: 0, expense: 0 },
        { name: 'Sat', income: 0, expense: 0 },
        { name: 'Sun', income: 0, expense: 0 },
      ]
    };
  }
}

export async function getWeatherData() {
  try {
    const res = await fetch('https://wttr.in/Buenos%20Aires?format=%t|%C|%h|%w');
    if (res.ok) {
      const txt = await res.text();
      const [temp, cond, humidity, wind] = txt.split('|');
      return { temp, cond, humidity, wind };
    }
  } catch (e) {
    return { temp: "--", cond: "No disponible", humidity: "--", wind: "--" };
  }
  return { temp: "--", cond: "No disponible", humidity: "--", wind: "--" };
}

export async function updatePropuestaStatus(id: number, status: 'aprobada' | 'rechazada') {
  try {
    await sql`
      UPDATE propuestas_automatizacion 
      SET estado = ${status}
      WHERE id = ${id}
    `;
    return { success: true };
  } catch (e) {
    console.error("Error updating proposal:", e);
    return { success: false };
  }
}

export async function clearAllLogs() {
  try {
    await sql`DELETE FROM log_eventos`;
    return { success: true };
  } catch (e) {
    return { success: false };
  }
}

export async function addQuickTransaction(monto: number, descripcion: string, tipo: 'gasto' | 'ingreso' = 'gasto') {
  try {
    await sql`
      INSERT INTO transacciones (tipo, monto, descripcion, fecha)
      VALUES (${tipo}, ${monto}, ${descripcion}, NOW())
    `;
    return { success: true };
  } catch (e) {
    return { success: false };
  }
}

export async function getSystemStatus() {
  try {
    const res = await sql`
      SELECT valor FROM preferencias_usuario 
      WHERE clave = 'modo_sistema'
      ORDER BY fecha_actualizacion DESC LIMIT 1
    `;
    return res[0]?.valor || "Estándar";
  } catch (e) {
    return "Estándar";
  }
}

export async function setSystemMode(modo: string) {
  try {
    // Usamos DELETE + INSERT para asegurar actualización sin depender de constraints de unicidad
    await sql`DELETE FROM preferencias_usuario WHERE clave = 'modo_sistema'`;
    await sql`
      INSERT INTO preferencias_usuario (chat_id, clave, valor, fecha_actualizacion)
      VALUES ('general', 'modo_sistema', ${modo}, NOW())
    `;
    // Log the change
    await sql`INSERT INTO log_eventos (chat_id, evento, fecha) VALUES ('system', ${'Cambio de modo a: ' + modo}, NOW())`;
    return { success: true };
  } catch (e) {
    console.error("Error setting mode:", e);
    return { success: false };
  }
}
