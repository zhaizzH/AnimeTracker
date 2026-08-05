import type { TrendPoint } from '../mock/dashboard';

interface TrendChartProps {
  data: TrendPoint[];
}

const W = 720;
const H = 210;
const PAD_X = 34;
const PAD_TOP = 18;
const PAD_BOTTOM = 26;

export default function TrendChart({ data }: TrendChartProps) {
  if (data.length === 0) {
    return <div className="chart-empty">暂无趋势数据</div>;
  }

  const series = [
    { key: 'newUsers', label: '新增用户', color: '#00b3a4', values: data.map((d) => d.newUsers) },
    { key: 'newCollections', label: '新增收藏', color: '#e99b2f', values: data.map((d) => d.newCollections) },
    { key: 'logins', label: '登录数', color: '#2f7fe8', values: data.map((d) => d.logins) },
  ] as const;

  const maxValue = Math.max(...series.flatMap((s) => s.values)) * 1.15;
  const innerW = W - PAD_X * 2;
  const innerH = H - PAD_TOP - PAD_BOTTOM;
  const x = (i: number) => PAD_X + (i * innerW) / (data.length - 1);
  const y = (v: number) => PAD_TOP + innerH - (v / maxValue) * innerH;
  const toLine = (values: readonly number[]) =>
    values.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const toArea = (values: readonly number[]) =>
    `${toLine(values)} L ${x(values.length - 1).toFixed(1)} ${(PAD_TOP + innerH).toFixed(1)} L ${x(0).toFixed(1)} ${(PAD_TOP + innerH).toFixed(1)} Z`;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => PAD_TOP + innerH * (1 - t));
  const labelIndexes =
    data.length > 10 ? [0, Math.floor(data.length / 2), data.length - 1] : data.map((_, i) => i);

  return (
    <div className="trend-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="运营趋势">
        {ticks.map((tick, idx) => (
          <g key={idx}>
            <line
              x1={PAD_X}
              x2={W - PAD_X}
              y1={tick}
              y2={tick}
              stroke="#dfe6ee"
              strokeDasharray="3 4"
              strokeWidth="1"
            />
            <text
              x={4}
              y={tick + 3}
              fill="#8a9aa8"
              fontSize="10"
              fontFamily="Cascadia Mono, Consolas, monospace"
            >
              {Math.round(maxValue * (1 - idx / 4))}
            </text>
          </g>
        ))}
        <path d={toArea(series[0].values)} fill="rgba(0,179,164,0.10)" />
        {series.map((s) => (
          <path
            key={s.key}
            d={toLine(s.values)}
            fill="none"
            stroke={s.color}
            strokeWidth="2"
            strokeLinejoin="round"
          />
        ))}
        {labelIndexes.map((i) => (
          <text
            key={i}
            x={x(i)}
            y={H - 6}
            fill="#8a9aa8"
            fontSize="10"
            textAnchor="middle"
            fontFamily="Cascadia Mono, Consolas, monospace"
          >
            {data[i].date}
          </text>
        ))}
      </svg>
      <div className="chart-legend">
        {series.map((s) => (
          <span className="legend-item" key={s.key}>
            <span className="legend-swatch" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}
