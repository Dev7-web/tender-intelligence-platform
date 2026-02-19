import { Link } from "react-router-dom";

import StatsCards from "@/components/dashboard/StatsCards";
import RecentActivity from "@/components/dashboard/RecentActivity";
import ProcessingQueue from "@/components/dashboard/ProcessingQueue";
import { buttonVariants } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useDashboard";

const Dashboard = () => {
  const { stats, activity, queue } = useDashboard();

  return (
    <div className="space-y-6 animate-rise">
      <StatsCards stats={stats.data} />
      <div className="flex flex-wrap gap-3">
        <Link className={buttonVariants()} to="/companies">
          Upload Company Profile
        </Link>
        <Link className={buttonVariants({ variant: "outline" })} to="/tenders">
          View All Tenders
        </Link>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <ProcessingQueue queue={queue.data || []} />
        <RecentActivity activity={activity.data || []} />
      </div>
    </div>
  );
};

export default Dashboard;
