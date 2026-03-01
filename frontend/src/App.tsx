import { Navigate, Route, Routes } from "react-router-dom";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import AdminProtectedRoute from "@/components/layout/AdminProtectedRoute";
import AdminLayout from "@/components/layout/AdminLayout";
import AuthPage from "@/pages/AuthPage";
import AdminLoginPage from "@/pages/AdminLoginPage";
import DashboardPage from "@/pages/DashboardPage";
import HelpPage from "@/pages/HelpPage";
import LoadingPage from "@/pages/LoadingPage";
import MyListPage from "@/pages/MyListPage";
import OrganizationPage from "@/pages/OrganizationPage";
import TenderDetailsPage from "@/pages/TenderDetailsPage";
import TendersPage from "@/pages/TendersPage";
import CompanyDetails from "@/pages/onboarding/CompanyDetails";
import SelectInterests from "@/pages/onboarding/SelectInterests";
import UploadDocuments from "@/pages/onboarding/UploadDocuments";
import AdminDashboard from "@/pages/Dashboard";
import ManageUsers from "@/pages/ManageUsers";

const App = () => {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/onboarding/company" element={<CompanyDetails />} />
      <Route path="/onboarding/documents" element={<UploadDocuments />} />
      <Route path="/onboarding/interests" element={<SelectInterests />} />
      <Route path="/loading/company-processing" element={<LoadingPage />} />

      <Route element={<ProtectedRoute />}>
        <Route
          path="/dashboard"
          element={
            <AppShell>
              <DashboardPage />
            </AppShell>
          }
        />
        <Route
          path="/tenders"
          element={
            <AppShell>
              <TendersPage />
            </AppShell>
          }
        />
        <Route
          path="/tenders/:id"
          element={
            <AppShell>
              <TenderDetailsPage />
            </AppShell>
          }
        />
        <Route
          path="/my-list"
          element={
            <AppShell>
              <MyListPage />
            </AppShell>
          }
        />
        <Route
          path="/organization"
          element={
            <AppShell>
              <OrganizationPage />
            </AppShell>
          }
        />
        <Route
          path="/help"
          element={
            <AppShell>
              <HelpPage />
            </AppShell>
          }
        />
      </Route>

      {/* Admin routes */}
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route element={<AdminProtectedRoute />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<ManageUsers />} />
          <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/auth" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
