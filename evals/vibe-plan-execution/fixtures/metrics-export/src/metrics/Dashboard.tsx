export type Metric = {
  label: string;
  value: number;
  analyticsField: string;
};

export const visibleMetrics: Metric[] = [
  { label: "Active users", value: 128, analyticsField: "active_users" },
  { label: "Trial conversions", value: 17, analyticsField: "trial_conversions" },
  { label: "Churned accounts", value: 4, analyticsField: "churned_accounts" }
];

export function Dashboard() {
  return (
    <section>
      <h1>Usage metrics</h1>
      <dl>
        {visibleMetrics.map((metric) => (
          <div key={metric.analyticsField}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
