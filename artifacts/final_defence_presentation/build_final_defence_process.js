const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { imageSizingContain } = require("./pptxgenjs_helpers/image");
const { warnIfSlideHasOverlaps, warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Haider Masood";
pptx.company = "NUST SEECS";
pptx.subject = "Final Thesis Defence - Process Version";
pptx.title = "Haider Masood Final Defence Process Version";
pptx.lang = "en-US";
pptx.theme = { headFontFace: "Calibri", bodyFontFace: "Calibri", lang: "en-US" };

const W = 13.333;
const colors = {
  NAVY: "0F2B46",
  WHITE: "FFFFFF",
  TEXT: "1A2530",
  MUTED: "4E5D6C",
  LINE: "D9E3EE",
  PANEL: "EFF4FA",
  GREEN: "1E7A3E",
  ORANGE: "B36B00",
  RED: "B42318",
};
const asset = (n) => path.join(__dirname, "assets", n);
let page = 0;

function footer(s) {
  s.addShape(pptx.ShapeType.line, { x: 0, y: 7.06, w: W, h: 0, line: { color: colors.LINE, pt: 0.8 } });
  s.addText("Haider Masood | Process-Focused Defence Deck | March 2026", { x: 0.45, y: 7.1, w: 10.9, h: 0.22, fontFace: "Calibri", fontSize: 9, color: colors.MUTED });
  s.addText(String(page), { x: 12.15, y: 7.1, w: 0.85, h: 0.22, fontFace: "Calibri", fontSize: 10, color: colors.MUTED, align: "right" });
}

function header(s, title, section = "") {
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 0.66, fill: { color: colors.NAVY }, line: { color: colors.NAVY, pt: 0 } });
  s.addText(title, { x: 0.45, y: 0.13, w: 9.3, h: 0.36, fontFace: "Calibri", fontSize: 19, bold: true, color: colors.WHITE });
  if (section) {
    s.addText(section.toUpperCase(), { x: 10.2, y: 0.18, w: 2.7, h: 0.24, fontFace: "Calibri", fontSize: 9, bold: true, color: "B9D1E7", align: "right", charSpace: 1 });
  }
  footer(s);
}

function bullets(s, items, x, y, w, h, fs = 15, c = colors.TEXT) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i !== items.length - 1 } }));
  s.addText(runs, { x, y, w, h, fontFace: "Calibri", fontSize: fs, color: c, margin: 2, valign: "top", lineSpacingMultiple: 1.1 });
}

function done(s) {
  warnIfSlideHasOverlaps(s, pptx);
  warnIfSlideElementsOutOfBounds(s, pptx);
}

function slide(title, section = "") {
  page += 1;
  const s = pptx.addSlide();
  header(s, title, section);
  return s;
}

// 1 title
page += 1;
{
  const s = pptx.addSlide();
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 7.5, fill: { color: colors.NAVY }, line: { color: colors.NAVY, pt: 0 } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 6.52, w: W, h: 0.98, fill: { color: "0A1E33" }, line: { color: "0A1E33", pt: 0 } });
  s.addImage({ path: asset("nust-logo.png"), ...imageSizingContain(asset("nust-logo.png"), 10.82, 0.42, 2.0, 2.0) });
  s.addText("Final Defence (Process Version)", { x: 0.75, y: 1.2, w: 8.2, h: 0.7, fontFace: "Calibri", fontSize: 34, bold: true, color: colors.WHITE });
  s.addText("What I Actually Built, Verified, and Finalized", { x: 0.75, y: 2.0, w: 9.8, h: 0.8, fontFace: "Calibri", fontSize: 24, italic: true, color: "D6E6F4" });
  s.addText("Optimizing Agricultural Resource Allocation through Reinforcement Learning", { x: 0.75, y: 3.1, w: 9.9, h: 0.6, fontFace: "Calibri", fontSize: 18, color: "A7D3F2" });
  s.addText("Haider Masood (401636)\nMS Artificial Intelligence\nSupervisor: Dr. Zuhair Zafar", { x: 0.75, y: 4.25, w: 7.8, h: 1.2, fontFace: "Calibri", fontSize: 16, color: colors.WHITE, lineSpacingMultiple: 1.1 });
  s.addText("Department of Computing, NUST SEECS | March 2026", { x: 0.75, y: 6.83, w: 10.5, h: 0.34, fontFace: "Calibri", fontSize: 12, color: "B8CADC" });
  s.addText(String(page), { x: 12.15, y: 7.1, w: 0.85, h: 0.22, fontFace: "Calibri", fontSize: 10, color: "B8CADC", align: "right" });
  done(s);
}

// 2 agenda
{
  const s = slide("Agenda: Real Work and Real Status", "Agenda");
  bullets(s, [
    "Starting point: what existed before thesis customization",
    "Implementation phases and what changed in each phase",
    "Verification trail: tests, smoke runs, and generated artifacts",
    "How to interpret old 'fresh 113-job campaign pending' text",
    "What worked, what remains limited, and why",
    "Next steps beyond finalized thesis evidence",
  ], 0.9, 1.1, 11.6, 5.6, 20);
  done(s);
}

// 3 starting point
{
  const s = slide("Starting Point vs Thesis Target", "Context");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 1.05, w: 5.9, h: 5.5, fill: { color: "F4F8FD" }, line: { color: "D6E3F1", pt: 1 }, radius: 0.06 });
  s.addText("Original Base", { x: 1.0, y: 1.32, w: 5.4, h: 0.32, fontFace: "Calibri", fontSize: 18, bold: true, color: colors.NAVY });
  bullets(s, [
    "CyclesGym core envs and training scripts",
    "General simulator integration",
    "No thesis-specific evidence discipline",
    "Limited localization depth for Pakistan narrative",
  ], 1.0, 1.75, 5.3, 3.9, 14);

  s.addShape(pptx.ShapeType.roundRect, { x: 6.7, y: 1.05, w: 5.9, h: 5.5, fill: { color: "EAF7F0" }, line: { color: "C6E6D5", pt: 1 }, radius: 0.06 });
  s.addText("Thesis Target", { x: 6.95, y: 1.32, w: 5.3, h: 0.32, fontFace: "Calibri", fontSize: 18, bold: true, color: colors.GREEN });
  bullets(s, [
    "Pakistan-adapted weather/soil/pricing stack",
    "NPK-aware reward and reporting support",
    "Hierarchical planning + fertilization integration",
    "Clear implemented-vs-future evidence policy",
  ], 6.95, 1.75, 5.3, 3.9, 14, "1A5C42");
  done(s);
}

// 4 phase timeline
{
  const s = slide("What I Actually Did: 5 Implementation Phases", "Process");
  const titles = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"];
  const desc = [
    "Pakistan crop-calendar alignment",
    "Price localization + NPK scaffolding",
    "Hierarchical integration",
    "Reporting and artifact hardening",
    "Final NPK run-readiness checks",
  ];
  for (let i = 0; i < 5; i++) {
    const x = 0.55 + i * 2.55;
    s.addShape(pptx.ShapeType.roundRect, { x, y: 1.28, w: 2.35, h: 5.0, fill: { color: i % 2 === 0 ? "ECF3FB" : "F4F8FD" }, line: { color: "BFD4E8", pt: 1 }, radius: 0.06 });
    s.addText(titles[i], { x: x + 0.12, y: 1.5, w: 2.1, h: 0.26, fontFace: "Calibri", fontSize: 13, bold: true, color: colors.NAVY, align: "center" });
    s.addText(desc[i], { x: x + 0.12, y: 1.88, w: 2.1, h: 1.2, fontFace: "Calibri", fontSize: 13, bold: true, color: colors.TEXT, align: "center", lineSpacingMultiple: 1.05 });
  }
  done(s);
}

// 5 architecture
{
  const s = slide("System I Ended Up Building", "System");
  s.addImage({ path: asset("system_architecture_diagram.png"), ...imageSizingContain(asset("system_architecture_diagram.png"), 0.8, 1.02, 8.0, 5.8) });
  bullets(s, [
    "SB3 policies drive environment actions",
    "Environment writes simulator files and invokes CYCLES",
    "Outputs are parsed to observations and reward components",
    "Reporting layer captures explainable per-run artifacts",
  ], 8.95, 1.1, 3.7, 5.3, 14);
  done(s);
}

// 6 verification
{
  const s = slide("How I Verified It Works", "Verification");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 1.02, w: 7.2, h: 5.65, fill: { color: "F5FAFF" }, line: { color: "CDDEEF", pt: 1 }, radius: 0.06 });
  s.addText("Passing checks (March 8, 2026)", { x: 1.0, y: 1.28, w: 6.8, h: 0.32, fontFace: "Calibri", fontSize: 15, bold: true, color: colors.NAVY });
  bullets(s, [
    "test_thesis_reporting",
    "test_pricing_utils",
    "test_crop_planning",
    "test_hierarchical_env",
    "LaTeX thesis build pipeline",
  ], 1.0, 1.72, 6.7, 3.1, 14);

  s.addShape(pptx.ShapeType.roundRect, { x: 8.2, y: 1.02, w: 4.5, h: 5.65, fill: { color: "EEF9F5" }, line: { color: "CBE9DC", pt: 1 }, radius: 0.06 });
  s.addText("Smoke Run Evidence", { x: 8.5, y: 1.28, w: 3.9, h: 0.3, fontFace: "Calibri", fontSize: 16, bold: true, color: colors.GREEN, align: "center" });
  s.addText("offline_20260308_071804\nPPO | fertilization | NPK\nfixed weather | 1000 years", { x: 8.55, y: 1.7, w: 3.9, h: 1.3, fontFace: "Calibri", fontSize: 12, color: colors.TEXT, lineSpacingMultiple: 1.08 });
  s.addText("Deterministic: 1819.76\nStochastic mean: 1805.40\nStd: 17.60\nPK holdout: 1816.86", { x: 8.55, y: 3.2, w: 3.9, h: 1.8, fontFace: "Calibri", fontSize: 13, bold: true, color: "1F5A43", lineSpacingMultiple: 1.08 });
  done(s);
}

// 7 matrix status
{
  const s = slide("Final Matrix Status (Completed Frozen Runs)", "Status");
  s.addImage({ path: asset("latest_matrix_status.png"), ...imageSizingContain(asset("latest_matrix_status.png"), 0.75, 1.0, 6.25, 5.2) });
  s.addShape(pptx.ShapeType.roundRect, { x: 7.2, y: 1.0, w: 5.45, h: 5.2, fill: { color: "EEF9F5" }, line: { color: "CBE9DC", pt: 1 }, radius: 0.06 });
  s.addText("Numbers", { x: 7.5, y: 1.27, w: 4.8, h: 0.3, fontFace: "Calibri", fontSize: 17, bold: true, color: colors.GREEN });
  bullets(s, [
    "Final matrix jobs in final_113: 113",
    "Completed final_113 jobs: 113",
    "Completed final_42_ablation jobs: 42",
    "Frozen reporting packs generated and archived",
  ], 7.5, 1.7, 4.8, 2.8, 14);
  s.addShape(pptx.ShapeType.roundRect, { x: 7.5, y: 4.8, w: 4.8, h: 1.2, fill: { color: "EAF7F0" }, line: { color: "CBE8D9", pt: 1 }, radius: 0.06 });
  s.addText("Final broad comparison is backed by frozen completed runs.", { x: 7.75, y: 5.14, w: 4.3, h: 0.55, fontFace: "Calibri", fontSize: 13, bold: true, color: colors.GREEN, align: "center" });
  done(s);
}

// 8 phrase explanation
{
  const s = slide("What This Old Phrase Means", "Clarification");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.85, y: 1.15, w: 11.7, h: 1.1, fill: { color: "E9F1FB" }, line: { color: "C8DDF2", pt: 1 }, radius: 0.06 });
  s.addText("Old phrase: 'Fresh 113-job campaign is pending for final comparative chapter'", { x: 1.1, y: 1.5, w: 11.2, h: 0.32, fontFace: "Calibri", fontSize: 18, bold: true, color: colors.NAVY, align: "center" });

  bullets(s, [
    "That statement came from an older provisional extraction snapshot.",
    "Canonical final evidence now comes from completed final_113 and final_42_ablation folders.",
    "Final comparative claims should be built from those frozen reporting packs.",
    "Old pending wording should not override the finalized run directories.",
  ], 1.0, 2.75, 11.3, 3.3, 16);

  s.addShape(pptx.ShapeType.roundRect, { x: 1.0, y: 6.15, w: 11.3, h: 0.5, fill: { color: "EAF7F0" }, line: { color: "CBE8D9", pt: 1 }, radius: 0.06 });
  s.addText("Simple version: planning and full execution are both complete; use the frozen final packs.", { x: 1.2, y: 6.28, w: 10.9, h: 0.24, fontFace: "Calibri", fontSize: 13, color: "1A5C42", align: "center" });
  done(s);
}

// 9 historical context
{
  const s = slide("Historical Runs: Context, Not Canonical Final Pack", "Context");
  s.addImage({ path: asset("historical_fertilization_scores.png"), ...imageSizingContain(asset("historical_fertilization_scores.png"), 0.75, 1.0, 6.2, 3.1) });
  s.addImage({ path: asset("historical_crop_scores.png"), ...imageSizingContain(asset("historical_crop_scores.png"), 7.05, 1.0, 5.55, 3.1) });
  s.addImage({ path: asset("historical_runtime_profile.png"), ...imageSizingContain(asset("historical_runtime_profile.png"), 0.75, 4.18, 6.2, 2.3) });
  s.addImage({ path: asset("historical_failure_signatures.png"), ...imageSizingContain(asset("historical_failure_signatures.png"), 7.05, 4.18, 5.55, 2.3) });
  done(s);
}

// 10 what worked
{
  const s = slide("What Worked Well", "Outcomes");
  bullets(s, [
    "Localization pipeline became coherent (weather, soil, yearly pricing).",
    "NPK-aware reward and reporting integrated across modules.",
    "Hierarchical environment implemented with report-rich outputs.",
    "Verification discipline improved confidence (tests + smoke runs).",
    "Thesis narrative became honest about implemented vs future scope.",
  ], 0.9, 1.15, 11.6, 5.2, 18, "1A5C42");
  done(s);
}

// 11 what did not
{
  const s = slide("What Is Still Limited", "Gaps");
  bullets(s, [
    "No field validation yet, so evidence remains simulation-bounded.",
    "Irrigation as learned action still not implemented in active flow.",
    "Rice-specific finalized localization/campaign is deferred.",
    "Large matrix reruns are compute-intensive and expensive in wall-clock time.",
    "Some old markdown and extracted-status notes had drift and needed correction.",
  ], 0.9, 1.15, 11.6, 5.2, 17, "7A2E1C");
  done(s);
}

// 12 next steps
{
  const s = slide("Next Steps Beyond Final Thesis Evidence", "Roadmap");
  s.addImage({ path: asset("future_work_roadmap.png"), ...imageSizingContain(asset("future_work_roadmap.png"), 6.7, 1.0, 5.95, 5.2) });
  bullets(s, [
    "Keep final_113 and final_42_ablation immutable as thesis evidence baselines.",
    "Add irrigation/rice-focused experiments as post-thesis extension packs.",
    "Document compute budgets and reproducibility scripts for reruns.",
    "Plan field-adjacent validation with agronomy stakeholders.",
    "Maintain strict implemented-vs-future claim boundaries.",
  ], 0.8, 1.1, 5.7, 5.0, 15);
  done(s);
}

// 13 doc updates done
{
  const s = slide("Repo Documentation Alignment Completed", "Docs");
  bullets(s, [
    "Active docs rewritten to match completed final frozen run status.",
    "Stale 'pending fresh campaign' wording removed from active surfaces.",
    "Added comprehensive noob guide: noobs_guide_to_the_whole_work.md.",
    "Report markdowns aligned to final completed evidence packs.",
    "Demo docs updated with thesis-boundary disclaimer and final status.",
  ], 0.9, 1.2, 11.6, 5.2, 16);
  done(s);
}

// 14 conclusion
{
  const s = slide("Conclusion", "Closing");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.82, y: 1.02, w: 12.0, h: 5.8, fill: { color: "F3F7FC" }, line: { color: "CFDEEE", pt: 1 }, radius: 0.08 });
  s.addText("Final Message", { x: 1.1, y: 1.35, w: 4.5, h: 0.4, fontFace: "Calibri", fontSize: 24, bold: true, color: colors.NAVY });
  bullets(s, [
    "The core thesis engineering work is real, deep, and verified.",
    "The evidence policy is intentionally strict to avoid over-claiming.",
    "The comparative chapter is now supported by completed frozen runs (113 + 42).",
    "Remaining work is post-thesis extension: irrigation, rice, and field validation.",
  ], 1.1, 1.95, 7.1, 2.9, 17);
  s.addShape(pptx.ShapeType.roundRect, { x: 8.55, y: 1.75, w: 3.9, h: 2.4, fill: { color: "0F2B46" }, line: { color: "0F2B46", pt: 1 }, radius: 0.09 });
  s.addText("Thank you\nQuestions?", { x: 8.8, y: 2.25, w: 3.4, h: 1.2, fontFace: "Calibri", fontSize: 20, bold: true, color: "E3EEF9", align: "center", valign: "mid" });
  done(s);
}

const out = path.join(__dirname, "Haider_Masood_ Final_defence_process_version.pptx");
pptx.writeFile({ fileName: out });
console.log(`Generated: ${out}`);
