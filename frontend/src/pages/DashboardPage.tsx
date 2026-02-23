import { useMemo, useState } from "react";
import { format } from "date-fns";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getCompanyId } from "@/lib/auth";
import { fetchDashboardReport, fetchDashboardStats, triggerScrapeAnalyze } from "@/services/tenderAgentApi";
import { useToastSimple } from "@/components/ui/toaster-simple";
import totalAnalyzedIcon from "@/assets/dashboard/total-analyzed-card-icon.svg";
import bestFoundIcon from "@/assets/dashboard/best-found.svg";
import savedIcon from "@/assets/dashboard/saved.svg";
import appliedIcon from "@/assets/dashboard/applied.svg";
import findMatchingTendersButton from "@/assets/dashboard/find-matching-tenders-button.svg";
import reportGatheringDot from "@/assets/dashboard/report-gathering-dot.svg";
import reportAnalyzeDot from "@/assets/dashboard/report-analyze-dot.svg";
import reportSavedDot from "@/assets/dashboard/report-saved-dot.svg";
import reportGatheringBar from "@/assets/dashboard/report-gathering-bar.svg";
import reportAnalyzeBar from "@/assets/dashboard/report-analyze-bar.svg";
import reportSavedBar from "@/assets/dashboard/report-saved-bar-alt.svg";

const DashboardPage = () => {
  const companyId = getCompanyId() || undefined;
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();
  const [reportRange, setReportRange] = useState("12m");
  const [overviewRange, setOverviewRange] = useState("7d");

  const rangeOptions = [
    { value: "7d", label: "7 Days" },
    { value: "10d", label: "10 Days" },
    { value: "6m", label: "6 Months" },
    { value: "12m", label: "12 Months" },
  ] as const;

  const { data: stats } = useQuery({
    queryKey: ["dashboardStats", companyId, overviewRange],
    queryFn: () => fetchDashboardStats(companyId, overviewRange),
    enabled: Boolean(companyId),
  });

  const { data: report } = useQuery({
    queryKey: ["dashboardReport", companyId, reportRange],
    queryFn: () => fetchDashboardReport(reportRange, companyId),
    enabled: Boolean(companyId),
  });

  const chartData = useMemo(() => {
    if (!report) return [];
    return report.labels.map((label, index) => ({
      label,
      gathering: report.series.gathering[index] || 0,
      analyze: report.series.analyze[index] || 0,
      saved: report.series.saved[index] || 0,
    }));
  }, [report]);

  const todayText = `Today is ${format(new Date(), "EEEE, d MMMM yyyy")}`;

  const reportLegend = [
    { label: "Gathering", dot: reportGatheringDot },
    { label: "Analyze", dot: reportAnalyzeDot },
    { label: "Saved", dot: reportSavedDot },
  ];
  const selectedOverview = stats?.overview || stats?.overview_last_7_days;

  const cards = [
    {
      title: "TOTAL TENDERS ANALYZED",
      value: stats?.totals.tenders_analyzed || 0,
      icon: totalAnalyzedIcon,
      iconAlt: "Total tenders analyzed icon",
    },
    {
      title: "BEST TENDERS FOUND",
      value: stats?.totals.best_tenders_found || 0,
      icon: bestFoundIcon,
      iconAlt: "Best tenders found icon",
    },
    {
      title: "TENDERS SAVED",
      value: stats?.totals.tenders_saved || 0,
      icon: savedIcon,
      iconAlt: "Tenders saved icon",
    },
    {
      title: "TENDERS APPLIED",
      value: stats?.totals.tenders_applied || 0,
      icon: appliedIcon,
      iconAlt: "Tenders applied icon",
    },
  ];

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-[#2a3040] md:text-4xl">Hello, [{stats?.company_name || "Company Name"}]</h1>
          <p className="mt-1 text-base text-[#4d556c] md:text-xl">{todayText}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              try {
                await triggerScrapeAnalyze();
                pushToast("Scrape & Analyze triggered", "success");
              } catch {
                pushToast("Unable to trigger scrape job", "error");
              }
            }}
            className="h-11 rounded-full border border-[#4040E0] px-5 text-sm text-[#4040E0]"
          >
            Scrape & Analyze now
          </button>
          <button
            onClick={() => navigate("/tenders")}
            className="h-[50px] w-[250px] shrink-0 overflow-hidden rounded-[18px]"
          >
            <img src={findMatchingTendersButton} alt="Find Matching Tenders" className="h-full w-full object-cover" />
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.title} className="rounded-xl border border-[#d8dce6] bg-white p-4">
            <p className="text-xs tracking-[0.2em] text-[#8a92a7]">{card.title}</p>
            <div className="mt-1 flex items-end justify-between gap-3">
              <p className="text-3xl font-semibold text-[#1f2533]">{card.value}</p>
              <img src={card.icon} alt={card.iconAlt} className="h-9 w-9 shrink-0 object-contain md:h-10 md:w-10" />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_320px]">
        <div className="rounded-xl border border-[#d8dce6] bg-white px-5 py-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[#262b38]">Tenders Report</h2>
            <div className="flex items-center gap-2">
              {rangeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setReportRange(option.value)}
                  className={[
                    "h-8 rounded-md px-3 text-xs transition",
                    reportRange === option.value
                      ? "border border-[#b7bdca] bg-white font-medium text-[#1f2533]"
                      : "text-[#7f8799] hover:text-[#4e5567]",
                  ].join(" ")}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex h-[320px] gap-4">
            <div className="min-w-0 flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} barSize={4}>
                  <CartesianGrid stroke="#eef0f5" vertical={false} />
                  <XAxis dataKey="label" fontSize={11} />
                  <YAxis fontSize={11} />
                  <Tooltip />
                  <Bar
                    dataKey="gathering"
                    shape={(props: any) => (
                      <image
                        href={reportGatheringBar}
                        x={props.x}
                        y={props.y}
                        width={props.width}
                        height={props.height}
                        preserveAspectRatio="none"
                      />
                    )}
                  />
                  <Bar
                    dataKey="analyze"
                    shape={(props: any) => (
                      <image
                        href={reportAnalyzeBar}
                        x={props.x}
                        y={props.y}
                        width={props.width}
                        height={props.height}
                        preserveAspectRatio="none"
                      />
                    )}
                  />
                  <Bar
                    dataKey="saved"
                    shape={(props: any) => (
                      <image
                        href={reportSavedBar}
                        x={props.x}
                        y={props.y}
                        width={props.width}
                        height={props.height}
                        preserveAspectRatio="none"
                      />
                    )}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="w-[90px] pt-6">
              <div className="space-y-3 text-[13px] text-[#3f4759]">
                {reportLegend.map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    <img src={item.dot} alt={`${item.label} legend dot`} className="h-2 w-2 shrink-0" />
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[#d8dce6] bg-white px-5 py-5">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[#262b38]">Tenders Overview</h2>
            <select
              value={overviewRange}
              onChange={(event) => setOverviewRange(event.target.value)}
              className="rounded border border-transparent bg-transparent px-1 py-1 text-xs font-medium text-[#1f2533] outline-none"
            >
              {rangeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  Last {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-5 text-[14px] text-[#434a5f]">
            <div className="flex items-center justify-between">
              <span>Tenders Gathering</span>
              <span className="font-semibold text-[#1f2533]">{(selectedOverview?.gathering || 0).toLocaleString("en-IN")}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Tenders Analyzed</span>
              <span className="font-semibold text-[#1f2533]">{(selectedOverview?.analyzed || 0).toLocaleString("en-IN")}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Tenders Saved</span>
              <span className="font-semibold text-[#1f2533]">{(selectedOverview?.saved || 0).toLocaleString("en-IN")}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Tenders Applied</span>
              <span className="font-semibold text-[#1f2533]">{(selectedOverview?.applied || 0).toLocaleString("en-IN")}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
