import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
  type FormEvent,
} from "react";
import { createClient } from "@supabase/supabase-js";
import { setTokenProvider, apiUrl } from "./api";

export function SupabaseGate({
  url,
  publicKey,
  children,
}: {
  url: string;
  publicKey: string;
  children: ReactNode;
}) {
  const client = useMemo(
    () =>
      createClient(url, publicKey, {
        auth: {
          storage: sessionStorage,
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: false,
        },
      }),
    [url, publicKey],
  );
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  useEffect(() => {
    let active = true;
    const subscription = client.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT" && active) {
        setReady(false);
        setTokenProvider(null);
      }
    }).data.subscription;
    client.auth
      .getSession()
      .then(async ({ data, error }) => {
        if (error) throw error;
        if (!data.session) return;
        const response = await fetch(apiUrl("/api/v1/me"), {
          headers: { Authorization: `Bearer ${data.session.access_token}` },
        });
        if (!response.ok)
          throw new Error(
            "Your account needs an assigned workspace role. Contact the workspace owner.",
          );
        setTokenProvider(async () => {
          const { data, error } = await client.auth.getSession();
          if (error || !data.session) throw new Error("Please sign in again.");
          return data.session.access_token;
        });
        if (active) setReady(true);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
      subscription.unsubscribe();
      setTokenProvider(null);
    };
  }, [client]);

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { data, error } = await client.auth.signInWithPassword({
        email,
        password,
      });
      setPassword("");
      if (error || !data.session)
        throw new Error("Unable to sign in. Check your email and password.");
      const response = await fetch(apiUrl("/api/v1/me"), {
        headers: { Authorization: `Bearer ${data.session.access_token}` },
      });
      if (!response.ok)
        throw new Error(
          "Your account needs an assigned workspace role. Contact the workspace owner.",
        );
      location.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  if (ready)
    return (
      <>
        <div
          className="panel"
          style={{
            display: "flex",
            justifyContent: "flex-end",
            padding: "8px 24px",
          }}
        >
          <button
            className="secondary"
            onClick={async () => {
              await client.auth.signOut({ scope: "local" });
              location.reload();
            }}
          >
            Sign out
          </button>
        </div>
        {children}
      </>
    );
  return (
    <div className="sign-in">
      <form className="panel" onSubmit={signIn}>
        <div className="eyebrow">PACK MANAGER</div>
        <h1>Your packing workspace.</h1>
        <p>Sign in with the account provided by your workspace owner.</p>
        <label>
          Email
          <input
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <button className="primary" disabled={busy}>
          {busy ? "Please wait…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
