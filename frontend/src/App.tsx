import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewDashboard } from './pages/OverviewDashboard';
import { TargetAssayPage } from './pages/TargetAssayPage';
import { MoleculeExplorerPage } from './pages/MoleculeExplorerPage';
import { ModelLabPage } from './pages/ModelLabPage';
import { QuantumLabPage } from './pages/QuantumLabPage';
import { BatchOptimizerPage } from './pages/BatchOptimizerPage';
import { RetrospectivePage } from './pages/RetrospectivePage';
import { ReportPage } from './pages/ReportPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [qcloudStatus, setQcloudStatus] = useState('LOCAL');
  const [optStatus, setOptStatus] = useState('QUBO');

  useEffect(() => {
    async function loadStatus() {
      try {
        const data = await api.getIntegrationsStatus();
        if (data.qcloud.auth_status === 'AUTHENTICATED') {
          setQcloudStatus('QCLOUD LIVE');
        } else {
          setQcloudStatus('SIMULATOR');
        }
        if (data.qpiai_opt.status === 'CONFIGURED') {
          setOptStatus('CLOUD OPT');
        } else {
          setOptStatus('QUBO (SA)');
        }
      } catch (e) {
        // Fallback default
      }
    }
    loadStatus();
  }, []);

  return (
    <div className="min-h-screen bg-[#0B1120] text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        qcloudStatus={qcloudStatus}
        optStatus={optStatus}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewDashboard onNavigate={setActiveTab} />}
        {activeTab === 'target-assay' && <TargetAssayPage onNavigate={setActiveTab} />}
        {activeTab === 'molecules' && <MoleculeExplorerPage />}
        {activeTab === 'models' && <ModelLabPage />}
        {activeTab === 'quantum' && <QuantumLabPage />}
        {activeTab === 'optimizer' && <BatchOptimizerPage />}
        {activeTab === 'validation' && <RetrospectivePage />}
        {activeTab === 'reports' && <ReportPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>

      <footer className="border-t border-slate-800/80 bg-navy-900 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Q-PharmaSelect &bull; QML-04 Challenge Prototype &bull; Quantum Machine Learning Track</span>
          <span className="text-[11px] text-slate-400">
            Powered by QpiAI Quantum SDK &bull; QpiAI Opt &bull; RDKit &bull; FastAPI &bull; React
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;

