import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import "./index.css";
import { ToastProviderSimple } from "@/components/ui/toaster-simple";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ToastProviderSimple>
       <BrowserRouter basename="/tender-frontend">
          <App />
        </BrowserRouter>
      </ToastProviderSimple>
    </QueryClientProvider>
  </React.StrictMode>
);
