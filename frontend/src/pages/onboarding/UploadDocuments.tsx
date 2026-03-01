import { useEffect, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ArrowLeft, Check, Plus, UploadCloud, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

import StepHeader from "@/components/onboarding/StepHeader";
import AuthShell from "@/components/layout/AuthShell";
import { getCompanyId } from "@/lib/auth";
import { deleteCompanyDocument, fetchCompanyProfile, uploadCompanyDocuments } from "@/services/tenderAgentApi";
import { useToastSimple } from "@/components/ui/toaster-simple";

interface UploadItem {
  localId: string;
  name: string;
  progress: number;
  status: "uploading" | "done" | "failed";
  fileHash?: string;
}

const EXT_COLORS: Record<string, { color: string; label: string }> = {
  pdf:  { color: "#EF4444", label: "PDF" },
  doc:  { color: "#3B82F6", label: "DOC" },
  docx: { color: "#3B82F6", label: "DOCX" },
  ppt:  { color: "#F97316", label: "PPT" },
  pptx: { color: "#F97316", label: "PPTX" },
  txt:  { color: "#6366F1", label: "TXT" },
  md:   { color: "#22C55E", label: "MD" },
  png:  { color: "#7C3AED", label: "PNG" },
  jpg:  { color: "#10B981", label: "JPG" },
  jpeg: { color: "#10B981", label: "JPEG" },
  gif:  { color: "#EAB308", label: "GIF" },
};

const FileTypeIcon = ({ filename }: { filename: string }) => {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  const { color, label } = EXT_COLORS[ext] ?? {
    color: "#9CA3AF",
    label: ext.toUpperCase().slice(0, 4) || "FILE",
  };

  return (
    <svg
      width="36"
      height="44"
      viewBox="0 0 36 44"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="flex-shrink-0"
    >
      {/* Document body */}
      <path
        d="M0 4C0 1.79 1.79 0 4 0H22L36 14V40C36 42.21 34.21 44 32 44H4C1.79 44 0 42.21 0 40V4Z"
        fill="#F8FAFC"
        stroke="#E2E8F0"
        strokeWidth="1"
      />
      {/* Folded corner */}
      <path
        d="M22 0L36 14H25C23.34 14 22 12.66 22 11V0Z"
        fill="#E2E8F0"
      />
      {/* Content lines */}
      <rect x="6" y="20" width="14" height="1.5" rx="0.75" fill="#CBD5E1" />
      <rect x="6" y="24" width="20" height="1.5" rx="0.75" fill="#CBD5E1" />
      <rect x="6" y="28" width="16" height="1.5" rx="0.75" fill="#CBD5E1" />
      {/* Extension badge */}
      <rect x="3" y="34" width="30" height="8" rx="3" fill={color} />
      <text
        x="18"
        y="40.5"
        textAnchor="middle"
        fill="white"
        fontSize="6.5"
        fontWeight="700"
        fontFamily="system-ui, -apple-system, sans-serif"
        letterSpacing="0.3"
      >
        {label}
      </text>
    </svg>
  );
};

const UploadDocuments = () => {
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();
  const [items, setItems] = useState<UploadItem[]>([]);
  const [loadingExisting, setLoadingExisting] = useState(true);

  const companyId = useMemo(() => getCompanyId(), []);

  useEffect(() => {
    if (!companyId) {
      navigate("/onboarding/company");
      return;
    }

    fetchCompanyProfile(companyId)
      .then((profile) => {
        const existing = (profile.uploaded_files || []).map((file) => ({
          localId: file.file_hash,
          name: file.original_name,
          progress: 100,
          status: "done" as const,
          fileHash: file.file_hash,
        }));
        setItems(existing);
      })
      .finally(() => setLoadingExisting(false));
  }, [companyId, navigate]);

  const uploadFiles = async (files: File[]) => {
    if (!companyId || files.length === 0) return;

    for (const file of files) {
      const localId = `${file.name}-${Date.now()}-${Math.random()}`;
      setItems((prev) => [...prev, { localId, name: file.name, progress: 0, status: "uploading" }]);

      try {
        const response = await uploadCompanyDocuments(companyId, [file], (progress) => {
          setItems((prev) =>
            prev.map((item) => (item.localId === localId ? { ...item, progress: progress } : item))
          );
        });

        const uploadedFile = response.files?.[0];
        setItems((prev) =>
          prev.map((item) =>
            item.localId === localId
              ? {
                  ...item,
                  progress: 100,
                  status: uploadedFile?.status === "failed" ? "failed" : "done",
                  fileHash: uploadedFile?.file_hash,
                }
              : item
          )
        );
      } catch {
        setItems((prev) =>
          prev.map((item) =>
            item.localId === localId ? { ...item, progress: 0, status: "failed" } : item
          )
        );
      }
    }
  };

  const removeItem = async (item: UploadItem) => {
    if (!companyId || !item.fileHash) {
      setItems((prev) => prev.filter((entry) => entry.localId !== item.localId));
      return;
    }

    try {
      await deleteCompanyDocument(companyId, item.fileHash);
      setItems((prev) => prev.filter((entry) => entry.localId !== item.localId));
    } catch {
      pushToast("Unable to remove file", "error");
    }
  };

  const { getRootProps, getInputProps, open } = useDropzone({
    onDrop: uploadFiles,
    noClick: true,
    multiple: true,
  });

  const uploadedCount = items.filter((item) => item.status === "done").length;
  const canContinue = uploadedCount > 0;

  return (
    <AuthShell>
      <div className="w-full max-w-[860px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-7 shadow-sm">
        <StepHeader step={2} />

        <h2 className="mt-4 text-3xl font-semibold text-[#232836] md:text-4xl">Upload Company Documents</h2>

        {loadingExisting ? (
          <p className="mt-6 text-sm text-[#6f768a]">Loading uploaded files...</p>
        ) : items.length === 0 ? (
          <div
            {...getRootProps()}
            className="mt-8 rounded-2xl border border-dashed border-[#8f97ff] bg-[#ebedf4] p-10 text-center"
          >
            <input {...getInputProps()} />
            <UploadCloud size={36} className="mx-auto text-[#4040E0]" />
            <p className="mt-3 text-base text-[#5a6174]">Drag & drop your files here</p>
            <button onClick={open} className="mt-3 rounded bg-[#4040E0] px-4 py-2 text-sm text-white">
              Browse files
            </button>
            <p className="mt-2 text-xs text-[#8d94a6]">Supported file formats: pdf/doc/docx/ppt/pptx/txt/md</p>
          </div>
        ) : (
          <div className="mt-6">
            <p className="text-sm text-[#737b8f]">Adding files</p>
            <div className="mt-2 space-y-4">
              {items.map((item) => (
                <div key={item.localId} className="flex items-center gap-3">
                  <FileTypeIcon filename={item.name} />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-[#252a39]">{item.name}</p>
                      <p className="text-xs text-[#757d91]">{item.progress}%</p>
                    </div>
                    <div className="mt-1 h-[4px] rounded-full bg-[#d8dded]">
                      <div className="h-full rounded-full bg-[#4040E0]" style={{ width: `${item.progress}%` }} />
                    </div>
                  </div>
                  {item.status === "done" ? (
                    <div className="flex items-center gap-2">
                      <Check className="text-green-600" size={18} />
                      <button
                        onClick={() => removeItem(item)}
                        title="Remove file"
                        className="flex h-6 w-6 items-center justify-center rounded-full hover:bg-[#F3F4F6]"
                      >
                        <X size={14} className="text-[#9CA3AF] hover:text-[#EF4444]" />
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => removeItem(item)}>
                      <X size={16} className="text-[#626a80]" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <button onClick={open} className="mt-4 text-sm text-[#4040E0]">
              <Plus size={14} className="mr-1 inline" /> Add more files
            </button>
          </div>
        )}

        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={() => navigate("/onboarding/company")}
            className="h-10 rounded-md bg-[#eceef3] px-5 text-sm text-[#7f879b]"
          >
            <ArrowLeft size={14} className="mr-1 inline" /> Back
          </button>
          <button
            disabled={!canContinue}
            onClick={() => navigate("/onboarding/interests")}
            className="h-11 rounded-full bg-[#4040E0] px-8 text-base text-white disabled:opacity-50"
          >
            Continue
          </button>
        </div>
      </div>
    </AuthShell>
  );
};

export default UploadDocuments;
