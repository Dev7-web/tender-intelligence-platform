import { useNavigate } from "react-router-dom";

import CompanyList from "@/components/companies/CompanyList";
import CompanyUpload from "@/components/companies/CompanyUpload";
import { useCompanies } from "@/hooks/useCompanies";

const Companies = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useCompanies({ skip: 0, limit: 50 });

  return (
    <div className="space-y-6 animate-rise">
      <CompanyUpload onUploadComplete={(company) => navigate(`/companies/${company.company_id}`)} />
      {isLoading && <p className="text-sm text-muted">Loading companies...</p>}
      {data && <CompanyList companies={data.items} onSelect={(id) => navigate(`/companies/${id}`)} />}
    </div>
  );
};

export default Companies;
