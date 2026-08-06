import { Sidebar } from "@/components/Sidebar";
import { MobileNav } from "@/components/MobileNav";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="app-shell">
      <Sidebar />
      <MobileNav />
      <main className="canvas">
        <div className="canvas-inner">{children}</div>
      </main>
    </div>
  );
}
