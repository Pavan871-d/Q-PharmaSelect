import React from 'react';
import { ShieldCheck, Cpu, CheckCircle2, AlertTriangle, Database } from 'lucide-react';

interface EvidenceBadgeProps {
  status: string;
  className?: string;
}

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({ status, className = '' }) => {
  let color = 'bg-slate-800 text-slate-300 border-slate-700';
  let icon = <Database className="w-3.5 h-3.5 mr-1" />;

  const upper = status.toUpperCase();

  if (upper.includes('VERIFIED') || upper.includes('COMPLETE') || upper.includes('EXHAUSTIVE')) {
    color = 'bg-emerald-950/70 text-emerald-300 border-emerald-700/60 shadow-sm shadow-emerald-900/30';
    icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" />;
  } else if (upper.includes('QUANTUM')) {
    color = 'bg-purple-950/70 text-purple-300 border-purple-700/60 shadow-sm shadow-purple-900/30';
    icon = <Cpu className="w-3.5 h-3.5 mr-1 text-purple-400" />;
  } else if (upper.includes('USER-PROVIDED')) {
    color = 'bg-sky-950/70 text-sky-300 border-sky-700/60';
    icon = <ShieldCheck className="w-3.5 h-3.5 mr-1 text-sky-400" />;
  } else if (upper.includes('FALLBACK') || upper.includes('PENDING') || upper.includes('KEY_REQUIRED')) {
    color = 'bg-amber-950/70 text-amber-300 border-amber-700/60';
    icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-400" />;
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color} ${className}`}
      title={`Evidence Status: ${status}`}
    >
      {icon}
      {status}
    </span>
  );
};

