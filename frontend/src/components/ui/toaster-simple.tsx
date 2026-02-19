import { createContext, PropsWithChildren, useCallback, useContext, useMemo, useState } from "react";

type ToastType = "success" | "error" | "info";

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  pushToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export const ToastProviderSimple = ({ children }: PropsWithChildren) => {
  const [items, setItems] = useState<ToastItem[]>([]);

  const pushToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setItems((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, 3200);
  }, []);

  const value = useMemo(() => ({ pushToast }), [pushToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-[90] flex w-[320px] flex-col gap-2">
        {items.map((item) => (
          <div
            key={item.id}
            className={[
              "rounded-lg border px-4 py-3 text-sm shadow-lg",
              item.type === "success" && "border-green-200 bg-green-50 text-green-800",
              item.type === "error" && "border-red-200 bg-red-50 text-red-700",
              item.type === "info" && "border-blue-200 bg-white text-slate-700",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToastSimple = () => {
  const value = useContext(ToastContext);
  if (!value) {
    throw new Error("useToastSimple must be used inside ToastProviderSimple");
  }
  return value;
};
