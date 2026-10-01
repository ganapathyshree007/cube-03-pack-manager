import { test, expect } from "@playwright/test";

test("software fixture: per-check review preserves the original result and blocks packing", async ({
  page,
}) => {
  const id = "SOFTWARE-REVIEW-FIXTURE";
  const row: any = {
    id,
    version: 1,
    data: {
      status: "completed",
      image_id: null,
      order_id: "TEST-ORDER",
      order_snapshot: {
        reference: "SOFTWARE TEST ONLY",
        unit_id: "TEST-UNIT",
        lines: [],
      },
      catalogue_snapshot: [],
      overrides: [],
      check_overrides: [],
      superseded_by: null,
      result: {
        decision: "seal",
        checks: [
          {
            check_key: "quantities_correct",
            verdict: "PASS",
            detail: "Explicit UI fixture; no model inference",
          },
        ],
        observed: [],
        provenance: { model_version: "TEST-ONLY" },
      },
    },
  };
  await page.addInitScript(
    (value) => localStorage.setItem("pack-attempt", value),
    id,
  );
  await page.route(`**/api/v1/inspections/${id}**`, async (route) => {
    if (route.request().url().endsWith("/events")) {
      await route.fulfill({json: []});
      return;
    }
    if (route.request().method() === "POST") {
      expect(route.request().url()).toContain(
        "/checks/quantities_correct/review",
      );
      const payload = route.request().postDataJSON();
      expect(payload.verdict).toBe("fail");
      expect(payload.expected_version).toBe(1);
      expect(payload.reason).toContain("Software test");
      row.version = 2;
      row.data.review_decision = "stop_and_fix";
      row.data.check_overrides = [
        {
          check_key: "quantities_correct",
          from_verdict: "pass",
          to_verdict: "fail",
          reason: payload.reason,
          by: "TEST-SUPERVISOR",
        },
      ];
    }
    await route.fulfill({ json: row });
  });
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Inspection", exact: true }).click();
  await page
    .getByRole("button", { name: "Review quantities correct", exact: true })
    .click();
  await page.getByLabel("Review: quantities correct").selectOption("fail");
  await page
    .getByLabel("Reason", { exact: true })
    .fill("Software test: supervisor counted a discrepancy.");
  await page.getByRole("button", { name: "Save attributed review" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByText("Human check reviews", { exact: true }),
  ).toBeVisible();
  await expect(
    page.locator(".decision-panel").getByText("Stop & fix", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".check-row > .mono")).toHaveText("PASS");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
