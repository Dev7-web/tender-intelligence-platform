import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import StepHeader from "@/components/onboarding/StepHeader";
import AuthShell from "@/components/layout/AuthShell";
import { setCompanyId } from "@/lib/auth";
import { createCompany, scrapeCompanyWebsite } from "@/services/tenderAgentApi";
import { useToastSimple } from "@/components/ui/toaster-simple";

const CompanyDetails = () => {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [experience, setExperience] = useState("5");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();

  const canContinue = useMemo(() => {
    const years = Number(experience);
    return name.trim() && url.trim() && !Number.isNaN(years) && years >= 0 && years <= 100;
  }, [name, url, experience]);

  const handleContinue = async () => {
    if (!canContinue || loading) return;
    setLoading(true);
    try {
      const created = await createCompany({
        name: name.trim(),
        company_url: url.trim(),
        experience_years: Number(experience),
      });
      const companyId = created.company_id;
      setCompanyId(companyId);

      try {
        await scrapeCompanyWebsite(companyId);
      } catch {
        pushToast("Website scrape failed. You can still continue.", "info");
      }

      navigate("/onboarding/documents");
    } catch {
      pushToast("Unable to save company details", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell>
      <div className="w-full max-w-[860px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-7 shadow-sm">
        <StepHeader step={1} />

        <h2 className="mt-4 text-3xl font-semibold text-[#232836] md:text-4xl">Enter Details of your Company</h2>

        <div className="mt-10 space-y-5">
          <div>
            <label className="mb-2 block text-sm text-[#262b39]">Company Name</label>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Enter name"
              className="h-12 w-full rounded border border-[#d6dae3] bg-[#eef0f4] px-3 text-base"
            />
          </div>
          <div>
            <label className="mb-2 block text-sm text-[#262b39]">Company URL</label>
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="Enter URL"
              className="h-12 w-full rounded border border-[#d6dae3] bg-[#eef0f4] px-3 text-base"
            />
          </div>
          <div>
            <label className="mb-2 block text-sm text-[#262b39]">Experience</label>
            <input
              value={experience}
              onChange={(event) => setExperience(event.target.value)}
              placeholder="5 years"
              className="h-12 w-full rounded border border-[#d6dae3] bg-[#eef0f4] px-3 text-base"
            />
          </div>
        </div>

        <div className="mt-9 flex items-center justify-between">
          <button className="h-10 rounded-md bg-[#eceef3] px-5 text-sm text-[#b4bac9]" disabled>
            Back
          </button>
          <button
            onClick={handleContinue}
            disabled={!canContinue || loading}
            className="h-11 rounded-full bg-[#4040E0] px-8 text-base text-white disabled:opacity-50"
          >
            {loading ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    </AuthShell>
  );
};

export default CompanyDetails;
