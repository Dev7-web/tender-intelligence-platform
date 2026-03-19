import { Download } from "lucide-react";
import { format } from "date-fns";

import calendarIcon from "@/assets/tenders/calendar-outline.svg";
import calendarRedIcon from "@/assets/tenders/calendar-red.svg";
import locationIcon from "@/assets/tenders/location.svg";
import rupeeIcon from "@/assets/tenders/rupee.svg";
import saveIcon from "@/assets/tenders/save.svg";
import shareIcon from "@/assets/tenders/share.svg";
import { downloadTenderFile } from "@/services/tenderAgentApi";
import { MatchItem } from "@/types/tender-agent";

interface TenderMatchCardProps {
  item: MatchItem;
  onOpen: (tenderId: string) => void;
  onAction: (tenderId: string, action: "saved" | "applied" | "discarded" | null) => void;
  onShare: (tenderId: string) => void;
}

const badgeClass = "rounded-full border border-[#d6dae8] px-2 py-0.5 text-[11px] text-[#646d84]";

const safeDate = (value?: string) => {
  if (!value) return "N/A";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value).slice(0, 10);
  }
  return format(parsed, "d MMM yyyy");
};

type DeadlineStatus = "expired" | "closing_soon" | "active";

const getDeadlineStatus = (endDate?: string): DeadlineStatus => {
  if (!endDate) return "active";
  const parsed = new Date(endDate);
  if (Number.isNaN(parsed.getTime())) return "active";
  const now = new Date();
  if (parsed < now) return "expired";
  const hoursLeft = (parsed.getTime() - now.getTime()) / (1000 * 60 * 60);
  if (hoursLeft <= 48) return "closing_soon";
  return "active";
};

const getDaysLeft = (endDate?: string): string => {
  if (!endDate) return "";
  const parsed = new Date(endDate);
  if (Number.isNaN(parsed.getTime())) return "";
  const now = new Date();
  const hoursLeft = (parsed.getTime() - now.getTime()) / (1000 * 60 * 60);
  if (hoursLeft < 0) return "Expired";
  if (hoursLeft < 1) return "< 1 hour left";
  if (hoursLeft < 24) return `${Math.ceil(hoursLeft)} hours left`;
  const daysLeft = Math.ceil(hoursLeft / 24);
  if (daysLeft === 1) return "1 day left";
  return `${daysLeft} days left`;
};

const TenderMatchCard = ({ item, onOpen, onAction, onShare }: TenderMatchCardProps) => {
  const tender = item.tender;
  const meta = tender.metadata || {};
  const scraped = tender.scraped_info || {};
  const title = meta.title || scraped.items || tender.bid_id || "Tender";
  const department = meta.department || scraped.department || "Department";
  const location = meta.location || department || "India";
  const scorePercent = Math.round((item.match?.score || 0) * 100);
  const deadlineStatus = getDeadlineStatus(scraped.end_date);
  const daysLeft = getDaysLeft(scraped.end_date);

  const handleDownload = async () => {
    try {
      await downloadTenderFile(tender.id);
    } catch (error) {
      console.error("Download failed", error);
    }
  };

  return (
    <div className="rounded-xl border border-[#d8dce6] bg-white p-4 shadow-sm transition hover:border-[#bfc5d8]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <button
            onClick={() => onOpen(tender.id)}
            className="block w-full truncate text-left text-lg font-semibold text-[#1f2533] hover:text-[#4040E0] md:text-xl"
          >
            {title}
          </button>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-[13px] text-[#666e83]">
            <img src={locationIcon} alt="" className="h-3.5 w-3.5" />
            <span className="min-w-0 break-words">{location}</span>
            <span>•</span>
            <img src={calendarIcon} alt="" className="h-3.5 w-3.5" />
            <span>Published {safeDate(scraped.start_date)}</span>
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
          <p className="mt-2 break-words text-sm text-[#5f667a]">{meta.summary || department}</p>
        </div>

        <div className="flex h-[86px] w-[86px] flex-col items-center justify-center rounded-full border-4 border-[#4040E0] text-center">
          <p className="text-lg font-semibold text-[#202532]">{scorePercent}%</p>
          <p className="text-[11px] text-[#687088]">Matched</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#ebedf4] pt-3">
        <div className="flex items-center gap-4 text-sm text-[#525a70]">
          <span className="inline-flex items-center gap-1 font-medium text-[#159d76]">
            <img src={rupeeIcon} alt="" className="h-4 w-4" />
            {scraped.bid_value_range || meta.estimated_value || "N/A"}
          </span>
          <span
            className={[
              "inline-flex items-center gap-1",
              deadlineStatus === "expired"
                ? "font-semibold text-[#b91c1c]"
                : deadlineStatus === "closing_soon"
                  ? "font-semibold text-[#d97706]"
                  : "text-[#d75252]",
            ].join(" ")}
          >
            <img src={calendarRedIcon} alt="" className="h-4 w-4" />
            {safeDate(scraped.end_date)}
          </span>
          {deadlineStatus === "expired" && (
            <span className="rounded-full bg-[#fef2f2] px-2 py-0.5 text-[11px] font-semibold text-[#b91c1c] border border-[#fecaca]">
              Expired
            </span>
          )}
          {deadlineStatus === "closing_soon" && (
            <span className="rounded-full bg-[#fffbeb] px-2 py-0.5 text-[11px] font-semibold text-[#d97706] border border-[#fde68a]">
              {daysLeft}
            </span>
          )}
          {deadlineStatus === "active" && daysLeft && (
            <span className="text-[12px] text-[#6b7280]">
              {daysLeft}
            </span>
          )}
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
            <img src={shareIcon} alt="" className="mr-1 inline h-3 w-3" /> Share
          </button>
          <button
            onClick={() => onAction(tender.id, item.action === "saved" ? null : "saved")}
            className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
          >
            <img src={saveIcon} alt="" className="mr-1 inline h-3.5 w-3.5" />
            {item.action === "saved" ? "Saved" : "Save"}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="rounded-full bg-[#4040E0] px-3 py-1.5 text-xs text-white"
          >
            <Download size={12} className="mr-1 inline" /> Download
          </button>
        </div>
      </div>
    </div>
  );
};

export default TenderMatchCard;
