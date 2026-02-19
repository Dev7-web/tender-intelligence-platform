interface StepHeaderProps {
  step: number;
  total?: number;
}

const StepHeader = ({ step, total = 3 }: StepHeaderProps) => {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        {Array.from({ length: total }).map((_, index) => (
          <div
            key={index}
            className={[
              "h-[6px] w-10 rounded-full",
              index < step ? "bg-[#4040E0]" : "bg-[#d0d4de]",
            ].join(" ")}
          />
        ))}
      </div>
      <p className="text-sm text-[#8a91a4]">
        {step} of {total}
      </p>
    </div>
  );
};

export default StepHeader;
