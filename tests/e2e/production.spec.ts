import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow, openApplication, selectSection } from "./helpers";

test("deployed release is healthy and all workspaces are reachable", async ({ page }) => {
  const expectedVersion = process.env.E2E_EXPECTED_VERSION || "v1.12.1";
  const browserErrors: string[] = [];
  page.on("console", (message) => message.type() === "error" && browserErrors.push(message.text()));
  page.on("pageerror", (error) => browserErrors.push(error.message));
  const app = await openApplication(page);
  await expect(app.locator(`[data-app-version="${expectedVersion}"]`)).toBeVisible();
  await expectNoHorizontalOverflow(app);
  for (const name of [/Overview/, /Explore data/, /Ask AI/, /Advanced/, /Quality & speed/, /Export reports/]) {
    await selectSection(app, name);
  }
  // Streamlit Community Cloud probes optional shell resources that can emit a
  // generic 404 console message even while the application iframe is healthy.
  // Keep application exceptions and all non-404 console errors blocking.
  const blockingErrors = browserErrors.filter((message) => !message.includes("Failed to load resource: the server responded with a status of 404"));
  expect(blockingErrors).toEqual([]);
});
