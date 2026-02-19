import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tender } from "@/types/tender";

interface TenderListProps {
  tenders: Tender[];
  onSelect: (id: string) => void;
}

const TenderList = ({ tenders, onSelect }: TenderListProps) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Bid ID</TableHead>
          <TableHead>Title</TableHead>
          <TableHead>Department</TableHead>
          <TableHead>Domains</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>End Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tenders.map((tender) => {
          const status = tender.status?.llm_processed
            ? "processed"
            : tender.status?.last_error
            ? "failed"
            : "pending";
          return (
            <TableRow
              key={tender.id || tender._id || tender.bid_id}
              onClick={() => onSelect(tender.id || tender._id || "")}
              className="cursor-pointer">
              <TableCell>{tender.bid_id}</TableCell>
              <TableCell>{tender.metadata?.title || tender.scraped_info?.items}</TableCell>
              <TableCell>{tender.scraped_info?.department}</TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-2">
                  {(tender.metadata?.domains || []).slice(0, 2).map((domain) => (
                    <Badge key={domain}>{domain}</Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                <Badge
                  className={
                    status === "processed"
                      ? "bg-success/10 text-success"
                      : status === "failed"
                      ? "bg-error/10 text-error"
                      : "bg-warning/10 text-warning"
                  }
                >
                  {status}
                </Badge>
              </TableCell>
              <TableCell>{tender.scraped_info?.end_date || "-"}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

export default TenderList;
