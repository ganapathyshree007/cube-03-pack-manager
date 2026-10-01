import { useEffect, useState, type ReactNode } from "react";
import { PublicClientApplication } from "@azure/msal-browser";
import { setTokenProvider } from "./api";
import { SupabaseGate } from "./supabase-auth";

export function AuthGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [demo, setDemo] = useState(false);
  const [supabaseConfig, setSupabaseConfig] = useState<{
    url: string;
    key: string;
  } | null>(null);
  const [login, setLogin] = useState<(() => Promise<void>) | null>(null);
  useEffect(() => {
    let active = true;
    (async () => {
      const cfg = await fetch("/api/v1/config").then((r) => r.json());
      if (active) setDemo(cfg.demo_enabled);
      if (cfg.auth_mode === "supabase") {
        if (!cfg.supabase_url || !cfg.supabase_publishable_key)
          throw new Error("Hosted sign-in is not configured.");
        if (active)
          setSupabaseConfig({
            url: cfg.supabase_url,
            key: cfg.supabase_publishable_key,
          });
        return;
      }
      if (cfg.demo_enabled) {
        const current = await fetch("/api/v1/me");
        if (current.ok) {
          if (active) setReady(true);
          return;
        }
      }
      if (cfg.auth_mode === "local") {
        if (active) setReady(true);
        return;
      }
      if (!cfg.entra_client_id || !cfg.entra_tenant_id || !cfg.entra_scope)
        throw new Error("Hosted sign-in is not configured.");
      const msal = new PublicClientApplication({
        auth: {
          clientId: cfg.entra_client_id,
          authority: `https://login.microsoftonline.com/${cfg.entra_tenant_id}`,
          redirectUri: location.origin + "/workspace",
        },
        cache: { cacheLocation: "sessionStorage" },
      });
      await msal.initialize();
      await msal.handleRedirectPromise();
      const account = msal.getAllAccounts()[0];
      if (!account) {
        if (active)
          setLogin(
            () => () => msal.loginRedirect({ scopes: [cfg.entra_scope] }),
          );
        return;
      }
      setTokenProvider(async () => {
        try {
          return (
            await msal.acquireTokenSilent({
              account,
              scopes: [cfg.entra_scope],
            })
          ).accessToken;
        } catch {
          await msal.acquireTokenRedirect({
            account,
            scopes: [cfg.entra_scope],
          });
          throw new Error("Please sign in again.");
        }
      });
      if (active) setReady(true);
    })().catch((e) => {
      if (active) setError(e.message);
    });
    return () => {
      active = false;
    };
  }, []);
  if (supabaseConfig)
    return (
      <SupabaseGate url={supabaseConfig.url} publicKey={supabaseConfig.key}>
        {children}
      </SupabaseGate>
    );
  if (ready) return children;
  return (
    <div className="sign-in">
      <div className="panel">
        <div className="eyebrow">PACK MANAGER</div>
        <h1>
          Order verification
          <br />
          before sealing.
        </h1>
        <p>{error || "Sign in to your packing workspace."}</p>
        {login && (
          <button className="primary" onClick={() => login()}>
            Sign in with Microsoft
          </button>
        )}
        {demo && (
          <button
            className="secondary full"
            onClick={async () => {
              const r = await fetch("/api/v1/demo-session", { method: "POST" });
              if (r.ok) {
                localStorage.removeItem("pack-attempt");
                location.reload();
              } else {
                setError((await r.json()).message);
              }
            }}
          >
            Try an isolated demo session
          </button>
        )}
        {demo && (
          <p className="micro">
            Your session has its own orders, catalogue and images. Up to two
            inspections and ten images; uploads expire after 24 hours.
            Supervisor overrides require a signed-in supervisor.
          </p>
        )}
      </div>
    </div>
  );
}
