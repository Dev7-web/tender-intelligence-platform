import { PropsWithChildren } from "react";

import Header from "./Header";
import Sidebar from "./Sidebar";

const Layout = ({ children }: PropsWithChildren) => {
  return (
    <div className="min-h-screen flex bg-transparent">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 px-6 pb-10 pt-6">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
