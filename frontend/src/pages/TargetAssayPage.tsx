import React, { useState } from 'react';
import { Target, DollarSign, Layers, CheckCircle2, Sliders, ShieldCheck } from 'lucide-react';
import { EvidenceBadge } from '../components/EvidenceBadge';

interface TargetAssayProps {
  onNavigate: (tab: string) => void;
}

export const TargetAssayPage: React.FC<TargetAssayProps> = ({ onNavigate }) => {
  const [targetId, setTargetId] = useState('CHEMBL203');
  const [targetName, setTargetName] = useState('Epidermal Growth Factor Receptor (EGFR)');
  const [organism, setOrganism] = useState('Homo sapiens');
  const [uniprot, setUniprot] = useState('P00533');
  const [assayId, setAssayId] = useState('CHEMBL615112');
  const [assayName, setAssayName] = useState('In vitro wild-type EGFR tyrosine kinase domain inhibition');
  const [assayType, setAssayType] = useState('Biochemical');
  const [endpoint, setEndpoint] = useState('IC50');
  const [endpointUnit, setEndpointUnit] = useState('nM');
  const [activityThresholdNm, setActivityThresholdNm] = useState(316.0);
  const [batchSize, setBatchSize] = useState(15);
  const [budget, setBudget] = useState(10000.0);
  const [unknownPolicy, setUnknownPolicy] = useState('EXCLUDE');
  const [saved, setSaved] = useState(false);

  // Unit transformation calculation
  // pIC50 = 9 - log10(IC50_in_nM)
  const pic50Threshold = (9.0 - Math.log10(Math.max(activityThresholdNm, 0.01))).toFixed(2);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Target & Assay Configuration</h1>
          <p className="text-xs text-slate-400">
            Define biological target, assay context, unit transformations, screening capacity, and budgetary bounds.
          </p>
        </div>
        <EvidenceBadge status="VERIFIED SOURCE DATA" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Section 1: Biological Target */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2 text-teal-400 font-semibold text-sm">
            <Target className="w-4 h-4" />
            <span>1. Biological Target Specifications</span>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Name</label>
            <input
              type="text"
              value={targetName}
              onChange={(e) => setTargetName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">ChEMBL Target ID</label>
              <input
                type="text"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">UniProt Accession</label>
              <input
                type="text"
                value={uniprot}
                onChange={(e) => setUniprot(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Organism</label>
            <input
              type="text"
              value={organism}
              onChange={(e) => setOrganism(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
            />
          </div>
        </div>

        {/* Section 2: Assay & Endpoint */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2 text-teal-400 font-semibold text-sm">
            <Sliders className="w-4 h-4" />
            <span>2. Assay & Scientifically Valid Endpoints</span>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Assay Description / ID</label>
            <input
              type="text"
              value={assayName}
              onChange={(e) => setAssayName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Assay Type</label>
              <select
                value={assayType}
                onChange={(e) => setAssayType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              >
                <option value="Biochemical">Biochemical</option>
                <option value="Cell-based">Cell-based</option>
                <option value="Biophysical">Biophysical</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Endpoint</label>
              <select
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              >
                <option value="IC50">IC50</option>
                <option value="Ki">Ki</option>
                <option value="EC50">EC50</option>
                <option value="Kd">Kd</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Unit</label>
              <select
                value={endpointUnit}
                onChange={(e) => setEndpointUnit(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              >
                <option value="nM">nM</option>
                <option value="uM">&mu;M</option>
                <option value="mol/L">mol/L (M)</option>
              </select>
            </div>
          </div>

          {/* Unit Conversion Info Box */}
          <div className="bg-slate-800/80 rounded-xl p-3 border border-slate-700/60 text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Activity Threshold ({endpointUnit}):</span>
              <input
                type="number"
                value={activityThresholdNm}
                onChange={(e) => setActivityThresholdNm(parseFloat(e.target.value) || 0)}
                className="w-24 bg-slate-900 border border-slate-700 rounded px-2 py-0.5 text-right font-medium text-teal-300 text-xs"
              />
            </div>
            <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-700/50">
              <span>Standardized Potency Threshold:</span>
              <span className="font-semibold text-white">pIC50 &ge; {pic50Threshold}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: Experimental Capacity and Budgetary Constraints */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center space-x-2 text-teal-400 font-semibold text-sm">
          <DollarSign className="w-4 h-4" />
          <span>3. Capacity, Budget, and Availability Policies</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
              <span>Batch Screening Size (K):</span>
              <span className="text-teal-400 font-bold">{batchSize} compounds</span>
            </div>
            <input
              type="range"
              min="5"
              max="35"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">Number of test wells allocated in next experimental run.</p>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
              <span>Assay Screening Budget:</span>
              <span className="text-emerald-400 font-bold">${budget.toLocaleString()} USD</span>
            </div>
            <input
              type="range"
              min="2000"
              max="25000"
              step="500"
              value={budget}
              onChange={(e) => setBudget(parseFloat(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">Maximum financial allowance for candidate synthesis/reagents.</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Unknown Availability Policy</label>
            <select
              value={unknownPolicy}
              onChange={(e) => setUnknownPolicy(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
            >
              <option value="EXCLUDE">Strict Exclude (Hard constraint x_i = 0)</option>
              <option value="PENALIZE">Include with Uncertainty Penalty</option>
            </select>
            <p className="text-[11px] text-slate-500 mt-1">Prevents unverified candidates from wasting test budget.</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end space-x-3 pt-2">
        <button
          onClick={handleSave}
          className="px-6 py-2.5 bg-teal-500 hover:bg-teal-400 text-white font-medium text-sm rounded-xl shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition-all"
        >
          {saved ? <CheckCircle2 className="w-4 h-4" /> : null}
          <span>{saved ? 'Configuration Saved!' : 'Save Parameters'}</span>
        </button>
        <button
          onClick={() => onNavigate('optimizer')}
          className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-sm rounded-xl transition-all"
        >
          <span>Proceed to Optimizer &rarr;</span>
        </button>
      </div>
    </div>
  );
};

