import "./globals.css";
import { WorkspaceProvider } from "../context/WorkspaceContext";
import AppShell from "../components/AppShell";

export const metadata = {
  title: "RCY RECOVERY — Evidence Operations Center",
  description: "AI-Powered Evidence-to-Recovery Platform for Defensible E-Commerce Reimbursement Claims",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#080c15] text-slate-100 min-h-screen antialiased">
        <WorkspaceProvider>
          <AppShell>
            {children}
          </AppShell>
        </WorkspaceProvider>
      </body>
    </html>
  );
}
