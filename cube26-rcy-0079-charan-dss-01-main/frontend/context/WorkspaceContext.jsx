"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../lib/api";

const WorkspaceContext = createContext();

export function WorkspaceProvider({ children }) {
  const [companies, setCompanies] = useState([
    { id: "org_demo_alpha", name: "Alpha Retail Corp" },
    { id: "org_demo_bravo", name: "Bravo Logistics Inc" },
  ]);
  const [currentCompany, setCurrentCompany] = useState("org_demo_alpha");
  const [loadingCompanies, setLoadingCompanies] = useState(false);

  useEffect(() => {
    async function loadCompanies() {
      try {
        setLoadingCompanies(true);
        const data = await api.getCompanies();
        if (data && data.length > 0) {
          setCompanies(data);
        }
      } catch (err) {
        console.error("Failed to load companies, using defaults:", err);
      } finally {
        setLoadingCompanies(false);
      }
    }
    loadCompanies();
  }, []);

  const switchCompany = (companyId) => {
    setCurrentCompany(companyId);
  };

  const currentCompanyName =
    companies.find((c) => c.id === currentCompany)?.name || currentCompany;

  return (
    <WorkspaceContext.Provider
      value={{
        companies,
        currentCompany,
        currentCompanyName,
        switchCompany,
        setCompanies,
        loadingCompanies,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
