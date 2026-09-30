import { test, expect } from "@playwright/test";
import fs from "node:fs";
import AxeBuilder from "@axe-core/playwright";

test("real API: create order, save pending evidence, refresh, review and retake", async ({
  page,
}) => {
  const suffix = Date.now().toString();
  await page.goto("/workspace");
  await expect(
    page.getByText("Model not configured", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../.local/qa/overview-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Catalogue", exact: true }).click();
  await page.getByRole("button", { name: "Add product", exact: true }).click();
  await page.getByLabel("SKU", { exact: true }).fill(`TEST-${suffix}`);
  await page.getByLabel("Product name").fill("SOFTWARE TEST ONLY");
  await page
    .getByLabel("Distinguishing visual attributes")
    .fill("Synthetic browser fixture, not merchandise or evaluation evidence.");
  await page.getByRole("button", { name: "Save product", exact: true }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.getByRole("button", { name: "Orders", exact: true }).click();
  await page.getByRole("button", { name: "Create order", exact: true }).click();
  await page.getByLabel("Order reference").fill(`TEST ORDER ${suffix}`);
  await page.getByLabel("Physical unit ID").fill(`TEST-UNIT-${suffix}`);
  await page.getByLabel("Order lines").fill(`TEST-${suffix}, 1`);
  await page.getByRole("button", { name: "Save order", exact: true }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page
    .getByRole("row")
    .filter({ hasText: `TEST ORDER ${suffix}` })
    .getByRole("button", { name: "Inspect", exact: true })
    .click();
  await page
    .getByLabel("Box photograph", { exact: true })
    .setInputFiles("../.local/test-only.png");
  await page
    .getByRole("button", { name: "Save for review", exact: true })
    .click();
  await expect(page.getByText("Pending review", { exact: true })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Inspection", exact: true }).click();
  await expect(
    page.getByText(`TEST ORDER ${suffix}`, { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Supervisor review", exact: true })
    .click();
  await page.getByLabel("Human decision").selectOption("stop_and_fix");
  await page
    .getByLabel("Reason", { exact: true })
    .fill("Software test: human review attribution is being verified.");
  await page.getByRole("button", { name: "Save attributed review" }).click();
  await expect(page.getByText("Human decision: Stop & fix")).toBeVisible();
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    accessibility.violations.map((v) => ({
      id: v.id,
      targets: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  await page.screenshot({
    path: "../.local/qa/inspection-desktop.png",
    fullPage: true,
  });
  for (const [name, width, height] of [
    ["tablet", 820, 1180],
    ["phone", 390, 844],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.screenshot({
      path: `../.local/qa/inspection-${name}.png`,
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  await page
    .getByRole("button", { name: "New capture / attempt", exact: true })
    .click();
  await expect(
    page.getByText("Awaiting capture", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Box photograph", { exact: true }),
  ).toBeVisible();
  fs.writeFileSync(
    "../.local/qa/browser-run.json",
    JSON.stringify({
      kind: "software-fixture-only",
      reference: `TEST ORDER ${suffix}`,
      status: "passed",
    }),
  );
});

test("keyboard dialog traps focus and Escape closes it", async ({ page }) => {
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Orders", exact: true }).click();
  await page.getByRole("button", { name: "Create order", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Shift+Tab");
  expect(
    await page.evaluate(() => !!document.activeElement?.closest("dialog")),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
});

test("overview has no detected WCAG AA violations", async ({ page }) => {
  await page.goto("/workspace");
  await expect(page.getByText("Every order, accounted for.")).toBeVisible();
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    result.violations.map((v) => ({
      id: v.id,
      targets: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
});
