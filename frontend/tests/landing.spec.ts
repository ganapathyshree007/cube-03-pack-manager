import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("public landing explains the product and opens the real workspace", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Before you seal.",
  );
  await expect(
    page.getByRole("navigation", { name: "Main navigation" }),
  ).toHaveCount(0);
  const a11y = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    a11y.violations.map((v) => ({
      id: v.id,
      targets: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  await page.screenshot({
    path: "../.local/qa/landing-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../.local/qa/landing-phone.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Enter your workspace" }).click();
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(
    page.getByRole("heading", { name: "Every order, accounted for." }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Workspace setup" }),
  ).toBeVisible();
});
