import { FileText } from "lucide-react";

const BrandMark = () => {
  return (
    <div className="flex items-center gap-2 text-lg font-semibold text-slate-900 md:text-xl">
      <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-[#4040E0] text-white">
        <FileText size={14} />
      </div>
      <span className="text-xl leading-none md:text-2xl">Tender Agent</span>
    </div>
  );
};

export default BrandMark;
