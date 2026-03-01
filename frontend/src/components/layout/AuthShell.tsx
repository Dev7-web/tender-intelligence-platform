import { PropsWithChildren } from "react";

import BrandMark from "@/components/layout/BrandMark";

const AuthShell = ({ children }: PropsWithChildren) => {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#f1f2f6]">
      <div className="absolute right-0 top-0 h-24 w-36 rounded-bl-2xl bg-[#4040E0]" />
      <div className="absolute bottom-0 left-0 h-28 w-56 rounded-tr-2xl bg-[#4040E0]" />
      <div className="absolute bottom-6 right-8 grid gap-2.5 opacity-40" style={{ gridTemplateColumns: "repeat(16, minmax(0, 1fr))" }}>
        {Array.from({ length: 256 }).map((_, idx) => (
          <div key={idx} className="h-1.5 w-1.5 rounded-full bg-[#7c85ff]" />
        ))}
      </div>

      <div className="relative z-10 px-10 pt-8">
        <BrandMark />
      </div>

      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-80px)] w-full max-w-[980px] items-center justify-center px-4 pb-8">
        {children}
      </div>
    </div>
  );
};

export default AuthShell;
