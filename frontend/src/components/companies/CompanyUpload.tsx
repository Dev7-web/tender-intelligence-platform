import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUploadCompany } from "@/hooks/useCompanies";
import { Company } from "@/types/company";

interface CompanyUploadProps {
  onUploadComplete: (company: Company) => void;
}

const CompanyUpload = ({ onUploadComplete }: CompanyUploadProps) => {
  const [files, setFiles] = useState<File[]>([]);
  const [companyName, setCompanyName] = useState("");
  const { mutateAsync, isPending } = useUploadCompany();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
  });

  const handleUpload = async () => {
    if (!files.length) {
      return;
    }
    const response = await mutateAsync({ files, companyName: companyName || undefined });
    onUploadComplete(response);
    setFiles([]);
    setCompanyName("");
  };

  return (
    <div className="rounded-2xl border border-dashed border-border bg-white p-6 shadow-card">
      <div
        {...getRootProps()}
        className={`rounded-xl border border-dashed px-6 py-10 text-center transition ${
          isDragActive ? "border-primary bg-primary/5" : "border-border"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm font-semibold text-text">
          Drag and drop company PDFs here
        </p>
        <p className="text-xs text-muted">PDF only, up to 50MB each.</p>
      </div>
      <div className="mt-4">
        <label className="text-xs uppercase text-muted">Company Name (optional)</label>
        <Input value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
      </div>
      {files.length > 0 && (
        <ul className="mt-4 text-sm text-muted">
          {files.map((file) => (
            <li key={file.name}>{file.name}</li>
          ))}
        </ul>
      )}
      <Button className="mt-4" onClick={handleUpload} disabled={isPending}>
        {isPending ? "Uploading..." : "Upload Profile"}
      </Button>
    </div>
  );
};

export default CompanyUpload;
