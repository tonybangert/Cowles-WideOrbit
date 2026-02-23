import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  data: any;
}

export default function RevenueDaypartPanel({ data }: Props) {
  if (!data?.dayparts) return null;

  const chartData = data.dayparts.map((d: any) => ({
    name: d.daypart,
    'Current Year': d.cy_revenue,
    'Prior Year': d.py_revenue,
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Revenue by Daypart</h3>
      <p className="text-xs text-gray-500 mb-4">
        CY vs PY &nbsp;|&nbsp; YoY: {data.total_yoy_pct >= 0 ? '+' : ''}{data.total_yoy_pct}%
      </p>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} barGap={2}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis
            tickFormatter={(v: number) =>
              v >= 1000 ? `$${(v / 1000).toFixed(0)}K` : `$${v}`
            }
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value: number | string | undefined) => [`$${Number(value ?? 0).toLocaleString()}`, undefined]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Current Year" fill="#673791" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Prior Year" fill="#41BEB0" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
