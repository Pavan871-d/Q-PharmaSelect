import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Play,
  Copy,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Activity,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { QuantumRunResult } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const QuantumLabPage: React.FC = () => {
  const [backend, setBackend] = useState('QpiAI-QSV-Simulator');
  const [numQubits, setNumQubits] = useState(4);
  const [numShots, setNumShots] = useState(1024);
  const [result, setResult] = useState<QuantumRunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadLatest() {
      const data = await api.getLatestQuantumRun();
      if (data) setResult(data);
    }
    loadLatest();
  }, []);

  const handleExecute = async () => {
    setLoading(true);
    try {
      const res = await api.runQuantumExperiment({
        backend_name: backend,
        num_qubits: numQubits,
        num_shots: numShots,
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyQasm = () => {
    if (!result?.qasm_preview) return;
    navigator.clipboard.writeText(result.qasm_preview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">QpiAI Quantum Lab & QCloud</h1>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800">
              SDK v0.7.5
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Molecular feature encoding circuits, multi-qubit entanglement ladders, and hybrid quantum property prediction.
          </p>
        </div>
        {result && <EvidenceBadge status={result.evidence_status} />}
      </div>

      {/* Circuit Execution Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-violet-400" />
          <span>Quantum Circuit & Backend Parameters</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target QpiAI Backend</label>
            <select
              value={backend}
              onChange={(e) => setBackend(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500"
            >
              <option value="QpiAI-QSV-Simulator">QpiAI-QSV-Simulator (Statevector Simulator)</option>
              <option value="QpiAI-QSV-Local">QpiAI-QSV-Local (Local CPU Backend)</option>
              <option value="QpiAI-QDM-Simulator">QpiAI-QDM-Simulator (Density Matrix)</option>
              <option value="QpiAI-Indus-1">QpiAI-Indus-1 (Superconducting QPU)</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-1">
              <span>Quantum Register Width:</span>
              <span className="text-violet-400 font-bold">{numQubits} Qubits</span>
            </div>
            <input
              type="range"
              min="2"
              max="8"
              value={numQubits}
              onChange={(e) => setNumQubits(parseInt(e.target.value))}
              className="w-full accent-violet-500 cursor-pointer mt-1"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-1">
              <span>Measurement Shots:</span>
              <span className="text-violet-400 font-bold">{numShots} shots</span>
            </div>
            <input
              type="range"
              min="256"
              max="4096"
              step="256"
              value={numShots}
              onChange={(e) => setNumShots(parseInt(e.target.value))}
              className="w-full accent-violet-500 cursor-pointer mt-1"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            onClick={handleExecute}
            disabled={loading}
            className="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 text-white font-medium text-xs rounded-xl shadow-lg shadow-violet-500/20 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{loading ? 'Synthesizing & Executing...' : 'Run Quantum Circuit'}</span>
          </button>
        </div>
      </div>

      {/* Execution Results View */}
      {result && (
        <div className="space-y-6">
          {/* Circuit Architecture Diagram */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Quantum Feature Circuit Architecture</h3>
                <p className="text-xs text-slate-400">
                  Angle rotation encoding of principal molecular features with cyclic CNOT entanglement ladder.
                </p>
              </div>
              <span className="text-xs text-violet-300 bg-violet-950/80 px-2.5 py-1 rounded-lg border border-violet-800/60">
                Depth: {result.circuit_depth} | Execution: {result.execution_time_ms} ms
              </span>
            </div>

            {/* Interactive Schematic Diagram */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs overflow-x-auto">
              {Array.from({ length: result.num_qubits }).map((_, q) => (
                <div key={q} className="flex items-center space-x-2">
                  <span className="text-slate-500 w-8">q[{q}]:</span>
                  <div className="flex items-center space-x-1 flex-1">
                    <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800 text-[10px]">
                      H
                    </span>
                    <span className="text-slate-600">&horbar;&horbar;</span>
                    <span className="px-2 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800 text-[10px]">
                      Ry(&theta;_{q})
                    </span>
                    <span className="text-slate-600">&horbar;&horbar;</span>
                    <span className="px-2 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800 text-[10px]">
                      Rz(&phi;_{q})
                    </span>
                    <span className="text-slate-600">&horbar;&horbar;</span>
                    <span className="px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800 text-[10px]">
                      &oplus; CNOT
                    </span>
                    <span className="text-slate-600">&horbar;&horbar;</span>
                    <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px]">
                      [M]
                    </span>
                    <span className="text-slate-700 flex-1">&horbar;&horbar;&horbar;&horbar;&horbar;</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Measurements and Classical Benchmark Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Bitstring Histogram */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-3">
                Measurement Bitstring Distribution ({result.num_shots} shots)
              </h3>
              <div className="space-y-2">
                {Object.entries(result.measurement_counts_summary).map(([bitstring, count]) => {
                  const pct = Math.round((count / result.num_shots) * 100);
                  return (
                    <div key={bitstring} className="text-xs space-y-0.5">
                      <div className="flex justify-between text-slate-300 font-mono">
                        <span>|{bitstring}&rang;</span>
                        <span className="text-slate-400">{count} ({pct}%)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-violet-500 to-teal-400 h-full rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Benchmark Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Quantum Hybrid vs Classical Baseline Comparison
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Both models evaluated on the identical held-out test split under standardized conditions.
              </p>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
                  <span className="text-[10px] text-slate-400 block uppercase">Classical Baseline RMSE</span>
                  <span className="text-xl font-bold text-white mt-1 block">
                    {result.classical_baseline_rmse.toFixed(3)}
                  </span>
                  <span className="text-[10px] text-slate-500 block">R&sup2;: {result.classical_baseline_r2.toFixed(3)}</span>
                </div>

                <div className="bg-violet-950/40 p-3 rounded-xl border border-violet-800/60">
                  <span className="text-[10px] text-violet-300 block uppercase">Quantum Hybrid RMSE</span>
                  <span className="text-xl font-bold text-violet-300 mt-1 block">
                    {result.quantum_hybrid_rmse.toFixed(3)}
                  </span>
                  <span className="text-[10px] text-violet-400 block">R&sup2;: {result.quantum_hybrid_r2.toFixed(3)}</span>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 bg-slate-800/40 p-3 rounded-xl border border-slate-700/50">
                <span className="text-slate-300 font-semibold block mb-0.5">Scientific Evaluation Policy:</span>
                We do not assume quantum advantage automatically. The experiment is successful because it encodes real
                molecular descriptors into valid quantum circuits, executes on supported backends, and compares
                rigorously against classical baselines.
              </div>
            </div>
          </div>

          {/* QASM and Logs Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-semibold text-white">
                <Terminal className="w-4 h-4 text-violet-400" />
                <span>Generated OpenQASM 2.0 Circuit Code</span>
              </div>
              <button
                onClick={handleCopyQasm}
                className="text-xs text-violet-300 hover:text-white flex items-center space-x-1"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copied ? 'Copied!' : 'Copy QASM'}</span>
              </button>
            </div>
            <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-48 scrollbar-thin">
              {result.qasm_preview}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

