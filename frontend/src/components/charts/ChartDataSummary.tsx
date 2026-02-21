interface PriceDataPoint {
  time: string | number;
  value: number;
}

export interface ChartSummary {
  open: number;
  close: number;
  min: number;
  max: number;
  trend: 'up' | 'down' | 'flat';
  samplePoints: { label: string; value: number }[];
}

function formatTimeLabel(time: string | number): string {
  if (typeof time === 'number') {
    return new Date(time * 1000).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
  return String(time);
}

export function buildChartSummary(data: PriceDataPoint[]): ChartSummary | null {
  if (data.length === 0) return null;

  const values = data.map((d) => d.value);
  const open = values[0];
  const close = values[values.length - 1];
  const min = Math.min(...values);
  const max = Math.max(...values);

  const delta = close - open;
  const threshold = open !== 0 ? Math.abs(open) * 0.001 : 0.001;
  const trend: 'up' | 'down' | 'flat' =
    Math.abs(delta) < threshold ? 'flat' : delta > 0 ? 'up' : 'down';

  const sampleCount = Math.min(10, data.length);
  let samplePoints: { label: string; value: number }[];

  if (sampleCount === 1) {
    samplePoints = [{ label: formatTimeLabel(data[0].time), value: data[0].value }];
  } else {
    const step = (data.length - 1) / (sampleCount - 1);
    samplePoints = Array.from({ length: sampleCount }, (_, i) => {
      const idx = Math.min(Math.round(i * step), data.length - 1);
      const point = data[idx];
      return { label: formatTimeLabel(point.time), value: point.value };
    });
  }

  return { open, close, min, max, trend, samplePoints };
}

interface ChartDataSummaryProps {
  id: string;
  data: PriceDataPoint[];
}

export function ChartDataSummary({ id, data }: ChartDataSummaryProps) {
  const summary = buildChartSummary(data);

  if (!summary) return null;

  const { open, close, min, max, trend, samplePoints } = summary;
  const trendText = trend === 'up' ? 'upward' : trend === 'down' ? 'downward' : 'flat';
  const narrative = `Price range from ${min.toFixed(2)} to ${max.toFixed(2)}. Opened at ${open.toFixed(2)}, closed at ${close.toFixed(2)}. Overall trend is ${trendText}.`;

  return (
    <div id={id} className="sr-only">
      <p>{narrative}</p>
      <table>
        <caption>Sampled price data points</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Price</th>
          </tr>
        </thead>
        <tbody>
          {samplePoints.map((point, i) => (
            <tr key={i}>
              <td>{point.label}</td>
              <td>{point.value.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
