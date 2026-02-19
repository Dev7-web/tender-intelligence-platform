import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Job } from "@/types/job";

interface JobListProps {
  jobs: Job[];
  onSelect: (jobId: string) => void;
}

const JobList = ({ jobs, onSelect }: JobListProps) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Job ID</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Started</TableHead>
          <TableHead>Completed</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => (
          <TableRow
            key={job.job_id}
            onClick={() => onSelect(job.job_id)}
            className="cursor-pointer"
          >
            <TableCell>{job.job_id}</TableCell>
            <TableCell>{job.job_type}</TableCell>
            <TableCell>{job.status}</TableCell>
            <TableCell>{job.started_at}</TableCell>
            <TableCell>{job.completed_at || "-"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default JobList;
