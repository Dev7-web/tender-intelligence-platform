import { useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

import AuthShell from "@/components/layout/AuthShell";
import StepHeader from "@/components/onboarding/StepHeader";
import { getCompanyId } from "@/lib/auth";
import { processCompanyProfile, setCompanyInterests } from "@/services/tenderAgentApi";
import { useToastSimple } from "@/components/ui/toaster-simple";

const TAGS = [
  "Infrastructure",
  "Technology",
  "Healthcare",
  "Energy",
  "Services",
  "Supply of Goods",
  "Professional Services",
  "Business",
  "Product Works",
  "Maintenance",
  "Local",
  "ISO Certified",
  "Fashion & Beauty",
  "Entrepreneurship",
  "Networking",
  "News",
  "Climate",
  "Politics",
  "Productivity",
  "Road Construction",
  "Education",
  "Security Clearance",
  "Framework",
  "Cybersecurity",
  "AI & Automation",
  "Data Governance",
];

const SelectInterests = () => {
  const companyId = useMemo(() => getCompanyId(), []);
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const toggleTag = (tag: string) => {
    setSelected((prev) => (prev.includes(tag) ? prev.filter((item) => item !== tag) : [...prev, tag]));
  };

  const handleDone = async () => {
    if (!companyId) {
      navigate("/onboarding/company");
      return;
    }

    setLoading(true);
    try {
      await setCompanyInterests(companyId, selected);
      const process = await processCompanyProfile(companyId);
      navigate(`/loading/company-processing?companyId=${companyId}&jobId=${process.job_id}`);
    } catch {
      pushToast("Unable to save interests", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell>
      <div className="w-full max-w-[860px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-7 shadow-sm">
        <StepHeader step={3} />

        <h2 className="mt-4 text-3xl font-semibold text-[#232836] md:text-4xl">What fields are you interested in?</h2>
        <p className="text-sm text-[#7b8298]">Select tags to specify your interests</p>

        <div className="mt-6 flex flex-wrap gap-3">
          {TAGS.map((tag) => {
            const isSelected = selected.includes(tag);
            return (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={[
                  "rounded-md border px-4 py-2 text-xs",
                  isSelected
                    ? "border-[#4040E0] bg-[#eef0ff] text-[#4040E0]"
                    : "border-[#d6dae5] bg-[#f8f9fc] text-[#5d657b]",
                ].join(" ")}
              >
                {tag}
              </button>
            );
          })}
        </div>

        <div className="mt-9 flex items-center justify-between">
          <button
            onClick={() => navigate("/onboarding/documents")}
            className="h-10 rounded-md bg-[#eceef3] px-5 text-sm text-[#7f879b]"
          >
            <ArrowLeft size={14} className="mr-1 inline" /> Back
          </button>
          <button
            disabled={loading}
            onClick={handleDone}
            className="h-11 rounded-full bg-[#4040E0] px-8 text-base text-white disabled:opacity-50"
          >
            {loading ? "Saving..." : "Done"}
          </button>
        </div>
      </div>
    </AuthShell>
  );
};

export default SelectInterests;
