import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  Play,
  CheckCircle2,
  TrendingUp,
  DollarSign,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { ValidationResult } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const RetrospectivePage: React.FC = () => {
  const [valResult, setValResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadLatest() {
      const data = await api.getLatestValidation();
      if (data) setValResult(data);
    }
    loadLatest();
  }, []);

  const handleRunValidation = async () => {
    setLoading(true);
    try {
      const res = await api.runValidation();
      setValResult(res);
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
          <h1 className="text-xl font-bold text-white tracking-tight">Retrospective Assay Validation</h1>
          <p className="text-xs text-slate-400">
            Simulates prospective screening on held-out experimental outcomes and benchmarks against classical baselines.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {valResult && <EvidenceBadge status={valResult.evidence_status} />}
          <button
            onClick={handleRunValidation}
            disabled={loading}
            className="px-4 py-2 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{loading ? 'Evaluating Held-out Labels...' : 'Execute Validation'}</span>
          </button>
        </div>
      </div>

      {/* Scientific Integrity & Leakage Protocol Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
        <div className="flex items-center space-x-2 text-teal-400 font-semibold text-xs uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4" />
          <span>Leakage-Resistant Protocol Guaranteed</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Held-out experimental activity values were excluded from model training, feature selection, uncertainty estimation,
          and QUBO batch optimization. Experimental outcomes were revealed strictly during this evaluation step to calculate
          unbiased Enrichment Factor (EF), Hit Rate, and Novel Scaffold Coverage.
        </p>
      </div>

      {valResult && (
        <div className="space-y-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Enrichment Factor (EF)</span>
              <span className="text-3xl font-bold text-emerald-400 mt-1 block">
                {valResult.selected_batch_enrichment_factor.toFixed(2)}x
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">vs overall hit prevalence</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Observed Hit Rate</span>
              <span className="text-3xl font-bold text-teal-300 mt-1 block">
                {Math.round(valResult.selected_batch_hit_rate * 100)}%
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {valResult.selected_batch_observed_hits} / {valResult.evaluated_batch_size} hits verified
              </span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Novel Scaffold %</span>
              <span className="text-3xl font-bold text-violet-400 mt-1 block">
                {valResult.selected_batch_novel_scaffold_pct}%
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                {valResult.selected_batch_novel_scaffolds} new chemotypes discovered
              </span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Cost Efficiency</span>
              <span className="text-3xl font-bold text-white mt-1 block">
                {valResult.selected_batch_cost_efficiency.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">Observed hits per $1,000 USD</span>
            </div>
          </div>

          {/* Benchmark Comparison Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-semibold text-white">Comparative Baseline Performance on Identical Candidate Pool</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 uppercase tracking-wider text-[11px] text-slate-400">
                  <tr>
                    <th className="py-3 px-4">Selection Strategy</th>
                    <th className="py-3 px-4">Enrichment Factor</th>
                    <th className="py-3 px-4">Hit Rate</th>
                    <th className="py-3 px-4">Observed Hits</th>
                    <th className="py-3 px-4">Novel Scaffolds</th>
                    <th className="py-3 px-4">Diversity Ratio</th>
                    <th className="py-3 px-4">Total Cost</th>
                    <th className="py-3 px-4">Hits / $1,000</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {valResult.baselines.map((b, i) => {
                    const isOptimal = b.strategy_name.includes('QUBO') || b.strategy_name.includes('Optimizer');
                    return (
                      <tr key={i} className={isOptimal ? 'bg-teal-950/20 font-medium' : 'hover:bg-slate-800/40'}>
                        <td className="py-3 px-4 flex items-center space-x-2">
                          {isOptimal && <CheckCircle2 className="w-4 h-4 text-teal-400" />}
                          <span className={isOptimal ? 'text-teal-300 font-bold' : 'text-white'}>
                            {b.strategy_name}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-bold text-white">{b.enrichment_factor.toFixed(2)}x</td>
                        <td className="py-3 px-4 text-slate-200">{(b.hit_rate * 100).toFixed(1)}%</td>
                        <td className="py-3 px-4 text-emerald-400 font-semibold">{b.observed_hits}</td>
                        <td className="py-3 px-4 text-violet-300">{b.novel_scaffold_count}</td>
                        <td className="py-3 px-4">{b.scaffold_diversity_ratio}</td>
                        <td className="py-3 px-4 text-slate-300">${b.total_cost.toLocaleString()}</td>
                        <td className="py-3 px-4 text-emerald-300 font-bold">{b.cost_per_hit > 0 ? (1000 / b.cost_per_hit).toFixed(2) : '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Visual Bar Comparison Chart */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Enrichment Factor (EF) Comparison Chart</h3>
            <div className="space-y-4">
              {valResult.baselines.map((b, idx) => {
                const maxEf = Math.max(...valResult.baselines.map((x) => x.enrichment_factor), 2.0);
                const widthPct = Math.min(100, Math.round((b.enrichment_factor / maxEf) * 100));
                const isOpt = b.strategy_name.includes('QUBO') || b.strategy_name.includes('Optimizer');

                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className={isOpt ? 'font-bold text-teal-300' : 'text-slate-300'}>
                        {b.strategy_name}
                      </span>
                      <span className="font-bold text-white">{b.enrichment_factor.toFixed(2)}x</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isOpt ? 'bg-gradient-to-r from-teal-500 to-teal-400' : 'bg-slate-600'
                        }`}
                        style={{ width: `${widthPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

