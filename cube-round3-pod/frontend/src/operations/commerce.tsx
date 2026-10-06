import React, { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { OperationsApi, Session } from "./api";

type Product = {
  fixture?: boolean;
  id: string;
  sku: string;
  name: string;
  description: string;
  category: string;
  price_minor: number;
  available: number;
  return_window_days: number;
};
type Order = {
  fixture?: boolean;
  id: string;
  status: string;
  created_at: string;
  lines: {
    product_id: string;
    name: string;
    quantity: number;
    price_minor: number;
  }[];
  total_minor: number;
  next_step: string;
};
const money = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(
    v / 100,
  );
function Problem({ error }: { error: unknown }) {
  return error ? (
    <p className="notice error" role="alert">
      {error instanceof Error
        ? error.message
        : "Request unavailable. Please refresh."}
    </p>
  ) : null;
}
export function CustomerPortal({
  api,
  session,
  onDisconnect,
}: {
  api: OperationsApi;
  session: Session;
  onDisconnect: () => void;
}) {
  const [cart, setCart] = useState<Record<string, number>>({});
  const [error, setError] = useState<unknown>();
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const q = useQuery({
    queryKey: ["customer"],
    queryFn: async () => ({
      products: await api.get<Product[]>("/v1/commerce/catalogue"),
      orders: await api.get<Order[]>("/v1/commerce/orders"),
      returns: await api.get<
        {
          id: string;
          status: string;
          quantity: number;
          next_step: string;
          disposition: string | null;
        }[]
      >("/v1/commerce/returns"),
    }),
    refetchInterval: 15000,
  });
  async function act(path: string, body: unknown, success: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(undefined);
    try {
      await api.post(path, body);
      setNotice(success);
      setCart({});
      await q.refetch();
    } catch (e) {
      setError(e);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  const total = (q.data?.products || []).reduce(
    (n, p) => n + (cart[p.id] || 0) * p.price_minor,
    0,
  );
  return (
    <main className="customer-shell">
      <header className="section-head">
        <div className="wordmark">
          CUBE <span>ORDER REQUESTS</span>
        </div>
        <button onClick={onDisconnect}>Sign out</button>
      </header>
      <h1>Your products and orders</h1>
      <p>
        Signed in as {session.operator}. This checkout sends an order request.
        No payment or card details are collected.
      </p>
      <Problem error={error || q.error} />
      <p role="status">
        {notice}
        {q.isLoading ? "Loading your catalogue and orders…" : ""}
      </p>
      <section aria-label="Products">
        <h2>Available products</h2>
        {q.data?.products.length === 0 && (
          <p>No active products are available yet.</p>
        )}
        <div className="commerce-products">
          {q.data?.products.map((p) => (
            <article className="card" key={p.id}>
              <small>
                {p.category} · {p.sku}
              </small>
              <h3>{p.name}</h3>
              <p>{p.description}</p>
              <strong>{money(p.price_minor)}</strong>
              <p>{p.available} available</p>
              <label>
                Quantity for {p.name}
                <input
                  type="number"
                  min="0"
                  max={Math.min(100, p.available)}
                  step="1"
                  value={cart[p.id] || 0}
                  disabled={!p.available || busy}
                  onChange={(e) =>
                    setCart({ ...cart, [p.id]: Number(e.target.value) })
                  }
                />
              </label>
              <small>
                Return requests:{" "}
                {p.return_window_days
                  ? `within ${p.return_window_days} days of recorded delivery`
                  : "not enabled for this product"}
                .
              </small>
            </article>
          ))}
        </div>
        <div className="section-head">
          <strong>Order total {money(total)}</strong>
          <button
            className="primary"
            disabled={
              busy ||
              !!q.error ||
              !total ||
              Object.values(cart).some((x) => !Number.isInteger(x) || x < 0)
            }
            onClick={() =>
              void act(
                "/v1/commerce/orders",
                {
                  lines: Object.entries(cart)
                    .filter(([, q]) => q > 0)
                    .map(([product_id, quantity]) => ({
                      product_id,
                      quantity,
                    })),
                  quoted_total_minor: total,
                },
                "Order request saved. Operations will confirm the next step.",
              )
            }
          >
            {busy ? "Saving…" : "Place order request"}
          </button>
        </div>
      </section>
      <section>
        <h2>Your orders</h2>
        {q.data?.orders.length === 0 && <p>You have no orders yet.</p>}
        {q.data?.orders.map((o) => (
          <article className="card" key={o.id}>
            <div className="section-head">
              <h3>Order {o.id.slice(0, 8)}</h3>
              {o.fixture && <span className="fixture-note">Test order</span>}
              <span className={"badge " + o.status}>
                {o.status.replaceAll("_", " ")}
              </span>
            </div>
            <p>{o.next_step}</p>
            <ul>
              {o.lines.map((l) => (
                <li key={l.product_id}>
                  {l.name} × {l.quantity} · {money(l.price_minor * l.quantity)}
                </li>
              ))}
            </ul>
            <strong>{money(o.total_minor)}</strong>
            {o.status === "delivered" && (
              <details>
                <summary>Request a return</summary>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const f = new FormData(e.currentTarget);
                    void act(
                      `/v1/commerce/orders/${o.id}/returns`,
                      {
                        product_id: f.get("product"),
                        quantity: Number(f.get("quantity")),
                        reason: f.get("reason"),
                        note: f.get("note"),
                      },
                      "Return request saved. Wait for confirmed return instructions.",
                    );
                  }}
                >
                  <label>
                    Purchased item
                    <select name="product">
                      {o.lines.map((l) => (
                        <option value={l.product_id} key={l.product_id}>
                          {l.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Return quantity
                    <input
                      name="quantity"
                      type="number"
                      min="1"
                      max="100"
                      required
                      defaultValue="1"
                    />
                  </label>
                  <label>
                    Reason
                    <select name="reason">
                      <option value="damaged">Damaged</option>
                      <option value="wrong_item">Wrong item</option>
                      <option value="not_needed">No longer needed</option>
                      <option value="other">Other</option>
                    </select>
                  </label>
                  <label>
                    Details
                    <textarea
                      name="note"
                      minLength={5}
                      maxLength={1000}
                      required
                    />
                  </label>
                  <button disabled={busy}>Submit return request</button>
                </form>
              </details>
            )}
          </article>
        ))}
      </section>
      <section>
        <h2>Your returns</h2>
        {q.data?.returns.length === 0 && <p>No return requests.</p>}
        {q.data?.returns.map((r) => (
          <article className="card" key={r.id}>
            <h3>Return {r.id.slice(0, 8)}</h3>
            <p>
              {r.status} · {r.quantity} item(s)
              {r.disposition ? ` · Recorded disposition: ${r.disposition}` : ""}
            </p>
            <p>{r.next_step}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

export function CommerceAdmin({
  api,
  onOpen,
}: {
  api: OperationsApi;
  onOpen: (id: string) => void;
}) {
  const [error, setError] = useState<unknown>();
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const [notice, setNotice] = useState("");
  const q = useQuery({
    queryKey: ["commerce-admin"],
    queryFn: async () => ({
      products:
        await api.get<
          { id: string; version: number; data: { name: string; sku: string } }[]
        >("/v1/catalogue"),
      policies: await api.get<{ id: string }[]>("/v1/commerce/admin/policies"),
      orders: await api.get<
        {
          id: string;
          state: string;
          workflow_id: string;
          version: number;
          data: { total_minor: number };
        }[]
      >("/v1/commerce/admin/orders"),
    }),
  });
  async function submit(path: string, body: unknown) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(undefined);
    try {
      await api.post(path, body);
      setNotice("Saved with an audit record.");
      await q.refetch();
    } catch (e) {
      setError(e);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  const productOptions = q.data?.products.map((p) => (
    <option key={p.id} value={p.id}>
      {p.data.name} · {p.data.sku}
    </option>
  ));
  return (
    <section>
      <h1>Commerce setup</h1>
      <p>
        Product rules are operator-configured business policies, not organiser
        exemptions. An unverified Pod assignment holds fulfillment.
      </p>
      <Problem error={error || q.error} />
      <p role="status">{busy ? "Saving…" : notice}</p>
      <details className="card">
        <summary>Publish a policy version</summary>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            void submit("/v1/commerce/admin/policies", {
              version: f.get("version"),
              source_reference: f.get("source"),
              rules: [
                {
                  id: f.get("rule"),
                  categories: [f.get("category")],
                  routes: [f.get("route")],
                  required_checks: {
                    [f.get("route") === "fba" ? "prep" : "pack"]: String(
                      f.get("checks") || "",
                    )
                      .split(",")
                      .map((x) => x.trim())
                      .filter(Boolean),
                  },
                },
              ],
            });
          }}
        >
          <label>
            Version
            <input name="version" pattern="[A-Za-z0-9._-]+" required />
          </label>
          <label>
            Rule identifier
            <input name="rule" required />
          </label>
          <label>
            Product category
            <input name="category" required />
          </label>
          <label>
            Fulfillment route
            <select name="route">
              <option value="merchant">Merchant → Pack</option>
              <option value="3pl">3PL → Pack</option>
              <option value="fba">FBA → Prep</option>
            </select>
          </label>
          <label>
            Additional required check keys (comma-separated)
            <input name="checks" />
          </label>
          <label>
            Policy source or approval reference
            <input name="source" minLength={5} required />
          </label>
          <button disabled={busy}>Publish immutable version</button>
        </form>
      </details>
      <details className="card">
        <summary>Configure a catalogue product</summary>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            const product = q.data?.products.find(
              (p) => p.id === f.get("product"),
            );
            if (!product) return;
            void submit(`/v1/commerce/admin/products/${product.id}`, {
              fixture: f.get("fixture") === "on",
              expected_version: product.version,
              active: f.get("active") === "on",
              category: f.get("category"),
              price_minor: Math.round(Number(f.get("price")) * 100),
              route: f.get("route"),
              policy_version: f.get("policy"),
              return_window_days: Number(f.get("days")),
            });
          }}
        >
          <label>
            Product
            <select name="product" required>
              {productOptions}
            </select>
          </label>
          <label>
            Category
            <input name="category" required />
          </label>
          <label>
            Price (INR)
            <input name="price" type="number" min="0.01" step="0.01" required />
          </label>
          <label>
            Route
            <select name="route">
              <option value="merchant">Merchant</option>
              <option value="3pl">3PL</option>
              <option value="fba">FBA</option>
            </select>
          </label>
          <label>
            Policy version
            <select name="policy" required>
              {q.data?.policies.map((p) => (
                <option key={p.id}>{p.id}</option>
              ))}
            </select>
          </label>
          <label>
            Return window after delivery (days; 0 disables)
            <input
              name="days"
              type="number"
              min="0"
              max="365"
              required
              defaultValue="0"
            />
          </label>
          <label className="check-line">
            <input name="active" type="checkbox" />
            Active in customer catalogue
          </label>
          <label className="check-line">
            <input name="fixture" type="checkbox" />
            Synthetic software test product
          </label>
          <button disabled={busy}>Save product configuration</button>
        </form>
      </details>
      <details className="card">
        <summary>Record an actual inventory receipt</summary>
        <p>
          This is an attributed receiving record. Do not use checkout as a
          receiving event.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            void submit(
              `/v1/commerce/admin/inventory/${f.get("product")}/receipts`,
              {
                quantity: Number(f.get("quantity")),
                source_reference: f.get("source"),
                note: f.get("note"),
              },
            );
          }}
        >
          <label>
            Received product<select name="product">{productOptions}</select>
          </label>
          <label>
            Received quantity
            <input
              name="quantity"
              type="number"
              min="1"
              max="100000"
              required
            />
          </label>
          <label>
            Receiving document/event reference
            <input name="source" minLength={5} required />
          </label>
          <label>
            Receipt details
            <textarea name="note" minLength={10} required />
          </label>
          <button disabled={busy}>Record receipt</button>
        </form>
      </details>
      <h2>Customer order requests</h2>
      {q.isLoading && <p role="status">Loading orders…</p>}
      {q.data?.orders.length === 0 && <p>No customer order requests.</p>}
      {q.data?.orders.map((o) => (
        <article className="card" key={o.id}>
          <h3>Order {o.id.slice(0, 8)}</h3>
          <p>
            {o.state.replaceAll("_", " ")} · {money(o.data.total_minor)} · No
            payment collected
          </p>
          <button onClick={() => onOpen(o.workflow_id)}>
            Open fulfillment workflow
          </button>
          {o.state !== "delivered" && (
            <details>
              <summary>Confirm actual delivery</summary>
              <p>
                Requires completed, approved fulfillment evidence. This records
                a delivery event, not payment.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  void submit(`/v1/commerce/admin/orders/${o.id}/delivered`, {
                    expected_version: o.version,
                    source_reference: f.get("source"),
                  });
                }}
              >
                <label>
                  Delivery evidence reference
                  <input name="source" minLength={5} required />
                </label>
                <button disabled={busy}>Confirm delivery</button>
              </form>
            </details>
          )}
        </article>
      ))}
    </section>
  );
}

type Analytics = {
  technical_failures: number;
  verified_discrepancies: number;
  total_orders: number;
  total_returns: number;
  workflow_counts: Record<string, number>;
  run_counts: Record<string, number>;
  by_stage: Record<string, Record<string, number>>;
  return_dispositions: Record<string, number>;
  oldest_wait_seconds: number | null;
  processing_time_by_stage: Record<
    string,
    { sample_count: number; mean_seconds: number; max_seconds: number }
  >;
  definitions: Record<string, string>;
};
export function AnalyticsPanel({ api }: { api: OperationsApi }) {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const params = new URLSearchParams(
    Object.entries(filters).filter(([, v]) => v),
  );
  const q = useQuery({
    queryKey: ["analytics", params.toString()],
    queryFn: () => api.get<Analytics>("/v1/commerce/admin/analytics?" + params),
    refetchInterval: 15000,
  });
  return (
    <section>
      <h1>Operations analytics</h1>
      <p>
        Calculated from saved customer orders and their linked workflows. No
        example totals.
      </p>
      <label className="check-line">
        <input
          type="checkbox"
          onChange={(e) =>
            setFilters({
              ...filters,
              include_fixtures: e.target.checked ? "true" : "",
            })
          }
        />
        Include labelled test orders
      </label>
      <div className="filters">
        {["start", "end"].map((key) => (
          <label key={key}>
            {key === "start" ? "From date (UTC)" : "Before date (UTC)"}
            <input
              type="date"
              onChange={(e) =>
                setFilters({
                  ...filters,
                  [key]: e.target.value ? e.target.value + "T00:00:00Z" : "",
                })
              }
            />
          </label>
        ))}
        {["category", "product_id", "route", "status", "stage"].map((key) => (
          <label key={key}>
            {key.replaceAll("_", " ")}
            <input
              value={filters[key] || ""}
              onChange={(e) =>
                setFilters({ ...filters, [key]: e.target.value })
              }
            />
          </label>
        ))}
      </div>
      <Problem error={q.error} />
      {q.isLoading ? (
        <p role="status">Calculating from saved records…</p>
      ) : (
        q.data && (
          <>
            <div className="commerce-products">
              {Object.entries({
                Orders: q.data.total_orders,
                Returns: q.data.total_returns,
                "Technical failures": q.data.technical_failures,
                "Verified discrepancies": q.data.verified_discrepancies,
                ...q.data.workflow_counts,
              }).map(([name, value]) => (
                <article className="card" key={name}>
                  <h2>{value}</h2>
                  <p>{name.replaceAll("_", " ")}</p>
                </article>
              ))}
            </div>
            {q.data.total_orders === 0 && <p>No orders match these filters.</p>}
            <h2>Stage volume and queues</h2>
            {Object.entries(q.data.by_stage).map(([stage, states]) => (
              <article className="card" key={stage}>
                <h3>{stage}</h3>
                {Object.entries(states).map(([state, n]) => (
                  <p key={state}>
                    {state.replaceAll("_", " ")}: {n}
                  </p>
                ))}
              </article>
            ))}
            <p>
              Oldest waiting run:{" "}
              {q.data.oldest_wait_seconds === null
                ? "No waiting runs"
                : Math.floor(q.data.oldest_wait_seconds / 60) + " minutes"}
            </p>
            <h2>Measured worker time</h2>
            {Object.entries(q.data.processing_time_by_stage).length === 0 ? (
              <p>No measured stage durations yet.</p>
            ) : (
              Object.entries(q.data.processing_time_by_stage).map(
                ([stage, t]) => (
                  <p key={stage}>
                    {stage}: {t.mean_seconds.toFixed(2)} s mean;{" "}
                    {t.sample_count} measured runs
                  </p>
                ),
              )
            )}
            <h2>Recorded return dispositions</h2>
            {Object.entries(q.data.return_dispositions).map(([state, n]) => (
              <p key={state}>
                {state}: {n}
              </p>
            ))}
            <p>
              Damaged disposition: unavailable in the current evidence contract.
              A customer's reason is not an inspection finding.
            </p>
            <details>
              <summary>Metric definitions</summary>
              {Object.entries(q.data.definitions).map(([key, text]) => (
                <p key={key}>
                  <strong>{key}</strong>: {text}
                </p>
              ))}
            </details>
          </>
        )
      )}
    </section>
  );
}
