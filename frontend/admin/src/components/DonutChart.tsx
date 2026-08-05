import type { TypeCount } from '../mock/dashboard';

interface DonutChartProps {
  items: TypeCount[];
  centerLabel: string;
  centerValue: string;
}

export default function DonutChart({ items, centerLabel, centerValue }: DonutChartProps) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  let acc = 0;
  const stops = items
    .filter((item) => item.value > 0)
    .map((item) => {
      const start = (acc / total) * 100;
      acc += item.value;
      const end = (acc / total) * 100;
      return `${item.color} ${start.toFixed(2)}% ${end.toFixed(2)}%`;
    })
    .join(', ');

  return (
    <div className="donut-wrap">
      <div className="donut" style={{ background: `conic-gradient(${stops})` }}>
        <div className="donut-inner">
          <div>
            <strong>{centerValue}</strong>
            <span>{centerLabel}</span>
          </div>
        </div>
      </div>
      <div className="donut-legend">
        {items.map((item) => (
          <div className="bar-row" key={item.label}>
            <span className="bar-label">{item.label}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: total > 0 ? `${(item.value / total) * 100}%` : '0%', background: item.color }}
              />
            </div>
            <span className="bar-value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
