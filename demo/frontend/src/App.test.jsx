import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import App from "./App";

function buildOptionsResponse() {
  return {
    title: { en: "Kissan Demo Advisor", urdu_hint: "hint" },
    region_note: { en: "Single region", urdu_hint: "urdu" },
    crops: [
      { value: "maize", label: "Maize", urdu_hint: "Makai" },
      { value: "soybean", label: "Soybean", urdu_hint: "Soyabean" }
    ],
    maize_stages: [
      { value: "vegetative", label: "Vegetative", urdu_hint: "hint" },
      { value: "flowering", label: "Flowering", urdu_hint: "hint" }
    ],
    soybean_stages: [
      { value: "vegetative", label: "Vegetative", urdu_hint: "hint" },
      { value: "flowering", label: "Flowering", urdu_hint: "hint" }
    ],
    soil_conditions: [
      { value: "balanced", label: "Balanced", urdu_hint: "hint" }
    ],
    recent_rain: [
      { value: "moderate", label: "Moderate rain", urdu_hint: "hint" }
    ],
    expected_weather: [
      { value: "stable", label: "Stable season", urdu_hint: "hint" },
      { value: "uncertain", label: "Uncertain season", urdu_hint: "hint" }
    ],
    languages: [
      { value: "en_pk", label: "English + Urdu hints", urdu_hint: "hint" },
      { value: "en", label: "English only", urdu_hint: "hint" }
    ]
  };
}

beforeEach(() => {
  global.fetch = vi.fn((url, options) => {
    if (url.includes("/api/v1/options")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(buildOptionsResponse())
      });
    }

    if (url.includes("/api/v1/advice/seasonal")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            summary: "Soybean is light-support only.",
            today_action: null,
            next_steps: [
              {
                title: "Season start reference",
                status: "reference",
                timing: "Start of season",
                nutrients_per_hectare_kg: { n: 10, p: 8, k: 5 },
                nutrients_per_acre_kg: { n: 4, p: 3, k: 2 },
                field_total_kg: { n: 20, p: 15, k: 10 },
                estimated_cost_pkr: 1000,
                note: "Reference"
              }
            ],
            season_estimate: {
              title: "Soybean seasonal reference",
              nutrients_per_hectare_kg: { n: 20, p: 12, k: 9 },
              nutrients_per_acre_kg: { n: 8, p: 5, k: 4 },
              field_total_kg: { n: 40, p: 24, k: 18 },
              estimated_cost_pkr: 2000,
              budget_remaining_pkr: 1000,
              budget_utilization_pct: 66
            },
            baseline_comparison: {
              baseline_label: "Fixed soybean reference schedule",
              recommended_cost_pkr: 2000,
              baseline_cost_pkr: 2400,
              cost_delta_pkr: -400,
              recommended_nutrients_per_acre_kg: { n: 8, p: 5, k: 4 },
              baseline_nutrients_per_acre_kg: { n: 7, p: 4, k: 3 },
              summary: "Seasonal reference"
            },
            warnings: ["Soybean flow is light-support only."],
            confidence: "low",
            explanation: ["One", "Two"],
            support_level: "light",
            metadata: { bundle_index: 75 }
          })
      });
    }

    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          summary: "Apply a measured NPK top-up this week.",
          today_action: {
            title: "Today's move",
            status: "do_now",
            timing: "This week",
            nutrients_per_hectare_kg: { n: 20, p: 10, k: 8 },
            nutrients_per_acre_kg: { n: 8, p: 4, k: 3 },
            field_total_kg: { n: 40, p: 20, k: 16 },
            estimated_cost_pkr: 1500,
            note: "Clamp and budget guardrails have already been applied."
          },
          next_steps: [
            {
              title: "Next check-in",
              status: "watch",
              timing: "Next week",
              nutrients_per_hectare_kg: { n: 10, p: 6, k: 4 },
              nutrients_per_acre_kg: { n: 4, p: 2, k: 2 },
              field_total_kg: { n: 20, p: 12, k: 8 },
              estimated_cost_pkr: 900,
              note: "Watch moisture."
            },
            {
              title: "Two weeks out",
              status: "watch",
              timing: "Week 3",
              nutrients_per_hectare_kg: { n: 8, p: 4, k: 2 },
              nutrients_per_acre_kg: { n: 3, p: 1.5, k: 1 },
              field_total_kg: { n: 16, p: 8, k: 4 },
              estimated_cost_pkr: 700,
              note: "Watch moisture."
            }
          ],
          season_estimate: {
            title: "Remaining season estimate",
            nutrients_per_hectare_kg: { n: 80, p: 30, k: 24 },
            nutrients_per_acre_kg: { n: 32, p: 12, k: 9.7 },
            field_total_kg: { n: 160, p: 60, k: 48 },
            estimated_cost_pkr: 6000,
            budget_remaining_pkr: 54000,
            budget_utilization_pct: 10
          },
          baseline_comparison: {
            baseline_label: "Fixed maize demo schedule",
            recommended_cost_pkr: 6000,
            baseline_cost_pkr: 7200,
            cost_delta_pkr: -1200,
            recommended_nutrients_per_acre_kg: { n: 32, p: 12, k: 9.7 },
            baseline_nutrients_per_acre_kg: { n: 30, p: 10, k: 9 },
            summary: "Recommended plan stays lighter on cost than the fixed baseline."
          },
          warnings: ["Uncertain weather uses the robust random-weather policy."],
          confidence: "medium",
          explanation: ["One", "Two", "Three"],
          support_level: "full",
          metadata: { bundle_index: 3 }
        })
    });
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("guided assistant completes on a mobile-sized viewport", async () => {
  window.innerWidth = 390;
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: /start assistant/i }));
  fireEvent.click(screen.getByRole("button", { name: /get advice/i }));

  await waitFor(() => {
    expect(screen.getByText(/today's move/i)).toBeInTheDocument();
  });

  expect(screen.getByText(/fixed maize demo schedule/i)).toBeInTheDocument();
});

test("soybean path shows seasonal reference wording", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: /start assistant/i }));
  fireEvent.click(screen.getAllByRole("button", { name: /soybean/i })[0]);
  fireEvent.click(screen.getByRole("button", { name: /soybean seasonal reference/i }));

  await waitFor(() => {
    expect(screen.getByText(/soybean seasonal reference/i)).toBeInTheDocument();
  });

  expect(screen.getAllByText(/light-support only/i).length).toBeGreaterThan(0);
});
