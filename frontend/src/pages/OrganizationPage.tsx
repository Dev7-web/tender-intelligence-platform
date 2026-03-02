import { useCallback, useEffect, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Check, ChevronRight, Info, Paperclip, Pencil, Plus, UploadCloud, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { useToastSimple } from "@/components/ui/toaster-simple";
import { getCompanyId } from "@/lib/auth";
import {
  deleteCompanyDocument,
  fetchCompanyProfile,
  updateCompanyProfile,
  uploadCompanyDocuments,
} from "@/services/tenderAgentApi";
import { CompanyProfile } from "@/types/tender-agent";

/* ── file extension helper ──────────────────────── */
const getFileExt = (name: string) => {
  const idx = name.lastIndexOf(".");
  return idx > 0 ? name.slice(idx + 1).toLowerCase() : "";
};
const extColor: Record<string, string> = {
  pdf: "#ef4444",
  doc: "#3b82f6",
  docx: "#3b82f6",
  png: "#8b5cf6",
  jpg: "#8b5cf6",
  jpeg: "#8b5cf6",
  txt: "#6b7280",
  ppt: "#f59e0b",
  pptx: "#f59e0b",
};

/* ── upload item type ──────────────────────────── */
interface UploadItem {
  localId: string;
  name: string;
  progress: number;
  status: "uploading" | "done" | "failed";
  fileHash?: string;
  sizeBytes?: number;
}

/* ── tag chip with remove ──────────────────────── */
const TagChip = ({ label, onRemove, editing }: { label: string; onRemove: () => void; editing: boolean }) => (
  <span className="inline-flex items-center gap-1.5 rounded-full border border-[#d0d4e2] bg-[#eef0ff] px-3 py-1 text-sm text-[#4040E0]">
    {label}
    {editing && (
      <button onClick={onRemove} className="text-[#4040E0] hover:text-[#2020c0]">
        <X size={14} />
      </button>
    )}
  </span>
);

/* ── inline add input ──────────────────────────── */
const AddTagButton = ({ onAdd }: { onAdd: (v: string) => void }) => {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  const submit = () => {
    if (value.trim()) {
      onAdd(value.trim());
      setValue("");
      setOpen(false);
    }
  };

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="inline-flex items-center gap-1 text-sm text-[#4040E0]">
        <Plus size={14} /> Add
      </button>
    );
  }

  return (
    <span className="inline-flex items-center gap-1">
      <input
        autoFocus
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") submit();
          if (e.key === "Escape") { setOpen(false); setValue(""); }
        }}
        placeholder="Type and press Enter"
        className="h-8 w-48 rounded border border-[#d0d4e2] px-2 text-sm outline-none focus:border-[#4040E0]"
      />
      <button onClick={submit} className="text-sm text-[#4040E0]">Add</button>
      <button onClick={() => { setOpen(false); setValue(""); }} className="text-sm text-[#8690a6]">Cancel</button>
    </span>
  );
};

/* ── format file size ──────────────────────────── */
const formatBytes = (bytes?: number) => {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} b`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kb`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} mb`;
};

/* ── field component (outside to preserve focus) ── */
const Field = ({ label, value, onChange, placeholder, textarea, disabled }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; textarea?: boolean; disabled?: boolean;
}) => (
  <div>
    <label className="mb-1.5 block text-sm font-medium text-[#232937]">{label}</label>
    {textarea ? (
      <textarea
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        className="w-full rounded-lg border border-[#d6dae3] bg-white px-4 py-3 text-sm text-[#232937] outline-none focus:border-[#4040E0] disabled:bg-[#f9fafb] disabled:text-[#6b7280]"
      />
    ) : (
      <input
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-12 w-full rounded-lg border border-[#d6dae3] bg-white px-4 text-sm text-[#232937] outline-none focus:border-[#4040E0] disabled:bg-[#f9fafb] disabled:text-[#6b7280]"
      />
    )}
  </div>
);

/* ── tag section component (outside to preserve focus) ── */
const TagSection = ({ label, items, setItems, editing }: {
  label: string; items: string[]; setItems: (v: string[]) => void; editing: boolean;
}) => (
  <div>
    <p className="mb-2 text-sm font-semibold text-[#232937]">{label}</p>
    <div className="flex flex-wrap items-center gap-2">
      {items.map((tag) => (
        <TagChip key={tag} label={tag} editing={editing} onRemove={() => setItems(items.filter((t) => t !== tag))} />
      ))}
      {editing && <AddTagButton onAdd={(v) => { if (!items.includes(v)) setItems([...items, v]); }} />}
    </div>
  </div>
);

/* ════════════════════════════════════════════════ */
/*  MAIN COMPONENT                                  */
/* ════════════════════════════════════════════════ */
const OrganizationPage = () => {
  const companyId = useMemo(() => getCompanyId(), []);
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();
  const queryClient = useQueryClient();

  /* ── state ─────────────────────────────────── */
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [experience, setExperience] = useState("");
  const [turnover, setTurnover] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [interestedStates, setInterestedStates] = useState<string[]>([]);
  const [tenderTopics, setTenderTopics] = useState<string[]>([]);
  const [fileItems, setFileItems] = useState<UploadItem[]>([]);

  /* ── query ─────────────────────────────────── */
  const { data: company } = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => fetchCompanyProfile(companyId || ""),
    enabled: Boolean(companyId),
  });

  /* populate local state from fetched company */
  useEffect(() => {
    if (!company) return;
    setName(company.name || "");
    setUrl(company.company_url || "");
    setExperience(company.experience_years != null ? String(company.experience_years) : "");
    setTurnover(company.turnover || "");
    setDescription(company.description || "");
    setTags(company.interest_tags || []);
    setInterestedStates(company.interested_states || []);
    setTenderTopics(company.tender_topics || []);
    setFileItems(
      (company.uploaded_files || []).map((f) => ({
        localId: f.file_hash,
        name: f.original_name,
        progress: 100,
        status: "done" as const,
        fileHash: f.file_hash,
        sizeBytes: f.size_bytes,
      }))
    );
  }, [company]);

  /* ── mutations ─────────────────────────────── */
  const saveMutation = useMutation({
    mutationFn: (updates: Partial<CompanyProfile>) => updateCompanyProfile(companyId || "", updates),
    onSuccess: (data: Record<string, unknown>) => {
      queryClient.invalidateQueries({ queryKey: ["company", companyId] });
      setEditing(false);
      if (data?.rescraping) {
        pushToast("Profile saved. Re-scraping website & rebuilding profile in background...", "success");
      } else if (data?.reprocessing) {
        pushToast("Profile saved. Rebuilding company profile in background...", "success");
      } else {
        pushToast("Profile saved", "success");
      }
    },
    onError: () => pushToast("Unable to save profile", "error"),
  });

  const removeMutation = useMutation({
    mutationFn: (fileHash: string) => deleteCompanyDocument(companyId || "", fileHash),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["company", companyId] }),
    onError: () => pushToast("Unable to remove file", "error"),
  });

  /* ── save handler ──────────────────────────── */
  const handleSave = () => {
    saveMutation.mutate({
      name: name.trim(),
      company_url: url.trim(),
      experience_years: Number(experience) || 0,
      turnover: turnover.trim(),
      description: description.trim(),
      interest_tags: tags,
      interested_states: interestedStates,
      tender_topics: tenderTopics,
    });
  };

  /* ── file upload ───────────────────────────── */
  const uploadFiles = useCallback(
    async (files: File[]) => {
      if (!companyId || files.length === 0) return;
      for (const file of files) {
        const localId = `${file.name}-${Date.now()}-${Math.random()}`;
        setFileItems((prev) => [...prev, { localId, name: file.name, progress: 0, status: "uploading" }]);
        try {
          const response = await uploadCompanyDocuments(companyId, [file], (pct) => {
            setFileItems((prev) => prev.map((i) => (i.localId === localId ? { ...i, progress: pct } : i)));
          });
          const uploaded = response.files?.[0];
          setFileItems((prev) =>
            prev.map((i) =>
              i.localId === localId
                ? {
                    ...i,
                    progress: 100,
                    status: uploaded?.status === "failed" ? "failed" : "done",
                    fileHash: uploaded?.file_hash,
                    sizeBytes: uploaded?.size_bytes,
                  }
                : i
            )
          );
          if (response.reprocessing) {
            pushToast("File uploaded. Rebuilding company profile in background...", "success");
          }
        } catch {
          setFileItems((prev) =>
            prev.map((i) => (i.localId === localId ? { ...i, progress: 0, status: "failed" } : i))
          );
        }
      }
      queryClient.invalidateQueries({ queryKey: ["company", companyId] });
    },
    [companyId, queryClient, pushToast]
  );

  const removeFile = async (item: UploadItem) => {
    if (!companyId || !item.fileHash) {
      setFileItems((prev) => prev.filter((i) => i.localId !== item.localId));
      return;
    }
    removeMutation.mutate(item.fileHash, {
      onSuccess: () => setFileItems((prev) => prev.filter((i) => i.localId !== item.localId)),
    });
  };

  const { getRootProps, getInputProps, open } = useDropzone({ onDrop: uploadFiles, noClick: true, multiple: true });

  /* ════════════════════════════════════════════ */
  /*  RENDER                                      */
  /* ════════════════════════════════════════════ */
  return (
    <div className="space-y-6">
      {/* ── header ───────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold text-[#232937] md:text-4xl">Company Profile Details</h1>
        <div className="flex items-center gap-3">
          {editing ? (
            <>
              <button
                onClick={() => {
                  setEditing(false);
                  /* reset from server data */
                  if (company) {
                    setName(company.name || "");
                    setUrl(company.company_url || "");
                    setExperience(company.experience_years != null ? String(company.experience_years) : "");
                    setTurnover(company.turnover || "");
                    setDescription(company.description || "");
                    setTags(company.interest_tags || []);
                    setInterestedStates(company.interested_states || []);
                    setTenderTopics(company.tender_topics || []);
                  }
                }}
                className="flex items-center gap-1.5 text-sm text-[#6b7280] hover:text-[#374151]"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saveMutation.isPending}
                className="rounded-full bg-[#4040E0] px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
              >
                {saveMutation.isPending ? "Saving..." : "Save Changes"}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-1.5 text-sm text-[#4040E0]"
              >
                <Pencil size={14} /> Edit Details
              </button>
              <button
                onClick={() => navigate("/tenders")}
                className="flex items-center gap-2 rounded-full bg-[#4040E0] px-5 py-2.5 text-sm font-medium text-white"
              >
                Find Matching Tenders <ChevronRight size={16} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── basic info card ──────────────────── */}
      <div className="rounded-xl border border-[#d8dce6] bg-white p-6">
        <div className="grid gap-8 md:grid-cols-[280px_1fr]">
          {/* left sidebar label */}
          <div className="flex items-start gap-3">
            <Info size={20} className="mt-0.5 shrink-0 text-[#4040E0]" />
            <div>
              <p className="text-base font-semibold text-[#232937]">Basic Info</p>
              <p className="text-sm text-[#8690a6]">View company details</p>
            </div>
          </div>

          {/* right form fields */}
          <div className="space-y-5">
            <Field label="Company Name" value={name} onChange={setName} placeholder="Enter name" disabled={!editing} />
            <Field label="Company URL" value={url} onChange={setUrl} placeholder="www.example.com" disabled={!editing} />
            <Field label="Experience" value={experience} onChange={setExperience} placeholder="5 years" disabled={!editing} />
            <Field label="Turnover" value={turnover} onChange={setTurnover} placeholder="$250,000" disabled={!editing} />
            <Field label="Description" value={description} onChange={setDescription} placeholder="Description about Company..." textarea disabled={!editing} />

            <TagSection label="Tags" items={tags} setItems={setTags} editing={editing} />
            <TagSection label="Interested States" items={interestedStates} setItems={setInterestedStates} editing={editing} />
            <TagSection label="Tender Topics" items={tenderTopics} setItems={setTenderTopics} editing={editing} />
          </div>
        </div>
      </div>

      {/* ── company files card ───────────────── */}
      <div className="rounded-xl border border-[#d8dce6] bg-white p-6">
        <div className="grid gap-8 md:grid-cols-[280px_1fr]">
          {/* left sidebar label */}
          <div className="flex items-start gap-3">
            <Paperclip size={20} className="mt-0.5 shrink-0 text-[#4040E0]" />
            <div>
              <p className="text-base font-semibold text-[#232937]">Company Files</p>
              <p className="text-sm text-[#8690a6]">View uploaded documents</p>
            </div>
          </div>

          {/* right upload area */}
          <div>
            {/* drop zone */}
            <div
              {...getRootProps()}
              className="rounded-2xl border-2 border-dashed border-[#a5abff] bg-[#f5f6ff] p-10 text-center"
            >
              <input {...getInputProps()} />
              <UploadCloud size={36} className="mx-auto text-[#4040E0]" />
              <p className="mt-3 text-sm text-[#5a6174]">Drag & drop your files here</p>
              <button onClick={open} className="mt-3 rounded-md bg-[#4040E0] px-5 py-2 text-sm text-white">
                Browse files
              </button>
              <p className="mt-2 text-xs text-[#8d94a6]">Supported file formats: Any file</p>
            </div>

            {/* file list */}
            {fileItems.length > 0 && (
              <div className="mt-6">
                <p className="mb-3 text-sm text-[#737b8f]">Adding files</p>
                <div className="space-y-4">
                  {fileItems.map((item) => {
                    const ext = getFileExt(item.name);
                    const color = extColor[ext] || "#6b7280";
                    return (
                      <div key={item.localId} className="flex items-center gap-3">
                        {/* file icon */}
                        <div
                          className="flex h-10 w-10 flex-col items-center justify-center rounded border border-[#d8dce6] bg-white text-[9px] font-semibold"
                          style={{ color }}
                        >
                          <span className="leading-none">.{ext || "?"}</span>
                        </div>
                        {/* name + progress */}
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm text-[#252a39]">{item.name}</p>
                            <p className="text-xs text-[#757d91]">
                              {item.status === "done" ? formatBytes(item.sizeBytes) : `${item.progress}%`}
                            </p>
                          </div>
                          {item.status === "uploading" && (
                            <div className="mt-1 h-[4px] rounded-full bg-[#d8dded]">
                              <div
                                className="h-full rounded-full bg-[#4040E0] transition-all"
                                style={{ width: `${item.progress}%` }}
                              />
                            </div>
                          )}
                        </div>
                        {/* status / actions */}
                        {item.status === "done" ? (
                          <div className="flex items-center gap-2">
                            <Check className="text-green-600" size={18} />
                            <button
                              onClick={() => removeFile(item)}
                              title="Remove file"
                              className="flex h-6 w-6 items-center justify-center rounded-full hover:bg-[#F3F4F6]"
                            >
                              <X size={14} className="text-[#9CA3AF] hover:text-[#EF4444]" />
                            </button>
                          </div>
                        ) : (
                          <button onClick={() => removeFile(item)} title="Cancel">
                            <X size={16} className="text-[#626a80]" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganizationPage;
