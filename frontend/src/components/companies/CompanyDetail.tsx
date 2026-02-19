import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Company } from "@/types/company";
import ProfileMetadata from "@/components/companies/ProfileMetadata";

interface CompanyDetailProps {
  company: Company;
  searchHistory: Array<Record<string, any>>;
  onSearch: () => void;
}

const CompanyDetail = ({ company, searchHistory, onSearch }: CompanyDetailProps) => {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted">{company.company_id}</p>
          <h2 className="text-3xl font-semibold">
            {company.name || company.metadata?.company_name || "Company Profile"}
          </h2>
        </div>
        <Button onClick={onSearch}>Find Matching Tenders</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Uploaded Files</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {(company.uploaded_files || []).map((file) => (
            <div key={file.file_hash} className="flex items-center justify-between">
              <span>{file.original_name}</span>
              <span className="text-xs text-muted">{file.uploaded_at}</span>
            </div>
          ))}
          {!company.uploaded_files?.length && <p className="text-sm text-muted">No files.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Extracted Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <ProfileMetadata metadata={company.metadata} />
          <div className="mt-4 flex flex-wrap gap-2">
            {(company.metadata?.domains || []).map((domain) => (
              <Badge key={domain}>{domain}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Searches</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {searchHistory.map((entry, index) => (
            <div key={index} className="flex items-center justify-between">
              <span>{entry.search_query || "Profile match"}</span>
              <span className="text-xs text-muted">{entry.searched_at}</span>
            </div>
          ))}
          {!searchHistory.length && <p className="text-sm text-muted">No searches yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
};

export default CompanyDetail;
