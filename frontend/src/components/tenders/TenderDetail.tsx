import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tender } from "@/types/tender";

interface TenderDetailProps {
  tender: Tender;
  matches?: Array<{ company_id: string; name: string; score: number; match_reasons: string[] }>;
  onReprocess: () => void;
}

const TenderDetail = ({ tender, matches, onReprocess }: TenderDetailProps) => {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted">{tender.bid_id}</p>
          <h2 className="text-3xl font-semibold">
            {tender.metadata?.title || tender.scraped_info?.items || "Tender details"}
          </h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {(tender.metadata?.domains || []).map((domain) => (
              <Badge key={domain}>{domain}</Badge>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-sm text-muted">
            {tender.gem_url && (
              <a className="underline" href={tender.gem_url} target="_blank" rel="noreferrer">
                View on GeM
              </a>
            )}
            {tender.pdf_url && (
              <a className="underline" href={tender.pdf_url} target="_blank" rel="noreferrer">
                PDF Source
              </a>
            )}
          </div>
        </div>
        <Button variant="outline" onClick={onReprocess}>
          Reprocess
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scraped Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>Department: {tender.scraped_info?.department || "-"}</p>
          <p>Items: {tender.scraped_info?.items || "-"}</p>
          <p>Quantity: {tender.scraped_info?.quantity || "-"}</p>
          <p>Bid Type: {tender.scraped_info?.bid_type || "-"}</p>
          <p>End Date: {tender.scraped_info?.end_date || "-"}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>LLM Metadata</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted">{tender.metadata?.summary || "No summary yet."}</p>
          <div className="flex flex-wrap gap-2">
            {(tender.metadata?.required_certifications || []).map((cert) => (
              <Badge key={cert}>{cert}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Matching Companies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {(matches || []).map((match) => (
              <div key={match.company_id} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold">{match.name || match.company_id}</p>
                  <p className="text-xs text-muted">{match.match_reasons?.join(" | ")}</p>
                </div>
                <Badge className="bg-primary/10 text-primary">{Math.round(match.score * 100)}%</Badge>
              </div>
            ))}
            {!matches?.length && <p className="text-sm text-muted">No matches yet.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TenderDetail;
