import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: process.env.PACK_TEST_BASE_URL || "http://127.0.0.1:8000",
    trace: "retain-on-failure",
  },
  workers: 1,
  reporter: "list",
});
