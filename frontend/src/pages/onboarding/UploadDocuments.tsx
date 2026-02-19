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
                  <div className="h-9 w-9 rounded border border-[#d8dce6] bg-white" />
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
                    <Check className="text-green-600" size={18} />
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
