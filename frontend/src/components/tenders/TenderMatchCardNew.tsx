import { CalendarDays, Download, MapPin, Share2 } from "lucide-react";

import { downloadTenderUrl } from "@/services/tenderAgentApi";
import { MatchItem } from "@/types/tender-agent";

interface TenderMatchCardProps {
  item: MatchItem;
  onOpen: (tenderId: string) => void;
  onAction: (tenderId: string, action: "saved" | "applied" | "discarded" | null) => void;
  onShare: (tenderId: string) => void;
}

const badgeClass = "rounded-full border border-[#d6dae8] px-2 py-0.5 text-[11px] text-[#646d84]";

const TenderMatchCard = ({ item, onOpen, onAction, onShare }: TenderMatchCardProps) => {
  const tender = item.tender;
  const meta = tender.metadata || {};
  const scraped = tender.scraped_info || {};
  const title = meta.title || scraped.items || tender.bid_id;
  const department = meta.department || scraped.department || "Department";
  const location = meta.location || "India";
  const scorePercent = Math.round((item.match?.score || 0) * 100);

  return (
    <div className="rounded-xl border border-[#d8dce6] bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <button
            onClick={() => onOpen(tender.id)}
            className="truncate text-left text-lg font-semibold text-[#1f2533] hover:text-[#4040E0] md:text-xl"
          >
            {department}
          </button>
          <div className="mt-2 flex items-center gap-2 text-[13px] text-[#666e83]">
            <MapPin size={13} />
            <span>{location}</span>
            <span>•</span>
            <CalendarDays size={13} />
            <span>Published {String(scraped.start_date || "N/A").slice(0, 10)}</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-[#4040E0] px-2 py-1 text-[10px] text-white">GeM</span>
            <span className={badgeClass}>Product Bid/RAs</span>
            {(meta.domains || []).slice(0, 2).map((tag) => (
              <span key={tag} className={badgeClass}>
                {tag}
              </span>
            ))}
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-[#5f667a]">{meta.summary || title}</p>
        </div>

        <div className="flex h-[86px] w-[86px] flex-col items-center justify-center rounded-full border-4 border-[#4040E0] text-center">
          <p className="text-lg font-semibold text-[#202532]">{scorePercent}%</p>
          <p className="text-[11px] text-[#687088]">Matched</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#ebedf4] pt-3">
        <div className="flex items-center gap-4 text-sm text-[#525a70]">
          <span className="font-medium text-[#159d76]">{scraped.bid_value_range || meta.estimated_value || "N/A"}</span>
          <span className="text-[#d75252]">{String(scraped.end_date || "N/A").slice(0, 10)}</span>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onAction(tender.id, "discarded")}
            className="rounded-full border border-[#ef8f93] px-3 py-1.5 text-xs text-[#dd5056]"
          >
            Discard tender
          </button>
          <button
            onClick={() => onShare(tender.id)}
            className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
          >
            <Share2 size={12} className="mr-1 inline" /> Share
          </button>
          <button
            onClick={() => onAction(tender.id, item.action === "saved" ? null : "saved")}
            className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
          >
            {item.action === "saved" ? "Saved" : "Save"}
          </button>
          <a
            href={downloadTenderUrl(tender.id)}
            className="rounded-full bg-[#4040E0] px-3 py-1.5 text-xs text-white"
            target="_blank"
            rel="noreferrer"
          >
            <Download size={12} className="mr-1 inline" /> Download
          </a>
        </div>
      </div>
    </div>
  );
};

export default TenderMatchCard;
