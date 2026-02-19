import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Settings = () => {
  return (
    <div className="space-y-6 animate-rise">
      <Card>
        <CardHeader>
          <CardTitle>Scraper Settings</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted">
          Update `.env` to change scrape limits and intervals, then restart the API.
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted">
          Gemini API key is stored in `.env` as `GEMINI_API_KEY`.
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
