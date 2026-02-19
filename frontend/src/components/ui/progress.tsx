import * as React from "react";

import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
}

const Progress = ({ value, className, ...props }: ProgressProps) => {
  const clamped = Math.min(Math.max(value, 0), 100);
  return (
    <div className={cn("h-2 w-full rounded-full bg-slate-100", className)} {...props}>
      <div
        className="h-2 rounded-full bg-primary transition-all"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
};

export { Progress };
