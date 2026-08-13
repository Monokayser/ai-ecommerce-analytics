import { expect, Frame, Page } from "@playwright/test";

export type AppContext = Page | Frame;

export async function openApplication(page: Page): Promise<AppContext> {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1_000);
  if (page.url().includes("streamlit.app")) {
    await expect.poll(
      () => page.frames().some((frame) => frame !== page.mainFrame() && frame.url().includes("/~/+/")),
      { timeout: 45_000 },
    ).toBe(true);
  }
  const cloudFrame = page.frames().find((frame) => frame !== page.mainFrame() && frame.url().includes("/~/+/"));
  const app = cloudFrame || page;
  await expect(app.locator('[data-app-version]')).toBeVisible({ timeout: 45_000 });
  return app;
}

export async function selectSection(app: AppContext, accessibleName: RegExp): Promise<void> {
  const mobileViewport = await app.locator("html").evaluate(() => window.innerWidth <= 900);
  const sidebar = app.getByTestId("stSidebar");
  if (mobileViewport && (await sidebar.getAttribute("aria-expanded")) === "true") {
    const collapse = app.locator('button[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] button');
    if (await collapse.count()) {
      await collapse.first().click({ force: true });
      await expect(sidebar).toHaveAttribute("aria-expanded", "false");
    }
  }
  const navigation = app.getByRole("radio", { name: accessibleName });
  await navigation.locator("xpath=ancestor::label[1]").click();
  await expect(navigation).toBeChecked();
}

export async function expectNoHorizontalOverflow(app: AppContext): Promise<void> {
  const overflow = await app.locator("html").evaluate((element) => element.scrollWidth - element.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

export async function expectBalancedNavigation(app: AppContext): Promise<void> {
  const names = [/Overview/, /Explore data/, /Ask AI/, /Advanced/, /Quality & speed/, /Export reports/];
  const boxes = [];
  for (const name of names) {
    const box = await app.getByRole("radio", { name }).locator("xpath=ancestor::label[1]").boundingBox();
    if (box) boxes.push({ width: box.width, height: box.height, top: Math.round(box.y) });
  }
  expect(boxes).toHaveLength(6);
  for (const box of boxes) expect(box.height).toBeGreaterThanOrEqual(44);
  const rows = new Map<number, number[]>();
  for (const box of boxes) rows.set(box.top, [...(rows.get(box.top) || []), box.width]);
  for (const widths of rows.values()) expect(Math.max(...widths) - Math.min(...widths)).toBeLessThanOrEqual(2);
}
