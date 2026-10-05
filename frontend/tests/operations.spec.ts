import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("hosted auth fixture: development tokens unavailable and invalid sign-in stays signed out", async ({
  page,
}) => {
  await page.route("**/operations-config", (route) =>
    route.fulfill({
      json: {
        mode: "hosted",
        supabase_url: "https://fixture.supabase.co",
        publishable_key: "public-fixture",
      },
    }),
  );
  await page.route("https://fixture.supabase.co/**", (route) =>
    route.fulfill({
      status: 400,
      json: {
        error: "invalid_grant",
        error_description: "Invalid credentials",
      },
    }),
  );
  await page.goto("/operations.html");
  await expect(
    page.getByRole("heading", { name: "Sign in to your workspace" }),
  ).toBeVisible();
  await expect(page.getByLabel("Development token")).toHaveCount(0);
  await page.getByLabel("Email", { exact: true }).fill("fixture@example.test");
  await page
    .getByLabel("Password", { exact: true })
    .fill("test-only-not-a-real-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Sign-in failed");
  await expect(
    page.getByRole("heading", { name: "A clearer view of every unit." }),
  ).toHaveCount(0);
});
test.use({
  baseURL: process.env.OPERATIONS_TEST_BASE_URL || "http://127.0.0.1:5173",
  trace: "off",
  timezoneId: "Asia/Kolkata",
});

test("real local backend: persisted workflow, private upload, human review, refresh and mobile", async ({
  page,
  request,
}) => {
  const externalRequests: string[] = [];
  if (process.env.OPERATIONS_TEST_BASE_URL) {
    await page.context().route("**/*", (route) => {
      const hostname = new URL(route.request().url()).hostname;
      if (!["127.0.0.1", "localhost"].includes(hostname)) {
        externalRequests.push(hostname);
        return route.abort();
      }
      return route.continue();
    });
  }
  await page.goto("/operations.html");
  await page.getByLabel("Keep this session in this browser tab").check();
  await page
    .getByLabel("Local account file")
    .setInputFiles("../.local/integrated-client.json");
  await expect(
    page.getByRole("heading", { name: "A clearer view of every unit." }),
  ).toBeVisible();
  await expect(
    page.getByText("Automatic inspection is blocked.", { exact: true }),
  ).toBeVisible();
  const suffix = Date.now();
  const sku = "UI-TEST-" + suffix,
    unit = "UI-FIXTURE-" + suffix;
  await page.getByRole("button", { name: "Add product", exact: true }).click();
  await page.getByLabel("SKU", { exact: true }).fill(sku);
  await page.getByLabel("Product name").fill("SYNTHETIC UI TEST PRODUCT");
  await page
    .getByLabel("Visible description")
    .fill("Software fixture only; no real merchandise or inference.");
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Register unit", exact: true })
    .click();
  await page.getByLabel("Official unit ID").fill(unit);
  await page.getByLabel("Order ID", { exact: true }).fill("UI-ORDER-" + suffix);
  await page.getByLabel("Verified route").selectOption("merchant");
  await page
    .getByLabel("Order lines (one SKU, quantity per line)")
    .fill(sku + ", 2");
  await page.getByLabel("This is synthetic software test data").check();
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Start workflow", exact: true })
    .click();
  await page.getByLabel("Registered unit").selectOption(unit);
  await page.getByRole("button", { name: "Start Receiving workflow" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByLabel("Search unit or order").fill(unit);
  await page.getByRole("button", { name: unit, exact: true }).click();
  await expect(
    page.getByRole("heading", { name: unit, exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator(".run-card")
      .filter({ hasText: "Receiving" })
      .getByRole("button", { name: "Manual review" }),
  ).toBeEnabled({ timeout: 15000 });
  await expect(
    page.getByText(
      "Synthetic test data · These records do not establish model accuracy.",
    ),
  ).toBeVisible();
  await page
    .getByLabel("Evidence photograph", { exact: true })
    .setInputFiles("../.local/test-only.png");
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "saved. Uploading does not run an inspection." }),
  ).toBeVisible();
  await expect(page.getByAltText(/^Saved evidence /).first()).toBeVisible();
  const receiving = page.locator(".run-card").filter({ hasText: "Receiving" });
  await receiving.getByRole("button", { name: "Manual review" }).click();
  for (const key of ["damage", "identity", "quality", "quantity"]) {
    await page
      .getByRole("combobox", { name: "Verdict for " + key, exact: true })
      .selectOption("pass");
    await page
      .getByLabel("Evidence for " + key, { exact: true })
      .fill("Synthetic software fixture assertion; not a model finding.");
  }
  await page.getByRole("dialog").getByRole("checkbox").first().check();
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
  await page.getByLabel("Actual photograph capture time").fill(local);
  await page
    .getByLabel("Reason for this review")
    .fill("Explicit synthetic UI workflow review, not an accuracy result.");
  await page.getByRole("button", { name: "Review changes" }).click();
  await expect(
    page.getByText(
      "This is an attributed human decision, not an AI verification.",
      { exact: false },
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Confirm & save review" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(receiving.getByText("Completed", { exact: true })).toBeVisible();
  await receiving
    .getByText("Human review history (1)", { exact: true })
    .click();
  await expect(
    receiving.getByText(
      "Explicit synthetic UI workflow review, not an accuracy result.",
    ),
  ).toBeVisible();
  await expect(
    page
      .locator(".run-card")
      .filter({ hasText: "Pack" })
      .getByText("Blocked", { exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await page.reload();
  await expect(
    page.getByRole("heading", { name: unit, exact: true }),
  ).toBeVisible();
  await expect(page.getByAltText(/^Saved evidence /).first()).toBeVisible();
  const imageId = await page
    .getByAltText(/^Saved evidence /)
    .first()
    .getAttribute("alt");
  expect(
    (
      await request.get(
        (process.env.OPERATIONS_TEST_BASE_URL
          ? process.env.OPERATIONS_TEST_BASE_URL + "/operations-api"
          : "http://127.0.0.1:8010") +
          "/v1/images/" +
          imageId!.replace("Saved evidence ", ""),
      )
    ).status(),
  ).toBe(401);
  const issues = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    issues.violations.map((v) => ({
      id: v.id,
      targets: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  await page.screenshot({
    path: "../.local/qa/operations-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByLabel("Phone camera photograph")).toHaveAttribute(
    "capture",
    "environment",
  );
  await page.screenshot({
    path: "../.local/qa/operations-phone.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "All workflows", exact: true })
    .last()
    .click();
  await expect(page.getByLabel("Search unit or order")).toHaveValue(unit);
  await page.screenshot({
    path: "../.local/qa/operations-overview-phone.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByLabel("Search unit or order").fill("");
  await page.screenshot({
    path: "../.local/qa/operations-overview-desktop.png",
    fullPage: true,
  });
  expect(externalRequests).toEqual([]);
});

test("UI fixture: empty state, keyboard navigation and accessible connection screen", async ({
  page,
}) => {
  await page.route("**/operations-api/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({
      json: path.endsWith("/session")
        ? {
            operator: "SOFTWARE TEST",
            role: "viewer",
            organization: "test",
            can_write: false,
            inference: "blocked",
            checks: {},
            upload_limits: {
              max_bytes: 10485760,
              min_dimension: 64,
              max_pixels: 20000000,
            },
          }
        : [],
    });
  });
  await page.goto("/operations.html");
  const loginAudit = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(loginAudit.violations.map((v) => v.id)).toEqual([]);
  await page
    .getByLabel("Development token")
    .fill("explicit-software-test-token");
  await page.getByRole("button", { name: "Connect locally" }).click();
  await expect(
    page.getByRole("heading", { name: "No workflows yet" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start workflow", exact: true }),
  ).toBeDisabled();
  await page.keyboard.press("Tab");
  expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe(
    "BODY",
  );
});

test("client fixture: stable error, duplicate guard and timeout never auto-resubmits", async ({
  page,
}) => {
  await page.goto("/operations.html");
  let calls = 0;
  const keys: string[] = [];
  await page.route("**/operations-api/v1/test", async (route) => {
    calls++;
    keys.push(route.request().headers()["idempotency-key"]);
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route
      .fulfill({ status: 409, json: { error: { code: "STALE_REVIEW" } } })
      .catch(() => {});
  });
  const result = await page.evaluate(async () => {
    const { OperationsApi } = await import("/src/operations/api.ts");
    const api = new OperationsApi("software-fixture", "/operations-api", 35);
    const one = api.post("/v1/test", { test: true }).catch((e: any) => e.code);
    const two = api.post("/v1/test", { test: true }).catch((e: any) => e.code);
    const results = await Promise.all([one, two]);
    await new Promise((resolve) => setTimeout(resolve, 200));
    const three = await api
      .post("/v1/test", { test: true })
      .catch((e: any) => e.code);
    return { results, three };
  });
  expect(result.results).toEqual(["REQUEST_TIMEOUT", "REQUEST_IN_FLIGHT"]);
  expect(result.three).toBe("REQUEST_TIMEOUT");
  expect(calls).toBe(2);
  expect(keys[0]).toBe(keys[1]);
});

test("UI fixture: FBA timeline, absent Pack, original review, image denial and stale review draft", async ({
  page,
}) => {
  const at = new Date().toISOString();
  let writes = 0;
  const output = {
    basis: "fixture_human",
    verdict: "uncertain",
    findings: [
      {
        check_key: "packaging",
        verdict: "uncertain",
        detail: "Explicit UI fixture: unclear packaging",
      },
    ],
    image_ids: ["test-image"],
    evidence_run_ids: [],
    claim_supported: false,
  };
  const run = {
    id: "test-run",
    workflow_id: "test-workflow",
    manager: "prep",
    state: "review_needed",
    version: 3,
    created_at: at,
    retry_at: null,
    data: {
      correlation_id: "test-run",
      output,
      human_reviews: [
        {
          reviewer: "fixture-supervisor",
          at,
          reason: "Original fixture review reason",
          verdict: "uncertain",
          findings: output.findings,
          image_ids: ["test-image"],
          original_verdict: null,
          basis: "fixture_human",
        },
      ],
      error: {
        code: "MALFORMED_RESPONSE",
        retryable: false,
        safe_action: "Fixture review needed; do not redispatch",
      },
    },
  };
  const workflow = {
    id: "test-workflow",
    unit_id: "FIXTURE-FBA",
    version: 1,
    created_at: at,
    data: { state: "active", route: "fba", fixture: true },
    runs: [run],
    events: [],
  };
  const unit = {
    id: "FIXTURE-FBA",
    data: {
      order_id: "FIXTURE-ORDER",
      route: "fba",
      fixture: true,
      shipment_id: null,
      lines: [{ sku: "FIXTURE-SKU", quantity: 2 }],
    },
  };
  const no = { allowed: false, reason: "RETRY_NOT_ALLOWED" };
  const context = {
    workflow,
    unit,
    images: [
      { id: "test-image", bytes: 100, dimensions: [80, 80], taken_at: at },
    ],
    actions: {
      upload: no,
      event: no,
      route: no,
      hold: no,
      resume: no,
      cancel: no,
    },
    run_actions: {
      "test-run": { review: { allowed: true, reason: null }, retry: no },
    },
  };
  await page.route("**/operations-api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/review")) {
      writes++;
      await new Promise((r) => setTimeout(r, 200));
      return route.fulfill({
        status: 409,
        json: { error: { code: "STALE_REVIEW" } },
      });
    }
    if (path.includes("/images/"))
      return route.fulfill({
        status: 401,
        json: { error: { code: "AUTH_REQUIRED" } },
      });
    let data: unknown = [];
    if (path.endsWith("/session"))
      data = {
        operator: "fixture-supervisor",
        role: "supervisor",
        organization: "fixture",
        can_write: true,
        inference: "blocked",
        checks: { prep: ["packaging"] },
        upload_limits: {
          max_bytes: 10485760,
          min_dimension: 64,
          max_pixels: 20000000,
        },
      };
    else if (path.endsWith("/context")) data = context;
    else if (path.endsWith("/workflows")) data = [workflow];
    else if (path.endsWith("/units")) data = [unit];
    else if (path.endsWith("/runs")) data = [run];
    await route.fulfill({ json: data });
  });
  await page.goto("/operations.html#workflow=test-workflow");
  await page.getByLabel("Development token").fill("explicit-test-only");
  await page.getByRole("button", { name: "Connect locally" }).click();
  await expect(
    page.getByText("Receiving → Prep", { exact: true }),
  ).toBeVisible();
  await expect(
    page.locator(".not-scheduled").filter({ hasText: "Pack" }),
  ).toContainText("Not scheduled for this route.");
  await expect(
    page.locator(".not-scheduled").filter({ hasText: "Returns" }),
  ).toContainText("No return event recorded.");
  await expect(
    page.locator(".run-card").getByText("Needs review", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".evidence-photo")).toContainText("AUTH_REQUIRED");
  // Explicit fixture transitions must be the only source of processing animation.
  run.state = "running";
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(
    page.getByText("Prep is processing saved evidence", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".is-processing")).toHaveCount(1);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(page.locator(".is-processing .stage-number")).toHaveCSS(
    "animation-name",
    "none",
  );
  run.state = "completed";
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(page.locator(".is-processing")).toHaveCount(0);
  run.state = "review_needed";
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(
    page.locator(".run-card").getByText("Needs review", { exact: true }),
  ).toBeVisible();

  await page.getByText("Original saved findings", { exact: true }).click();
  await expect(
    page
      .getByText("Explicit UI fixture: unclear packaging", { exact: true })
      .first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Manual review" }).click();
  await page
    .getByLabel("Evidence for packaging")
    .fill("Draft retained across a stale review conflict.");
  await page.getByRole("dialog").getByRole("checkbox").check();
  const now = new Date();
  await page
    .getByLabel("Actual photograph capture time")
    .fill(
      new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16),
    );
  await page
    .getByLabel("Reason for this review")
    .fill("This draft must survive the conflict response.");
  await page.getByRole("button", { name: "Review changes" }).click();
  await page.getByRole("button", { name: "Confirm & save review" }).dblclick();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "STALE_REVIEW",
  );
  expect(writes).toBe(1);
  await page.getByRole("button", { name: "Back to edit" }).click();
  await expect(page.getByLabel("Reason for this review")).toHaveValue(
    "This draft must survive the conflict response.",
  );
  page.once("dialog", (d) => d.dismiss());
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeVisible();
});

test("UI fixture: visible loading and server failure without false success", async ({
  page,
}) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((r) => (release = r));
  await page.route("**/operations-api/**", async (route) => {
    if (route.request().url().endsWith("/session"))
      return route.fulfill({
        json: {
          operator: "fixture",
          role: "viewer",
          organization: "fixture",
          can_write: false,
          inference: "blocked",
          checks: {},
          upload_limits: {
            max_bytes: 10485760,
            min_dimension: 64,
            max_pixels: 20000000,
          },
        },
      });
    await gate;
    return route.fulfill({
      status: 503,
      json: { error: { code: "DATABASE_UNAVAILABLE" } },
    });
  });
  await page.goto("/operations.html");
  await page.getByLabel("Development token").fill("test");
  await page.getByRole("button", { name: "Connect locally" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Loading your workflows",
  );
  release();
  await expect(page.getByRole("alert")).toContainText("DATABASE_UNAVAILABLE");
  await expect(
    page.getByRole("button", { name: "Start workflow", exact: true }),
  ).toBeDisabled();
});
