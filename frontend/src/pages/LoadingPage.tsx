import { useEffect, useMemo, useState } from "react";
import { Check } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";

import AuthShell from "@/components/layout/AuthShell";
import { connectWs } from "@/lib/ws";
import { fetchCompanyProfile, processCompanyProfile } from "@/services/tenderAgentApi";
import { useToastSimple } from "@/components/ui/toaster-simple";

const LoadingPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();

  const companyId = useMemo(() => searchParams.get("companyId") || "", [searchParams]);
  const jobId = useMemo(() => searchParams.get("jobId") || "", [searchParams]);
  const [progress, setProgress] = useState(12);
  const [done, setDone] = useState(false);
  const [failedMessage, setFailedMessage] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [runKey, setRunKey] = useState(0);

  const handleRetry = async () => {
    if (!companyId) {
      navigate("/onboarding/company");
      return;
    }

    setRetrying(true);
    setFailedMessage(null);
    setProgress(12);
    try {
      await processCompanyProfile(companyId);
      setRunKey((prev) => prev + 1);
    } catch {
      const message = "Unable to restart company processing";
      setFailedMessage(message);
      pushToast(message, "error");
    } finally {
      setRetrying(false);
    }
  };

  useEffect(() => {
    if (!companyId) {
      navigate("/onboarding/company");
      return;
    }

    let isMounted = true;
    let hasFailure = false;

    const socket = connectWs((event) => {
      if (!isMounted) return;
      if (event.type !== "JOB_PROGRESS") return;
      if (jobId && event.job_id !== jobId) return;
      if (event.job === "PROCESS_COMPANY" && event.progress?.percent !== undefined) {
        setProgress(Math.max(10, Math.round(event.progress.percent * 100)));
        if (event.status === "completed") {
          setProgress(100);
          setDone(true);
          setFailedMessage(null);
          clearInterval(poll);
        }
        if (event.status === "failed") {
          if (hasFailure) return;
          hasFailure = true;
          const message = event.message || "Company processing failed";
          setFailedMessage(message);
          pushToast(message, "error");
          clearInterval(poll);
        }
      }
    });

    const poll = window.setInterval(async () => {
      try {
        const profile = await fetchCompanyProfile(companyId);
        const status = profile.status?.processing_status;
        if (status === "ready") {
          setProgress(100);
          setDone(true);
          setFailedMessage(null);
          clearInterval(poll);
        } else if (status === "processing") {
          setProgress((prev) => Math.min(95, prev + 3));
        } else if (status === "failed") {
          if (hasFailure) return;
          hasFailure = true;
          const message = profile.status?.last_error || "Company processing failed";
          setFailedMessage(message);
          pushToast(message, "error");
          clearInterval(poll);
        }
      } catch {
        return;
      }
    }, 2500);

    return () => {
      isMounted = false;
      clearInterval(poll);
      socket.close();
    };
  }, [companyId, jobId, navigate, pushToast, runKey]);

  if (done) {
    return (
      <AuthShell>
        <div className="w-full max-w-[860px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-7 text-center shadow-sm">
          <div className="mx-auto mt-10 flex h-28 w-28 items-center justify-center rounded-full bg-[#19dd1f] text-white">
            <Check size={64} />
          </div>
          <p className="mt-8 text-2xl font-semibold text-[#252a39] md:text-4xl">
            Your company profile is set! Begin your tender
            <br />
            search now.
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="mt-10 rounded-full bg-[#4040E0] px-8 py-3 text-base text-white"
          >
            Start Exploring Tenders
          </button>
        </div>
      </AuthShell>
    );
  }

  if (failedMessage) {
    return (
      <AuthShell>
        <div className="w-full max-w-[860px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-7 text-center shadow-sm">
          <p className="mt-4 text-2xl font-semibold text-[#252a39] md:text-3xl">Company processing failed</p>
          <p className="mx-auto mt-4 max-w-[720px] text-sm text-[#525b73] md:text-base">{failedMessage}</p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="rounded-full bg-[#4040E0] px-6 py-3 text-base text-white disabled:opacity-60"
            >
              {retrying ? "Retrying..." : "Retry Processing"}
            </button>
            <button
              onClick={() => navigate("/onboarding/interests")}
              className="rounded-full border border-[#4040E0] px-6 py-3 text-base text-[#4040E0]"
            >
              Back to Interests
            </button>
          </div>
        </div>
      </AuthShell>
    );
  }

  const circumference = 2 * Math.PI * 102;
  const stroke = circumference - (progress / 100) * circumference;

  return (
    <AuthShell>
      <div className="w-full max-w-[860px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-7 text-center shadow-sm">
        <div className="mx-auto mt-8 w-[238px]">
          <svg width="238" height="238" viewBox="0 0 238 238">
            <circle cx="119" cy="119" r="102" stroke="#d7dbe6" strokeWidth="14" fill="none" />
            <circle
              cx="119"
              cy="119"
              r="102"
              stroke="#4040E0"
              strokeWidth="14"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={stroke}
              transform="rotate(-90 119 119)"
            />
            <text
              x="119"
              y="133"
              textAnchor="middle"
              fill="#2a3040"
              fontSize="42"
              fontWeight="600"
              fontFamily="system-ui, -apple-system, sans-serif"
            >
              {progress}%
            </text>
          </svg>
        </div>
        <p className="mx-auto mt-6 max-w-[560px] text-[22px] font-medium leading-relaxed text-[#323743]">
          Analyzing company profile and identifying relevant tenders.
          Please allow some time for this process.
        </p>
      </div>
    </AuthShell>
  );
};

export default LoadingPage;
