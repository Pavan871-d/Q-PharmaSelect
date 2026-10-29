import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  Upload,
  ExternalLink,
  X,
  FileSpreadsheet,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';
import { api } from '../services/api';
import { Compound } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const MoleculeExplorerPage: React.FC = () => {
  const [compounds, setCompounds] = useState<Compound[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [scaffoldFilter, setScaffoldFilter] = useState('');
  const [availFilter, setAvailFilter] = useState('');
  const [selectedMolecule, setSelectedMolecule] = useState<Compound | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);

  useEffect(() => {
    loadCompounds();
  }, [scaffoldFilter, availFilter]);

  async function loadCompounds() {
    setLoading(true);
    try {
      const data = await api.getCompounds(0, 100, search || undefined, scaffoldFilter || undefined);
      setCompounds(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCompounds();
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploadStatus('Processing and validating chemical structures...');
    try {
      const res = await api.uploadCsv(uploadFile);
      setUploadResult(res);
      setUploadStatus(`Successfully imported ${res.imported_count} compounds! (${res.rejected_count} rejected)`);
      loadCompounds();
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message}`);
    }
  };

  // Distinct scaffolds for filtering
  const distinctScaffolds = Array.from(new Set(compounds.map((c) => c.scaffold_id).filter(Boolean)));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Molecule Explorer & Provenance</h1>
          <p className="text-xs text-slate-400">
            Inspect verified candidate chemical space, Bemis-Murcko scaffolds, physicochemical descriptors, and audit trails.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setUploadModalOpen(true)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center space-x-2 transition-all"
          >
            <Upload className="w-4 h-4 text-teal-400" />
            <span>Upload Candidate CSV</span>
          </button>
        </div>
      </div>

      {/* 2D Chemical Space Visualizer */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-white">2D Chemical Space Embedding (PCA on Morgan ECFP4)</h2>
            <p className="text-[11px] text-slate-400">
              Dimensionality reduction of 1,024-bit Morgan fingerprints. Points colored by Bemis-Murcko scaffold series.
            </p>
          </div>
          <span className="text-[11px] text-slate-500">N={compounds.length} molecules</span>
        </div>

        {/* Interactive SVG Scatter Plot */}
        <div className="relative w-full h-64 bg-slate-950/70 rounded-xl border border-slate-800/80 flex items-center justify-center overflow-hidden">
          <svg className="w-full h-full p-4" viewBox="-12 -12 24 24">
            {/* Grid Lines */}
            <line x1="-12" y1="0" x2="12" y2="0" stroke="#1E293B" strokeWidth="0.1" strokeDasharray="0.5,0.5" />
            <line x1="0" y1="-12" x2="0" y2="12" stroke="#1E293B" strokeWidth="0.1" strokeDasharray="0.5,0.5" />

            {/* Molecule Scatter Points */}
            {compounds.map((c, i) => {
              const x = c.pca_x ?? 0.0;
              const y = c.pca_y ?? 0.0;
              const isSelected = selectedMolecule?.compound_id === c.compound_id;
              const isPotent = (c.historical_pic50 ?? 0) >= 7.5;
              const isAcyclic = c.scaffold_id === 'SCAF-00000' || c.scaffold === 'Acyclic';

              return (
                <circle
                  key={c.compound_id || i}
                  cx={x}
                  cy={-y}
                  r={isSelected ? 0.9 : isPotent ? 0.6 : 0.45}
                  fill={
                    isPotent
                      ? '#2DD4BF'
                      : isAcyclic
                      ? '#94A3B8'
                      : '#A78BFA'
                  }
                  stroke={isSelected ? '#FFFFFF' : '#0B1120'}
                  strokeWidth="0.15"
                  className="cursor-pointer transition-transform hover:opacity-100 hover:scale-125 opacity-85"
                  onClick={() => setSelectedMolecule(c)}
                >
                  <title>{`${c.compound_id} (${c.source_id})\npIC50: ${c.historical_pic50 ?? 'N/A'}\nScaffold: ${c.scaffold_id}`}</title>
                </circle>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="absolute bottom-2 right-3 flex items-center space-x-3 text-[10px] bg-slate-900/90 px-2.5 py-1 rounded-lg border border-slate-800">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-teal-400"></span>
              <span className="text-slate-300">Potent Hit (pIC50 &ge; 7.5)</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-violet-400"></span>
              <span className="text-slate-300">Diverse Kinase Series</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-slate-400"></span>
              <span className="text-slate-300">Negative Control / Probe</span>
            </span>
          </div>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by compound ID, ChEMBL source ID, or SMILES..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={scaffoldFilter}
              onChange={(e) => setScaffoldFilter(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
            >
              <option value="">All Scaffolds ({distinctScaffolds.length})</option>
              {distinctScaffolds.map((scaff) => (
                <option key={scaff} value={scaff}>
                  {scaff}
                </option>
              ))}
            </select>

            <button
              type="submit"
              className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-white text-xs font-medium rounded-xl transition-colors"
            >
              Search
            </button>
          </div>
        </form>
      </div>

      {/* Candidate Molecules Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/80 uppercase tracking-wider text-[11px] text-slate-400">
              <tr>
                <th className="py-3 px-4">Compound</th>
                <th className="py-3 px-4">Structure SMILES</th>
                <th className="py-3 px-4">Scaffold</th>
                <th className="py-3 px-4">MW</th>
                <th className="py-3 px-4">LogP</th>
                <th className="py-3 px-4">TPSA</th>
                <th className="py-3 px-4">Cost</th>
                <th className="py-3 px-4">Availability</th>
                <th className="py-3 px-4">Hist Potency</th>
                <th className="py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {compounds.map((c) => (
                <tr
                  key={c.compound_id}
                  className="hover:bg-slate-800/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedMolecule(c)}
                >
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{c.compound_id}</div>
                    <div className="text-[10px] text-slate-400">{c.source_id}</div>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-300 truncate max-w-xs" title={c.canonical_smiles}>
                    {c.canonical_smiles}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-violet-950/80 text-violet-300 border border-violet-800/60 font-mono text-[10px]">
                      {c.scaffold_id || 'SCAF-00000'}
                    </span>
                  </td>
                  <td className="py-3 px-4">{c.mw?.toFixed(1) ?? '-'}</td>
                  <td className="py-3 px-4">{c.logp?.toFixed(1) ?? '-'}</td>
                  <td className="py-3 px-4">{c.tpsa?.toFixed(1) ?? '-'}</td>
                  <td className="py-3 px-4 text-emerald-400 font-medium">${c.cost}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        c.availability === 'AVAILABLE'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
                          : c.availability === 'UNAVAILABLE'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800/60'
                          : 'bg-amber-950 text-amber-300 border border-amber-800/60'
                      }`}
                    >
                      {c.availability}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-white">
                    {c.historical_pic50 ? `pIC50 ${c.historical_pic50.toFixed(2)}` : 'Unmeasured'}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedMolecule(c);
                      }}
                      className="text-teal-400 hover:text-teal-300 text-xs font-medium"
                    >
                      Inspect &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Molecule Details Modal */}
      {selectedMolecule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl relative">
            <button
              onClick={() => setSelectedMolecule(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3">
              <h2 className="text-lg font-bold text-white">{selectedMolecule.compound_id} Details</h2>
              <EvidenceBadge status={selectedMolecule.evidence_status} />
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px] mb-1 font-semibold uppercase tracking-wider">
                  Canonical SMILES
                </span>
                <span className="font-mono text-teal-300 break-all select-all">
                  {selectedMolecule.canonical_smiles}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <span className="text-slate-400 block text-[10px]">Molecular Weight</span>
                  <span className="text-sm font-semibold text-white">{selectedMolecule.mw} g/mol</span>
                </div>
                <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <span className="text-slate-400 block text-[10px]">LogP (Lipophilicity)</span>
                  <span className="text-sm font-semibold text-white">{selectedMolecule.logp}</span>
                </div>
                <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <span className="text-slate-400 block text-[10px]">TPSA</span>
                  <span className="text-sm font-semibold text-white">{selectedMolecule.tpsa} &Aring;&sup2;</span>
                </div>
                <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <span className="text-slate-400 block text-[10px]">HBD / HBA</span>
                  <span className="text-sm font-semibold text-white">{selectedMolecule.hbd} / {selectedMolecule.hba}</span>
                </div>
              </div>

              {/* Provenance Audit Card */}
              <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-3.5 space-y-2">
                <span className="text-xs font-semibold text-teal-400 flex items-center space-x-1">
                  <Info className="w-3.5 h-3.5" />
                  <span>Provenance & Source Audit Record</span>
                </span>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-400">Source Identifier:</span>{' '}
                    <span className="text-white font-medium">{selectedMolecule.source_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Source Database:</span>{' '}
                    <span className="text-white font-medium">{selectedMolecule.source_database}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Assay Screening Cost:</span>{' '}
                    <span className="text-emerald-400 font-semibold">${selectedMolecule.cost}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Availability:</span>{' '}
                    <span className="text-white font-medium">{selectedMolecule.availability}</span>
                  </div>
                </div>
                {selectedMolecule.source_url && (
                  <div className="pt-2 border-t border-slate-700/50">
                    <a
                      href={selectedMolecule.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-teal-400 hover:text-teal-300 inline-flex items-center space-x-1 text-xs"
                    >
                      <span>View Official ChEMBL Report Card</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CSV Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative">
            <button
              onClick={() => {
                setUploadModalOpen(false);
                setUploadStatus(null);
                setUploadResult(null);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <FileSpreadsheet className="w-5 h-5 text-teal-400" />
              <span>Import Candidate Compound Dataset</span>
            </h2>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-6 text-center hover:border-teal-500 transition-colors">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="csv-file-input"
                />
                <label htmlFor="csv-file-input" className="cursor-pointer block space-y-2">
                  <Upload className="w-8 h-8 text-teal-400 mx-auto" />
                  <span className="text-xs text-slate-300 block">
                    {uploadFile ? uploadFile.name : 'Click to select .CSV file with SMILES column'}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Supports compound_id, smiles, cost, availability, endpoint_value columns.
                  </span>
                </label>
              </div>

              {uploadStatus && (
                <div className="text-xs p-3 rounded-lg bg-slate-800 border border-slate-700 text-teal-300">
                  {uploadStatus}
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl hover:bg-slate-700"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={!uploadFile}
                  className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-white text-xs font-medium rounded-xl disabled:opacity-50"
                >
                  Process & Import
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

