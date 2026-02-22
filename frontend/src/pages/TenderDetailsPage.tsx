import { useMemo, useState } from "react";
import { ArrowLeft, Download, Share2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import calendarRedIcon from "@/assets/tenders/calendar-red.svg";
import discardIcon from "@/assets/tenders/discard.svg";
import locationPurpleIcon from "@/assets/tenders/location-purple.svg";
import organizationIcon from "@/assets/tenders/organization.svg";
import rupeeIcon from "@/assets/tenders/rupee.svg";
import saveIcon from "@/assets/tenders/save.svg";
import sparkleIcon from "@/assets/tenders/sparkle.svg";
import DiscussWithAI from "@/components/modals/DiscussWithAI";
import ShareTender from "@/components/modals/ShareTender";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { getCompanyId } from "@/lib/auth";
import { downloadTenderFile, fetchTenderDetail, updateTenderAction } from "@/services/tenderAgentApi";

const TenderDetailsPage = () => {
  const { id = "" } = useParams();
  const companyId = getCompanyId() || "";
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();
  const queryClient = useQueryClient();

  const [openDiscuss, setOpenDiscuss] = useState(false);
  const [openShare, setOpenShare] = useState(false);

  const { data: tender } = useQuery({
    queryKey: ["tender", id],
    queryFn: () => fetchTenderDetail(id),
    enabled: Boolean(id),
  });

  const actionMutation = useMutation({
    mutationFn: (action: "saved" | "applied" | "discarded" | null) =>
      updateTenderAction(id, { company_id: companyId, action }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches", companyId] });
      queryClient.invalidateQueries({ queryKey: ["myList", companyId] });
      pushToast("Tender updated", "success");
    },
    onError: () => pushToast("Unable to update action", "error"),
  });

  const handleDownload = async () => {
    try {
      await downloadTenderFile(id);
    } catch (error) {
      pushToast("Unable to download document", "error");
    }
  };

  const meta = tender?.metadata || {};
  const scraped = tender?.scraped_info || {};
  const title = meta.title || scraped.items || tender?.bid_id;

  const amount = useMemo(() => meta.estimated_value || scraped.bid_value_range || "N/A", [meta, scraped]);

  return (
    <div>
      <button onClick={() => navigate("/tenders")} className="mb-4 text-sm text-[#4040E0]">
        <ArrowLeft size={14} className="mr-1 inline" /> Back to Search
      </button>

      <div className="rounded-xl border border-[#d8dce6] bg-white p-6">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap gap-2 text-[10px]">
              <span className="rounded-full bg-[#4040E0] px-2 py-1 text-white">GeM</span>
              <span className="rounded-full bg-[#eef0ff] px-2 py-1 text-[#4040E0]">Active</span>
              <span className="rounded-full border border-[#dde1eb] px-2 py-1 text-[#6d7386]">Goods</span>
              {scraped.items && (
                <span className="rounded-full border border-[#dde1eb] px-2 py-1 text-[#6d7386]">{scraped.items}</span>
              )}
              <span className="rounded-full border border-[#dde1eb] px-2 py-1 text-[#6d7386]">PRODUCT</span>
            </div>
            <h1 className="text-2xl font-semibold text-[#222835] md:text-4xl">{title}</h1>
          </div>
          <button
            onClick={() => setOpenDiscuss(true)}
            className="flex h-11 shrink-0 items-center gap-2 rounded-full bg-[#4040E0] px-5 text-sm text-white"
          >
            <img src={sparkleIcon} alt="" className="h-5 w-5" /> Discuss with AI
          </button>
        </div>

        <p className="flex items-center gap-2 text-xl font-semibold text-[#212734] md:text-2xl">
          <img src={organizationIcon} alt="" className="h-6 w-6" />
          {meta.department || scraped.department || "Department"}
        </p>
        <p className="mt-2 flex items-center gap-1.5 text-sm text-[#5f667a]">
          <img src={locationPurpleIcon} alt="" className="h-5 w-5" /> {meta.location || "India"}
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-[#475068]">
          <span className="flex items-center gap-1.5">
            <img src={rupeeIcon} alt="" className="h-5 w-5" /> Amount: <strong>{amount}</strong>
          </span>
          <span className="flex items-center gap-1.5">
            <img src={calendarRedIcon} alt="" className="h-5 w-5" /> Closes: <strong>{String(scraped.end_date || "N/A").slice(0, 10)}</strong>
          </span>
          <span className="rounded bg-[#daf4eb] px-2 py-1 text-xs text-[#16835e]">12d left</span>
          <span className="rounded bg-[#fdeecf] px-2 py-1 text-xs text-[#c98300]">4d left</span>
          <span className="rounded bg-[#fddcdb] px-2 py-1 text-xs text-[#d35353]">1d left</span>
        </div>

        <div className="mt-6 border-t border-[#ebedf4] pt-4">
          <div className="flex flex-wrap justify-end gap-2">
            <button
              onClick={() => actionMutation.mutate("discarded")}
              className="flex items-center gap-1.5 rounded-full border border-[#ef8f93] px-3 py-1.5 text-xs text-[#dd5056]"
            >
              <img src={discardIcon} alt="" className="h-4 w-4" /> Discard tender
            </button>
            <button
              onClick={() => setOpenShare(true)}
              className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
            >
              <Share2 size={12} className="mr-1 inline" /> Share
            </button>
            <button
              onClick={() => actionMutation.mutate("saved")}
              className="flex items-center gap-1.5 rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
            >
              <img src={saveIcon} alt="" className="h-4 w-4" /> Save
            </button>
            <button
              onClick={() => actionMutation.mutate("applied")}
              className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={handleDownload}
              className="rounded-full bg-[#4040E0] px-3 py-1.5 text-xs text-white"
            >
              <Download size={12} className="mr-1 inline" /> Download Documents
            </button>
          </div>
        </div>
      </div>

      <DiscussWithAI
        open={openDiscuss}
        onClose={() => setOpenDiscuss(false)}
        tenderId={id}
        companyId={companyId}
      />

      <ShareTender
        open={openShare}
        onClose={() => setOpenShare(false)}
        tenderId={id}
        companyId={companyId}
      />
    </div>
  );
};

export default TenderDetailsPage;
