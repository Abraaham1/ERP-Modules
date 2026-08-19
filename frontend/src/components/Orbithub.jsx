const MODULES = ["HRM", "Payroll", "Attendance", "Leave", "Employees"];
const SIZE = 400;
const CENTER = SIZE / 2;
const RADIUS = 150;
const NODE_R = 26;
const HUB_R = 34;

function nodePosition(index, total) {
  const angle = ((-90 + (360 / total) * index) * Math.PI) / 180;
  return {
    x: CENTER + RADIUS * Math.cos(angle),
    y: CENTER + RADIUS * Math.sin(angle),
  };
}

export default function OrbitHub() {
  const nodes = MODULES.map((label, i) => ({
    label,
    ...nodePosition(i, MODULES.length),
  }));

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      className="w-full h-full max-w-sm mx-auto"
      role="img"
      aria-label="Diagram of ERP modules — HRM, Payroll, Attendance, Leave and Employees — connected to a central hub"
    >
      <defs>
        <radialGradient id="hubGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#818cf8" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#a5b4fc" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#a5b4fc" stopOpacity="0.12" />
        </linearGradient>
      </defs>

      <circle cx={CENTER} cy={CENTER} r={RADIUS + 40} fill="url(#hubGlow)" />

      {nodes.map((n, i) => (
        <g key={`line-${i}`}>
          <line
            x1={CENTER}
            y1={CENTER}
            x2={n.x}
            y2={n.y}
            stroke="url(#lineGrad)"
            strokeWidth="1.5"
          />
          <circle r="3.5" fill="#c7d2fe" className="motion-reduce:hidden">
            <animateMotion
              dur={`${2.6 + i * 0.35}s`}
              repeatCount="indefinite"
              path={`M${CENTER},${CENTER} L${n.x},${n.y}`}
            />
            <animate
              attributeName="opacity"
              values="0;1;1;0"
              dur={`${2.6 + i * 0.35}s`}
              repeatCount="indefinite"
            />
          </circle>
        </g>
      ))}

      {nodes.map((n, i) => (
        <g
          key={`node-${i}`}
          className="motion-safe:animate-node-pulse"
          style={{ animationDelay: `${i * 0.4}s` }}
        >
          <circle cx={n.x} cy={n.y} r={NODE_R} fill="#111735" stroke="#4f46e5" strokeWidth="1.5" />
          <circle cx={n.x} cy={n.y} r="4" fill="#34d399" />
          <text
            x={n.x}
            y={n.y + NODE_R + 16}
            textAnchor="middle"
            className="fill-slate-300"
            style={{ fontSize: "10px", fontFamily: "ui-monospace, monospace", letterSpacing: "0.05em" }}
          >
            {n.label.toUpperCase()}
          </text>
        </g>
      ))}

      <g>
        <circle
          cx={CENTER}
          cy={CENTER}
          r={HUB_R}
          fill="none"
          stroke="#818cf8"
          strokeWidth="1.5"
          opacity="0.5"
          className="motion-safe:animate-ping"
        />
        <circle cx={CENTER} cy={CENTER} r={HUB_R} fill="#1c2452" stroke="#818cf8" strokeWidth="2" />
        <text
          x={CENTER}
          y={CENTER + 5}
          textAnchor="middle"
          className="fill-white"
          style={{ fontSize: "14px", fontWeight: 700, letterSpacing: "0.03em" }}
        >
          ERP
        </text>
      </g>
    </svg>
  );
}