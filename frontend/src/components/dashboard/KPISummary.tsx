import { DollarSign, TrendingUp, Percent, AlertTriangle } from 'lucide-react';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  revenueData: any;
  selloutData: any;
  makegoodData: any;
  aurData: any;
}

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export default function KPISummary({ revenueData, selloutData, makegoodData, aurData }: Props) {
  // Total Revenue
  const totalRevenue = revenueData?.total_cy ?? 0;
  const revenueYoY = revenueData?.total_yoy_pct ?? 0;

  // Overall AUR — average across all daypart series
  let overallAUR = 0;
  if (aurData?.series) {
    const allValues: number[] = [];
    Object.values(aurData.series).forEach((vals: any) => {
      (vals as (number | null)[]).forEach(v => {
        if (v !== null) allValues.push(v);
      });
    });
    overallAUR = allValues.length > 0 ? allValues.reduce((a, b) => a + b, 0) / allValues.length : 0;
  }

  // Average sell-out rate
  let avgSellout = 0;
  let selloutFlag = false;
  if (selloutData?.dayparts) {
    const rates = selloutData.dayparts.map((d: any) => d.cy_rate);
    avgSellout = rates.reduce((a: number, b: number) => a + b, 0) / rates.length;
    selloutFlag = selloutData.dayparts.some((d: any) => d.pricing_flag);
  }

  // Average makegood combined rate
  let avgMakegood = 0;
  let makegoodFlag = false;
  if (makegoodData?.stations) {
    const rates = makegoodData.stations.map((s: any) => s.combined_rate);
    avgMakegood = rates.length > 0 ? rates.reduce((a: number, b: number) => a + b, 0) / rates.length : 0;
    makegoodFlag = makegoodData.stations.some((s: any) => s.flag);
  }

  const cards = [
    {
      label: 'Total Revenue (CY)',
      value: formatCurrency(totalRevenue),
      sub: `${revenueYoY >= 0 ? '+' : ''}${revenueYoY}% YoY`,
      icon: DollarSign,
      flag: false,
    },
    {
      label: 'Overall AUR',
      value: `$${overallAUR.toFixed(0)}`,
      sub: 'Avg unit rate',
      icon: TrendingUp,
      flag: false,
    },
    {
      label: 'Sell-out Rate',
      value: `${avgSellout.toFixed(1)}%`,
      sub: selloutFlag ? 'Pricing opportunity' : 'Across dayparts',
      icon: Percent,
      flag: selloutFlag,
    },
    {
      label: 'Makegood Rate',
      value: `${avgMakegood.toFixed(1)}%`,
      sub: makegoodFlag ? 'Operational flag' : 'Combined rate',
      icon: AlertTriangle,
      flag: makegoodFlag,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(card => (
        <div
          key={card.label}
          className={`bg-white rounded-xl p-4 border ${
            card.flag ? 'border-amber-300' : 'border-gray-200'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {card.label}
            </span>
            <card.icon className={`w-4 h-4 ${card.flag ? 'text-amber-500' : 'text-gray-400'}`} />
          </div>
          <p className="text-2xl font-bold text-gray-900">{card.value}</p>
          <p className={`text-xs mt-1 ${card.flag ? 'text-amber-600 font-medium' : 'text-gray-500'}`}>
            {card.sub}
          </p>
        </div>
      ))}
    </div>
  );
}
