import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { fetchAdminStats, fetchTenderStats, AdminStats, TenderStats } from "@/services/adminApi";

const PERIODS = [
  { label: "7 Days", value: "7d" },
  { label: "10 Days", value: "10d" },
  { label: "6 Months", value: "6m" },
  { label: "12 Months", value: "12m" },
];

const STAT_LABELS: Record<keyof AdminStats, string> = {
  total_users: "TOTAL USERS",
  active_users: "ACTIVE USERS",
  applied_tenders: "APPLIED TENDERS",
  discarded_tenders: "DISCARDED TENDERS",
};

const todayLabel = () =>
  new Date().toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

const Dashboard = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [chartData, setChartData] = useState<TenderStats | null>(null);
  const [period, setPeriod] = useState("7d");
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingChart, setLoadingChart] = useState(true);

  useEffect(() => {
    fetchAdminStats()
      .then(setStats)
      .finally(() => setLoadingStats(false));
  }, []);

  useEffect(() => {
    setLoadingChart(true);
    fetchTenderStats(period)
      .then(setChartData)
      .finally(() => setLoadingChart(false));
  }, [period]);

  const chartRows =
    chartData?.labels.map((label, i) => ({
      label,
      Applied: chartData.applied[i],
      Discarded: chartData.discarded[i],
    })) ?? [];

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-3xl font-bold text-[#4040E0]">Hello Admin</h1>
        <p className="text-sm text-[#68708a] mt-1">Today is {todayLabel()}</p>
      </div>

      {/* Stat cards */}
      {loadingStats ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-white animate-pulse" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {(Object.keys(STAT_LABELS) as Array<keyof AdminStats>).map((key) => (
            <div key={key} className="bg-white rounded-xl p-5 shadow-sm border border-[#F3F4F6]">
              <p className="text-xs font-semibold tracking-widest text-[#9CA3AF] uppercase mb-3">
                {STAT_LABELS[key]}
              </p>
              <p className="text-3xl font-bold text-[#252a39]">
                {stats[key].toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {/* Chart */}
      <div className="bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-[#F3F4F6]">
        {/* Chart header: title left, period buttons + legend (stacked) right */}
        <div className="flex items-start justify-between gap-3 mb-5">
          <h2 className="text-base font-semibold text-[#252a39]">Tenders Statistics</h2>

          <div className="flex flex-col items-end gap-2">
            {/* Period buttons */}
            <div className="flex gap-1">
              {PERIODS.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setPeriod(p.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    period === p.value
                      ? "border border-[#4040E0] text-[#4040E0] bg-white"
                      : "text-[#9CA3AF] hover:text-[#252a39]"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Legend — stacked vertically below period buttons */}
            <div className="flex flex-col gap-1">
              <span className="flex items-center gap-1.5 text-xs text-[#6B7280]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#4040E0] inline-block" />
                Applied
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[#6B7280]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#1F2937] inline-block" />
                Discarded
              </span>
            </div>
          </div>
        </div>

        {loadingChart ? (
          <div className="h-56 flex items-center justify-center text-sm text-[#68708a]">
            Loading chart...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartRows} barGap={4} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="0" stroke="#F3F4F6" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: "#9CA3AF" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: "#9CA3AF" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #E5E7EB", fontSize: 12 }}
                cursor={{ fill: "#F9FAFB" }}
              />
              <Bar dataKey="Applied" fill="#4040E0" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Discarded" fill="#1F2937" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
