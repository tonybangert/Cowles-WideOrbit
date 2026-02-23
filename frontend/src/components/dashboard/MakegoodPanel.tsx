/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  data: any;
}

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

export default function MakegoodPanel({ data }: Props) {
  if (!data) return null;

  const stations: any[] = data.stations ?? [];
  const byDaypart: any[] = data.by_daypart ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">
        Makegood &amp; Preemption Summary
      </h3>
      <p className="text-xs text-gray-500 mb-4">
        Combined rate &gt; 5% flagged as operational issue
      </p>

      {/* By Station */}
      <div className="overflow-x-auto mb-6">
        <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
          By Station
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs text-gray-500 uppercase tracking-wide">
              <th className="py-2 pr-4">Station</th>
              <th className="py-2 pr-4 text-right">Preempted</th>
              <th className="py-2 pr-4 text-right">Makegood</th>
              <th className="py-2 pr-4 text-right">Total</th>
              <th className="py-2 pr-4 text-right">Combined %</th>
              <th className="py-2 pr-4 text-right">Revenue Impact</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {stations.map((s: any) => (
              <tr key={s.station} className="border-b border-gray-100">
                <td className="py-2 pr-4 font-medium text-gray-900">{s.station}</td>
                <td className="py-2 pr-4 text-right text-gray-600">{s.preempted}</td>
                <td className="py-2 pr-4 text-right text-gray-600">{s.makegood}</td>
                <td className="py-2 pr-4 text-right text-gray-600">{s.total_spots}</td>
                <td className={`py-2 pr-4 text-right font-medium ${s.flag ? 'text-amber-600' : 'text-gray-900'}`}>
                  {s.combined_rate}%
                </td>
                <td className="py-2 pr-4 text-right text-gray-600">
                  {formatCurrency(s.revenue_impact)}
                </td>
                <td className="py-2">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                    s.flag
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {s.flag ? 'Flag' : 'OK'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* By Daypart */}
      <div className="overflow-x-auto">
        <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
          By Daypart
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs text-gray-500 uppercase tracking-wide">
              <th className="py-2 pr-4">Daypart</th>
              <th className="py-2 pr-4 text-right">Preempted</th>
              <th className="py-2 pr-4 text-right">Makegood</th>
              <th className="py-2 pr-4 text-right">Total</th>
              <th className="py-2 pr-4 text-right">Combined %</th>
              <th className="py-2 pr-4 text-right">Revenue Impact</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {byDaypart.map((d: any) => (
              <tr key={d.daypart} className="border-b border-gray-100">
                <td className="py-2 pr-4 font-medium text-gray-900">
                  {d.daypart}
                  <span className="text-xs text-gray-500 ml-1">({d.daypart_name})</span>
                </td>
                <td className="py-2 pr-4 text-right text-gray-600">{d.preempted}</td>
                <td className="py-2 pr-4 text-right text-gray-600">{d.makegood}</td>
                <td className="py-2 pr-4 text-right text-gray-600">{d.total_spots}</td>
                <td className={`py-2 pr-4 text-right font-medium ${d.flag ? 'text-amber-600' : 'text-gray-900'}`}>
                  {d.combined_rate}%
                </td>
                <td className="py-2 pr-4 text-right text-gray-600">
                  {formatCurrency(d.revenue_impact)}
                </td>
                <td className="py-2">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                    d.flag
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {d.flag ? 'Flag' : 'OK'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
