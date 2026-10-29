import React, { useEffect, useState } from 'react';
import {
  Layers,
  Play,
  Sliders,
  DollarSign,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  Info,
  TrendingUp,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';
import { OptimizationResult } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const BatchOptimizerPage: React.FC = () => {
  const [batchSize, setBatchSize] = useState(12);
  const [budget, setBudget] = useState(8000.0);
  const [wActivity, setWActivity] = useState(1.0);
  const [wExploration, setWExploration] = useState(0.5);
  const [wNovelty, setWNovelty] = useState(0.8);
  const [wDiversity, setWDiversity] = useState(0.7);
  const [wCost, setWCost] = useState(0.3);
  const [solverMode, setSolverMode] = useState('QPIAI_OPT_AUTO');
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadLatest() {
      const data = await api.getLatestOptimization();
      if (data) setResult(data);
    }
    loadLatest();
  }, []);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const res = await api.runOptimization({
        batch_size: batchSize,
        total_budget: budget,
        weight_activity: wActivity,
        weight_exploration: wExploration,
        weight_novelty: wNovelty,
        weight_diversity: wDiversity,
        weight_cost: wCost,
        solver_mode: solverMode,
        unknown_availability_policy: 'EXCLUDE',
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">QpiAI Opt Combinatorial Batch Selection</h1>
          <p className="text-xs text-slate-400">
            Formulates multi-objective QUBO, penalizes pairwise redundancy, and enforces strict batch & budget constraints.
          </p>
        </div>
        {result && <EvidenceBadge status={result.evidence_status} />}
      </div>

      {/* Optimizer Configuration & Sliders */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-teal-400" />
            <span>Multi-Objective Discovery Trade-Off Weights</span>
          </h2>
          <span className="text-xs text-slate-400">Target: Exact K={batchSize} compounds &le; ${budget.toLocaleString()}</span>
        </div>

        {/* 5 Sliders for Weights */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs mb-1 font-medium text-slate-300">
              <span>Potency (w_act):</span>
              <span className="text-teal-400 font-bold">{wActivity.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={wActivity}
              onChange={(e) => setWActivity(parseFloat(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">Predicted pIC50</span>
          </div>

          <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs mb-1 font-medium text-slate-300">
              <span>Exploration (w_exp):</span>
              <span className="text-sky-400 font-bold">{wExploration.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={wExploration}
              onChange={(e) => setWExploration(parseFloat(e.target.value))}
              className="w-full accent-sky-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">Epistemic Uncertainty</span>
          </div>

          <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs mb-1 font-medium text-slate-300">
              <span>Novelty (w_nov):</span>
              <span className="text-violet-400 font-bold">{wNovelty.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={wNovelty}
              onChange={(e) => setWNovelty(parseFloat(e.target.value))}
              className="w-full accent-violet-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">1 - max Tanimoto(hist)</span>
          </div>

          <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs mb-1 font-medium text-slate-300">
              <span>Diversity (w_div):</span>
              <span className="text-amber-400 font-bold">{wDiversity.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={wDiversity}
              onChange={(e) => setWDiversity(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">Pairwise similarity penalty</span>
          </div>

          <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs mb-1 font-medium text-slate-300">
              <span>Cost (w_cost):</span>
              <span className="text-rose-400 font-bold">{wCost.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={wCost}
              onChange={(e) => setWCost(parseFloat(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">Expense minimization</span>
          </div>
        </div>

        {/* Solver Mode and Capacity */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Batch Size (K)</label>
            <input
              type="number"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value) || 12)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Budget ($ USD)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(parseFloat(e.target.value) || 8000)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Optimization Engine</label>
            <select
              value={solverMode}
              onChange={(e) => setSolverMode(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
            >
              <option value="QPIAI_OPT_AUTO">QpiAI Opt Cloud (Auto / Fallback)</option>
              <option value="CLASSICAL_SA">Simulated Annealing QUBO Heuristic</option>
              <option value="EXHAUSTIVE">Exact Exhaustive Enumeration (N &le; 18)</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-3 border-t border-slate-800">
          <button
            onClick={handleOptimize}
            disabled={loading}
            className="px-6 py-2.5 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{loading ? 'Solving QUBO Problem...' : 'Solve Optimal Batch'}</span>
          </button>
        </div>
      </div>

      {/* Optimization Results */}
      {result && (
        <div className="space-y-6">
          {/* KPI Feasibility Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Selected Batch Size</span>
              <div className="flex items-center space-x-2 mt-1">
                <span className="text-2xl font-bold text-white">{result.selected_count}</span>
                {result.batch_size_satisfied ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                )}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Constraint K satisfied</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Total Assay Cost</span>
              <div className="flex items-center space-x-2 mt-1">
                <span className="text-2xl font-bold text-emerald-400">${result.total_cost.toLocaleString()}</span>
                {result.budget_satisfied ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                )}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Within allocated budget</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Avg Predicted Potency</span>
              <span className="text-2xl font-bold text-white mt-1 block">pIC50 {result.avg_predicted_pic50}</span>
              <span className="text-[10px] text-slate-500 mt-1 block">Mean candidate potency</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Novel Scaffold Coverage</span>
              <span className="text-2xl font-bold text-violet-400 mt-1 block">{result.novel_scaffolds_count} Scaffolds</span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {Math.round((result.novel_scaffolds_count / result.selected_count) * 100)}% unseen series
              </span>
            </div>
          </div>

          {/* Selected Compounds Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">Recommended Experimental Shortlist</h3>
                <p className="text-xs text-slate-400">
                  Molecules selected to maximize expected discovery value while eliminating pairwise structural redundancy.
                </p>
              </div>
              <a
                href={api.getSelectedCsvUrl()}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-medium inline-flex items-center space-x-1"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-teal-400" />
                <span>Export CSV</span>
              </a>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 uppercase tracking-wider text-[11px] text-slate-400">
                  <tr>
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">ID / Source</th>
                    <th className="py-2.5 px-3">Structure SMILES</th>
                    <th className="py-2.5 px-3">Pred pIC50</th>
                    <th className="py-2.5 px-3">Uncertainty</th>
                    <th className="py-2.5 px-3">Novelty</th>
                    <th className="py-2.5 px-3">Scaffold</th>
                    <th className="py-2.5 px-3">Cost</th>
                    <th className="py-2.5 px-3">Marginal Utility</th>
                    <th className="py-2.5 px-3">Scientific Selection Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.selected_compounds.map((c) => (
                    <tr key={c.compound_id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 font-semibold text-teal-400">#{c.rank}</td>
                      <td className="py-2.5 px-3">
                        <div className="font-medium text-white">{c.compound_id}</div>
                        <div className="text-[10px] text-slate-400">{c.source_id}</div>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-300 truncate max-w-xs" title={c.canonical_smiles}>
                        {c.canonical_smiles}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-white">{c.predicted_pic50}</td>
                      <td className="py-2.5 px-3 text-slate-300">&plusmn;{c.uncertainty}</td>
                      <td className="py-2.5 px-3 text-sky-400 font-medium">{c.novelty_score}</td>
                      <td className="py-2.5 px-3 text-violet-300">{c.scaffold_id}</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-medium">${c.cost}</td>
                      <td className="py-2.5 px-3 text-teal-300 font-bold">{c.marginal_utility}</td>
                      <td className="py-2.5 px-3 text-slate-300 max-w-sm">{c.selection_rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

