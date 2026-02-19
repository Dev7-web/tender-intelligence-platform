import CompanyCard from "@/components/companies/CompanyCard";
import { Company } from "@/types/company";

interface CompanyListProps {
  companies: Company[];
  onSelect: (id: string) => void;
}

const CompanyList = ({ companies, onSelect }: CompanyListProps) => {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {companies.map((company) => (
        <CompanyCard
          key={company.company_id}
          company={company}
          onClick={() => onSelect(company.company_id)}
        />
      ))}
    </div>
  );
};

export default CompanyList;
