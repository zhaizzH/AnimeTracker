export interface BarItem {
  label: string;
  value: number;
  color?: string;
}

interface BarListProps {
  items: BarItem[];
}

export default function BarList({ items }: BarListProps) {
  const max = items.length ? Math.max(...items.map((item) => item.value)) : 0;
  return (
    <div className="bar-list">
      {items.map((item) => (
        <div className="bar-row" key={item.label}>
          <span className="bar-label">{item.label}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: max > 0 ? `${(item.value / max) * 100}%` : '0%', background: item.color }}
            />
          </div>
          <span className="bar-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
