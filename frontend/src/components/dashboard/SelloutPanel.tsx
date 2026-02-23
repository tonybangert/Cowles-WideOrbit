import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, Cell, ResponsiveContainer,
} from 'recharts';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  data: any;
}

export default function SelloutPanel({ data }: Props) {
  if (!data?.dayparts) return null;

  const chartData = data.dayparts.map((d: any) => ({
    name: d.daypart,
    'Current Year': d.cy_rate,
    'Prior Year': d.py_rate,
    flag: d.pricing_flag,
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Sell-out Rates</h3>
      <p className="text-xs text-gray-500 mb-4">
        Inventory utilization by daypart — 85% threshold for pricing opportunity
      </p>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} barGap={2}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(v: number) => `${v}%`}
            tick={{ fontSize: 11 }}
          />
          <Tooltip formatter={(v: number | string | undefined) => [`${v ?? 0}%`, undefined]} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <ReferenceLine
            y={85}
            stroke="#f59e0b"
            strokeDasharray="6 3"
            label={{ value: '85%', position: 'right', fontSize: 10, fill: '#f59e0b' }}
          />
          <Bar dataKey="Current Year" radius={[3, 3, 0, 0]}>
            {chartData.map((entry: any, idx: number) => (
              <Cell
                key={idx}
                fill={entry.flag ? '#f59e0b' : '#673791'}
              />
            ))}
          </Bar>
          <Bar dataKey="Prior Year" fill="#41BEB0" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
