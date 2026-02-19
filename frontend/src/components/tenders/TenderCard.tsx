import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tender } from "@/types/tender";

interface TenderCardProps {
  tender: Tender;
  onClick?: () => void;
}

const TenderCard = ({ tender, onClick }: TenderCardProps) => {
  const status = tender.status?.llm_processed
    ? "processed"
    : tender.status?.last_error
    ? "failed"
    : "pending";

  const statusColor =
    status === "processed"
      ? "bg-success/10 text-success"
      : status === "failed"
      ? "bg-error/10 text-error"
      : "bg-warning/10 text-warning";

  return (
    <Card className="cursor-pointer transition hover:-translate-y-1 hover:shadow-soft" onClick={onClick}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted">{tender.bid_id}</p>
          <h3 className="text-lg font-semibold text-text">
            {tender.metadata?.title || tender.scraped_info?.items || "Untitled Tender"}
          </h3>
          <p className="text-sm text-muted mt-1">{tender.scraped_info?.department}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(tender.metadata?.domains || []).slice(0, 3).map((domain) => (
              <Badge key={domain}>{domain}</Badge>
            ))}
          </div>
        </div>
        <Badge className={statusColor}>{status}</Badge>
      </div>
    </Card>
  );
};

export default TenderCard;
