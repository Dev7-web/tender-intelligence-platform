import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface StatsCardsProps {
  stats: any;
}

const StatsCards = ({ stats }: StatsCardsProps) => {
  const items = [
    {
      label: "Total Tenders",
      value: stats?.tenders?.total ?? 0,
      detail: `${stats?.tenders?.processed ?? 0} processed`,
    },
    {
      label: "Companies",
      value: stats?.companies?.total ?? 0,
      detail: "Profiles uploaded",
    },
    {
      label: "Active Jobs",
      value: stats?.jobs?.running ?? 0,
      detail: `${stats?.jobs?.completed_today ?? 0} completed today`,
    },
    {
      label: "Searches Today",
      value: stats?.searches?.today ?? 0,
      detail: `${stats?.searches?.total ?? 0} total`,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardHeader>
            <CardTitle className="text-sm text-muted">{item.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-text">{item.value}</p>
            <p className="text-xs text-muted mt-2">{item.detail}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default StatsCards;
