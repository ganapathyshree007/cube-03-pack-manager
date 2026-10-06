"use client";
import React from "react";

export function TableSkeletonRows({ rows = 5, cols = 7 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, rIdx) => (
        <tr key={rIdx} className="border-b border-slate-800/30">
          {Array.from({ length: cols }).map((_, cIdx) => {
            const widths = ["w-20", "w-28", "w-32", "w-16", "w-24", "w-36", "w-20", "w-16", "w-24"];
            const widthClass = widths[cIdx % widths.length];
            const isRight = cIdx === 3 || cIdx === cols - 1;

            return (
              <td key={cIdx} className={`py-4 px-4 ${isRight ? "text-right" : ""}`}>
                <div
                  className={`h-4 rounded-md ${widthClass} ${
                    isRight ? "ml-auto" : ""
                  }`}
                  style={{
                    background: "linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)",
                    backgroundSize: "200% 100%",
                    animation: `shimmer 1.5s linear infinite`,
                    animationDelay: `${rIdx * 0.08 + cIdx * 0.03}s`,
                  }}
                />
              </td>
            );
          })}
        </tr>
      ))}
    </>
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/50 shadow-card relative overflow-hidden">
      <div className="flex justify-between items-start">
        <div className="space-y-3">
          <div
            className="h-3 w-28 rounded-md"
            style={{
              background: "linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.6) 75%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.5s linear infinite",
            }}
          />
          <div
            className="h-7 w-36 rounded-md"
            style={{
              background: "linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.6) 75%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.5s linear infinite",
              animationDelay: "0.1s",
            }}
          />
        </div>
        <div
          className="w-10 h-10 rounded-xl"
          style={{
            background: "linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.6) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            animationDelay: "0.2s",
          }}
        />
      </div>
      <div
        className="mt-4 h-3 w-44 rounded-md"
        style={{
          background: "linear-gradient(90deg, rgba(30,41,59,0.4) 25%, rgba(51,65,85,0.2) 50%, rgba(30,41,59,0.4) 75%)",
          backgroundSize: "200% 100%",
          animation: "shimmer 1.5s linear infinite",
          animationDelay: "0.15s",
        }}
      />
    </div>
  );
}

export function EvidenceCardSkeleton() {
  return (
    <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/50 shadow-card space-y-3">
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <div
            className="h-4 w-16 rounded-md"
            style={{
              background: "linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.6) 75%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.5s linear infinite",
            }}
          />
          <div
            className="h-4 w-28 rounded-md"
            style={{
              background: "linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.6) 75%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.5s linear infinite",
              animationDelay: "0.1s",
            }}
          />
        </div>
        <div
          className="h-5 w-20 rounded-md"
          style={{
            background: "linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.6) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            animationDelay: "0.15s",
          }}
        />
      </div>
      <div className="space-y-1.5 pt-1">
        <div
          className="h-3.5 w-full rounded-md"
          style={{
            background: "linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.2) 50%, rgba(30,41,59,0.5) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            animationDelay: "0.1s",
          }}
        />
        <div
          className="h-3.5 w-4/5 rounded-md"
          style={{
            background: "linear-gradient(90deg, rgba(30,41,59,0.4) 25%, rgba(51,65,85,0.2) 50%, rgba(30,41,59,0.4) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            animationDelay: "0.2s",
          }}
        />
      </div>
      <div className="pt-2 border-t border-slate-800/50 flex items-center justify-between">
        <div
          className="h-3 w-24 rounded-md"
          style={{
            background: "linear-gradient(90deg, rgba(30,41,59,0.4) 25%, rgba(51,65,85,0.2) 50%, rgba(30,41,59,0.4) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            animationDelay: "0.15s",
          }}
        />
        <div
          className="h-3 w-20 rounded-md"
          style={{
            background: "linear-gradient(90deg, rgba(30,41,59,0.4) 25%, rgba(51,65,85,0.2) 50%, rgba(30,41,59,0.4) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            animationDelay: "0.25s",
          }}
        />
      </div>
    </div>
  );
}
