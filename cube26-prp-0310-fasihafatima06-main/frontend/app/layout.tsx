import "./globals.css";
import React from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { AgentStatusBar } from "@/components/layout/AgentStatusBar";

export const metadata = {
  title: "AgentPrep - Visual Prep Compliance Agent",
  description: "AI-Powered Visual Prep Compliance Agent for E-Commerce Inbound Fulfillment",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 min-h-screen flex flex-col antialiased">
        <Header />
        <div className="flex flex-1 overflow-hidden pb-10">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
            {children}
          </main>
        </div>
        <AgentStatusBar />
      </body>
    </html>
  );
}
