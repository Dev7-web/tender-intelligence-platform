import brandMarkIcon from "@/assets/dashboard/brand-mark-icon.svg";

const BrandMark = () => {
  return (
    <div className="flex items-center gap-2 text-lg font-semibold text-slate-900 md:text-xl">
      <img src={brandMarkIcon} alt="Tender Agent logo" className="h-10 w-10 shrink-0" />
      <span className="text-xl leading-none md:text-2xl">Tender Agent</span>
    </div>
  );
};

export default BrandMark;
