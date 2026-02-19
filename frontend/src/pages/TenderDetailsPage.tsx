import { useMemo, useState } from "react";
import { ArrowLeft, Download, MapPin, Share2, Sparkles } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import DiscussWithAI from "@/components/modals/DiscussWithAI";
import ShareTender from "@/components/modals/ShareTender";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { getCompanyId } from "@/lib/auth";
import { downloadTenderUrl, fetchTenderDetail, updateTenderAction } from "@/services/tenderAgentApi";

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
              <span className="rounded-full border border-[#dde1eb] px-2 py-1 text-[#6d7386]">PRODUCT</span>
            </div>
            <h1 className="text-2xl font-semibold text-[#222835] md:text-4xl">{title}</h1>
          </div>
          <button
            onClick={() => setOpenDiscuss(true)}
            className="h-11 rounded-full bg-[#4040E0] px-5 text-sm text-white"
          >
            <Sparkles size={14} className="mr-1 inline" /> Discuss with AI
          </button>
        </div>

        <p className="text-xl font-semibold text-[#212734] md:text-2xl">{meta.department || scraped.department || "Department"}</p>
        <p className="mt-2 text-sm text-[#5f667a]">
          <MapPin size={14} className="mr-1 inline" /> {meta.location || "India"}
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-[#475068]">
          <span>Amount: {amount}</span>
          <span>Closes: {String(scraped.end_date || "N/A").slice(0, 10)}</span>
          <span className="rounded bg-[#daf4eb] px-2 py-1 text-xs text-[#16835e]">12d left</span>
          <span className="rounded bg-[#fdeecf] px-2 py-1 text-xs text-[#c98300]">4d left</span>
          <span className="rounded bg-[#fddcdb] px-2 py-1 text-xs text-[#d35353]">1d left</span>
        </div>

        <div className="mt-6 border-t border-[#ebedf4] pt-4">
          <div className="flex flex-wrap justify-end gap-2">
            <button
              onClick={() => actionMutation.mutate("discarded")}
              className="rounded-full border border-[#ef8f93] px-3 py-1.5 text-xs text-[#dd5056]"
            >
              Discard tender
            </button>
            <button
              onClick={() => setOpenShare(true)}
              className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
            >
              <Share2 size={12} className="mr-1 inline" /> Share
            </button>
            <button
              onClick={() => actionMutation.mutate("saved")}
              className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
            >
              Save
            </button>
            <button
              onClick={() => actionMutation.mutate("applied")}
              className="rounded-full border border-[#d5d9e5] px-3 py-1.5 text-xs text-[#30374a]"
            >
              Apply
            </button>
            <a
              href={downloadTenderUrl(id)}
              target="_blank"
              rel="noreferrer"
              className="rounded-full bg-[#4040E0] px-3 py-1.5 text-xs text-white"
            >
              <Download size={12} className="mr-1 inline" /> Download Documents
            </a>
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
