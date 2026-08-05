import type { ReactNode } from 'react';

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string;
  delta?: string;
  tone?: 'cyan' | 'green' | 'amber' | 'blue' | 'red';
}

export default function StatCard({ icon, label, value, delta, tone = 'cyan' }: StatCardProps) {
  const deltaClass = delta && delta.startsWith('-') ? 'down' : 'up';
  return (
    <div className="stat-card">
      <div className={`stat-icon tone-${tone}`}>{icon}</div>
      <div className="stat-body">
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {delta && <div className={`stat-delta ${deltaClass}`}>{delta}</div>}
      </div>
    </div>
  );
}
