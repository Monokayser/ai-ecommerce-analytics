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

  test("persistent chat launcher opens the autonomous agent", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The launcher routing regression runs once; responsive navigation covers every engine.");
    await page.setViewportSize({ width: 390, height: 844 });
    const app = await openApplication(page);
    const launcher = app.locator('a.agent-launcher[aria-label="Open the AI analytics agent"]');
    await expect(launcher).toBeVisible();
    const bounds = await launcher.boundingBox();
    expect(bounds).not.toBeNull();
    expect(bounds!.width).toBeGreaterThanOrEqual(58);
    expect(bounds!.height).toBeGreaterThanOrEqual(58);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(390);
    expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(844);

    await launcher.click();
    await expect(app.getByRole("heading", { name: "Autonomous Analytics Agent" })).toBeVisible({ timeout: 45_000 });
    await expect(app.getByRole("textbox", { name: "Describe the task or outcome" })).toBeVisible();
    await expect(app.locator('a.agent-launcher[aria-label="Jump to the AI task composer"]')).toBeVisible();
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

  test("animation workspace prioritizes a large chart in a compact layout", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The visual sizing regression runs once; all engines retain navigation coverage.");
    await page.setViewportSize({ width: 1440, height: 900 });
    const app = await openApplication(page);
    await selectSection(app, /Explore data/);
    await app.getByRole("radio", { name: "Animation", exact: true }).click();
    const workspace = app.locator(".st-key-animation_workspace");
    const chart = workspace.locator('[data-testid="stPlotlyChart"]');
    await expect(workspace).toBeVisible();
    await expect(chart).toBeVisible();
    const chartBox = await chart.boundingBox();
    const introBox = await app.getByRole("heading", { name: "Data Exploration" }).locator("xpath=ancestor::div[@data-testid='stLayoutWrapper'][1]").boundingBox();
    expect(chartBox).not.toBeNull();
    expect(chartBox!.height).toBeGreaterThanOrEqual(640);
    expect(chartBox!.width).toBeGreaterThan(900);
    expect(introBox).not.toBeNull();
    expect(introBox!.height).toBeLessThan(160);
    await expect(app.getByText("See category performance change year by year")).toBeVisible();
    await expectNoHorizontalOverflow(app);
  });

  test("renders only the selected exploration chart", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The lazy-render regression runs once; browser engines retain section coverage.");
    const app = await openApplication(page);
    await selectSection(app, /Explore data/);
    await expect(app.getByRole("radiogroup", { name: "Visualization view" })).toBeVisible();
    await expect(app.locator('[data-testid="stPlotlyChart"]')).toHaveCount(1);
    await app.getByRole("radio", { name: "Correlation", exact: true }).click();
    await expect(app.getByText("Correlation Matrix", { exact: false })).toBeVisible();
    await expect(app.locator('[data-testid="stPlotlyChart"]')).toHaveCount(1);
  });

  test("six sections, release marker, responsive navigation, and no browser errors", async ({ page }) => {
    const browserErrors: string[] = [];
    page.on("console", (message) => message.type() === "error" && browserErrors.push(message.text()));
    page.on("pageerror", (error) => browserErrors.push(error.message));
    const app = await openApplication(page);
    await expect(app.locator('[data-app-version="v1.13.0"]')).toBeVisible();
    await expectBalancedNavigation(app);
    await expectNoHorizontalOverflow(app);
    for (const [name, heading] of [
      [/Overview/, "Overview"],
      [/Explore data/, "Data Exploration"],
      [/Ask AI/, "Autonomous Analytics Agent"],
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
    // Keep the sidebar in its browser-native state. Streamlit exposes a collapse
    // affordance differently between branded Chrome and bundled Chromium, while
    // the primary workspace navigation remains usable in both states.
    await selectSection(app, /Ask AI/);
    await expect(app.getByRole("button", { name: /Generate Commerce Insights/i })).toBeEnabled();
    await app.getByText(/Agent settings and privacy/i).click();
    await expect(app.getByRole("button", { name: /Reset agent/i })).toBeEnabled();
  });

  test("AI composer is readable and completes a verified chat workflow", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The complete assistant workflow runs once; provider contracts are covered in Python tests.");
    test.setTimeout(90_000);
    const app = await openApplication(page);
    await selectSection(app, /Ask AI/);

    const question = app.getByRole("textbox", { name: "Describe the task or outcome" });
    const submit = app.getByRole("button", { name: "Run task autonomously" });
    const buttonPresentation = await submit.evaluate((element) => {
      const button = element as HTMLElement;
      const label = button.querySelector("p") || button;
      const bounds = button.getBoundingClientRect();
      return {
        height: bounds.height,
        background: getComputedStyle(button).backgroundImage,
        text: getComputedStyle(label).color,
        weight: getComputedStyle(label).fontWeight,
      };
    });
    const placeholder = await question.evaluate((element) => getComputedStyle(element, "::placeholder").color);
    expect(buttonPresentation.height).toBeGreaterThanOrEqual(44);
    expect(buttonPresentation.background).toContain("linear-gradient");
    expect(buttonPresentation.text).toBe("rgb(3, 32, 25)");
    expect(Number(buttonPresentation.weight)).toBeGreaterThanOrEqual(700);
    expect(placeholder).toBe("rgb(170, 195, 186)");

    const prompt = "Compare total sales by region from highest to lowest.";
    await question.fill(prompt);
    await submit.click();
    await expect(app.locator('article[aria-label="Your question"]')).toContainText(prompt, { timeout: 45_000 });
    await expect(app.locator('article[aria-label="Verified assistant answer"]')).toBeVisible();
    await expect(app.locator('.agent-task-receipt')).toContainText("Delivered");
    await expect(app.getByText("Query validated", { exact: false })).toBeVisible();
    await expect(app.locator('[data-testid="stPlotlyChart"]')).toHaveCount(0);
    await app.getByRole("radio", { name: "Chart" }).click();
    await expect(app.locator('[data-testid="stPlotlyChart"]')).toHaveCount(1);
    const capturesWheel = await app.locator(".js-plotly-plot").evaluate((element) => Boolean((element as any)._context?.scrollZoom));
    expect(capturesWheel).toBe(false);
    await app.getByRole("button", { name: "Prepare Word + PDF" }).click();
    await expect(app.getByRole("button", { name: "Download Word" })).toBeVisible();
    await expect(app.getByRole("button", { name: "Download PDF" })).toBeVisible();

    await app.getByRole("button", { name: "Save response" }).click();
    await expect(app.getByText(/Verified response saved/i)).toBeVisible();
    await app.getByText(/Agent settings and privacy/i).click();
    await app.getByRole("button", { name: /Reset agent/i }).click();
    await expect(app.getByText(/What should the agent accomplish/i)).toBeVisible();
  });

  test("keeps wheel scrolling on a repaint-safe path", async ({ page }, testInfo) => {
    const app = await openApplication(page);
    const main = app.locator('[data-testid="stMain"]');
    const presentation = await app.evaluate(() => {
      const root = document.documentElement;
      const surface = document.querySelector(".stApp") as HTMLElement;
      const header = document.querySelector('[data-testid="stHeader"]') as HTMLElement;
      return {
        scrollBehavior: getComputedStyle(root).scrollBehavior,
        backgroundScrolls: getComputedStyle(surface).backgroundAttachment.split(",").every((value) => value.trim() === "scroll"),
        headerBackdrop: getComputedStyle(header).backdropFilter,
      };
    });
    expect(presentation).toEqual({ scrollBehavior: "auto", backgroundScrolls: true, headerBackdrop: "none" });

    // Mobile WebKit exposes touch scrolling and intentionally has no desktop
    // mouse-wheel API. Its CSS path is still verified above; pointer projects
    // additionally exercise a real wheel gesture below.
    if (testInfo.project.name === "mobile-safari") return;

    await main.hover();
    await page.mouse.wheel(0, 480);
    await expect.poll(() => main.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
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
