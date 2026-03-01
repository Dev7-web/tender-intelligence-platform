import { useMemo, useState } from "react";
import { X } from "lucide-react";

import { shareTenderByEmail } from "@/services/tenderAgentApi";
import { useToastSimple } from "@/components/ui/toaster-simple";

interface ShareTenderProps {
  open: boolean;
  onClose: () => void;
  tenderId: string;
  companyId: string;
}

interface Recipient {
  email: string;
  name: string;
}

const AVATAR_COLORS = [
  { bg: "bg-pink-200", text: "text-pink-700" },
  { bg: "bg-teal-200", text: "text-teal-700" },
  { bg: "bg-purple-200", text: "text-purple-700" },
  { bg: "bg-blue-200", text: "text-blue-700" },
  { bg: "bg-amber-200", text: "text-amber-700" },
  { bg: "bg-green-200", text: "text-green-700" },
];

const getAvatarColor = (index: number) => AVATAR_COLORS[index % AVATAR_COLORS.length];

const ShareTender = ({ open, onClose, tenderId, companyId }: ShareTenderProps) => {
  const [input, setInput] = useState("");
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [sending, setSending] = useState(false);
  const { pushToast } = useToastSimple();

  const canDone = useMemo(() => recipients.length > 0 && !sending, [recipients.length, sending]);

  const addRecipient = () => {
    const email = input.trim().toLowerCase();
    if (!email) return;
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      pushToast("Enter a valid email", "error");
      return;
    }
    if (recipients.some((item) => item.email === email)) {
      setInput("");
      return;
    }

    const namePart = email.split("@")[0];
    const name = namePart
      .split(/[._-]/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

    setRecipients((prev) => [...prev, { email, name: name || "User" }]);
    setInput("");
  };

  const removeRecipient = (email: string) => {
    setRecipients((prev) => prev.filter((item) => item.email !== email));
  };

  const submit = async () => {
    if (!canDone) return;
    setSending(true);
    try {
      const result = await shareTenderByEmail(tenderId, {
        company_id: companyId,
        recipients: recipients.map((item) => item.email),
      });
      if (result.sent) {
        pushToast(`Shared with ${result.count} recipient(s)`, "success");
        onClose();
      } else {
        pushToast("Unable to share tender", "error");
      }
    } catch {
      pushToast("Unable to share tender", "error");
    } finally {
      setSending(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-[860px] rounded-2xl bg-white px-8 py-6">
        <div className="flex items-center justify-between">
          <h3 className="text-2xl font-bold text-[#111827]">Share Tender by Email</h3>
          <button onClick={onClose} className="text-[#111827]">
            <X size={24} strokeWidth={2.5} />
          </button>
        </div>

        <div className="mt-5 flex gap-3">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Example@gmail.com"
            className="h-12 flex-1 rounded-lg border border-[#c9ceda] bg-white px-4 text-base text-[#111827] placeholder:text-[#9ca3af]"
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                addRecipient();
              }
            }}
          />
          <button onClick={addRecipient} className="h-12 rounded-lg bg-[#4040E0] px-7 text-base font-medium text-white">
            Add
          </button>
        </div>

        <fieldset className="mt-5 min-h-[200px] rounded-lg border border-[#c9ceda] px-5 pb-5 pt-1">
          <legend className="px-1 text-sm font-semibold text-[#111827]">
            Individuals authorized to receive the tender
          </legend>
          <div className="flex flex-col gap-4 pt-2">
            {recipients.map((recipient, index) => {
              const color = getAvatarColor(index);
              const initials = recipient.name
                .split(" ")
                .slice(0, 2)
                .map((part) => part[0])
                .join("")
                .toUpperCase();
              return (
                <div
                  key={recipient.email}
                  className="flex w-fit items-center gap-3 rounded-xl border border-[#e5e7eb] bg-[#fafafa] px-4 py-2.5"
                >
                  <div
                    className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold ${color.bg} ${color.text}`}
                  >
                    {initials}
                  </div>
                  <div className="mr-2">
                    <p className="text-sm font-semibold text-[#111827]">{recipient.name}</p>
                    <p className="text-xs text-[#6b7280]">{recipient.email}</p>
                  </div>
                  <button onClick={() => removeRecipient(recipient.email)} className="text-[#111827]">
                    <X size={20} strokeWidth={2.5} />
                  </button>
                </div>
              );
            })}
          </div>
        </fieldset>

        <button
          disabled={!canDone}
          onClick={submit}
          className="mx-auto mt-5 block h-12 min-w-[220px] rounded-full bg-[#4040E0] px-8 text-base font-medium text-white disabled:opacity-50"
        >
          {sending ? "Sending..." : "Done"}
        </button>
      </div>
    </div>
  );
};

export default ShareTender;
