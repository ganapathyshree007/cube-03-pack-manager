import { test, expect } from "@playwright/test";

test("camera permission failure offers file upload and a visible escape", async ({ page }) => {
  // Explicit software fixture: never access the user's real camera in this test.
  await page.addInitScript(() => {
    Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
      value: async () => { throw new DOMException("Software fixture", "NotAllowedError"); },
    });
  });
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Inspection", exact: true }).click();
  await page.getByRole("button", { name: "Use rear camera" }).click();
  await expect(page.getByRole("alert")).toContainText("permission declined");
  await expect(page.getByRole("button", { name: "Capture primary photograph" })).toBeDisabled();
  await page.getByRole("button", { name: "Close camera" }).click();
  await expect(page.getByRole("button", { name: "Use rear camera" })).toBeVisible();
  await expect(page.getByLabel("Box photograph", { exact: true })).toBeAttached();
});
