import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow, openApplication, selectSection } from "./helpers";

test("deployed release is healthy and all workspaces are reachable", async ({ page }) => {
  const expectedVersion = process.env.E2E_EXPECTED_VERSION || "v1.12.0";
  const browserErrors: string[] = [];
  page.on("console", (message) => message.type() === "error" && browserErrors.push(message.text()));
  page.on("pageerror", (error) => browserErrors.push(error.message));
  const app = await openApplication(page);
  await expect(app.locator(`[data-app-version="${expectedVersion}"]`)).toBeVisible();
  await expectNoHorizontalOverflow(app);
  for (const name of [/Overview/, /Explore data/, /Ask AI/, /Advanced/, /Quality & speed/, /Export reports/]) {
    await selectSection(app, name);
  }
  expect(browserErrors).toEqual([]);
});
