"use client";

import React, { useState, useEffect } from 'react';
import { 
  Activity, Shield, Mic, Cpu, Cloud, Database, 
  Wifi, Camera, BatteryCharging, ChevronRight, 
  Bitcoin, TrendingUp, AlertCircle
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

import { getFinancialData } from './actions';

// Util for tailwind class merging
function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

const cryptoData = [
  { time: '10:00', price: 61200 },
  { time: '12:00', price: 61500 },
  { time: '14:00', price: 62100 },
  { time: '16:00', price: 61850 },
  { time: '18:00', price: 62400 },
  { time: '20:00', price: 62800 },
];

export default function Dashboard() {
  const [time, setTime] = useState(new Date());
  
  // Real data states
  const [btcPrice, setBtcPrice] = useState<number | null>(null);
  const [btcChange, setBtcChange] = useState<number>(0);
  
  const [financeData, setFinanceData] = useState<any[]>([
    { name: '-', income: 0, expense: 0 }
  ]);
  const [totalBalance, setTotalBalance] = useState<number>(0);
  const [mtdExpense, setMtdExpense] = useState<number>(0);
  const [dbStatus, setDbStatus] = useState<string>("Offline");
  
  const [logs, setLogs] = useState<any[]>([]);
  const [propuestas, setPropuestas] = useState<any[]>([]);
  
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch BTC logic
  useEffect(() => {
    const fetchBtc = async () => {
      try {
        // Fetch Binance 24hr ticker to get current price and percent change
        const res = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
        if (res.ok) {
          const data = await res.json();
          setBtcPrice(parseFloat(data.lastPrice));
          setBtcChange(parseFloat(data.priceChangePercent));
          return;
        }
      } catch (err) {
        console.error("Binance fallback needed");
      }
      
      // CoinGecko fallback (doesn't give 24h change as easily but gives price)
      try {
        const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
        if (res.ok) {
          const data = await res.json();
          setBtcPrice(parseFloat(data.bitcoin.usd));
          setBtcChange(parseFloat(data.bitcoin.usd_24h_change));
        }
      } catch (err) {
        console.error("CoinGecko fallback failed");
      }
    };
    
    fetchBtc();
    // Update every 15 seconds
    const interval = setInterval(fetchBtc, 15000);
    return () => clearInterval(interval);
  }, []);

  // Fetch DB Finance logic
  useEffect(() => {
    const fetchDb = async () => {
      try {
        const data = await getFinancialData();
        setTotalBalance(data.totalBalance);
        setMtdExpense(data.mtdExpense);
        setFinanceData(data.chartData);
        setLogs(data.logs || []);
        setPropuestas(data.propuestas || []);
        setDbStatus("Online");
      } catch(err) {
        setDbStatus("Failed");
      }
    };
    fetchDb();
    // Refresh DB logic every 30 secs
    const dbInterval = setInterval(fetchDb, 30000);
    return () => clearInterval(dbInterval);
  }, []);

  return (
    <div className="h-screen overflow-hidden p-4 md:p-6 flex flex-col gap-4 selection:bg-[var(--color-jarvis-cyan)] selection:text-black">
      
      {/* HEADER TOP BAR */}
      <header className="flex justify-between items-center glass-panel rounded-2xl px-6 py-4 neon-border">
        <div className="flex items-center gap-3">
          <Cpu className="text-[var(--color-jarvis-cyan)] glow-active" size={28} />
          <div>
            <h1 className="text-xl font-bold tracking-widest text-[#e5e7eb] uppercase">JARVIS SYSTEM</h1>
            <p className="text-xs text-[#06b6d4] font-mono tracking-wider">M.A.I.N. FRAME ONLINE</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6 font-mono text-sm">
          <div className="flex flex-col items-end">
            <span className="text-[#9ca3af]">LOCAL TIME</span>
            <span className="text-[#e5e7eb] text-lg font-semibold tabular-nums">
              {time.toLocaleTimeString('es-AR', { hour12: false })}
            </span>
          </div>
          <div className="h-10 w-px bg-white/10 hidden md:block" />
          <div className="hidden md:flex gap-4">
            <StatusIcon icon={Wifi} active color="cyan" label="NET" />
            <StatusIcon icon={Database} active={dbStatus === 'Online'} color="cyan" label="DB" />
            <StatusIcon icon={Camera} active color="orange" label="SEC" />
          </div>
        </div>
      </header>

       {/* MAIN GRID */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0 overflow-hidden">
        
        {/* LEFT COLUMN */}
        <div className="lg:col-span-3 flex flex-col gap-4 h-full overflow-hidden">
          <Card title="PROTOCOL STATUS" icon={Shield}>
            <ul className="space-y-4">
              <StatusCheck label="Centinela Security" status="Online" color="cyan" />
              <StatusCheck label="Home Automation" status="Active" color="cyan" />
              <StatusCheck label="Predictive Engine" status="Learning" color="orange" />
              <StatusCheck label="Cloud Backups" status="Synced" color="cyan" />
            </ul>
             <div className="mt-6 pt-4 border-t border-white/10">
              <button className="w-full flex items-center justify-between px-4 py-2 glass-panel rounded hover:bg-white/5 transition-colors border border-white/5 group">
                <span className="text-xs font-mono uppercase tracking-wider text-[var(--color-jarvis-orange)]">Initiate Protocol</span>
                <ChevronRight size={16} className="text-[var(--color-jarvis-orange)] group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </Card>

          <Card title="DAILY BRIEFING" icon={Cloud}>
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-[var(--color-jarvis-panel)] border border-white/5">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-mono text-[var(--color-jarvis-muted)]">WEATHER</span>
                  <span className="text-xs text-[var(--color-jarvis-cyan)]">BUENOS AIRES</span>
                </div>
                <div className="text-2xl font-bold flex items-end gap-2">
                  18°C <span className="text-sm font-normal text-[var(--color-jarvis-muted)] mb-1">Clear</span>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-[var(--color-jarvis-panel)] border border-white/5">
                <div className="flex items-start gap-3">
                  <AlertCircle size={18} className="text-[var(--color-jarvis-orange)] mt-0.5 shrink-0" />
                  <p className="text-sm text-gray-300">
                    Sir, your schedule is clear for today. I suggest reviewing the recent transactions.
                  </p>
                </div>
              </div>
            </div>
          </Card>

          <Card title="CEREBRO ML - PROPUESTAS" icon={Cpu}>
            <div className="space-y-4">
              {propuestas.length > 0 ? propuestas.map((p, i) => (
                <div key={i} className="p-3 rounded-lg bg-[var(--color-jarvis-panel)] border border-[var(--color-jarvis-orange)]/30 opacity-90 text-sm mb-2 glow-active shadow-[0_0_10px_rgba(249,115,22,0.1)]">
                  <div className="flex justify-between font-mono text-[10px] text-[var(--color-jarvis-orange)] mb-1 uppercase tracking-widest">
                    <span>REGLA PENDIENTE</span>
                    <span>{new Date(p.fecha).toLocaleDateString('es-AR')}</span>
                  </div>
                  <p className="text-[#e5e7eb] leading-tight text-xs">{p.descripcion}</p>
                </div>
              )) : (
                 <p className="text-sm font-mono text-center text-[var(--color-jarvis-muted)] p-4 opacity-70">Detectando patrones de comportamiento...</p>
              )}
            </div>
          </Card>
        </div>

        {/* CENTER COLUMN (THE AI CORE) */}
        <div className="lg:col-span-6 flex flex-col gap-4 items-center justify-center relative h-full">
          {/* Orbital rings */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
            <div className="w-[80%] h-[80%] max-w-[500px] border border-[var(--color-jarvis-cyan)]/20 rounded-full animate-[spin_60s_linear_infinite]" />
            <div className="absolute w-[60%] h-[60%] max-w-[350px] border border-[var(--color-jarvis-orange)]/10 rounded-full animate-[spin_40s_linear_infinite_reverse]" />
            <div className="absolute w-[40%] h-[40%] max-w-[200px] border border-[var(--color-jarvis-cyan)]/30 rounded-full animate-[spin_20s_linear_infinite]" />
          </div>

          <div 
            className="relative z-10 text-center glass-panel p-8 rounded-full border border-[var(--color-jarvis-cyan)]/30 w-64 h-64 flex flex-col items-center justify-center glow-active cursor-pointer hover:scale-105 transition-transform duration-500 group"
            onClick={() => alert("Módulo de voz web en desarrollo. ¡Por favor usa el audio de Telegram para comunicarte con JARVIS por ahora!")}
          >
            <div className="absolute inset-0 rounded-full bg-[var(--color-jarvis-cyan)]/5 blur-xl group-hover:bg-[var(--color-jarvis-cyan)]/20 transition-colors duration-500" />
            <Mic className="text-[var(--color-jarvis-cyan)] mb-4" size={48} />
            <h2 className="text-2xl font-light tracking-widest text-white">LISTENING</h2>
            <div className="flex gap-1 mt-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="w-1.5 bg-[var(--color-jarvis-cyan)] rounded-full animate-pulse" style={{ height: `${Math.max(10, Math.random() * 24)}px`, animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="lg:col-span-3 flex flex-col gap-4 h-full overflow-hidden">
          <Card title="CRYPTO WATCH" icon={Bitcoin}>
            <div className="mb-4">
               <div className="text-xs font-mono text-[var(--color-jarvis-muted)] mb-1">BTC/USDT</div>
               <div className="text-3xl font-bold text-white flex items-center gap-2">
                 {btcPrice ? `$${btcPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'Calculating...'}
                 {btcPrice !== null && (
                   <span className={cn("text-sm flex items-center px-2 py-0.5 rounded", btcChange >= 0 ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10")}>
                     {btcChange >= 0 ? <TrendingUp size={14} className="mr-1" /> : null}
                     {btcChange > 0 ? '+' : ''}{btcChange.toFixed(2)}%
                   </span>
                 )}
               </div>
            </div>
            <div className="h-32 -mx-4 -mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={cryptoData}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-jarvis-cyan)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--color-jarvis-cyan)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="price" stroke="var(--color-jarvis-cyan)" fillOpacity={1} fill="url(#colorPrice)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="FINANCE METRICS" icon={Activity}>
             <div className="flex justify-between items-center mb-6">
               <div>
                  <div className="text-xs font-mono text-[#9ca3af]">TOTAL BALANCE</div>
                  <div className="text-xl text-white">${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
               </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-[#9ca3af]">M.T.D EXPENSE</div>
                  <div className="text-xl text-[var(--color-jarvis-orange)]">${mtdExpense.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
               </div>
             </div>
             
             <div className="h-40 -mx-4 -mb-2 mt-4">
               <ResponsiveContainer width="100%" height="100%">
                <LineChart data={financeData}>
                  <XAxis dataKey="name" stroke="#4b5563" fontSize={10} axisLine={false} tickLine={false} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    itemStyle={{ color: '#e5e7eb' }}
                  />
                  <Line type="monotone" dataKey="income" stroke="var(--color-jarvis-cyan)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="expense" stroke="var(--color-jarvis-orange)" strokeWidth={2} dot={false} />
                </LineChart>
               </ResponsiveContainer>
             </div>
          </Card>

          <Card title="TELEMETRÍA EN VIVO" icon={Activity}>
             <div className="font-mono text-[10px] flex-1 overflow-y-auto space-y-1 pr-2 tracking-tight overflow-x-hidden custom-scrollbar max-h-[250px]">
                {logs.length > 0 ? logs.map((l, i) => (
                  <div key={i} className="flex gap-2 border-b border-white/5 py-1.5 opacity-80 hover:opacity-100 transition-opacity">
                    <span className="text-[var(--color-jarvis-cyan)] whitespace-nowrap">
                      [{new Date(l.fecha).toLocaleTimeString('es-AR', {hour: '2-digit', minute:'2-digit', second:'2-digit'})}]
                    </span>
                    <span className="text-gray-300 break-words">{l.evento}</span>
                  </div>
                )) : (
                  <p className="text-center text-[var(--color-jarvis-muted)] opacity-50 pt-4">No hay datos telemétricos.</p>
                )}
             </div>
          </Card>
        </div>

      </main>
    </div>
  );
}

// Subcomponents

function Card({ title, icon: Icon, children }: { title: string, icon: any, children: React.ReactNode }) {
  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col relative overflow-hidden group">
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-[var(--color-jarvis-cyan)] to-transparent opacity-50" />
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/10 border-dashed">
        <h3 className="font-mono text-sm tracking-widest text-[#e5e7eb]">{title}</h3>
        <Icon size={16} className="text-[var(--color-jarvis-cyan)]" />
      </div>
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}

function StatusIcon({ icon: Icon, active, color, label }: { icon: any, active: boolean, color: 'cyan' | 'orange', label: string }) {
  const colorClass = color === 'cyan' ? 'text-[var(--color-jarvis-cyan)]' : 'text-[var(--color-jarvis-orange)]';
  return (
    <div className="flex flex-col items-center gap-1 opacity-80 hover:opacity-100 transition-opacity">
      <Icon size={20} className={cn(active && colorClass, active && "glow-active")} />
      <span className="text-[10px] tracking-widest">{label}</span>
    </div>
  );
}

function StatusCheck({ label, status, color }: { label: string, status: string, color: 'cyan'|'orange' }) {
  const colorClass = color === 'cyan' ? 'text-[var(--color-jarvis-cyan)]' : 'text-[var(--color-jarvis-orange)]';
  const glowBorderClass = color === 'cyan' ? 'border-[var(--color-jarvis-cyan)]/30' : 'border-[var(--color-jarvis-orange)]/30';
  
  return (
    <li className="flex justify-between items-center text-sm font-mono cursor-default hover:bg-white/5 p-1 -mx-1 rounded transition-colors group">
      <span className="text-[#9ca3af] group-hover:text-white transition-colors">{label}</span>
      <div className="flex items-center gap-2">
        <span className={cn(colorClass, "text-xs tracking-wider uppercase")}>{status}</span>
        <div className={cn("w-2 h-2 rounded-full border shadow-sm", colorClass.replace('text-', 'bg-'), glowBorderClass, "opacity-80 animate-pulse")} />
      </div>
    </li>
  );
}
