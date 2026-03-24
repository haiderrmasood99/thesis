const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { imageSizingContain } = require("./pptxgenjs_helpers/image");
const { warnIfSlideHasOverlaps, warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Haider Masood";
pptx.company = "NUST SEECS";
pptx.subject = "Final Thesis Defence";
pptx.title = "Haider_Masood_ Final_defence";
pptx.lang = "en-US";
pptx.theme = { headFontFace: "Calibri", bodyFontFace: "Calibri", lang: "en-US" };

const W = 13.333;
const COLORS = {
  NAVY: "0F2B46",
  BG: "F4F7FB",
  WHITE: "FFFFFF",
  TEXT: "1A2530",
  MUTED: "4E5D6C",
  LINE: "D9E3EE",
  GOOD: "1E7A3E",
  WARN: "B36B00",
};

const asset = (name) => path.join(__dirname, "assets", name);
let page = 0;

function addFooter(slide) {
  slide.addShape(pptx.ShapeType.line, { x: 0, y: 7.06, w: W, h: 0, line: { color: COLORS.LINE, pt: 0.8 } });
  slide.addText("Haider Masood | MS-AI Thesis Defence | March 2026", {
    x: 0.45, y: 7.1, w: 10.9, h: 0.22, fontFace: "Calibri", fontSize: 9, color: COLORS.MUTED,
  });
  slide.addText(String(page), {
    x: 12.15, y: 7.1, w: 0.85, h: 0.22, fontFace: "Calibri", fontSize: 10, color: COLORS.MUTED, align: "right",
  });
}

function addHeader(slide, title, section = "") {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: W, h: 0.66, fill: { color: COLORS.NAVY }, line: { color: COLORS.NAVY, pt: 0 },
  });
  slide.addText(title, {
    x: 0.45, y: 0.13, w: 9.3, h: 0.36, fontFace: "Calibri", fontSize: 19, bold: true, color: COLORS.WHITE,
  });
  if (section) {
    slide.addText(section.toUpperCase(), {
      x: 10.2, y: 0.18, w: 2.7, h: 0.24, fontFace: "Calibri", fontSize: 9, bold: true, color: "B9D1E7", align: "right", charSpace: 1,
    });
  }
  addFooter(slide);
}

function bulletRuns(items) {
  return items.map((text, idx) => ({ text, options: { bullet: { indent: 14 }, breakLine: idx !== items.length - 1 } }));
}

function addBullets(slide, items, x, y, w, h, fontSize = 15, color = COLORS.TEXT) {
  slide.addText(bulletRuns(items), {
    x, y, w, h, fontFace: "Calibri", fontSize, color, margin: 2, valign: "top", lineSpacingMultiple: 1.1,
  });
}

function finish(slide) {
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function newSlide(title, section = "") {
  page += 1;
  const slide = pptx.addSlide();
  addHeader(slide, title, section);
  return slide;
}

// 1 Title slide
page += 1;
{
  const s = pptx.addSlide();
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 7.5, fill: { color: COLORS.NAVY }, line: { color: COLORS.NAVY, pt: 0 } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 6.52, w: W, h: 0.98, fill: { color: "0A1E33" }, line: { color: "0A1E33", pt: 0 } });
  s.addImage({ path: asset("nust-logo.png"), ...imageSizingContain(asset("nust-logo.png"), 10.82, 0.42, 2.0, 2.0) });
  s.addText("Optimizing Agricultural Resource Allocation through Reinforcement Learning for Yield Improvement", {
    x: 0.75, y: 1.24, w: 9.35, h: 1.6, fontFace: "Calibri", fontSize: 33, bold: true, color: COLORS.WHITE, lineSpacingMultiple: 1.02,
  });
  s.addText("A Cost-Driven Approach to Crop Efficiency Enhancement in Pakistan", {
    x: 0.75, y: 2.92, w: 9.35, h: 0.7, fontFace: "Calibri", fontSize: 21, italic: true, color: "D6E6F4",
  });
  s.addText("Final Thesis Defence Presentation", {
    x: 0.75, y: 4.16, w: 8.7, h: 0.4, fontFace: "Calibri", fontSize: 19, bold: true, color: "8ED4CE",
  });
  s.addText("Haider Masood (401636)\nMS Artificial Intelligence\nSupervisor: Dr. Zuhair Zafar", {
    x: 0.75, y: 4.74, w: 7.7, h: 1.1, fontFace: "Calibri", fontSize: 16, color: COLORS.WHITE, lineSpacingMultiple: 1.1,
  });
  s.addText("Department of Computing, NUST SEECS | March 2026", {
    x: 0.75, y: 6.83, w: 10.5, h: 0.34, fontFace: "Calibri", fontSize: 12, color: "B8CADC",
  });
  s.addText(String(page), { x: 12.15, y: 7.1, w: 0.85, h: 0.22, fontFace: "Calibri", fontSize: 10, color: "B8CADC", align: "right" });
  finish(s);
}

// 2 Outline
{
  const s = newSlide("Presentation Outline", "Outline");
  addBullets(s, [
    "Introduction, motivation, and Pakistan context",
    "Research gap, problem statement, and thesis scope",
    "Methodology and system architecture",
    "Implementation evidence and verification logs",
    "Latest broad NPK matrix and current status",
    "Historical benchmark context and runtime profile",
    "Contributions, limitations, and future work",
    "Conclusion",
  ], 0.9, 1.05, 11.6, 5.7, 20);
  finish(s);
}

// 3 Introduction and motivation
{
  const s = newSlide("Introduction and Motivation", "Context");
  addBullets(s, [
    "Pakistan agriculture is economically critical and operationally risk-sensitive.",
    "Field trial-and-error is expensive when weather and fertilizer costs are volatile.",
    "Simulation-first RL narrows viable policy space before field-adjacent validation.",
    "Defence claim: this thesis contributes a localized, evidence-disciplined RL stack.",
  ], 0.75, 1.05, 6.2, 4.5, 16);
  s.addImage({ path: asset("pakistan_weather_coverage.png"), ...imageSizingContain(asset("pakistan_weather_coverage.png"), 7.0, 1.0, 5.7, 4.9) });
  s.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 6.0, w: 12.0, h: 0.62, fill: { color: "EEF8F6" }, line: { color: "D0ECE7", pt: 1 }, radius: 0.05 });
  s.addText("Localized weather/soil/economic inputs are implemented, not just proposed.", {
    x: 1.0, y: 6.2, w: 11.5, h: 0.24, fontFace: "Calibri", fontSize: 13, color: "215C58", align: "center",
  });
  finish(s);
}

// 4 Gap and problem
{
  const s = newSlide("Research Gap and Problem Statement", "Research Gap");
  addBullets(s, [
    "Most RL agriculture stacks are built for non-Pakistan assumptions.",
    "Legacy setup lacked complete NPK-aware economics and report-level traceability.",
    "Proposal ambitions exceeded current implemented controls in some areas.",
  ], 0.75, 1.08, 6.0, 3.8, 16);
  s.addShape(pptx.ShapeType.roundRect, { x: 6.95, y: 1.06, w: 5.7, h: 4.95, fill: { color: "F9F4F2" }, line: { color: "E7C8BF", pt: 1 }, radius: 0.06 });
  s.addText("Problem Statement", {
    x: 7.22, y: 1.34, w: 5.2, h: 0.34, fontFace: "Calibri", fontSize: 18, bold: true, color: "7A1E10",
  });
  s.addText("Existing RL agricultural systems designed for North American/European contexts are not directly transferable to Pakistani climate, crop, and economic conditions.", {
    x: 7.22, y: 1.84, w: 5.2, h: 2.35, fontFace: "Calibri", fontSize: 15, italic: true, color: "4A2D25", lineSpacingMultiple: 1.1,
  });
  s.addText("Thesis response: localization + NPK expansion + hierarchical reporting + strict claims policy.", {
    x: 7.22, y: 4.55, w: 5.2, h: 1.0, fontFace: "Calibri", fontSize: 14, bold: true, color: COLORS.TEXT,
  });
  finish(s);
}

// 5 Scope closure
{
  const s = newSlide("Solution Scope: Implemented vs Deferred", "Scope");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.74, y: 1.02, w: 5.95, h: 5.5, fill: { color: "EAF7F0" }, line: { color: "BDE2CD", pt: 1 }, radius: 0.06 });
  s.addText("Implemented", { x: 1.0, y: 1.3, w: 5.4, h: 0.34, fontFace: "Calibri", fontSize: 18, bold: true, color: COLORS.GOOD });
  addBullets(s, [
    "Pakistan weather and soil integration",
    "Year-varying Pakistan crop and nutrient price series",
    "NPK-aware fertilization and reward decomposition",
    "Hierarchical planning + weekly fertilization control",
    "Standardized summary JSON and reporting callbacks",
  ], 1.0, 1.72, 5.35, 4.5, 14, "1B4F2E");

  s.addShape(pptx.ShapeType.roundRect, { x: 6.73, y: 1.02, w: 5.9, h: 5.5, fill: { color: "FFF4E9" }, line: { color: "F0D7B5", pt: 1 }, radius: 0.06 });
  s.addText("Deferred / Future", { x: 7.0, y: 1.3, w: 5.3, h: 0.34, fontFace: "Calibri", fontSize: 18, bold: true, color: COLORS.WARN });
  addBullets(s, [
    "Irrigation as learned action",
    "Rice-specific cultivar localization",
    "Rice-wheat finalized campaign",
    "Post-thesis rerun expansion beyond frozen 113+42 packs",
  ], 7.0, 1.72, 5.3, 4.5, 14, "6B3D00");
  finish(s);
}

// 6 Methodology
{
  const s = newSlide("Methodology Overview", "Methodology");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 1.0, w: 12.0, h: 0.95, fill: { color: "EBF2FA" }, line: { color: "C6D9ED", pt: 1 }, radius: 0.05 });
  s.addText("Objective: maximize discounted return with explicit NPK cost decomposition", {
    x: 1.0, y: 1.28, w: 11.5, h: 0.3, fontFace: "Calibri", fontSize: 16, bold: true, color: COLORS.NAVY, align: "center",
  });
  addBullets(s, [
    "Corn fertilization environment: 7-day decisions, N or NPK action channels.",
    "CropPlanningFixedPlanting: yearly crop + planting week decisions.",
    "Hierarchical environment: yearly planner plus within-season nutrient control.",
    "Reporting design keeps cost channels and compliance metrics interpretable.",
  ], 0.9, 2.25, 5.95, 4.2, 14);
  s.addImage({ path: asset("reward_decomposition_diagram.png"), ...imageSizingContain(asset("reward_decomposition_diagram.png"), 6.8, 2.05, 5.8, 2.15) });
  s.addImage({ path: asset("hierarchical_decision_diagram.png"), ...imageSizingContain(asset("hierarchical_decision_diagram.png"), 6.8, 4.3, 5.8, 2.15) });
  finish(s);
}

// 7 Architecture
{
  const s = newSlide("Current Thesis System Architecture", "Implementation");
  s.addImage({ path: asset("system_architecture_diagram.png"), ...imageSizingContain(asset("system_architecture_diagram.png"), 0.8, 1.0, 8.0, 5.8) });
  addBullets(s, [
    "Policy layer: PPO/A2C/DQN",
    "Environment layer: Corn, planning, hierarchical variants",
    "Simulation I/O: CYCLES inputs, execution, outputs",
    "Reporting layer: per-step info + per-run summary JSON",
  ], 8.95, 1.08, 3.8, 5.3, 14);
  finish(s);
}

// 8 Localization visuals
{
  const s = newSlide("Localized Economic Inputs", "Data");
  s.addImage({ path: asset("pakistan_crop_price_trends.png"), ...imageSizingContain(asset("pakistan_crop_price_trends.png"), 0.75, 1.02, 6.2, 4.9) });
  s.addImage({ path: asset("pakistan_nutrient_price_trends.png"), ...imageSizingContain(asset("pakistan_nutrient_price_trends.png"), 7.05, 1.02, 5.55, 4.9) });
  s.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 6.05, w: 12.0, h: 0.58, fill: { color: "F0F6FD" }, line: { color: "D2E1F1", pt: 1 }, radius: 0.05 });
  s.addText("Both series are consumed by Pakistan yearly price profiles used in reward calculations.", {
    x: 1.0, y: 6.24, w: 11.5, h: 0.25, fontFace: "Calibri", fontSize: 12, color: COLORS.TEXT, align: "center",
  });
  finish(s);
}

// 9 Experiment matrix
{
  const s = newSlide("Latest Broad NPK Experiment Matrix", "Evaluation Plan");
  addBullets(s, [
    "Runner: run_experiments_7_3_2026.py",
    "Total jobs encoded: 113",
    "Fertilization jobs: 75",
    "Crop-planning jobs: 38",
    "Main method: PPO, with A2C baseline and DQN ablation",
  ], 0.75, 1.15, 5.7, 4.8, 15);
  s.addImage({ path: asset("experiment_matrix_counts.png"), ...imageSizingContain(asset("experiment_matrix_counts.png"), 6.55, 1.0, 6.05, 5.2) });
  finish(s);
}

// 10 Verification logs
{
  const s = newSlide("Verification Logs and Smoke-Run Evidence", "Validation");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 1.02, w: 7.25, h: 5.65, fill: { color: "F5FAFF" }, line: { color: "CDDEEF", pt: 1 }, radius: 0.06 });
  s.addText("Verification commands (8 March 2026)", { x: 1.0, y: 1.26, w: 6.8, h: 0.3, fontFace: "Calibri", fontSize: 15, bold: true, color: COLORS.NAVY });
  addBullets(s, [
    "test_thesis_reporting: Passed",
    "test_pricing_utils: Passed",
    "test_crop_planning: Passed",
    "test_hierarchical_env: Passed",
    "build.ps1 thesis rebuild: Passed",
  ], 1.0, 1.7, 6.8, 3.2, 13);

  s.addShape(pptx.ShapeType.roundRect, { x: 8.25, y: 1.02, w: 4.45, h: 5.65, fill: { color: "EEF9F5" }, line: { color: "CBE9DC", pt: 1 }, radius: 0.06 });
  s.addText("Smoke Run", { x: 8.55, y: 1.27, w: 3.85, h: 0.3, fontFace: "Calibri", fontSize: 16, bold: true, color: COLORS.GOOD, align: "center" });
  s.addText("Run: offline_20260308_071804\nDomain: fertilization | Method: PPO\nMode: NPK, fixed weather, 1000 years", {
    x: 8.55, y: 1.7, w: 3.85, h: 1.25, fontFace: "Calibri", fontSize: 12, color: COLORS.TEXT, lineSpacingMultiple: 1.08,
  });
  s.addText("Deterministic: 1819.76\nStochastic mean: 1805.40\nStd: 17.60\nPakistan holdout: 1816.86", {
    x: 8.55, y: 3.2, w: 3.85, h: 1.8, fontFace: "Calibri", fontSize: 13, bold: true, color: "1F5A43", lineSpacingMultiple: 1.08,
  });
  finish(s);
}

// 11 Current status
{
  const s = newSlide("Final Results Status (Frozen Completed Packs)", "Results Status");
  s.addImage({ path: asset("latest_matrix_status.png"), ...imageSizingContain(asset("latest_matrix_status.png"), 0.75, 1.0, 6.3, 5.2) });
  s.addShape(pptx.ShapeType.roundRect, { x: 7.2, y: 1.0, w: 5.45, h: 5.2, fill: { color: "EEF9F5" }, line: { color: "CBE9DC", pt: 1 }, radius: 0.06 });
  s.addText("Status table", { x: 7.5, y: 1.28, w: 4.9, h: 0.3, fontFace: "Calibri", fontSize: 17, bold: true, color: COLORS.GOOD });
  addBullets(s, [
    "Final matrix rows (final_113): 113",
    "Completed final_113 jobs: 113",
    "Completed final_42_ablation jobs: 42",
    "Frozen reporting packs generated",
    "Final comparative chapter uses these completed packs",
  ], 7.5, 1.72, 4.8, 3.9, 14);
  finish(s);
}

// 12 Historical context
{
  const s = newSlide("Historical Benchmark Context (Not Final Evidence)", "Historical Context");
  s.addImage({ path: asset("historical_fertilization_scores.png"), ...imageSizingContain(asset("historical_fertilization_scores.png"), 0.75, 1.0, 6.2, 3.1) });
  s.addImage({ path: asset("historical_crop_scores.png"), ...imageSizingContain(asset("historical_crop_scores.png"), 7.05, 1.0, 5.55, 3.1) });
  s.addImage({ path: asset("historical_runtime_profile.png"), ...imageSizingContain(asset("historical_runtime_profile.png"), 0.75, 4.15, 6.2, 2.35) });
  s.addImage({ path: asset("historical_failure_signatures.png"), ...imageSizingContain(asset("historical_failure_signatures.png"), 7.05, 4.15, 5.55, 2.35) });
  finish(s);
}

// 13 Contributions
{
  const s = newSlide("Thesis Contributions", "Contributions");
  addBullets(s, [
    "Pakistan-adapted localization of weather, soil, and pricing inputs",
    "Shift from mostly N-centric to NPK-capable action/reward/reporting",
    "Hierarchical integration of yearly planning with weekly fertilization",
    "Standardized summary outputs for reproducible thesis evidence",
    "Explicit claims policy separating implemented, partial, and future work",
  ], 0.8, 1.1, 7.5, 5.0, 16);
  s.addShape(pptx.ShapeType.roundRect, { x: 8.45, y: 1.2, w: 4.2, h: 4.8, fill: { color: "ECF6F1" }, line: { color: "C8E4D8", pt: 1 }, radius: 0.07 });
  s.addText("Synopsis closure snapshot", { x: 8.7, y: 1.48, w: 3.7, h: 0.32, fontFace: "Calibri", fontSize: 15, bold: true, color: COLORS.GOOD, align: "center" });
  s.addText("Implemented: 4\nPartial: 2\nFuture: 3", {
    x: 9.0, y: 2.2, w: 3.1, h: 2.4, fontFace: "Calibri", fontSize: 20, bold: true, color: "1F5A43", lineSpacingMultiple: 1.15,
  });
  finish(s);
}

// 14 Limitations and roadmap
{
  const s = newSlide("Limitations and Future Work", "Discussion");
  addBullets(s, [
    "Field validation is not completed; evidence remains simulation-based.",
    "Working crop setup remains maize-soy.",
    "Irrigation is not yet a learned control variable.",
    "External validity remains simulation-based.",
    "Economics is cost-aware but still simplified.",
  ], 0.75, 1.05, 5.95, 4.9, 14);
  s.addImage({ path: asset("future_work_roadmap.png"), ...imageSizingContain(asset("future_work_roadmap.png"), 6.8, 1.0, 5.85, 5.2) });
  finish(s);
}

// 15 Conclusion
{
  const s = newSlide("Conclusion", "Closing");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.82, y: 1.02, w: 12.0, h: 5.8, fill: { color: "F3F7FC" }, line: { color: "CFDEEE", pt: 1 }, radius: 0.08 });
  s.addText("Final Takeaways", { x: 1.15, y: 1.36, w: 4.5, h: 0.38, fontFace: "Calibri", fontSize: 24, bold: true, color: COLORS.NAVY });
  addBullets(s, [
    "Thesis stack is materially improved and localized for Pakistan context.",
    "Engineering contributions are implemented and verification-backed.",
    "Empirical integrity is preserved by mapping claims to frozen 113 + 42 evidence packs.",
    "Next step: post-thesis extensions (irrigation, rice-focused studies, field-adjacent validation).",
  ], 1.1, 1.95, 7.2, 3.35, 16);
  s.addShape(pptx.ShapeType.roundRect, { x: 8.55, y: 1.75, w: 3.9, h: 2.45, fill: { color: "0F2B46" }, line: { color: "0F2B46", pt: 1 }, radius: 0.09 });
  s.addText("Thank you\nQuestions and discussion", {
    x: 8.82, y: 2.3, w: 3.35, h: 1.4, fontFace: "Calibri", fontSize: 17, bold: true, color: "E3EEF9", align: "center", valign: "mid", lineSpacingMultiple: 1.12,
  });
  finish(s);
}

const outputFile = path.join(__dirname, "Haider_Masood_ Final_defence.pptx");
pptx.writeFile({ fileName: outputFile });
console.log(`Generated: ${outputFile}`);
