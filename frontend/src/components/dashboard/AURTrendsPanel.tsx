import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  data: any;
}

const DAYPART_COLORS: Record<string, string> = {
  EM: '#6366f1',
  DT: '#f59e0b',
  EF: '#10b981',
  EN: '#3b82f6',
  PA: '#8b5cf6',
  PR: '#673791',
  LN: '#ef4444',
  LF: '#64748b',
};

const ALL_DAYPARTS = ['EM', 'DT', 'EF', 'EN', 'PA', 'PR', 'LN', 'LF'];
const DEFAULTS = new Set(['PR', 'EN', 'PA']);

export default function AURTrendsPanel({ data }: Props) {
  const [active, setActive] = useState<Set<string>>(DEFAULTS);

  if (!data?.periods || !data?.series) return null;

  const toggle = (dp: string) => {
    setActive(prev => {
      const next = new Set(prev);
      if (next.has(dp)) next.delete(dp);
      else next.add(dp);
      return next;
    });
  };

  // Build rows: { period, EM, DT, ... }
  const chartData = data.periods.map((p: string, i: number) => {
    const row: any = { period: p };
    ALL_DAYPARTS.forEach(dp => {
      row[dp] = data.series[dp]?.[i] ?? null;
    });
    return row;
  });

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">AUR Trends</h3>
      <p className="text-xs text-gray-500 mb-3">Average Unit Rate by daypart (monthly)</p>

      {/* Daypart toggle pills */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {ALL_DAYPARTS.map(dp => (
          <button
            key={dp}
            onClick={() => toggle(dp)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
              active.has(dp)
                ? 'text-white'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
            style={active.has(dp) ? { backgroundColor: DAYPART_COLORS[dp] } : undefined}
          >
            {dp}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={(v: number) => `$${v}`}
            tick={{ fontSize: 11 }}
          />
          <Tooltip formatter={(v: number | string | undefined) => [`$${Number(v ?? 0).toFixed(2)}`, undefined]} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {ALL_DAYPARTS.filter(dp => active.has(dp)).map(dp => (
            <Line
              key={dp}
              type="monotone"
              dataKey={dp}
              stroke={DAYPART_COLORS[dp]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
