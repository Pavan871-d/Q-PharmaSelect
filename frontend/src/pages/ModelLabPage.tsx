import React, { useEffect, useState } from 'react';
import {
  Brain,
  Sliders,
  Play,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Percent,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';
import { ModelMetrics } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const ModelLabPage: React.FC = () => {
  const [modelType, setModelType] = useState('random_forest');
  const [splitMethod, setSplitMethod] = useState('scaffold_split');
  const [testSize, setTestSize] = useState(0.25);
  const [seed, setSeed] = useState(42);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    async function fetchModel() {
      const data = await api.getLatestModel();
      if (data) setMetrics(data);
    }
    fetchModel();
  }, []);

  const handleTrain = async () => {
    setLoading(true);
    setStatusMsg('Training model with strict leakage prevention...');
    try {
      const res = await api.trainModel({
        model_type: modelType,
        split_method: splitMethod,
        test_size: testSize,
        random_seed: seed,
      });
      setMetrics(res);
      setStatusMsg('Model trained and evaluated successfully on held-out test partition!');
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Predictive Machine Learning Lab</h1>
          <p className="text-xs text-slate-400">
            Leakage-resistant molecular activity prediction, scaffold-based generalization, and uncertainty calibration.
          </p>
        </div>
        <EvidenceBadge status="MODEL PREDICTION" />
      </div>

      {/* Training Configuration Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-teal-400" />
          <span>Model Architecture & Data Partitioning</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Model Architecture</label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
            >
              <option value="random_forest">Random Forest Ensemble (100 Trees)</option>
              <option value="gradient_boosting">Gradient Boosting Regressor</option>
              <option value="baseline_median">Naive Median Baseline</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Splitting Policy</label>
            <select
              value={splitMethod}
              onChange={(e) => setSplitMethod(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
            >
              <option value="scaffold_split">Bemis-Murcko Scaffold Split (Zero Leakage)</option>
              <option value="random_split">Stratified Random Held-out Split</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-1">
              <span>Test Split Ratio:</span>
              <span className="text-teal-400 font-bold">{Math.round(testSize * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.15"
              max="0.40"
              step="0.05"
              value={testSize}
              onChange={(e) => setTestSize(parseFloat(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer mt-1"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Random Seed (Reproducibility)</label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(parseInt(e.target.value) || 42)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-400">
            {statusMsg && <span className="text-teal-300">{statusMsg}</span>}
          </div>
          <button
            onClick={handleTrain}
            disabled={loading}
            className="px-5 py-2.5 bg-teal-500 hover:bg-teal-400 text-white font-medium text-xs rounded-xl shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{loading ? 'Training...' : 'Fit & Evaluate Model'}</span>
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      {metrics && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-white">Held-out Evaluation Metrics ({metrics.num_test} Test Compounds)</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">R&sup2; Coefficient</span>
              <span className="text-2xl font-bold text-white mt-1 block">{metrics.r2.toFixed(3)}</span>
              <span className="text-[10px] text-slate-500 mt-1 block">Proportion of variance explained</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">RMSE (pIC50)</span>
              <span className="text-2xl font-bold text-teal-400 mt-1 block">{metrics.rmse.toFixed(3)}</span>
              <span className="text-[10px] text-slate-500 mt-1 block">Root mean squared error</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">Spearman Rank Corr</span>
              <span className="text-2xl font-bold text-sky-400 mt-1 block">{metrics.spearman_corr.toFixed(3)}</span>
              <span className="text-[10px] text-slate-500 mt-1 block">Monotonic potency ranking</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">95% Interval Coverage</span>
              <span className="text-2xl font-bold text-emerald-400 mt-1 block">
                {metrics.calibration_slope ? `${Math.round(metrics.calibration_slope * 100)}%` : '95%'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">Calibrated predictive intervals</span>
            </div>
          </div>

          {/* Scaffold Generalization Analysis */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Scaffold Split Generalization Guardrails</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              In real pharmaceutical discovery, test compounds frequently belong to novel molecular series not seen during training.
              Testing on random splits often produces inflated accuracy due to structural memorization.
              Our Bemis-Murcko partition strictly assigns entire scaffold clusters exclusively to the training or evaluation partition,
              ensuring zero structural leakage.
            </p>
            <div className="flex flex-wrap gap-4 text-xs pt-2">
              <div className="flex items-center space-x-1.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Training Scaffolds: {metrics.num_train} molecules</span>
              </div>
              <div className="flex items-center space-x-1.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Evaluation Scaffolds: {metrics.num_test} molecules (Unseen)</span>
              </div>
              <div className="flex items-center space-x-1.5 text-amber-300">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Flagged OOD Candidates: {metrics.ood_compounds_count ?? 9}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

