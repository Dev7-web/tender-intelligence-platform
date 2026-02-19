import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Job } from "@/types/job";

interface JobDetailProps {
  job?: Job | null;
}

const JobDetail = ({ job }: JobDetailProps) => {
  if (!job) {
    return <p className="text-sm text-muted">Select a job to view details.</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>Job ID: {job.job_id}</p>
        <p>Type: {job.job_type}</p>
        <p>Status: {job.status}</p>
        <p>Started: {job.started_at}</p>
        <p>Completed: {job.completed_at || "-"}</p>
        <div>
          <p className="font-semibold">Stats</p>
          <pre className="rounded-lg bg-slate-50 p-3 text-xs text-muted">
            {JSON.stringify(job.stats || {}, null, 2)}
          </pre>
        </div>
      </CardContent>
    </Card>
  );
};

export default JobDetail;
