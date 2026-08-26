import React, { useState } from "react";

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

interface ChartProps {
  data: ChartDataPoint[];
  height?: number;
  prefix?: string;
  suffix?: string;
}

// 1. Interactive Bar Chart
export function BarChart({ data, height = 200, prefix = "", suffix = "" }: ChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (data.length === 0) return null;

  const maxValue = Math.max(...data.map(d => d.value), 1);
  const chartHeight = height;
  const barWidth = 40;
  const barGap = 20;
  const paddingLeft = 40;
  const paddingBottom = 30;
  const paddingTop = 20;
  
  const chartWidth = data.length * (barWidth + barGap) + paddingLeft + 20;
  
  return (
    <div className="w-full overflow-x-auto text-[10px] text-neutral-500 font-mono">
      <svg width="100%" height={chartHeight + paddingTop + paddingBottom} viewBox={`0 0 ${chartWidth} ${chartHeight + paddingTop + paddingBottom}`} className="overflow-visible">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const y = paddingTop + chartHeight * (1 - ratio);
          const gridVal = Math.round(maxValue * ratio);
          return (
            <g key={i} className="opacity-40">
              <line x1={paddingLeft} y1={y} x2={chartWidth} y2={y} stroke="#262626" strokeDasharray="3,3" />
              <text x={paddingLeft - 8} y={y + 4} textAnchor="end" fill="#737373">{prefix}{gridVal}{suffix}</text>
            </g>
          );
        })}

        {/* Bars */}
        {data.map((item, idx) => {
          const barHeight = (item.value / maxValue) * chartHeight;
          const x = paddingLeft + idx * (barWidth + barGap);
          const y = paddingTop + chartHeight - barHeight;
          const isHovered = hoveredIndex === idx;

          return (
            <g 
              key={idx} 
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              className="cursor-pointer"
            >
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={Math.max(barHeight, 4)}
                rx={8}
                fill={item.color || "#10b981"}
                className="transition-all duration-300 hover:brightness-110"
                opacity={hoveredIndex === null || isHovered ? 0.85 : 0.4}
              />
              
              {/* Tooltip */}
              {isHovered && (
                <g>
                  <rect
                    x={x - 15}
                    y={y - 28}
                    width={barWidth + 30}
                    height={20}
                    rx={6}
                    fill="#0a0a0a"
                    stroke="#262626"
                    strokeWidth={1}
                  />
                  <text
                    x={x + barWidth / 2}
                    y={y - 14}
                    textAnchor="middle"
                    fill="#f5f5f5"
                    className="font-bold text-[9px]"
                  >
                    {prefix}{item.value}{suffix}
                  </text>
                </g>
              )}

              {/* X Labels */}
              <text
                x={x + barWidth / 2}
                y={paddingTop + chartHeight + 16}
                textAnchor="middle"
                fill={isHovered ? "#e5e5e5" : "#737373"}
                className="font-semibold transition-colors"
              >
                {item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// 2. Line Chart
export function LineChart({ data, height = 200, prefix = "", suffix = "" }: ChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (data.length === 0) return null;

  const maxValue = Math.max(...data.map(d => d.value), 1);
  const chartHeight = height;
  const paddingLeft = 40;
  const paddingBottom = 30;
  const paddingTop = 20;
  const gap = 60;
  const chartWidth = (data.length - 1) * gap + paddingLeft + 40;

  // Calculate points coordinates
  const points = data.map((d, i) => ({
    x: paddingLeft + i * gap,
    y: paddingTop + chartHeight - (d.value / maxValue) * chartHeight
  }));

  // Build SVG path
  const pathData = points.reduce((acc, p, i) => (
    i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`
  ), "");

  return (
    <div className="w-full overflow-x-auto text-[10px] text-neutral-500 font-mono">
      <svg width="100%" height={chartHeight + paddingTop + paddingBottom} viewBox={`0 0 ${chartWidth} ${chartHeight + paddingTop + paddingBottom}`} className="overflow-visible">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const y = paddingTop + chartHeight * (1 - ratio);
          const gridVal = Math.round(maxValue * ratio);
          return (
            <g key={i} className="opacity-40">
              <line x1={paddingLeft} y1={y} x2={chartWidth} y2={y} stroke="#262626" strokeDasharray="3,3" />
              <text x={paddingLeft - 8} y={y + 4} textAnchor="end" fill="#737373">{prefix}{gridVal}{suffix}</text>
            </g>
          );
        })}

        {/* Line Path */}
        <path
          d={pathData}
          fill="none"
          stroke="#10b981"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="opacity-80"
        />

        {/* Dots */}
        {points.map((p, idx) => {
          const isHovered = hoveredIndex === idx;
          return (
            <g 
              key={idx}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              className="cursor-pointer"
            >
              <circle
                cx={p.x}
                cy={p.y}
                r={isHovered ? 6 : 4}
                fill={isHovered ? "#34d399" : "#10b981"}
                stroke="#0a0a0a"
                strokeWidth={2}
                className="transition-all duration-200"
              />

              {/* Tooltip */}
              {isHovered && (
                <g>
                  <rect
                    x={p.x - 30}
                    y={p.y - 28}
                    width={60}
                    height={20}
                    rx={6}
                    fill="#0a0a0a"
                    stroke="#262626"
                    strokeWidth={1}
                  />
                  <text
                    x={p.x}
                    y={p.y - 14}
                    textAnchor="middle"
                    fill="#f5f5f5"
                    className="font-bold text-[9px]"
                  >
                    {prefix}{data[idx].value}{suffix}
                  </text>
                </g>
              )}

              {/* Label */}
              <text
                x={p.x}
                y={paddingTop + chartHeight + 16}
                textAnchor="middle"
                fill={isHovered ? "#e5e5e5" : "#737373"}
                className="font-semibold"
              >
                {data[idx].label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// 3. Interactive Pie Chart
export function PieChart({ data, height = 200, prefix = "", suffix = "" }: ChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (data.length === 0) return null;

  const total = data.reduce((sum, d) => sum + d.value, 0);
  const radius = 60;
  const cx = 90;
  const cy = 90;

  let accumulatedAngle = 0;

  return (
    <div className="flex flex-col md:flex-row items-center gap-6 justify-center text-[10px] text-neutral-500 font-mono p-4">
      <svg width={180} height={180} className="overflow-visible shrink-0">
        {data.map((item, idx) => {
          const angle = (item.value / total) * 360;
          
          // Coordinate calculations for SVG Arc segment path
          const x1 = cx + radius * Math.cos((accumulatedAngle - 90) * Math.PI / 180);
          const y1 = cy + radius * Math.sin((accumulatedAngle - 90) * Math.PI / 180);
          
          accumulatedAngle += angle;
          
          const x2 = cx + radius * Math.cos((accumulatedAngle - 90) * Math.PI / 180);
          const y2 = cy + radius * Math.sin((accumulatedAngle - 90) * Math.PI / 180);
          
          const largeArcFlag = angle > 180 ? 1 : 0;
          const pathString = `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
          
          const isHovered = hoveredIndex === idx;
          const transform = isHovered 
            ? `translate(${Math.cos((accumulatedAngle - angle / 2 - 90) * Math.PI / 180) * 4}, ${Math.sin((accumulatedAngle - angle / 2 - 90) * Math.PI / 180) * 4})`
            : "";

          return (
            <path
              key={idx}
              d={pathString}
              fill={item.color || "#10b981"}
              transform={transform}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              className="transition-all duration-300 cursor-pointer opacity-85 hover:opacity-100 hover:brightness-110"
            />
          );
        })}
      </svg>

      {/* Legends column */}
      <div className="flex flex-col gap-2 shrink-0">
        {data.map((item, idx) => {
          const isHovered = hoveredIndex === idx;
          const percent = ((item.value / total) * 100).toFixed(1);
          return (
            <div 
              key={idx} 
              className={`flex items-center gap-2 transition-colors ${isHovered ? 'text-neutral-100' : ''}`}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="font-bold">{item.label}:</span>
              <span>{prefix}{item.value}{suffix} ({percent}%)</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
