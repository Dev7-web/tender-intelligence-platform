import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";

import aiResponseSparkleIcon from "@/assets/tenders/ai-response-sparkle.svg";
import aiSparkleIcon from "@/assets/tenders/ai-sparkle.svg";
import aiSparkleBlueIcon from "@/assets/tenders/ai-sparkle-blue.svg";
import sendButtonIcon from "@/assets/tenders/send-button.svg";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { askTenderAi, fetchAiSuggestions } from "@/services/tenderAgentApi";

interface DiscussWithAIProps {
  open: boolean;
  onClose: () => void;
  tenderId: string;
  companyId: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const DiscussWithAI = ({ open, onClose, tenderId, companyId }: DiscussWithAIProps) => {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatId, setChatId] = useState<string | undefined>();
  const { pushToast } = useToastSimple();

  useEffect(() => {
    if (!open) return;
    fetchAiSuggestions(tenderId)
      .then((items) => setSuggestions(items))
      .catch(() => setSuggestions([]));
  }, [open, tenderId]);

  const sendMessage = async (value: string) => {
    if (!value.trim() || loading) return;
    const content = value.trim();
    setQuestion("");
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content }]);

    try {
      const response = await askTenderAi(tenderId, {
        company_id: companyId,
        message: content,
        chat_id: chatId,
      });
      setChatId(response.chat_id);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
    } catch {
      pushToast("Failed to get AI response", "error");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I could not generate a response right now. Please cross-check this with the official tender document.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/35 p-4">
      <div className="flex h-[92vh] w-full max-w-[980px] flex-col overflow-hidden rounded-lg bg-white">
        <div className="flex items-start justify-between border-b border-[#dce0ea] px-5 py-3">
          <div className="flex items-center gap-3">
            <img src={aiSparkleIcon} alt="" className="h-7 w-7" />
            <div>
              <h3 className="text-xl font-semibold text-[#202532] md:text-2xl">Discuss with AI</h3>
              <p className="text-xs text-[#8b91a2]">Tender Analysis</p>
            </div>
          </div>
          <button onClick={onClose} className="text-[#202532]">
            <X size={18} />
          </button>
        </div>

        <div className="mx-3 mt-3 flex-1 overflow-hidden rounded-md bg-[#eceef3] p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-5">
              <p className="text-center text-xl font-medium leading-snug text-[#303543] md:text-3xl">
                Hello, how can I assist you with<br />this tender?
              </p>
              <div className="flex w-full max-w-[700px] flex-col items-center gap-2">
                {suggestions.map((item) => (
                  <button
                    key={item}
                    className="inline-flex items-center gap-2 rounded-full border border-[#d6dae5] bg-white px-4 py-2 text-[14px] text-[#414758] hover:border-[#bec4d8]"
                    onClick={() => sendMessage(item)}
                  >
                    <Search size={14} className="shrink-0 text-[#8b91a2]" />
                    {item}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex h-full flex-col gap-3 overflow-y-auto pr-1">
              {messages.map((message, index) =>
                message.role === "assistant" ? (
                  <div key={`${message.role}-${index}`} className="flex max-w-[72%] items-start gap-2 self-start">
                    <img src={aiResponseSparkleIcon} alt="" className="mt-1 h-8 w-8 shrink-0" />
                    <div className="rounded-xl bg-[#dfe1f8] px-4 py-3 text-[15px] leading-6 text-[#30364a]">
                      {message.content}
                    </div>
                  </div>
                ) : (
                  <div
                    key={`${message.role}-${index}`}
                    className="max-w-[72%] self-end rounded-xl bg-white px-4 py-3 text-[15px] leading-6 text-[#30364a]"
                  >
                    {message.content}
                  </div>
                )
              )}
            </div>
          )}
        </div>

        <div className="mt-2 border-t border-[#dce0ea] px-3 pb-2 pt-2">
          <div className="flex items-center gap-2">
            <div className="flex flex-1 items-center rounded-full border border-[#d6dae5] bg-white px-3">
              <img src={aiSparkleBlueIcon} alt="" className="h-5 w-5 shrink-0" />
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask anything"
                className="h-10 flex-1 border-none bg-transparent px-2 text-sm outline-none"
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    sendMessage(question);
                  }
                }}
              />
            </div>
            <button
              onClick={() => sendMessage(question)}
              disabled={loading}
              className="shrink-0 disabled:opacity-60"
            >
              <img src={sendButtonIcon} alt="Send" className="h-11 w-11" />
            </button>
          </div>
          <p className="mt-2 text-center text-[11px] text-[#a1a8b8]">
            The AI provides an analysis of tender documents. Always cross-reference with official sources.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DiscussWithAI;
