import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, X } from "lucide-react";

import searchIcon from "@/assets/tenders/search.svg";
import sendIcon from "@/assets/tenders/send.svg";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import DiscardTender from "@/components/modals/DiscardTender";
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
  const [states, setStates] = useState<string[]>([]);
  const [stateDraft, setStateDraft] = useState("");
  const [cities, setCities] = useState<string[]>([]);
  const [cityDraft, setCityDraft] = useState("");
  const [certifications, setCertifications] = useState<string[]>([]);
  const [certDraft, setCertDraft] = useState("");
  const [organisations, setOrganisations] = useState<string[]>([]);
  const [orgDraft, setOrgDraft] = useState("");
  const [portalFilter, setPortalFilter] = useState("");
  const [procurementFilter, setProcurementFilter] = useState("");
  const [amountFilter, setAmountFilter] = useState("");
  const [sort, setSort] = useState("best_match");
  const [page, setPage] = useState(1);
  const [selectedShareTenderId, setSelectedShareTenderId] = useState<string | null>(null);
  const [discardTenderId, setDiscardTenderId] = useState<string | null>(null);
  const [sortOpen, setSortOpen] = useState(false);
  const sortRef = useRef<HTMLDivElement | null>(null);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    state: false,
    city: false,
    certification: false,
    procurement: false,
    organisation: false,
    amount: false,
    portal: true,
  });

  const addTag = (list: string[], setList: React.Dispatch<React.SetStateAction<string[]>>, value: string) => {
    const cleaned = value.trim();
    if (!cleaned) return;
    if (!list.some((v) => v.toLowerCase() === cleaned.toLowerCase())) {
      setList((prev) => [...prev, cleaned]);
      setPage(1);
    }
  };

  const searchQuery = useMemo(() => {
    const parts = [search.trim(), ...keywords].map((item) => item.trim()).filter(Boolean);
    return parts.join(" ");
  }, [search, keywords]);

  const params = useMemo(
    () => ({
      q: searchQuery || undefined,
      time_period: "latest",
      sort,
      min_score: 0.8,
      page,
      limit: 6,
      state: states.length ? states.join(",") : undefined,
      city: cities.length ? cities.join(",") : undefined,
      certification: certifications.length ? certifications.join(",") : undefined,
      portal: portalFilter || undefined,
      procurement: procurementFilter || undefined,
      organisation: organisations.length ? organisations.join(",") : undefined,
      amount_range: amountFilter || undefined,
    }),
    [searchQuery, sort, page, states, cities, certifications, portalFilter, procurementFilter, organisations, amountFilter]
  );

  const { data, isLoading } = useQuery({
    queryKey: ["matches", companyId, params],
    queryFn: () => fetchCompanyMatches(companyId || "", params),
    enabled: Boolean(companyId),
  });

  const items = data?.items || [];

  const actionMutation = useMutation({
    mutationFn: ({ tenderId, action, reason }: { tenderId: string; action: "saved" | "applied" | "discarded" | null; reason?: string }) =>
      updateTenderAction(tenderId, {
        company_id: companyId || "",
        action,
        reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches", companyId] });
      queryClient.invalidateQueries({ queryKey: ["dashboardStats", companyId] });
      setDiscardTenderId(null);
    },
    onError: () => {
      pushToast("Unable to update tender action", "error");
    },
  });

  const totalPages = Math.max(1, Math.ceil((data?.total || 0) / (data?.limit || 1)));

  const sortLabel =
    sort === "latest"
      ? "Latest"
      : sort === "closing_soon"
        ? "Closing Soon"
        : "Best Match (>80%)";

  useEffect(() => {
    if (!sortOpen) return;
    const handleClick = (event: MouseEvent) => {
      if (!sortRef.current) return;
      if (!sortRef.current.contains(event.target as Node)) {
        setSortOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [sortOpen]);

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
    setStates([]);
    setStateDraft("");
    setCities([]);
    setCityDraft("");
    setCertifications([]);
    setCertDraft("");
    setOrganisations([]);
    setOrgDraft("");
    setPortalFilter("");
    setProcurementFilter("");
    setAmountFilter("");
    setPage(1);
  };

  const toggleSection = (key: string) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const filterRowClass = "border-t border-[#e6e9f1] px-4 py-3";

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-baseline gap-2">
          <h1 className="text-[22px] font-semibold text-[#1f2533] md:text-[28px]">Current Active Tenders</h1>
          <p className="text-xs text-[#8a93a8] md:text-sm">{data?.total || 0} results</p>
        </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium text-[#6f768b]">Sort By</span>
            <div ref={sortRef} className="relative min-w-[170px]">
              <button
                type="button"
                onClick={() => setSortOpen((prev) => !prev)}
                className="flex h-9 w-full items-center rounded-md border border-[#d8dce6] bg-[#f2f4f8] pl-1 text-left focus:outline-none"
              >
                <span className="flex h-7 flex-1 items-center rounded-[6px] bg-white px-2 text-[12px] font-semibold text-[#232937]">
                  {sortLabel}
                </span>
                <span className="flex h-full w-9 items-center justify-center border-l border-[#e1e5f0] text-[#7b8293]">
                  <ChevronDown size={16} className={sortOpen ? "rotate-180" : ""} />
                </span>
              </button>
              {sortOpen ? (
                <div className="absolute right-0 z-10 mt-1 w-full overflow-hidden rounded-md border border-[#d8dce6] bg-white text-[12px] shadow-sm">
                  {[
                    { value: "best_match", label: "Best Match (>80%)" },
                    { value: "closing_soon", label: "Closing Soon" },
                    { value: "latest", label: "Latest" },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setSort(option.value);
                        setSortOpen(false);
                      }}
                      className={[
                        "w-full px-3 py-2 text-left hover:bg-[#eef1f7]",
                        option.value === sort ? "bg-[#f2f4ff] font-semibold text-[#232937]" : "text-[#232937]",
                      ].join(" ")}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </div>

      <div className="grid gap-5 xl:grid-cols-[250px_minmax(0,1fr)]">
        <aside className="sticky top-4 self-start overflow-y-auto max-h-[calc(100vh-6rem)] rounded-xl border border-[#dfe3ee] bg-white">
          <div className="flex items-center justify-between px-4 py-3">
            <h2 className="text-base font-semibold text-[#283043]">Filters</h2>
            <button onClick={clearAllFilters} className="text-xs text-[#4d55e0]">
              Clear all
            </button>
          </div>

          <div className={filterRowClass}>
            <p className="mb-2 text-xs font-semibold text-[#2f374a]">Keywords</p>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <span className="pointer-events-none absolute left-2 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-md border border-[#d6dbe8] bg-white">
                  <img src={searchIcon} alt="" className="h-4 w-4" />
                </span>
                <input
                  value={keywordDraft}
                  onChange={(event) => setKeywordDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      addKeyword();
                    }
                  }}
                  placeholder="Add keyword..."
                  className="h-9 w-full rounded-md border border-[#d6dbe8] pl-10 pr-3 text-sm"
                />
              </div>
              <button onClick={addKeyword} className="rounded-md bg-[#8e97ff] px-3 text-xs font-medium text-white">
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
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("state")}>
              <span>State</span>
              <ChevronDown size={16} className={openSections.state ? "rotate-180" : ""} />
            </button>
            {openSections.state ? (
              <>
                <input
                  value={stateDraft}
                  onChange={(event) => setStateDraft(event.target.value)}
                  onKeyDown={(event) => { if (event.key === "Enter") { addTag(states, setStates, stateDraft); setStateDraft(""); } }}
                  placeholder="e.g. Gujarat"
                  className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
                />
                {states.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {states.map((s) => (
                      <span key={s} className="inline-flex items-center gap-1 rounded-full border border-[#d4d9e8] bg-[#f3f5fb] px-2 py-0.5 text-xs">
                        {s}
                        <button onClick={() => setStates((prev) => prev.filter((v) => v !== s))} className="text-[#8a90a4]"><X size={12} /></button>
                      </span>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("city")}>
              <span>City</span>
              <ChevronDown size={16} className={openSections.city ? "rotate-180" : ""} />
            </button>
            {openSections.city ? (
              <>
                <input
                  value={cityDraft}
                  onChange={(event) => setCityDraft(event.target.value)}
                  onKeyDown={(event) => { if (event.key === "Enter") { addTag(cities, setCities, cityDraft); setCityDraft(""); } }}
                  placeholder="e.g. Jaipur"
                  className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
                />
                {cities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {cities.map((c) => (
                      <span key={c} className="inline-flex items-center gap-1 rounded-full border border-[#d4d9e8] bg-[#f3f5fb] px-2 py-0.5 text-xs">
                        {c}
                        <button onClick={() => setCities((prev) => prev.filter((v) => v !== c))} className="text-[#8a90a4]"><X size={12} /></button>
                      </span>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("certification")}>
              <span>Certification</span>
              <ChevronDown size={16} className={openSections.certification ? "rotate-180" : ""} />
            </button>
            {openSections.certification ? (
              <>
                <input
                  value={certDraft}
                  onChange={(event) => setCertDraft(event.target.value)}
                  onKeyDown={(event) => { if (event.key === "Enter") { addTag(certifications, setCertifications, certDraft); setCertDraft(""); } }}
                  placeholder="e.g. ISO"
                  className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
                />
                {certifications.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {certifications.map((c) => (
                      <span key={c} className="inline-flex items-center gap-1 rounded-full border border-[#d4d9e8] bg-[#f3f5fb] px-2 py-0.5 text-xs">
                        {c}
                        <button onClick={() => setCertifications((prev) => prev.filter((v) => v !== c))} className="text-[#8a90a4]"><X size={12} /></button>
                      </span>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("procurement")}>
              <span>Procurement Type</span>
              <ChevronDown size={16} className={openSections.procurement ? "rotate-180" : ""} />
            </button>
            {openSections.procurement ? (
              <select
                value={procurementFilter}
                onChange={(event) => { setProcurementFilter(event.target.value); setPage(1); }}
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              >
                <option value="">All</option>
                <option value="open">Open Bid</option>
                <option value="limited">Limited Bid</option>
                <option value="single">Single Bid</option>
              </select>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("organisation")}>
              <span>Organisation</span>
              <ChevronDown size={16} className={openSections.organisation ? "rotate-180" : ""} />
            </button>
            {openSections.organisation ? (
              <>
                <input
                  value={orgDraft}
                  onChange={(event) => setOrgDraft(event.target.value)}
                  onKeyDown={(event) => { if (event.key === "Enter") { addTag(organisations, setOrganisations, orgDraft); setOrgDraft(""); } }}
                  placeholder="e.g. Ministry of Defence"
                  className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
                />
                {organisations.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {organisations.map((o) => (
                      <span key={o} className="inline-flex items-center gap-1 rounded-full border border-[#d4d9e8] bg-[#f3f5fb] px-2 py-0.5 text-xs">
                        {o}
                        <button onClick={() => setOrganisations((prev) => prev.filter((v) => v !== o))} className="text-[#8a90a4]"><X size={12} /></button>
                      </span>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("amount")}>
              <span>Tender Amount</span>
              <ChevronDown size={16} className={openSections.amount ? "rotate-180" : ""} />
            </button>
            {openSections.amount ? (
              <select
                value={amountFilter}
                onChange={(event) => { setAmountFilter(event.target.value); setPage(1); }}
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              >
                <option value="">All</option>
                <option value="under_1L">Under 1 Lakh</option>
                <option value="1L_10L">1 - 10 Lakhs</option>
                <option value="10L_50L">10 - 50 Lakhs</option>
                <option value="50L_1Cr">50 Lakhs - 1 Crore</option>
                <option value="above_1Cr">Above 1 Crore</option>
              </select>
            ) : null}
          </div>

          <div className={filterRowClass}>
            <button className="flex w-full items-center justify-between text-xs text-[#2f374a]" onClick={() => toggleSection("portal")}>
              <span>Portal</span>
              <ChevronDown size={16} className={openSections.portal ? "rotate-180" : ""} />
            </button>
            {openSections.portal ? (
              <select
                value={portalFilter}
                onChange={(event) => { setPortalFilter(event.target.value); setPage(1); }}
                className="mt-2 h-9 w-full rounded-md border border-[#d6dbe8] px-2 text-sm"
              >
                <option value="">All</option>
                <option value="gem">GeM</option>
              </select>
            ) : null}
          </div>

        </aside>

        <section className="min-w-0">
          <div className="relative mb-4">
            <input
              value={searchDraft}
              onChange={(event) => {
                const value = event.target.value;
                setSearchDraft(value);
                if (!value.trim()) {
                  setSearch("");
                  setPage(1);
                }
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch();
                }
              }}
              placeholder="Search tender"
              className="h-11 w-full rounded-full border border-[#d5d9e3] bg-white pl-4 pr-12 text-sm text-[#232937]"
            />
            <button onClick={handleSearch} className="absolute right-1 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full">
              <img src={sendIcon} alt="" className="h-9 w-9" />
            </button>
          </div>

          {isLoading ? <p className="text-sm text-[#6f768b]">Loading matches...</p> : null}

          {!isLoading && !items.length ? (
            <div className="rounded-xl border border-[#d8dce6] bg-white p-6 text-sm text-[#5f667a]">
              No tenders matched your current filters. Try reducing filters or click <strong>Clear all</strong>.
            </div>
          ) : null}

          <div className="space-y-5">
            {items.map((item) => (
              <TenderMatchCard
                key={item.tender.id}
                item={item}
                onOpen={(tenderId) => navigate(`/tenders/${tenderId}`)}
                onAction={(tenderId, action) => {
                  if (action === "discarded") {
                    setDiscardTenderId(tenderId);
                  } else {
                    actionMutation.mutate({ tenderId, action });
                  }
                }}
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

      <DiscardTender
        open={Boolean(discardTenderId)}
        onClose={() => setDiscardTenderId(null)}
        tenderTitle={
          items.find((i) => i.tender.id === discardTenderId)?.tender.metadata?.title
          || items.find((i) => i.tender.id === discardTenderId)?.tender.bid_id
          || "this tender"
        }
        onConfirm={(reason) => {
          if (discardTenderId) {
            actionMutation.mutate({ tenderId: discardTenderId, action: "discarded", reason });
          }
        }}
        isPending={actionMutation.isPending}
      />
    </div>
  );
};

export default TendersPage;
