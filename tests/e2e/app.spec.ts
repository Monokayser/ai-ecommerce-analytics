import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { expectBalancedNavigation, expectNoHorizontalOverflow, openApplication, selectSection } from "./helpers";

test.describe("local production interface", () => {
  test("matches the approved responsive breakpoint matrix", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The full viewport matrix runs once; browser engines have separate functional coverage.");
    test.setTimeout(120_000);
    const viewports = [
      { width: 320, height: 568, columns: 2 },
      { width: 375, height: 812, columns: 2 },
      { width: 430, height: 932, columns: 2 },
      { width: 768, height: 1024, columns: 3 },
      { width: 1024, height: 768, columns: 3 },
      { width: 1280, height: 800, columns: 6 },
      { width: 1440, height: 900, columns: 6 },
      { width: 1920, height: 1080, columns: 6 },
    ];
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      const app = await openApplication(page);
      await expectNoHorizontalOverflow(app);
      const labels = [];
      for (const name of [/Overview/, /Explore data/, /Ask AI/, /Advanced/, /Quality & speed/, /Export reports/]) {
        const box = await app.getByRole("radio", { name }).locator("xpath=ancestor::label[1]").boundingBox();
        expect(box).not.toBeNull();
        labels.push(box!);
      }
      const rowCount = new Set(labels.map((box) => Math.round(box.y))).size;
      expect(rowCount).toBe(Math.ceil(6 / viewport.columns));
      for (const box of labels) expect(box.height).toBeGreaterThanOrEqual(44);
    }
  });

  test("chart canvas resizes with the Streamlit sidebar", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The layout regression runs once; engines retain functional chart coverage.");
    await page.setViewportSize({ width: 1280, height: 800 });
    const app = await openApplication(page);
    await selectSection(app, /Explore data/);
    const chart = app.locator('[data-testid="stPlotlyChart"]').first();
    const svg = chart.locator("svg.main-svg").first();
    await expect(chart).toBeVisible();
    await expect(svg).toBeVisible();
    const expandSidebar = app.getByTestId("stExpandSidebarButton");
    if (await expandSidebar.isVisible()) {
      await expandSidebar.click();
      await expect(app.getByTestId("stSidebarCollapseButton")).toBeVisible();
    }
    const before = await chart.boundingBox();
    const collapseSidebar = app.locator('button[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] button');
    await app.getByTestId("stSidebarHeader").hover();
    await expect(collapseSidebar).toBeVisible();
    await collapseSidebar.click();
    await expect(expandSidebar).toBeVisible();
    await expect.poll(async () => (await chart.boundingBox())?.width || 0).toBeGreaterThan(before!.width + 200);
    await expect.poll(async () => {
      const chartBox = await chart.boundingBox();
      const svgBox = await svg.boundingBox();
      return chartBox && svgBox ? Math.abs(chartBox.width - svgBox.width) : Number.POSITIVE_INFINITY;
    }).toBeLessThanOrEqual(2);
    const after = await chart.boundingBox();
    const svgAfter = await svg.boundingBox();
    expect(before).not.toBeNull();
    expect(after).not.toBeNull();
    expect(svgAfter).not.toBeNull();
    expect(after!.width).toBeGreaterThan(before!.width + 200);
    expect(Math.abs(after!.width - svgAfter!.width)).toBeLessThanOrEqual(2);
    await expectNoHorizontalOverflow(app);
  });

  test("six sections, release marker, responsive navigation, and no browser errors", async ({ page }) => {
    const browserErrors: string[] = [];
    page.on("console", (message) => message.type() === "error" && browserErrors.push(message.text()));
    page.on("pageerror", (error) => browserErrors.push(error.message));
    const app = await openApplication(page);
    await expect(app.locator('[data-app-version="v1.12.0"]')).toBeVisible();
    await expectBalancedNavigation(app);
    await expectNoHorizontalOverflow(app);
    for (const [name, heading] of [
      [/Overview/, "Overview"],
      [/Explore data/, "Data Exploration"],
      [/Ask AI/, "AI Assistant"],
      [/Advanced/, "Advanced Analytics"],
      [/Quality & speed/, "Data Quality and Performance"],
      [/Export reports/, "Report Export"],
    ] as const) {
      await selectSection(app, name);
      await expect(app.getByRole("heading", { name: heading, exact: false }).first()).toBeVisible();
    }
    expect(browserErrors).toEqual([]);
  });

  test("filters reset and AI fallback remain usable", async ({ page }) => {
    const app = await openApplication(page);
    await expect(app.getByText(/Local analytics/i).first()).toBeVisible();
    const expandSidebar = app.getByTestId("stExpandSidebarButton");
    if (await expandSidebar.isVisible()) {
      await expandSidebar.click();
      await expect(app.getByRole("button", { name: /Reset filters/i })).toBeVisible();
    }
    await expect(app.getByRole("button", { name: /Reset filters/i })).toBeEnabled();
    await app.getByRole("button", { name: /Reset filters/i }).click();
    if ((await app.getByTestId("stSidebar").getAttribute("aria-expanded")) === "true") {
      await app.locator('button[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] button').click({ force: true });
      await expect(expandSidebar).toBeVisible();
    }
    await selectSection(app, /Ask AI/);
    await expect(app.getByRole("button", { name: /Generate Commerce Insights/i })).toBeEnabled();
    await app.getByText(/Agent settings and privacy/i).click();
    await expect(app.getByRole("button", { name: /Reset agent/i })).toBeEnabled();
  });

  test("has no serious or critical automated accessibility violations", async ({ page }) => {
    const app = await openApplication(page);
    expect(app).toBe(page);
    const results = await new AxeBuilder({ page }).options({ runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] } }).analyze();
    const blocking = results.violations.filter((violation) => {
      if (!["serious", "critical"].includes(violation.impact || "")) return false;
      // Streamlit 1.61 owns this exact sidebar disclosure attribute. Keep the waiver
      // narrow so any application-owned or additional framework node still fails CI.
      const streamlitSidebarOnly = violation.id === "aria-allowed-attr" && violation.nodes.every((node) =>
        node.target.length === 1 && node.target[0] === ".stSidebar" && node.html.includes("<section") && node.html.includes("aria-expanded="),
      );
      return !streamlitSidebarOnly;
    });
    expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
  });

  test("honors reduced motion and exposes keyboard focus", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    const app = await openApplication(page);
    const animationDuration = await app.locator(".app-hero").evaluate((element) => getComputedStyle(element, "::before").animationDuration);
    expect(["0s", "0.00001s", "1e-05s"]).toContain(animationDuration);
    await page.keyboard.press("Tab");
    const focused = app.locator(":focus");
    await expect(focused).toBeVisible();
    const outline = await focused.evaluate((element) => getComputedStyle(element).outlineStyle);
    expect(outline).not.toBe("none");
  });
});
