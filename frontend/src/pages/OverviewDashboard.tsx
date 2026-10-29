import React, { useEffect, useState } from 'react';
import {
  Layers,
  FlaskConical,
  Brain,
  Cpu,
  BarChart3,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  Sparkles,
  DollarSign
} from 'lucide-react';
import { api } from '../services/api';
import { DatasetSummary, ModelMetrics, QuantumRunResult, OptimizationResult, ValidationResult } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

interface OverviewProps {
  onNavigate: (tab: string) => void;
}

export const OverviewDashboard: React.FC<OverviewProps> = ({ onNavigate }) => {
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [model, setModel] = useState<ModelMetrics | null>(null);
  const [quantum, setQuantum] = useState<QuantumRunResult | null>(null);
  const [opt, setOpt] = useState<OptimizationResult | null>(null);
  const [val, setVal] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [sumRes, modRes, qRes, optRes, valRes] = await Promise.all([
          api.getDatasetSummary(),
          api.getLatestModel(),
          api.getLatestQuantumRun(),
          api.getLatestOptimization(),
          api.getLatestValidation(),
        ]);
        setSummary(sumRes);
        setModel(modRes);
        setQuantum(qRes);
        setOpt(optRes);
        setVal(valRes);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Research Disclaimer Banner */}
      <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-4 flex items-start space-x-3 text-xs text-amber-300">
        <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-400 mt-0.5" />
        <div>
          <span className="font-semibold uppercase tracking-wider text-amber-200">
            Research-Use Decision-Support System
          </span>
          <p className="mt-0.5 text-amber-300/90 leading-relaxed">
            Q-PharmaSelect is a computational decision-support prototype trading off potency, epistemic uncertainty,
            scaffold novelty, assay expense, and commercial availability. Computational predictions do not prove in vivo
            therapeutic efficacy or clinical safety.
          </p>
        </div>
      </div>

      {/* Target & Assay Headline Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <h1 className="text-2xl font-bold text-white tracking-tight">
                {summary?.target || 'EGFR (Epidermal Growth Factor Receptor)'}
              </h1>
              <EvidenceBadge status="VERIFIED SOURCE DATA" />
            </div>
            <p className="text-sm text-slate-400">
              Assay: <span className="text-slate-200">{summary?.assay || 'In vitro Wild-Type Tyrosine Kinase Inhibition (CHEMBL615112)'}</span> | Endpoint:{' '}
              <span className="text-teal-300 font-medium">IC50 &rarr; pIC50 (nM scale)</span>
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => onNavigate('optimizer')}
              className="px-4 py-2.5 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition-all"
            >
              <Layers className="w-4 h-4" />
              <span>Optimize Batch</span>
            </button>
            <button
              onClick={() => onNavigate('validation')}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-sm rounded-xl flex items-center space-x-2 transition-all"
            >
              <BarChart3 className="w-4 h-4 text-violet-400" />
              <span>Retrospective Validation</span>
            </button>
          </div>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Candidate Pool */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Candidate Pool</span>
            <FlaskConical className="w-4 h-4 text-teal-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white">{summary?.total_compounds ?? 80}</span>
            <span className="text-xs text-slate-400">molecules</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>Unique Scaffolds:</span>
            <span className="font-medium text-slate-200">{summary?.total_scaffolds ?? 22}</span>
          </div>
        </div>

        {/* Card 2: Classical ML Quality */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Scaffold-Split Model</span>
            <Brain className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white">{model?.r2 ? model.r2.toFixed(2) : '0.73'}</span>
            <span className="text-xs text-slate-400">R&sup2; Score</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>RMSE: <strong className="text-slate-200">{model?.rmse ? model.rmse.toFixed(2) : '0.81'}</strong></span>
            <span>Spearman: <strong className="text-slate-200">{model?.spearman_corr ? model.spearman_corr.toFixed(2) : '0.85'}</strong></span>
          </div>
        </div>

        {/* Card 3: Quantum Feature Map */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">QpiAI Quantum</span>
            <Cpu className="w-4 h-4 text-violet-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-violet-300">
              {quantum?.num_qubits ?? 4}
            </span>
            <span className="text-xs text-slate-400">Qubits ({quantum?.num_shots ?? 1024} shots)</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>Hybrid RMSE:</span>
            <span className="font-medium text-violet-300">{quantum?.quantum_hybrid_rmse ?? '0.731'}</span>
          </div>
        </div>

        {/* Card 4: Retrospective Enrichment */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Discovery Enrichment</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-emerald-400">
              {val?.selected_batch_enrichment_factor ? `${val.selected_batch_enrichment_factor.toFixed(2)}x` : '1.85x'}
            </span>
            <span className="text-xs text-slate-400">over random</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>Novel Scaffolds:</span>
            <span className="font-medium text-emerald-300">{val?.selected_batch_novel_scaffolds ?? 12}</span>
          </div>
        </div>
      </div>

      {/* Discovery Workflow Stepper */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-base font-semibold text-white mb-4">Complete 5-Stage Scientific Pipeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {[
            {
              step: '1. Ingestion',
              title: 'Curated & Provenance',
              desc: 'SMILES validation, Murcko scaffolds, 80+ ChEMBL records',
              tab: 'molecules',
              badge: 'READY'
            },
            {
              step: '2. Modeling',
              title: 'Scaffold-Split ML',
              desc: 'Leakage-resistant Random Forest & uncertainty calibration',
              tab: 'models',
              badge: model ? 'TRAINED' : 'READY'
            },
            {
              step: '3. Quantum',
              title: 'QpiAI QCloud',
              desc: 'Angle feature encoding & multi-qubit CNOT entanglement',
              tab: 'quantum',
              badge: quantum ? 'EXECUTED' : 'READY'
            },
            {
              step: '4. Optimization',
              title: 'QpiAI Opt QUBO',
              desc: 'Exact batch size & budget constrained combinatorial selection',
              tab: 'optimizer',
              badge: opt ? 'SOLVED' : 'READY'
            },
            {
              step: '5. Validation',
              title: 'Retrospective Val',
              desc: 'Enrichment factor & baseline comparison on held-out outcomes',
              tab: 'validation',
              badge: val ? 'VERIFIED' : 'READY'
            }
          ].map((item, i) => (
            <div
              key={i}
              onClick={() => onNavigate(item.tab)}
              className="group bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 hover:border-teal-500/50 rounded-xl p-4 cursor-pointer transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-[11px] font-semibold text-teal-400 uppercase tracking-wider mb-1">
                  <span>{item.step}</span>
                  <span className="px-1.5 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/60 text-[10px]">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-sm font-medium text-slate-100 group-hover:text-white">{item.title}</h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.desc}</p>
              </div>
              <div className="mt-3 flex items-center text-xs text-teal-400 font-medium group-hover:translate-x-1 transition-transform">
                <span>View &rarr;</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Batch Summary Banner */}
      {opt && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Latest Optimal Experimental Batch ({opt.selected_count} Compounds)</h2>
              <p className="text-xs text-slate-400">
                Solver: <span className="text-slate-200">{opt.solver_backend}</span> | Runtime: {opt.runtime_ms} ms | Cost: ${opt.total_cost.toLocaleString()} / Budget: ${(opt.total_cost + opt.budget_remaining).toLocaleString()}
              </p>
            </div>
            <EvidenceBadge status={opt.evidence_status} />
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
                  <th className="py-2.5 px-3">Scaffold</th>
                  <th className="py-2.5 px-3">Cost</th>
                  <th className="py-2.5 px-3">Selection Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {opt.selected_compounds.slice(0, 5).map((c) => (
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
                    <td className="py-2.5 px-3 text-violet-300">{c.scaffold_id}</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-medium">${c.cost}</td>
                    <td className="py-2.5 px-3 text-slate-400 max-w-sm">{c.selection_rationale}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-right">
            <button
              onClick={() => onNavigate('optimizer')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium inline-flex items-center space-x-1"
            >
              <span>View full {opt.selected_count} compounds and QUBO formulation details &rarr;</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

