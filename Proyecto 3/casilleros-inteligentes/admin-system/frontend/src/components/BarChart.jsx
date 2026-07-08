// Grafico de barras simple en SVG (sin dependencias) para las aperturas por dia.
export default function BarChart({ data }) {
  if (!data || !data.length) return <p>Sin datos</p>;
  const max = Math.max(1, ...data.map((d) => d.count));
  const W = 100 / data.length;
  return (
    <svg viewBox="0 0 100 60" style={{ width: "100%", height: 140 }}>
      {data.map((d, i) => {
        const h = (d.count / max) * 45;
        return (
          <g key={d.date}>
            <rect x={i * W + 2} y={50 - h} width={W - 4} height={h}
                  fill="var(--accent)" rx="1" />
            <text x={i * W + W / 2} y={58} fontSize="3" textAnchor="middle"
                  fill="var(--muted)">
              {d.date.slice(5)}
            </text>
            <text x={i * W + W / 2} y={48 - h} fontSize="3.5" textAnchor="middle"
                  fill="var(--text)">
              {d.count}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
