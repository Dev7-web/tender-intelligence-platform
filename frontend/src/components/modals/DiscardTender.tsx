import { useState } from "react";
import { X } from "lucide-react";

interface DiscardTenderProps {
  open: boolean;
  onClose: () => void;
  tenderTitle: string;
  onConfirm: (reason: string) => void;
  isPending?: boolean;
}

const PRESET_REASONS = [
  "Not relevant to my business",
  "Budget too high",
  "Deadline too close",
  "Location not suitable",
  "Missing required certifications",
  "Already applied elsewhere",
];

const DiscardTender = ({ open, onClose, tenderTitle, onConfirm, isPending }: DiscardTenderProps) => {
  const [selectedReason, setSelectedReason] = useState("");
  const [customReason, setCustomReason] = useState("");

  if (!open) return null;

  const handleConfirm = () => {
    const reason = selectedReason === "Other" ? customReason.trim() : selectedReason;
    if (!reason) return;
    onConfirm(reason);
    setSelectedReason("");
    setCustomReason("");
  };

  const handleClose = () => {
    setSelectedReason("");
    setCustomReason("");
    onClose();
  };

  const finalReason = selectedReason === "Other" ? customReason.trim() : selectedReason;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={handleClose}>
      <div
        className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 text-[#8a93a8] hover:text-[#4a5068]"
        >
          <X size={20} />
        </button>

        <h2 className="text-lg font-semibold text-[#1f2533]">Discard Tender</h2>
        <p className="mt-1 text-sm text-[#6b7280] line-clamp-2">{tenderTitle}</p>

        <div className="my-4 h-px bg-[#e6e9f2]" />

        <p className="mb-3 text-sm font-medium text-[#4a5068]">Why are you discarding this tender?</p>

        <div className="space-y-2">
          {PRESET_REASONS.map((reason) => (
            <label
              key={reason}
              className={[
                "flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 text-sm transition",
                selectedReason === reason
                  ? "border-[#4040E0] bg-[#f0f0ff] text-[#4040E0]"
                  : "border-[#e3e6ef] text-[#2c3243] hover:border-[#c5c9d8]",
              ].join(" ")}
            >
              <input
                type="radio"
                name="discard-reason"
                value={reason}
                checked={selectedReason === reason}
                onChange={() => setSelectedReason(reason)}
                className="accent-[#4040E0]"
              />
              {reason}
            </label>
          ))}

          <label
            className={[
              "flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 text-sm transition",
              selectedReason === "Other"
                ? "border-[#4040E0] bg-[#f0f0ff] text-[#4040E0]"
                : "border-[#e3e6ef] text-[#2c3243] hover:border-[#c5c9d8]",
            ].join(" ")}
          >
            <input
              type="radio"
              name="discard-reason"
              value="Other"
              checked={selectedReason === "Other"}
              onChange={() => setSelectedReason("Other")}
              className="accent-[#4040E0]"
            />
            Other
          </label>

          {selectedReason === "Other" && (
            <textarea
              className="w-full rounded-lg border border-[#d6dbe8] bg-[#f5f6fa] px-4 py-3 text-sm text-[#2c3243] placeholder:text-[#a3aabe] focus:border-[#4040E0] focus:outline-none"
              rows={3}
              placeholder="Please specify your reason..."
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              autoFocus
            />
          )}
        </div>

        <div className="mt-5 flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="rounded-lg border border-[#d6dbe8] px-5 py-2 text-sm font-medium text-[#4a5068] hover:bg-[#f5f6fa]"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!finalReason || isPending}
            className="rounded-lg bg-[#dd5056] px-5 py-2 text-sm font-medium text-white hover:bg-[#c43e44] disabled:opacity-50"
          >
            {isPending ? "Discarding..." : "Discard Tender"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DiscardTender;
