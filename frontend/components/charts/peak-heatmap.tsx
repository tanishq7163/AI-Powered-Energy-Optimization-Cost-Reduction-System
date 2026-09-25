type HeatmapItem = {
  weekday?: number;
  hour?: number;
  value?: number;
};

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function PeakHeatmap({ data }: { data: HeatmapItem[] }) {
  const maxValue = Math.max(...data.map((item) => item.value ?? 0), 1);

  return (
    <div className="grid gap-2 md:grid-cols-7">
      {days.map((day, weekdayIndex) => (
        <div key={day} className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--muted-foreground)]">
            {day}
          </p>
          <div className="grid grid-cols-4 gap-2">
            {Array.from({ length: 24 }).map((_, hour) => {
              const point = data.find(
                (entry) => entry.weekday === weekdayIndex && entry.hour === hour,
              );
              const intensity = ((point?.value ?? 0) / maxValue) * 0.9 + 0.1;
              return (
                <div
                  key={`${day}-${hour}`}
                  className="aspect-square rounded-xl"
                  style={{
                    backgroundColor: `rgba(15, 118, 110, ${intensity})`,
                  }}
                  title={`${day} ${hour}:00 - ${(point?.value ?? 0).toFixed(2)} kWh`}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
