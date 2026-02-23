import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ResponsiveContainer,
} from 'recharts';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  data: any;
}

export default function AdvertiserPanel({ data }: Props) {
  if (!data?.advertisers) return null;

  const chartData = data.advertisers.map((a: any) => ({
    name: a.name,
    share: a.share_pct,
    flag: a.concentration_flag,
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Top Advertisers</h3>
      <p className="text-xs text-gray-500 mb-4">
        HHI: {data.hhi?.toLocaleString()} &nbsp;|&nbsp; Top 5 share: {data.top5_share}%
      </p>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} layout="vertical" barSize={16}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v: number) => `${v}%`}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={120}
            tick={{ fontSize: 10 }}
          />
          <Tooltip formatter={(v: number | string | undefined) => [`${v ?? 0}%`, 'Share']} />
          <Bar dataKey="share" radius={[0, 3, 3, 0]}>
            {chartData.map((entry: any, idx: number) => (
              <Cell
                key={idx}
                fill={entry.flag ? '#ef4444' : '#673791'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
