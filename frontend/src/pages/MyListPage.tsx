import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ChevronDown } from "lucide-react";

import SavedTenderCard from "@/components/tenders/SavedTenderCard";
import ShareTender from "@/components/modals/ShareTender";
import { getCompanyId } from "@/lib/auth";
import { fetchMyList, updateTenderAction } from "@/services/tenderAgentApi";

const MyListPage = () => {
  const companyId = getCompanyId() || "";
  const navigate = useNavigate();
  const [selectedShareTenderId, setSelectedShareTenderId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"applied" | "pinned" | "closing">("applied");
  const [sortOpen, setSortOpen] = useState(false);
  const sortRef = useRef<HTMLDivElement | null>(null);
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());
  const [appliedIds, setAppliedIds] = useState<Set<string>>(new Set());

  const sortOptions = [
    { value: "applied", label: "Applied" },
    { value: "pinned", label: "Pinned" },
    { value: "closing", label: "Closing soon" },
  ] as const;

  const { data, refetch } = useQuery({
    queryKey: ["myList", companyId, "saved"],
    queryFn: () => fetchMyList(companyId, "saved", 1, 20),
    enabled: Boolean(companyId),
  });

  const items = useMemo(() => {
    return (data?.items || [])
      .filter((entry: any) => entry.tender)
      .map((entry: any) => ({
        tender: entry.tender,
        match: { score: 0.95, reasons: [] },
        action: entry.action,
        updated_at: entry.updated_at,
      }));
  }, [data]);

  useEffect(() => {
    if (!companyId) return;
    const stored = localStorage.getItem(`ta_pinned_${companyId}`);
    if (!stored) {
      setPinnedIds(new Set());
      return;
    }
    try {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        setPinnedIds(new Set(parsed));
      }
    } catch {
      setPinnedIds(new Set());
    }
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    const stored = localStorage.getItem(`ta_applied_${companyId}`);
    if (!stored) {
      setAppliedIds(new Set());
      return;
    }
    try {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        setAppliedIds(new Set(parsed));
      }
    } catch {
      setAppliedIds(new Set());
    }
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    localStorage.setItem(`ta_pinned_${companyId}`, JSON.stringify(Array.from(pinnedIds)));
  }, [companyId, pinnedIds]);

  useEffect(() => {
    if (!companyId) return;
    localStorage.setItem(`ta_applied_${companyId}`, JSON.stringify(Array.from(appliedIds)));
  }, [companyId, appliedIds]);

  useEffect(() => {
    if (!sortOpen) return;
    const handleClick = (event: MouseEvent) => {
      const target = event.target as Node;
      if (sortRef.current?.contains(target)) return;
      setSortOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [sortOpen]);

  const sortedItems = useMemo(() => {
    const list = [...items];
    const getEndDate = (item: any) => {
      const value = item.tender?.scraped_info?.end_date;
      const parsed = value ? new Date(value) : null;
      return parsed && !Number.isNaN(parsed.getTime()) ? parsed : null;
    };
    const isPinned = (item: any) => pinnedIds.has(item.tender?.id);
    const isApplied = (item: any) => appliedIds.has(item.tender?.id);

    if (sortBy === "pinned") {
      list.sort((a, b) => Number(isPinned(b)) - Number(isPinned(a)));
    } else if (sortBy === "applied") {
      list.sort((a, b) => Number(isApplied(b)) - Number(isApplied(a)));
    } else if (sortBy === "closing") {
      list.sort((a, b) => {
        const aDate = getEndDate(a)?.getTime() ?? Number.POSITIVE_INFINITY;
        const bDate = getEndDate(b)?.getTime() ?? Number.POSITIVE_INFINITY;
        return aDate - bDate;
      });
    }

    return list;
  }, [items, pinnedIds, appliedIds, sortBy]);

  const handlePin = (tenderId: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(tenderId)) {
        next.delete(tenderId);
      } else {
        next.add(tenderId);
      }
      return next;
    });
  };

  const handleApplied = (tenderId: string) => {
    setAppliedIds((prev) => {
      const next = new Set(prev);
      if (next.has(tenderId)) {
        next.delete(tenderId);
      } else {
        next.add(tenderId);
      }
      return next;
    });
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-baseline gap-3">
          <h1 className="text-3xl font-semibold text-[#232937] md:text-4xl">Saved tenders</h1>
          <span className="text-sm text-[#8a93a8]">{data?.total || 0} saved</span>
        </div>

        <div className="flex items-center gap-2 text-sm text-[#6f768b]">
          <span>Sort by:</span>
          <div ref={sortRef} className="relative min-w-[200px]">
            <button
              type="button"
              onClick={() => setSortOpen((prev) => !prev)}
              className="flex h-10 w-full items-center justify-between rounded-md border border-[#d8dce6] bg-white px-3 text-sm text-[#232937]"
            >
              {sortOptions.find((option) => option.value === sortBy)?.label || "Applied"}
              <ChevronDown size={16} className={sortOpen ? "rotate-180" : ""} />
            </button>
            {sortOpen ? (
              <div className="absolute right-0 z-10 mt-2 w-full rounded-md border border-[#d8dce6] bg-white p-1 shadow-sm">
                {sortOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      setSortBy(option.value);
                      setSortOpen(false);
                    }}
                    className={[
                      "w-full rounded-md px-3 py-2 text-left text-sm",
                      option.value === sortBy ? "bg-[#eef0ff] font-semibold text-[#232937]" : "text-[#232937]",
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

      <div className="space-y-4">
        {sortedItems.map((item: any) => (
          <SavedTenderCard
            key={item.tender.id}
            item={item}
            isPinned={pinnedIds.has(item.tender.id)}
            isApplied={appliedIds.has(item.tender.id)}
            onOpen={(tenderId) => navigate(`/tenders/${tenderId}`)}
            onRemove={async (tenderId) => {
              await updateTenderAction(tenderId, { company_id: companyId, action: null });
              refetch();
            }}
            onPin={handlePin}
            onApplied={handleApplied}
            onShare={(tenderId) => setSelectedShareTenderId(tenderId)}
          />
        ))}
      </div>

      <ShareTender
        open={Boolean(selectedShareTenderId)}
        onClose={() => setSelectedShareTenderId(null)}
        tenderId={selectedShareTenderId || ""}
        companyId={companyId}
      />
    </div>
  );
};

export default MyListPage;
