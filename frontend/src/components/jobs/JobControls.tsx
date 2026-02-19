import { Button } from "@/components/ui/button";

interface JobControlsProps {
  onScrape: () => void;
  onProcess: () => void;
  schedulerRunning: boolean;
}

const JobControls = ({ onScrape, onProcess, schedulerRunning }: JobControlsProps) => {
  return (
    <div className="flex flex-wrap items-center gap-4">
      <Button onClick={onScrape}>Trigger Scrape Now</Button>
      <Button variant="outline" onClick={onProcess}>
        Process Pending Tenders
      </Button>
      <span className="text-xs text-muted">
        Scheduler: {schedulerRunning ? "Running" : "Stopped"}
      </span>
    </div>
  );
};

export default JobControls;
