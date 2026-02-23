import { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import KPISummary from '../components/dashboard/KPISummary';
import RevenueDaypartPanel from '../components/dashboard/RevenueDaypartPanel';
import AURTrendsPanel from '../components/dashboard/AURTrendsPanel';
import AdvertiserPanel from '../components/dashboard/AdvertiserPanel';
import SelloutPanel from '../components/dashboard/SelloutPanel';
import MakegoodPanel from '../components/dashboard/MakegoodPanel';

const API = import.meta.env.VITE_API_URL || '';

interface Alert {
  type: 'sellout' | 'concentration' | 'makegood';
  message: string;
}

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function DashboardPage() {
  const [stations, setStations] = useState<string[]>([]);
  const [selectedStation, setSelectedStation] = useState('');
  const [loading, setLoading] = useState(true);

  const [revenueData, setRevenueData] = useState<any>(null);
  const [aurData, setAurData] = useState<any>(null);
  const [advertiserData, setAdvertiserData] = useState<any>(null);
  const [selloutData, setSelloutData] = useState<any>(null);
  const [makegoodData, setMakegoodData] = useState<any>(null);

  const [alerts, setAlerts] = useState<Alert[]>([]);

  // Load station list once
  useEffect(() => {
    fetch(`${API}/api/data/stations`)
      .then(r => r.json())
      .then(d => setStations(d.stations))
      .catch(console.error);
  }, []);

  // Fetch all panels when station changes
  const fetchData = useCallback(() => {
    setLoading(true);
    const qs = selectedStation ? `?station=${encodeURIComponent(selectedStation)}` : '';

    Promise.all([
      fetch(`${API}/api/data/revenue-by-daypart${qs}`).then(r => r.json()),
      fetch(`${API}/api/data/aur-trends${qs}`).then(r => r.json()),
      fetch(`${API}/api/data/top-advertisers${qs}`).then(r => r.json()),
      fetch(`${API}/api/data/sellout-rates${qs}`).then(r => r.json()),
      fetch(`${API}/api/data/makegood-summary${qs}`).then(r => r.json()),
    ])
      .then(([rev, aur, adv, sell, mg]) => {
        setRevenueData(rev);
        setAurData(aur);
        setAdvertiserData(adv);
        setSelloutData(sell);
        setMakegoodData(mg);

        // Compute alerts
        const newAlerts: Alert[] = [];

        sell.dayparts?.forEach((dp: any) => {
          if (dp.pricing_flag) {
            newAlerts.push({
              type: 'sellout',
              message: `${dp.daypart_name} sell-out at ${dp.cy_rate}% — pricing opportunity`,
            });
          }
        });

        adv.advertisers?.forEach((a: any) => {
          if (a.concentration_flag) {
            newAlerts.push({
              type: 'concentration',
              message: `${a.name} at ${a.share_pct}% share — concentration risk`,
            });
          }
        });

        mg.stations?.forEach((s: any) => {
          if (s.flag) {
            newAlerts.push({
              type: 'makegood',
              message: `${s.station} combined rate ${s.combined_rate}% — operational issue`,
            });
          }
        });

        setAlerts(newAlerts);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedStation]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Station Filter */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Revenue Dashboard</h2>
          <select
            value={selectedStation}
            onChange={e => setSelectedStation(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-purple/50"
          >
            <option value="">All Stations</option>
            {stations.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Alert Banner */}
        {alerts.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-amber-800">
                  {alerts.length} alert{alerts.length > 1 ? 's' : ''} detected
                </p>
                {alerts.map((a, i) => (
                  <p key={i} className="text-sm text-amber-700">• {a.message}</p>
                ))}
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-brand-purple animate-spin" />
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <KPISummary
              revenueData={revenueData}
              selloutData={selloutData}
              makegoodData={makegoodData}
              aurData={aurData}
            />

            {/* 2-column chart grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RevenueDaypartPanel data={revenueData} />
              <AURTrendsPanel data={aurData} />
              <AdvertiserPanel data={advertiserData} />
              <SelloutPanel data={selloutData} />
            </div>

            {/* Full-width makegood table */}
            <MakegoodPanel data={makegoodData} />
          </>
        )}
      </div>
    </div>
  );
}
