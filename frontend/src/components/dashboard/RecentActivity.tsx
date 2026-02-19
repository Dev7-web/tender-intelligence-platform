import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface RecentActivityProps {
  activity: Array<{ type: string; message: string; timestamp: string }>;
}

const RecentActivity = ({ activity }: RecentActivityProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {(activity || []).map((item, index) => (
            <li key={`${item.type}-${index}`} className="flex items-start gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-primary" />
              <div>
                <p className="text-sm text-text">{item.message}</p>
                <p className="text-xs text-muted">{item.timestamp}</p>
              </div>
            </li>
          ))}
          {!activity?.length && <p className="text-sm text-muted">No recent activity.</p>}
        </ul>
      </CardContent>
    </Card>
  );
};

export default RecentActivity;
