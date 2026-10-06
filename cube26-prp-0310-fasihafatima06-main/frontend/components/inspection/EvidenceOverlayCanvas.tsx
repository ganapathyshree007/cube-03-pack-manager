"use client";
import React, { useState } from "react";
import { BoundingBox } from "@/lib/types";

interface EvidenceOverlayCanvasProps {
  imageUrl: string;
  width?: number;
  height?: number;
  boundingBoxes: BoundingBox[];
  activeToggles: {
    labels: boolean;
    barcodes: boolean;
    edges: boolean;
    text: boolean;
    packaging: boolean;
  };
}

export const EvidenceOverlayCanvas: React.FC<EvidenceOverlayCanvasProps> = ({
  imageUrl,
  width = 800,
  height = 600,
  boundingBoxes = [],
  activeToggles,
}) => {
  const [hoveredBox, setHoveredBox] = useState<BoundingBox | null>(null);

  // Filter boxes based on user toggle controls
  const visibleBoxes = boundingBoxes.filter((box) => {
    const t = box.type.toLowerCase();
    if (t.includes("fnsku") || t.includes("label")) return activeToggles.labels;
    if (t.includes("barcode") || t.includes("upc")) return activeToggles.barcodes;
    if (t.includes("edge") || t.includes("seam")) return activeToggles.edges;
    if (t.includes("warning") || t.includes("text")) return activeToggles.text;
    if (t.includes("polybag") || t.includes("seal") || t.includes("enclosure")) return activeToggles.packaging;
    return true;
  });

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-[#090D16] rounded-2xl overflow-hidden border border-[#1E263D] shadow-inner group">
      {/* Target Product Photo */}
      <img
        src={imageUrl}
        alt="Inspection Evidence"
        className="max-w-full max-h-[520px] object-contain select-none"
      />

      {/* SVG Evidence Bounding Box Overlay */}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="absolute inset-0 w-full h-full pointer-events-none"
        preserveAspectRatio="xMidYMid meet"
      >
        {visibleBoxes.map((box, idx) => {
          const isHovered = hoveredBox === box;
          const strokeColor = box.color || (box.type.includes("fnsku") ? "#6366F1" : "#10B981");

          return (
            <g key={idx} className="pointer-events-auto cursor-pointer" onMouseEnter={() => setHoveredBox(box)} onMouseLeave={() => setHoveredBox(null)}>
              {/* Bounding Rectangle */}
              <rect
                x={box.x}
                y={box.y}
                width={box.width}
                height={box.height}
                fill={isHovered ? `${strokeColor}25` : `${strokeColor}12`}
                stroke={strokeColor}
                strokeWidth={isHovered ? 4 : 2.5}
                strokeDasharray={box.type.includes("edge") ? "6,4" : undefined}
                className="transition-all duration-150"
              />

              {/* Box Corner Anchors */}
              <circle cx={box.x} cy={box.y} r="3.5" fill={strokeColor} />
              <circle cx={box.x + box.width} cy={box.y} r="3.5" fill={strokeColor} />
              <circle cx={box.x} cy={box.y + box.height} r="3.5" fill={strokeColor} />
              <circle cx={box.x + box.width} cy={box.y + box.height} r="3.5" fill={strokeColor} />

              {/* Box Label Tag */}
              <g transform={`translate(${box.x}, ${Math.max(16, box.y - 6)})`}>
                <rect
                  x="0"
                  y="-16"
                  width={Math.max(90, (box.label || box.type).length * 7 + 16)}
                  height="20"
                  rx="4"
                  fill={strokeColor}
                />
                <text
                  x="8"
                  y="-2"
                  fill="#090D16"
                  fontSize="11"
                  fontWeight="800"
                  fontFamily="'Plus Jakarta Sans', sans-serif"
                >
                  {box.label || box.type.toUpperCase()}
                </text>
              </g>
            </g>
          );
        })}
      </svg>

      {/* Hover Info Tooltip */}
      {hoveredBox && (
        <div className="absolute top-4 left-4 bg-[#111625]/95 border border-indigo-500/50 backdrop-blur-md px-3.5 py-2.5 rounded-xl text-xs shadow-xl z-20 pointer-events-none">
          <div className="font-bold text-indigo-300">{hoveredBox.label || hoveredBox.type}</div>
          <div className="text-slate-300 text-[11px] font-mono mt-0.5">
            Coords: ({hoveredBox.x}, {hoveredBox.y}) • Size: {hoveredBox.width}×{hoveredBox.height}px
          </div>
          {hoveredBox.confidence && (
            <div className="text-slate-400 text-[10px] mt-0.5 font-mono">
              Confidence: {Math.round(hoveredBox.confidence * 100)}%
            </div>
          )}
        </div>
      )}
    </div>
  );
};
