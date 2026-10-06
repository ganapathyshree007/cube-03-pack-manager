import { test, expect } from "@playwright/test";

test.use({
  baseURL: process.env.OPERATIONS_TEST_BASE_URL || "http://127.0.0.1:5174",
});
test("visual evidence fixture keeps unknown counts and model attribution visible", async ({
  page,
}) => {
  await page.goto("/operations.html");
  await page.evaluate(async () => {
    const { mount } = await import("/tests/vision-harness.tsx");
    mount();
  });
  await page.getByText("Visual inspection evidence", { exact: true }).click();
  await expect(page.getByText("Software fixture, not inference")).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "Unresolved", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("one: uncertain")).toBeVisible();
  await expect(page.getByText("No model regions supplied")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});
