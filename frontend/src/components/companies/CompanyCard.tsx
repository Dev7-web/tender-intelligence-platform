import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Company } from "@/types/company";

interface CompanyCardProps {
  company: Company;
  onClick?: () => void;
}

const CompanyCard = ({ company, onClick }: CompanyCardProps) => {
  return (
    <Card className="cursor-pointer transition hover:-translate-y-1 hover:shadow-soft" onClick={onClick}>
      <p className="text-sm text-muted">{company.company_id}</p>
      <h3 className="text-lg font-semibold text-text">
        {company.name || company.metadata?.company_name || "Unnamed Company"}
      </h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {(company.metadata?.domains || []).slice(0, 3).map((domain) => (
          <Badge key={domain}>{domain}</Badge>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted">Status: {company.status?.processing_status || "pending"}</p>
    </Card>
  );
};

export default CompanyCard;
