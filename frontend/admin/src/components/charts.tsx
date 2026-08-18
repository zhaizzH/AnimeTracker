import ReactECharts from 'echarts-for-react';

interface BarProps {
  title: string;
  data: Array<{ label: string; value: number }>;
}
export function BarChart({ title, data }: BarProps) {
  return (
    <>
      <h3>{title}</h3>
      <ReactECharts
        style={{ height: 260 }}
        option={{
          xAxis: { type: 'category', data: data.map((d) => d.label) },
          yAxis: { type: 'value' },
          series: [{ type: 'bar', data: data.map((d) => d.value) }],
        }}
      />
    </>
  );
}

interface LineProps {
  title: string;
  x: string[];
  series: Array<{ name: string; data: number[] }>;
}
export function LineChart({ title, x, series }: LineProps) {
  return (
    <>
      <h3>{title}</h3>
      <ReactECharts
        style={{ height: 260 }}
        option={{
          xAxis: { type: 'category', data: x },
          yAxis: { type: 'value' },
          legend: {},
          series: series.map((s) => ({ name: s.name, type: 'line', smooth: true, data: s.data })),
        }}
      />
    </>
  );
}
