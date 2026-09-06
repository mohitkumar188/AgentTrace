"use client";

import { useEffect, useState, useRef } from "react";
import { Activity, AlertTriangle, CheckCircle, Clock, RefreshCw, Terminal, GitCompare } from "lucide-react";

interface TraceStep {
  session_id: string;
  step_number: number;
  step_name: string;
  step_type: string;
  inputs: any;
  original_inputs?: any;
  output: any;
  latency_ms: number;
  status: string;
  was_healed: boolean;
  heal_notes: string;
  timestamp: string;
}

export default function AgentDashboard() {
  const [sessions, setSessions] = useState<{ [key: string]: TraceStep[] }>({});
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const selectedSessionRef = useRef<string | null>(null);

  // Keep ref synced with current selection to prevent poll overrides
  useEffect(() => {
    selectedSessionRef.current = selectedSession;
  }, [selectedSession]);

  const fetchTraces = async (isManual = false) => {
    if (isManual) setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://agenttrace-api-cdav.onrender.com";
      const res = await fetch(`${apiUrl}/api/v1/sessions`);
      const data = await res.json();
      const newSessions = data.sessions || {};
      setSessions(newSessions);

      // Only set initial session on very first load if none selected
      if (!selectedSessionRef.current) {
        const sessionKeys = Object.keys(newSessions);
        if (sessionKeys.length > 0) {
          const latest = sessionKeys[sessionKeys.length - 1];
          setSelectedSession(latest);
          selectedSessionRef.current = latest;
        }
      }
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    } finally {
      if (isManual) setLoading(false);
    }
  };

  useEffect(() => {
    fetchTraces(true);
    const interval = setInterval(() => {
      fetchTraces(false);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const currentSteps = selectedSession ? sessions[selectedSession] || [] : [];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans p-6">
      <header className="flex justify-between items-center pb-6 border-b border-neutral-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="text-emerald-400 w-6 h-6" /> Agent DevTools & Observability
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Real-time traces, multi-step agent debugging, and self-healing payload diff inspector
          </p>
        </div>
        <button
          onClick={() => fetchTraces(true)}
          className="flex items-center gap-2 bg-neutral-800 hover:bg-neutral-700 text-sm px-4 py-2 rounded-md transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </header>

      <div className="grid grid-cols-12 gap-6 mt-6">
        {/* Sessions Sidebar */}
        <div className="col-span-4 bg-neutral-900/60 border border-neutral-800 rounded-lg p-4 h-[calc(100vh-160px)] overflow-y-auto">
          <h2 className="text-sm font-semibold uppercase text-neutral-400 tracking-wider mb-3">
            Execution Sessions
          </h2>
          <div className="space-y-2">
            {Object.keys(sessions).length === 0 ? (
              <p className="text-neutral-500 text-sm">No agent sessions recorded yet.</p>
            ) : (
              Object.keys(sessions).map((sid) => {
                const steps = sessions[sid];
                const hasHealing = steps.some((s) => s.was_healed);
                const isSelected = selectedSession === sid;
                return (
                  <button
                    key={sid}
                    onClick={() => {
                      setSelectedSession(sid);
                      selectedSessionRef.current = sid;
                    }}
                    className={`w-full text-left p-3 rounded-md border text-sm transition flex flex-col gap-1 ${isSelected
                        ? "bg-neutral-800 border-emerald-500"
                        : "bg-neutral-900 border-neutral-800 hover:border-neutral-700"
                      }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-xs text-neutral-200 font-semibold">{sid}</span>
                      {hasHealing && (
                        <span className="bg-amber-500/20 text-amber-400 text-[10px] px-2 py-0.5 rounded border border-amber-500/30">
                          Auto-Healed
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-neutral-500">
                      {steps.length} Steps • {steps.reduce((acc, s) => acc + s.latency_ms, 0).toFixed(0)} ms total
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Steps Trace Flow */}
        <div className="col-span-8 space-y-4 h-[calc(100vh-160px)] overflow-y-auto pr-2">
          {currentSteps.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 border border-dashed border-neutral-800 rounded-lg text-neutral-500">
              <Terminal className="w-8 h-8 mb-2" />
              <p>Select a session to inspect step traces</p>
            </div>
          ) : (
            currentSteps.map((step) => {
              // Extract healed clean kwargs safely
              const healedPayload = step.inputs?.kwargs ? step.inputs.kwargs : step.inputs;
              const hasDiff = Boolean(step.was_healed && step.original_inputs);

              return (
                <div
                  key={`${step.session_id}_${step.step_number}`}
                  className={`bg-neutral-900/80 border rounded-lg p-5 transition ${step.was_healed ? "border-amber-500/40" : "border-neutral-800"
                    }`}
                >
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono bg-neutral-800 px-2 py-1 rounded text-neutral-400">
                        Step #{step.step_number}
                      </span>
                      <h3 className="font-semibold text-white font-mono text-base">{step.step_name}</h3>
                      <span className="text-[11px] bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded uppercase font-semibold">
                        {step.step_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 text-xs text-neutral-400">
                        <Clock className="w-3.5 h-3.5" /> {step.latency_ms} ms
                      </span>
                      {step.status === "success" ? (
                        <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                          <CheckCircle className="w-3 h-3" /> success
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
                          <AlertTriangle className="w-3 h-3" /> {step.status}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Self-Healing Callout */}
                  {step.was_healed && (
                    <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-300">
                      <strong className="font-semibold flex items-center gap-1 mb-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> Self-Healing Active
                      </strong>
                      <p className="font-mono text-[11px] text-amber-200/90 leading-relaxed">{step.heal_notes}</p>
                    </div>
                  )}

                  {/* Payload Diff Inspector */}
                  {hasDiff ? (
                    <div className="mb-4 p-3 bg-neutral-950 border border-neutral-800 rounded-lg">
                      <div className="flex items-center gap-2 text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
                        <GitCompare className="w-4 h-4 text-amber-400" /> Payload Diff Inspector
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="text-rose-400 font-semibold mb-1 block">Original (Malformed Payload)</span>
                          <pre className="bg-rose-950/20 border border-rose-500/30 p-3 rounded font-mono text-rose-200 overflow-x-auto max-h-40">
                            {JSON.stringify(step.original_inputs, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <span className="text-emerald-400 font-semibold mb-1 block">Healed (Schema-Compliant)</span>
                          <pre className="bg-emerald-950/20 border border-emerald-500/30 p-3 rounded font-mono text-emerald-200 overflow-x-auto max-h-40">
                            {JSON.stringify(healedPayload, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {/* Standard Inputs (Shown if NOT healed or if diff unavailable) */}
                  {!hasDiff && (
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-neutral-500 font-semibold mb-1 block">INPUT ARGS</span>
                        <pre className="bg-black/60 p-3 rounded border border-neutral-800/80 font-mono text-neutral-300 overflow-x-auto max-h-40">
                          {JSON.stringify(step.inputs, null, 2)}
                        </pre>
                      </div>
                      <div>
                        <span className="text-neutral-500 font-semibold mb-1 block">OUTPUT RESULT</span>
                        <pre className="bg-black/60 p-3 rounded border border-neutral-800/80 font-mono text-emerald-400/90 overflow-x-auto max-h-40">
                          {JSON.stringify(step.output, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Output for Healed Step */}
                  {hasDiff && (
                    <div className="mt-3 text-xs">
                      <span className="text-neutral-500 font-semibold mb-1 block">FINAL EXECUTION RESULT</span>
                      <pre className="bg-black/60 p-3 rounded border border-neutral-800/80 font-mono text-emerald-400/90 overflow-x-auto max-h-32">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}