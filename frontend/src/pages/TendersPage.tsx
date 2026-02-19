import { useMemo, useState } from "react";
import { ChevronDown, SendHorizontal, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import ShareTender from "@/components/modals/ShareTender";
import TenderMatchCard from "@/components/tenders/TenderMatchCardNew";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { getCompanyId } from "@/lib/auth";
import { fetchCompanyMatches, updateTenderAction } from "@/services/tenderAgentApi";

const TendersPage = () => {
  const navigate = useNavigate();
  const companyId = getCompanyId();
  const { pushToast } = useToastSimple();
  const queryClient = useQueryClient();

  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [keywordDraft, setKeywordDraft] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [stateFilter, setStateFilter] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [certificationFilter, setCertificationFilter] = useState("");
  const [portalFilter, setPortalFilter] = useState("");
  const [minVisibleScore, setMinVisibleScore] = useState(0);
  const [timePeriod, setTimePeriod] = useState("latest");
  const [sort, setSort] = useState("best_match");
  const [page, setPage] = useState(1);
  const [selectedShareTenderId, setSelectedShareTenderId] = useState<string | null>(null);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    state: false,
    city: false,
    certification: false,
    procurement: false,
    organisation: false,
    amount: false,
    portal: true,
    language: false,
  });

  const searchQuery = useMemo(() => {
    const parts = [search.trim(), ...keywords].map((item) => item.trim()).filter(Boolean);
    return parts.join(" ");
  }, [search, keywords]);

  const params = useMemo(
    () => ({
      q: searchQuery || undefined,
      time_period: timePeriod,
      sort,
      min_score: 0.8,
      page,
      limit: 6,
    }),
    [searchQuery, timePeriod, sort, page]
  );

  const { data, isLoading } = useQuery({
    queryKey: ["matches", companyId, params],
    queryFn: () => fetchCompanyMatches(companyId || "", params),
    enabled: Boolean(companyId),
  });

  const items = useMemo(() => {
    const all = data?.items || [];
    return all.filter((item) => {
      const meta = item.tender.metadata || {};
      const location = String(meta.location || "").toLowerCase();
      const domains = (meta.domains || []).map((value) => String(value).toLowerCase());
      const certs = (meta.required_certifications || []).map((value) => String(value).toLowerCase());
      const portal = String(item.tender.portal || "gem").toLowerCase();
      const score = item.match?.score || 0;

      if (stateFilter && !location.includes(stateFilter.toLowerCase())) return false;
      if (cityFilter && !location.includes(cityFilter.toLowerCase())) return false;
      if (certificationFilter && !certs.some((value) => value.includes(certificationFilter.toLowerCase()))) return false;
      if (portalFilter && portal !== portalFilter.toLowerCase()) return false;
      if (minVisibleScore > 0 && score < minVisibleScore / 100) return false;
      return true;
    });
  }, [data?.items, stateFilter, cityFilter, certificationFilter, portalFilter, minVisibleScore]);

  const actionMutation = useMutation({
    mutationFn: ({ tenderId, action }: { tenderId: string; action: "saved" | "applied" | "discarded" | null }) =>
      updateTenderAction(tenderId, {
        company_id: companyId || "",
        action,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches", companyId] });
      queryClient.invalidateQueries({ queryKey: ["dashboardStats", companyId] });
    },
    onError: () => {
      pushToast("Unable to update tender action", "error");
    },
  });

  const totalPages = Math.max(1, Math.ceil((data?.total || 0) / (data?.limit || 1)));

  const handleSearch = () => {
    setPage(1);
    setSearch(searchDraft);
  };

  const addKeyword = () => {
    const cleaned = keywordDraft.trim();
    if (!cleaned) return;
    if (!keywords.some((item) => item.toLowerCase() === cleaned.toLowerCase())) {
      setKeywords((prev) => [...prev, cleaned]);
      setPage(1);
    }
    setKeywordDraft("");
  };

  const clearAllFilters = () => {
    setSearchDraft("");
    setSearch("");
    setKeywordDraft("");
    setKeywords([]);
    setStateFilter("");
    setCityFilter("");
    setCertificationFilter("");
    setPortalFilter("");
    setMinVisibleScore(0);
    setPage(1);
  };

  const toggleSection = (key: string) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const filterRowClass = "border-t border-[#e6e9f1] px-4 py-3";

  return (
    <div>
      <div className="mb-4 flex items-center gap-2">
        <h1 className="text-3xl font-semibold text-[#232937] md:text-4xl">Current Active Tenders</h1>
        <p className="text-sm text-[#7d8599]">{data?.total || 0} results</p>
      </div>

      <div className="grid gap-5 xl:grid-cols-[250px_minmax(0,1fr)]">
        <aside className="rounded-xl border border-[#d8dce6] bg-white">
          <div className="flex items-center justify-between px-4 py-3">
            <h2 className="text-xl font-semibold text-[#283043]">Filters</h2>
            <button onClick={clearAllFilters} className="text-sm text-[#4d55e0]">
              Clear all
            </button>
          </div>

          <div className={filterRowClass}>
            <p className="mb-2 text-sm font-medium text-[#2f374a]">Keywords</p>
            <div className="flex gap-2">
              <input
                value={keywordDraft}
                onChange={(event) => setKeywordDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    addKeyword();
                  }
                }}
                placeholder="Add keyword..."
                className="h-10 min-w-0 flex-1 rounded-md border border-[#d6dbe8] px-3 text-sm"
              />
              <button onClick={addKeyword} className="rounded-md bg-[#8e97ff] px-3 text-sm text-white">
                Add
              </button>
            </div>
            {keywords.length ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="inline-flex items-center gap-1 rounded-full border border-[#d4d9e8] bg-[#f3f5fb] px-2 py-0.5 text-xs"
                  >
                    {keyword}
                    <button
                      onClick={() => setKeywords((prev) => prev.filter((value) => value !== keyword))}
                      className="text-[#8a90a4]"
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("state")}>
              <span>State</span>
              <ChevronDown size={16} className={openSections.state ? "rotate-180" : ""} />
            </button>
            {openSections.state ? (
              <input
                value={stateFilter}
                onChange={(event) => setStateFilter(event.target.value)}
                placeholder="e.g. Gujarat"
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              />
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("city")}>
              <span>City</span>
              <ChevronDown size={16} className={openSections.city ? "rotate-180" : ""} />
            </button>
            {openSections.city ? (
              <input
                value={cityFilter}
                onChange={(event) => setCityFilter(event.target.value)}
                placeholder="e.g. Jaipur"
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              />
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("certification")}>
              <span>Certification</span>
              <ChevronDown size={16} className={openSections.certification ? "rotate-180" : ""} />
            </button>
            {openSections.certification ? (
              <input
                value={certificationFilter}
                onChange={(event) => setCertificationFilter(event.target.value)}
                placeholder="e.g. ISO"
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              />
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("procurement")}>
              <span>Procurement Type</span>
              <ChevronDown size={16} className={openSections.procurement ? "rotate-180" : ""} />
            </button>
          </div>
          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("organisation")}>
              <span>Organisation</span>
              <ChevronDown size={16} className={openSections.organisation ? "rotate-180" : ""} />
            </button>
          </div>
          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("amount")}>
              <span>Tender Amount</span>
              <ChevronDown size={16} className={openSections.amount ? "rotate-180" : ""} />
            </button>
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("portal")}>
              <span>Portal</span>
              <ChevronDown size={16} className={openSections.portal ? "rotate-180" : ""} />
            </button>
            {openSections.portal ? (
              <select
                value={portalFilter}
                onChange={(event) => setPortalFilter(event.target.value)}
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              >
                <option value="">All</option>
                <option value="gem">GeM</option>
              </select>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-sm text-[#2f374a]" onClick={() => toggleSection("language")}>
              <span>Language</span>
              <ChevronDown size={16} className={openSections.language ? "rotate-180" : ""} />
            </button>
          </div>

          <div className={filterRowClass}>
            <p className="text-sm font-medium text-[#2f374a]">Minimum match shown</p>
            <input
              type="range"
              min={0}
              max={95}
              step={5}
              value={minVisibleScore}
              onChange={(event) => setMinVisibleScore(Number(event.target.value))}
              className="mt-2 w-full accent-[#4040E0]"
            />
            <p className="mt-1 text-xs text-[#7a8297]">{minVisibleScore}% and above</p>
          </div>
        </aside>

        <section className="min-w-0">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div className="flex items-end gap-2">
              <div>
                <p className="text-xs text-[#6f768b]">Time Period</p>
                <select
                  value={timePeriod}
                  onChange={(event) => {
                    setPage(1);
                    setTimePeriod(event.target.value);
                  }}
                  className="h-10 rounded border border-[#d3d7e2] bg-white px-3 text-sm"
                >
                  <option value="latest">Latest</option>
                  <option value="7d">7 Days</option>
                  <option value="30d">30 Days</option>
                </select>
              </div>
              <div>
                <p className="text-xs text-[#6f768b]">Sort By</p>
                <select
                  value={sort}
                  onChange={(event) => {
                    setPage(1);
                    setSort(event.target.value);
                  }}
                  className="h-10 rounded border border-[#d3d7e2] bg-white px-3 text-sm"
                >
                  <option value="best_match">Best Match (&gt;80%)</option>
                  <option value="latest">Latest</option>
                </select>
              </div>
            </div>
          </div>

          <div className="mb-4 flex items-center gap-2">
            <input
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch();
                }
              }}
              placeholder="Search tender"
              className="h-11 flex-1 rounded-full border border-[#d5d9e3] bg-white px-4 text-sm"
            />
            <button
              onClick={handleSearch}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-[#4040E0] text-white"
            >
              <SendHorizontal size={16} />
            </button>
          </div>

          {isLoading ? <p className="text-sm text-[#6f768b]">Loading matches...</p> : null}

          {!isLoading && !items.length ? (
            <div className="rounded-xl border border-[#d8dce6] bg-white p-6 text-sm text-[#5f667a]">
              No tenders matched your current filters. Try reducing filters or click <strong>Clear all</strong>.
            </div>
          ) : null}

          <div className="space-y-3">
            {items.map((item) => (
              <TenderMatchCard
                key={item.tender.id}
                item={item}
                onOpen={(tenderId) => navigate(`/tenders/${tenderId}`)}
                onAction={(tenderId, action) => actionMutation.mutate({ tenderId, action })}
                onShare={(tenderId) => setSelectedShareTenderId(tenderId)}
              />
            ))}
          </div>

          <div className="mt-5 flex items-center justify-between">
            <button
              disabled={page <= 1}
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              className="rounded-md bg-[#eff1f5] px-4 py-2 text-xs text-[#7f8798] disabled:opacity-60"
            >
              Prev
            </button>

            <div className="flex items-center gap-2">
              {Array.from({ length: totalPages }).map((_, index) => {
                const value = index + 1;
                return (
                  <button
                    key={value}
                    onClick={() => setPage(value)}
                    className={[
                      "h-8 w-8 rounded-full text-xs",
                      value === page ? "bg-[#4040E0] text-white" : "bg-[#eff1f5] text-[#7f8798]",
                    ].join(" ")}
                  >
                    {value}
                  </button>
                );
              })}
            </div>

            <button
              disabled={page >= totalPages}
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              className="rounded-md bg-[#eff1f5] px-4 py-2 text-xs text-[#7f8798] disabled:opacity-60"
            >
              Next
            </button>
          </div>
        </section>
      </div>

      <ShareTender
        open={Boolean(selectedShareTenderId)}
        onClose={() => setSelectedShareTenderId(null)}
        tenderId={selectedShareTenderId || ""}
        companyId={companyId || ""}
      />
    </div>
  );
};

export default TendersPage;
