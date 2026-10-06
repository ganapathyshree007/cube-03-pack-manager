import React from "react";
import { CheckCircle2, XCircle, HelpCircle, AlertTriangle } from "lucide-react";
import { CheckStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: CheckStatus | string;
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = "md", showText = true }) => {
  const upper = (status || "").toUpperCase();

  const iconSizes = {
    sm: "w-3.5 h-3.5",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  const textSizes = {
    sm: "text-xs px-2 py-0.5 font-bold",
    md: "text-xs px-2.5 py-1 font-bold",
    lg: "text-sm px-3.5 py-1.5 font-extrabold tracking-wide",
  };

  if (upper === "PASS") {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-[#E6F6F6] text-[#00A09D] border border-[#BCE7E6] shadow-xs ${textSizes[size]}`}>
        <CheckCircle2 className={`${iconSizes[size]} text-[#00A09D]`} />
        {showText && <span>PASS</span>}
      </span>
    );
  }

  if (upper === "FAIL") {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 shadow-xs ${textSizes[size]}`}>
        <XCircle className={`${iconSizes[size]} text-rose-600`} />
        {showText && <span>FAIL</span>}
      </span>
    );
  }

  if (upper === "UNCERTAIN" || upper === "NEEDS MORE EVIDENCE") {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 shadow-xs ${textSizes[size]}`}>
        <HelpCircle className={`${iconSizes[size]} text-amber-600`} />
        {showText && <span>UNCERTAIN</span>}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full bg-slate-100 text-slate-700 border border-slate-300 ${textSizes[size]}`}>
      <AlertTriangle className={iconSizes[size]} />
      {showText && <span>{upper || "PENDING"}</span>}
    </span>
  );
};
