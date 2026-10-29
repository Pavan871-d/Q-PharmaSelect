import React from 'react';
import {
  LayoutDashboard,
  Target,
  FlaskConical,
  Brain,
  Cpu,
  Layers,
  BarChart3,
  FileText,
  Settings as SettingsIcon,
  Atom
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  qcloudStatus?: string;
  optStatus?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  qcloudStatus = 'LOCAL',
  optStatus = 'QUBO'
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'target-assay', label: 'Target & Assay', icon: Target },
    { id: 'molecules', label: 'Molecule Explorer', icon: FlaskConical },
    { id: 'models', label: 'Model Lab', icon: Brain },
    { id: 'quantum', label: 'Quantum Lab', icon: Cpu },
    { id: 'optimizer', label: 'Batch Optimizer', icon: Layers },
    { id: 'validation', label: 'Retrospective Val', icon: BarChart3 },
    { id: 'reports', label: 'Experiment Report', icon: FileText },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <header className="bg-navy-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('overview')}>
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-teal-500 to-violet-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Atom className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-teal-300 bg-clip-text text-transparent">
                  Q-PharmaSelect
                </span>
                <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-teal-950/80 text-teal-400 border border-teal-800/50">
                  QML-04
                </span>
              </div>
              <p className="text-xs text-slate-400">Discover smarter. Test fewer. Learn faster.</p>
            </div>
          </div>

          {/* Technology Indicator Pills */}
          <div className="hidden lg:flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
              <span className="h-2 w-2 rounded-full bg-violet-400 animate-pulse"></span>
              <span className="text-slate-400">QpiAI Quantum:</span>
              <span className="font-medium text-violet-300">{qcloudStatus}</span>
            </div>
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
              <span className="h-2 w-2 rounded-full bg-teal-400"></span>
              <span className="text-slate-400">QpiAI Opt:</span>
              <span className="font-medium text-teal-300">{optStatus}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 overflow-x-auto py-2 scrollbar-none border-t border-slate-800/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-teal-500/15 text-teal-300 border border-teal-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-teal-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};

