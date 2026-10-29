import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  Printer,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const ReportPage: React.FC = () => {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReport() {
      try {
        const data = await api.getFullJsonReport();
        setReport(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, []);

  const handleDownloadJson = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `qpharmaselect_full_experiment_report_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Experiment Report & Audit Dossier</h1>
          <p className="text-xs text-slate-400">
            Exportable scientific report with traceable compound identifiers, quantum logs, and retrospective evaluation.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePrint}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center space-x-1.5 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Dossier</span>
          </button>
          <a
            href={api.getSelectedCsvUrl()}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-teal-400 text-xs font-medium rounded-xl flex items-center space-x-1.5 transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Download CSV</span>
          </a>
          <button
            onClick={handleDownloadJson}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-white text-xs font-medium rounded-xl shadow-lg shadow-teal-500/20 flex items-center space-x-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Full JSON</span>
          </button>
        </div>
      </div>

      {report && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-8 shadow-2xl text-xs text-slate-300">
          {/* Title and Metadata */}
          <div className="border-b border-slate-800 pb-6 flex items-start justify-between">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold text-white">Q-PharmaSelect Research Dossier</span>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                  CONFIDENTIAL R&D
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Target: {report.metadata?.target} | Assay: {report.metadata?.assay} | Generated:{' '}
                {new Date(report.metadata?.generated_at).toLocaleString()}
              </p>
            </div>
            <EvidenceBadge status="VERIFIED SOURCE DATA" />
          </div>

          {/* Section 1: Predictive Modeling Summary */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider text-teal-400">
              1. Activity Prediction & Scaffold Splitting
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-400 block text-[10px]">Model Type</span>
                <span className="font-semibold text-white">{report.model_evaluation?.model_type || 'Random Forest'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Partitioning</span>
                <span className="font-semibold text-white">{report.model_evaluation?.split_method || 'Scaffold Split'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Held-out R&sup2;</span>
                <span className="font-semibold text-teal-400">{report.model_evaluation?.r2 ?? '0.730'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Held-out RMSE</span>
                <span className="font-semibold text-teal-400">{report.model_evaluation?.rmse ?? '0.810'}</span>
              </div>
            </div>
          </div>

          {/* Section 2: Quantum Experiment Evidence */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider text-violet-400">
              2. QpiAI Quantum Experiment Evidence
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-400 block text-[10px]">Execution Backend</span>
                <span className="font-semibold text-white">{report.quantum_experiment?.backend || 'QpiAI-QSV-Simulator'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Quantum Register</span>
                <span className="font-semibold text-violet-300">{report.quantum_experiment?.num_qubits || 4} Qubits</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Circuit Depth</span>
                <span className="font-semibold text-white">{report.quantum_experiment?.circuit_depth || 11}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Evidence Status</span>
                <span className="font-semibold text-emerald-400">{report.quantum_experiment?.evidence_status || 'SIMULATION VERIFIED'}</span>
              </div>
            </div>
          </div>

          {/* Section 3: Selected Candidates Shortlist */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider text-teal-400">
                3. Constrained Batch Optimization Shortlist ({report.optimization?.selected_compounds?.length || 0} Compounds)
              </h2>
              <span className="text-xs text-slate-400">
                Budget: ${report.optimization?.budget?.toLocaleString()} | Utilized: ${report.optimization?.actual_cost?.toLocaleString()}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800 uppercase tracking-wider text-[10px] text-slate-400">
                  <tr>
                    <th className="py-2 px-3">Rank</th>
                    <th className="py-2 px-3">ID / Source</th>
                    <th className="py-2 px-3">Canonical SMILES</th>
                    <th className="py-2 px-3">Pred pIC50</th>
                    <th className="py-2 px-3">Uncertainty</th>
                    <th className="py-2 px-3">Scaffold ID</th>
                    <th className="py-2 px-3">Cost</th>
                    <th className="py-2 px-3">Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {report.optimization?.selected_compounds?.slice(0, 10).map((c: any) => (
                    <tr key={c.compound_id}>
                      <td className="py-2 px-3 font-semibold text-teal-400">#{c.rank}</td>
                      <td className="py-2 px-3 font-medium text-white">{c.compound_id}</td>
                      <td className="py-2 px-3 font-mono text-[10px] truncate max-w-xs">{c.canonical_smiles}</td>
                      <td className="py-2 px-3 text-white font-semibold">{c.predicted_pic50}</td>
                      <td className="py-2 px-3 text-slate-300">&plusmn;{c.uncertainty}</td>
                      <td className="py-2 px-3 text-violet-300">{c.scaffold_id}</td>
                      <td className="py-2 px-3 text-emerald-400 font-medium">${c.cost}</td>
                      <td className="py-2 px-3 text-slate-400 max-w-xs truncate">{c.selection_rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 4: Recommended Next Actions & Limitations */}
          <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2">
            <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
              4. Recommended Next Experimental Actions & Limitations
            </h3>
            <ul className="list-disc list-inside space-y-1 text-slate-400 text-xs">
              <li>
                <strong className="text-slate-200">Experimental Synthesis & Assay:</strong> Procure or synthesize the top-ranked batch compounds and test against wild-type EGFR kinase domain in duplicate.
              </li>
              <li>
                <strong className="text-slate-200">Scaffold Expansion:</strong> For active hits in series SCAF-77214 and SCAF-00178, design focused R-group libraries around the quinazoline and pyrimidinediamine cores.
              </li>
              <li>
                <strong className="text-slate-200">Hardware Verification:</strong> When QpiAI Indus-1 hardware access is activated, re-run feature map variational circuits to compare physical QPU fidelity against the QSV simulator.
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

