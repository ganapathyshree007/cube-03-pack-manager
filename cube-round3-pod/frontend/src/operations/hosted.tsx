import { useEffect, useState } from "react";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { OperationsApi, type Session } from "./api";

type Runtime = {
  mode: string;
  loading?: boolean;
  supabase_url?: string;
  publishable_key?: string;
};
let client: SupabaseClient | undefined;
export async function hostedSignOut() {
  await client?.auth.signOut({ scope: "local" });
}
export function useRuntime() {
  const [runtime, setRuntime] = useState<Runtime>({
    mode: "local",
    loading: true,
  });
  useEffect(() => {
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 10000);
    fetch("/operations-config", { signal: abort.signal, credentials: "omit" })
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then((value) =>
        setRuntime(value.mode === "hosted" ? value : { mode: ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname) ? "local" : "hosted" }),
      )
      .catch(() => setRuntime({ mode: ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname) ? "local" : "hosted" }))
      .finally(() => clearTimeout(timeout));
    return () => {
      abort.abort();
      clearTimeout(timeout);
    };
  }, []);
  return runtime;
}
export function HostedLogin({
  config,
  onConnect,
}: {
  config: Runtime;
  onConnect: (api: OperationsApi, session: Session) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function connect(token: string) {
    const api = new OperationsApi(token);
    api.tokenProvider = async () => {
      const result = await client!.auth.getSession();
      if (result.error || !result.data.session)
        throw new Error("Sign-in expired");
      return result.data.session.access_token;
    };
    const session = await api.get<Session>("/v1/session");
    onConnect(api, session);
  }
  useEffect(() => {
    if (!config.supabase_url || !config.publishable_key) {
      setError("Workspace sign-in is not configured.");
      return;
    }
    client ||= createClient(config.supabase_url, config.publishable_key, {
      auth: {
        storage: sessionStorage,
        storageKey: "cube-hosted-session",
        detectSessionInUrl: false,
      },
    });
    const { data } = client.auth.onAuthStateChange((_event, session) => {
      if (session)
        setTimeout(
          () =>
            void connect(session.access_token).catch(() =>
              setError(
                "Your account needs an assigned workspace role, or sign-in verification is unavailable.",
              ),
            ),
          0,
        );
    });
    return () => data.subscription.unsubscribe();
  }, []);
  return (
    <main className="login-shell">
      <header className="login-brand">
        <div className="wordmark">CUBE <span>OPERATIONS</span></div>
        <small>Workspace access</small>
      </header>
      <section className="login-card">
        <h1>Sign in to CUBE Operations</h1>
        <p>
          Use your assigned account. Development tokens are not accepted here.
        </p>
        {error && <p role="alert">{error}</p>}
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (busy || !client) return;
            setBusy(true);
            setError("");
            try {
              const { error: failure } = await client.auth.signInWithPassword({
                email,
                password,
              });
              setPassword("");
              if (failure)
                setError("Sign-in failed. Check your account details.");
            } catch {
              setError("Sign-in is temporarily unavailable.");
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Email
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="button" aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>
            {showPassword ? "Hide password" : "Show password"}
          </button>
          <button className="primary" disabled={busy || !config.supabase_url || !config.publishable_key}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="hint">
          Session credentials stay in this browser tab. Access is checked by the
          backend.
        </p>
      </section>
    </main>
  );
}
