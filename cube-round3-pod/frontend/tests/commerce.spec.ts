import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";

test.use({
  baseURL: process.env.OPERATIONS_TEST_BASE_URL || "http://127.0.0.1:8014",
  trace: "off",
});
test("real local commerce: customer request, owned status, operations hold and persisted analytics", async ({
  page,
  request,
}) => {
  const account = JSON.parse(
    await readFile("../.local/integrated-client.json", "utf8"),
  );
  const stamp = Date.now().toString();
  const version = "ui-commerce-" + stamp;
  const headers = { Authorization: "Bearer " + account.token };
  async function post(path: string, data: unknown) {
    const r = await request.post("/operations-api" + path, {
      headers: { ...headers, "Idempotency-Key": crypto.randomUUID() },
      data,
    });
    expect(r.ok()).toBeTruthy();
    return r.json();
  }
  await post("/v1/commerce/admin/policies", {
    version,
    source_reference: "Labelled synthetic browser-test policy",
    rules: [
      {
        id: "fixture-electronics",
        categories: ["fixture-" + stamp],
        routes: ["merchant"],
      },
    ],
  });
  const product = await post("/v1/catalogue", {
    sku: "COMMERCE-FIXTURE-" + stamp,
    name: "Synthetic commerce product " + stamp,
    visual_description:
      "Software test fixture only. No real product or model observation.",
  });
  await post("/v1/commerce/admin/products/" + product.id, {
    expected_version: product.version,
    fixture: true,
    active: true,
    category: "fixture-" + stamp,
    price_minor: 12500,
    route: "merchant",
    policy_version: version,
    return_window_days: 0,
  });
  await post("/v1/commerce/admin/inventory/" + product.id + "/receipts", {
    quantity: 2,
    source_reference: "SYNTHETIC-RECEIPT-" + stamp,
    note: "Synthetic browser test inventory event, not an actual shipment",
  });
  await page.goto("/shop.html");
  await page
    .getByLabel("Local account file")
    .setInputFiles("../.local/customer-client.json");
  await expect(
    page.getByRole("heading", { name: "Your products and orders" }),
  ).toBeVisible();
  await page
    .getByLabel("Quantity for Synthetic commerce product " + stamp)
    .fill("1");
  await page.getByRole("button", { name: "Place order request" }).click();
  await expect(page.getByRole("status")).toContainText("Order request saved");
  const card = page
    .locator("article")
    .filter({
      has: page.getByText("Synthetic commerce product " + stamp + " × 1", {
        exact: false,
      }),
    })
    .last();
  await expect(card).toContainText("review required"); // Pod assignment deliberately remains unresolved.
  await expect(card).toContainText("Test order");
  await expect(
    page.getByRole("button", { name: "Open fulfillment workflow" }),
  ).toHaveCount(0);
  await page.reload();
  // No optional session retention was selected, so explicitly reconnect.
  await page
    .getByLabel("Local account file")
    .setInputFiles("../.local/customer-client.json");
  await expect(
    page.getByText("Synthetic commerce product " + stamp + " × 1", {
      exact: false,
    }),
  ).toBeVisible();
  const issues = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(issues.violations.map((x) => x.id)).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.local/qa/customer-phone.png",
    fullPage: true,
  });
  const orders = await request.get("/operations-api/v1/commerce/admin/orders", {
    headers,
  });
  const saved = (await orders.json()).find((o: any) =>
    o.data.lines.some((l: any) => l.product_id === product.id),
  );
  expect(saved.state).toBe("review_required");
  const workflow = await request.get(
    "/operations-api/v1/workflows/" + saved.workflow_id,
    { headers },
  );
  expect((await workflow.json()).runs).toEqual([]);
  const analytics = await request.get(
    "/operations-api/v1/commerce/admin/analytics?include_fixtures=true&product_id=" +
      product.id,
    { headers },
  );
  expect((await analytics.json()).total_orders).toBe(1);
  const excluded = await request.get(
    "/operations-api/v1/commerce/admin/analytics?product_id=" + product.id,
    { headers },
  );
  expect((await excluded.json()).total_orders).toBe(0);
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.goto("/operations.html");
  await page
    .getByLabel("Local account file")
    .setInputFiles("../.local/integrated-client.json");
  await page.getByRole("button", { name: "Analytics", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Operations analytics" }),
  ).toBeVisible();
  await page.getByLabel("product id", { exact: true }).fill(product.id);
  await expect(page.getByText("No orders match these filters.")).toBeVisible();
  await page.getByLabel("Include labelled test orders").check();
  await expect(page.getByText("No orders match these filters.")).toHaveCount(0);
  await page.screenshot({
    path: "../.local/qa/analytics-phone.png",
    fullPage: true,
  });
});
