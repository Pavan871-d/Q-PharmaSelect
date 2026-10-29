import React, { useEffect, useState } from 'react';
import {
  KeyRound,
  ShieldAlert,
  Server,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Layers
} from 'lucide-react';
import { api } from '../services/api';
import { IntegrationStatus } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';

export const SettingsPage: React.FC = () => {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [qcloudKey, setQcloudKey] = useState('');
  const [optKey, setOptKey] = useState('');
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    try {
      const data = await api.getIntegrationsStatus();
      setStatus(data);
    } catch (err) {
      console.error(err);
    }
  }

  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.updateCredentials({
        qpiai_qcloud_api_key: qcloudKey ? qcloudKey : undefined,
        qpiai_opt_api_key: optKey ? optKey : undefined,
      });
      setSaveMsg('Credentials updated securely for this session!');
      loadStatus();
      setQcloudKey('');
      setOptKey('');
    } catch (err: any) {
      setSaveMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setSaveMsg(null), 3000);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Settings & Integrations</h1>
        <p className="text-xs text-slate-400">
          Configure external QpiAI Quantum and QpiAI Opt services, verify SDK versions, and check security boundaries.
        </p>
      </div>

      {/* Security Guidance Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2 text-xs">
        <div className="flex items-center space-x-2 text-teal-400 font-semibold">
          <Lock className="w-4 h-4" />
          <span>Security & API Key Management Policy</span>
        </div>
        <p className="text-slate-400 leading-relaxed">
          API keys are managed strictly server-side and never exposed in client bundles or public repositories.
          When credentials are not supplied, Q-PharmaSelect operates in a high-fidelity local simulator mode
          without fabricating remote execution claims.
        </p>
      </div>

      {/* API Key Configuration Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <KeyRound className="w-4 h-4 text-violet-400" />
          <span>QpiAI Authentication Credentials</span>
        </h2>

        <form onSubmit={handleSaveCredentials} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">QpiAI QCloud API Key</label>
              <input
                type="password"
                placeholder={status?.qcloud.has_api_key ? '•••••••••••••••• (Configured)' : 'Enter QpiAI QCloud API Key...'}
                value={qcloudKey}
                onChange={(e) => setQcloudKey(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-violet-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Portal: <a href="https://qcloud.qpiai.tech" target="_blank" rel="noreferrer" className="text-violet-400 hover:underline">https://qcloud.qpiai.tech</a>
              </span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">QpiAI Opt API Key / Token</label>
              <input
                type="password"
                placeholder={status?.qpiai_opt.has_api_key ? '•••••••••••••••• (Configured)' : 'Enter QpiAI Opt Access Token...'}
                value={optKey}
                onChange={(e) => setOptKey(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Portal: <a href="https://opt.qpiai.tech" target="_blank" rel="noreferrer" className="text-teal-400 hover:underline">https://opt.qpiai.tech</a>
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-emerald-400 font-medium">{saveMsg}</span>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-teal-500/20 transition-all disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Update Session Credentials'}
            </button>
          </div>
        </form>
      </div>

      {/* Backend Diagnostics and Package Status */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* QCloud Status */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center space-x-1.5">
                <Cpu className="w-4 h-4 text-violet-400" />
                <span>QpiAI QCloud Connection</span>
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-950 text-violet-300 border border-violet-800 font-semibold">
                {status.qcloud.auth_status}
              </span>
            </div>

            <div className="text-xs text-slate-400 space-y-1.5">
              <div className="flex justify-between">
                <span>SDK Version:</span>
                <span className="text-slate-200 font-mono">{status.qcloud.sdk_version}</span>
              </div>
              <div className="flex justify-between">
                <span>Supported Devices:</span>
                <span className="text-slate-200">QSV-Simulator, Indus-1, QSV-Local</span>
              </div>
            </div>
          </div>

          {/* QpiAI Opt Status */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center space-x-1.5">
                <Layers className="w-4 h-4 text-teal-400" />
                <span>QpiAI Opt Connection</span>
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-950 text-teal-300 border border-teal-800 font-semibold">
                {status.qpiai_opt.status}
              </span>
            </div>

            <div className="text-xs text-slate-400 space-y-1.5">
              <div className="flex justify-between">
                <span>Endpoint URL:</span>
                <span className="text-slate-200 font-mono text-[11px]">{status.qpiai_opt.opt_url}</span>
              </div>
              <div className="flex justify-between">
                <span>Formulations:</span>
                <span className="text-slate-200">QUBO, Ising, Max-Independent-Set</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Installed Scientific Stack Diagnostics */}
      {status && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center space-x-1.5">
            <Server className="w-4 h-4 text-teal-400" />
            <span>Installed Scientific Environment Packages</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {Object.entries(status.runtime_environment.python_packages).map(([pkg, ver]) => (
              <div key={pkg} className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/60 text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-mono">{pkg}</span>
                <span className="font-semibold text-white font-mono">{ver}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

