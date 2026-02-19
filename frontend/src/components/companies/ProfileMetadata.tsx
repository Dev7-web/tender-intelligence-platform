import { Badge } from "@/components/ui/badge";
import { CompanyMetadata } from "@/types/company";

interface ProfileMetadataProps {
  metadata?: CompanyMetadata;
}

const ProfileMetadata = ({ metadata }: ProfileMetadataProps) => {
  if (!metadata) {
    return <p className="text-sm text-muted">No metadata available.</p>;
  }

  return (
    <div className="space-y-4 text-sm">
      <p className="text-muted">{metadata.summary}</p>
      <div className="flex flex-wrap gap-2">
        {(metadata.certifications || []).map((cert) => (
          <Badge key={cert}>{cert}</Badge>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {(metadata.technologies || []).map((tech) => (
          <Badge key={tech}>{tech}</Badge>
        ))}
      </div>
    </div>
  );
};

export default ProfileMetadata;
