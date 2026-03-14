import { useEffect, useState } from "react";

import { fetchDailyAdvice, fetchOptions, fetchSeasonalAdvice } from "./api";

const initialForm = {
  crop: "maize",
  crop_stage: "vegetative",
  land_area_acres: "5",
  budget_pkr: "120000",
  prior_fertilizer: {
    n_kg_per_acre: "0",
    p_kg_per_acre: "0",
    k_kg_per_acre: "0"
  },
  soil_condition: "balanced",
  recent_rain: "moderate",
  expected_weather: "uncertain",
  language: "en_pk"
};

function formatKg(value) {
  return `${Number(value ?? 0).toFixed(1)} kg`;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0
  }).format(Number(value ?? 0));
}

function ChoiceGroup({ title, hint, options, value, onSelect }) {
  return (
    <section className="question-card">
      <header className="question-head">
        <div>
          <p className="eyebrow">{title}</p>
          {hint ? <p className="urdu-hint">{hint}</p> : null}
        </div>
      </header>
      <div className="chip-row">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`choice-chip ${value === option.value ? "is-active" : ""}`}
            onClick={() => onSelect(option.value)}
            aria-pressed={value === option.value}
          >
            <span>{option.label}</span>
            <small>{option.urdu_hint}</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function StatCard({ label, value, note }) {
  return (
    <article className="stat-card">
      <p className="stat-label">{label}</p>
      <strong className="stat-value">{value}</strong>
      {note ? <p className="stat-note">{note}</p> : null}
    </article>
  );
}

function ActionCard({ action }) {
  return (
    <article className="action-card">
      <div className="action-header">
        <div>
          <p className="eyebrow">{action.title}</p>
          <h4>{action.timing}</h4>
        </div>
        <span className={`status-pill status-${action.status}`}>{action.status.replace("_", " ")}</span>
      </div>
      <div className="nutrient-grid">
        <StatCard label="N / acre" value={formatKg(action.nutrients_per_acre_kg.n)} />
        <StatCard label="P / acre" value={formatKg(action.nutrients_per_acre_kg.p)} />
        <StatCard label="K / acre" value={formatKg(action.nutrients_per_acre_kg.k)} />
      </div>
      <div className="nutrient-grid compact">
        <StatCard label="Field cost" value={formatMoney(action.estimated_cost_pkr)} />
        <StatCard label="Field total NPK" value={`${formatKg(action.field_total_kg.n)} / ${formatKg(action.field_total_kg.p)} / ${formatKg(action.field_total_kg.k)}`} />
      </div>
      <p className="support-note">{action.note}</p>
    </article>
  );
}

function ResultPanel({ result, form, onRefreshSeasonal }) {
  const isSoybeanLight = result.support_level === "light";

  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-hero">
        <div>
          <p className="eyebrow">{isSoybeanLight ? "Seasonal reference" : "Today's recommendation"}</p>
          <h2>{result.summary}</h2>
        </div>
        <span className={`confidence-chip confidence-${result.confidence}`}>{result.confidence} confidence</span>
      </div>

      {result.warnings.length ? (
        <div className="warning-row">
          {result.warnings.map((warning) => (
            <span key={warning} className="warning-pill">
              {warning}
            </span>
          ))}
        </div>
      ) : null}

      <div className="result-grid">
        <div className="result-main">
          {result.today_action ? (
            <ActionCard action={result.today_action} />
          ) : (
            <article className="action-card reference-only">
              <p className="eyebrow">Light support only</p>
              <h4>Soybean seasonal reference</h4>
              <p className="support-note">
                The soybean path is shown as a seasonal reference card, not a daily fertilizer instruction.
              </p>
              <button type="button" className="secondary-button" onClick={onRefreshSeasonal}>
                Refresh soybean seasonal card
              </button>
            </article>
          )}

          <section className="timeline-card">
            <div className="section-header">
              <div>
                <p className="eyebrow">Next steps</p>
                <h3>{isSoybeanLight ? "Reference checkpoints" : "Guided follow-up"}</h3>
              </div>
            </div>
            <div className="step-grid">
              {result.next_steps.map((action) => (
                <ActionCard key={`${action.title}-${action.timing}`} action={action} />
              ))}
            </div>
          </section>
        </div>

        <aside className="result-side">
          <article className="summary-card">
            <p className="eyebrow">Season estimate</p>
            <h3>{result.season_estimate.title}</h3>
            <div className="nutrient-grid">
              <StatCard label="N / acre" value={formatKg(result.season_estimate.nutrients_per_acre_kg.n)} />
              <StatCard label="P / acre" value={formatKg(result.season_estimate.nutrients_per_acre_kg.p)} />
              <StatCard label="K / acre" value={formatKg(result.season_estimate.nutrients_per_acre_kg.k)} />
            </div>
            <div className="nutrient-grid compact">
              <StatCard label="Field cost" value={formatMoney(result.season_estimate.estimated_cost_pkr)} />
              <StatCard
                label="Budget left"
                value={formatMoney(result.season_estimate.budget_remaining_pkr)}
                note={`${result.season_estimate.budget_utilization_pct}% of remaining budget`}
              />
            </div>
          </article>

          {result.baseline_comparison ? (
            <article className="summary-card compare-card">
              <p className="eyebrow">Compare plan</p>
              <h3>{result.baseline_comparison.baseline_label}</h3>
              <div className="compare-row">
                <span>Recommended</span>
                <strong>{formatMoney(result.baseline_comparison.recommended_cost_pkr)}</strong>
              </div>
              <div className="compare-row">
                <span>Baseline</span>
                <strong>{formatMoney(result.baseline_comparison.baseline_cost_pkr)}</strong>
              </div>
              <div className="compare-row accent">
                <span>Delta</span>
                <strong>{formatMoney(result.baseline_comparison.cost_delta_pkr)}</strong>
              </div>
              <p className="support-note">{result.baseline_comparison.summary}</p>
            </article>
          ) : null}

          <article className="summary-card">
            <p className="eyebrow">Why this answer</p>
            <ul className="explanation-list">
              {result.explanation.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <details className="evidence-panel">
              <summary>Model evidence</summary>
              <pre>{JSON.stringify(result.metadata, null, 2)}</pre>
            </details>
          </article>

          <article className="summary-card">
            <p className="eyebrow">Current scenario</p>
            <div className="scenario-grid">
              <span>{form.crop}</span>
              <span>{form.crop_stage.replace("_", " ")}</span>
              <span>{form.soil_condition}</span>
              <span>{form.recent_rain}</span>
            </div>
          </article>
        </aside>
      </div>
    </section>
  );
}

export default function App() {
  const [options, setOptions] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [started, setStarted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchOptions()
      .then((payload) => {
        if (!cancelled) {
          setOptions(payload);
        }
      })
      .catch((fetchError) => {
        if (!cancelled) {
          setError(fetchError.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const cropStages = form.crop === "soybean" ? options?.soybean_stages ?? [] : options?.maize_stages ?? [];

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function updatePrior(field, value) {
    setForm((current) => ({
      ...current,
      prior_fertilizer: {
        ...current.prior_fertilizer,
        [field]: value
      }
    }));
  }

  async function handleAdviceRequest(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...form,
        land_area_acres: Number(form.land_area_acres),
        budget_pkr: Number(form.budget_pkr),
        prior_fertilizer: {
          n_kg_per_acre: Number(form.prior_fertilizer.n_kg_per_acre),
          p_kg_per_acre: Number(form.prior_fertilizer.p_kg_per_acre),
          k_kg_per_acre: Number(form.prior_fertilizer.k_kg_per_acre)
        }
      };
      const response = await fetchDailyAdvice(payload);
      setResult(response);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSeasonalRefresh() {
    setLoading(true);
    setError("");
    try {
      const response = await fetchSeasonalAdvice({
        crop: "soybean",
        land_area_acres: Number(form.land_area_acres),
        budget_pkr: Number(form.budget_pkr),
        language: form.language
      });
      setResult(response);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="background-orb orb-left" />
      <div className="background-orb orb-right" />

      <header className="hero-panel">
        <div>
          <p className="eyebrow">Farmer-first thesis MVP</p>
          <h1>{options?.title.en ?? "Kissan Demo Advisor"}</h1>
          <p className="hero-copy">
            A mobile-first local demo that turns audited RL runs into clear field actions for maize and seasonal
            reference cards for soybean.
          </p>
          <div className="hero-badges">
            <span>Single demo region</span>
            <span>English + Urdu hints</span>
            <span>NPK budget guardrails</span>
          </div>
        </div>
        <aside className="hero-note">
          <p>{options?.region_note.en ?? "Loading region note..."}</p>
          {form.language === "en_pk" && options?.region_note.urdu_hint ? <small>{options.region_note.urdu_hint}</small> : null}
          <button type="button" className="primary-button" onClick={() => setStarted(true)}>
            Start assistant
          </button>
        </aside>
      </header>

      <main className="content-grid">
        <form className="assistant-panel" onSubmit={handleAdviceRequest}>
          <div className="section-header">
            <div>
              <p className="eyebrow">Guided chat-form</p>
              <h2>Tell the app about the current field</h2>
            </div>
            {loading ? <span className="loading-badge">Running local inference...</span> : null}
          </div>

          {!started ? (
            <article className="summary-card start-card">
              <p>Press “Start assistant” to open the guided form.</p>
            </article>
          ) : null}

          <ChoiceGroup
            title="1. Which crop are you managing?"
            hint={form.language === "en_pk" ? "Crop select karein" : ""}
            options={options?.crops ?? []}
            value={form.crop}
            onSelect={(value) => {
              updateField("crop", value);
              updateField("crop_stage", value === "soybean" ? "vegetative" : "vegetative");
            }}
          />

          <ChoiceGroup
            title="2. What stage is the crop in?"
            hint={form.language === "en_pk" ? "Fasal ka marhala choose karein" : ""}
            options={cropStages}
            value={form.crop_stage}
            onSelect={(value) => updateField("crop_stage", value)}
          />

          <section className="question-card">
            <header className="question-head">
              <div>
                <p className="eyebrow">3. Field size and budget</p>
                {form.language === "en_pk" ? <p className="urdu-hint">Zameen aur budget details</p> : null}
              </div>
            </header>
            <div className="input-grid">
              <label className="input-field">
                <span>Land area (acres)</span>
                <input
                  type="number"
                  min="0.5"
                  step="0.5"
                  value={form.land_area_acres}
                  onChange={(event) => updateField("land_area_acres", event.target.value)}
                />
              </label>
              <label className="input-field">
                <span>Budget (PKR)</span>
                <input
                  type="number"
                  min="1000"
                  step="1000"
                  value={form.budget_pkr}
                  onChange={(event) => updateField("budget_pkr", event.target.value)}
                />
              </label>
            </div>
          </section>

          <section className="question-card">
            <header className="question-head">
              <div>
                <p className="eyebrow">4. What has already been applied?</p>
                {form.language === "en_pk" ? <p className="urdu-hint">Pehle se diya gaya fertilizer</p> : null}
              </div>
            </header>
            <div className="input-grid triple-grid">
              <label className="input-field">
                <span>N / acre</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.prior_fertilizer.n_kg_per_acre}
                  onChange={(event) => updatePrior("n_kg_per_acre", event.target.value)}
                />
              </label>
              <label className="input-field">
                <span>P / acre</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.prior_fertilizer.p_kg_per_acre}
                  onChange={(event) => updatePrior("p_kg_per_acre", event.target.value)}
                />
              </label>
              <label className="input-field">
                <span>K / acre</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.prior_fertilizer.k_kg_per_acre}
                  onChange={(event) => updatePrior("k_kg_per_acre", event.target.value)}
                />
              </label>
            </div>
          </section>

          <ChoiceGroup
            title="5. How does the soil feel?"
            hint={form.language === "en_pk" ? "Mitti ki halat" : ""}
            options={options?.soil_conditions ?? []}
            value={form.soil_condition}
            onSelect={(value) => updateField("soil_condition", value)}
          />

          <ChoiceGroup
            title="6. How much recent rain did you get?"
            hint={form.language === "en_pk" ? "Haal ki barish" : ""}
            options={options?.recent_rain ?? []}
            value={form.recent_rain}
            onSelect={(value) => updateField("recent_rain", value)}
          />

          <ChoiceGroup
            title="7. What season outlook should the app assume?"
            hint={form.language === "en_pk" ? "Mausami soorat-e-haal" : ""}
            options={options?.expected_weather ?? []}
            value={form.expected_weather}
            onSelect={(value) => updateField("expected_weather", value)}
          />

          <ChoiceGroup
            title="8. Choose your interface language"
            hint={form.language === "en_pk" ? "Language setting" : ""}
            options={options?.languages ?? []}
            value={form.language}
            onSelect={(value) => updateField("language", value)}
          />

          <div className="cta-row">
            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? "Working..." : "Get advice"}
            </button>
            <button type="button" className="secondary-button" onClick={handleSeasonalRefresh} disabled={loading}>
              Soybean seasonal reference
            </button>
          </div>

          {error ? <p className="error-banner">{error}</p> : null}
        </form>

        <aside className="summary-rail">
          <article className="summary-card">
            <p className="eyebrow">Current setup</p>
            <h3>{form.crop === "maize" ? "Maize daily mode" : "Soybean light mode"}</h3>
            <div className="scenario-grid">
              <span>{form.crop}</span>
              <span>{form.crop_stage.replace("_", " ")}</span>
              <span>{form.soil_condition}</span>
              <span>{form.expected_weather}</span>
            </div>
            <p className="support-note">
              The app keeps the RL policy local, then adds budget and moisture guardrails before showing advice.
            </p>
          </article>

          <article className="summary-card">
            <p className="eyebrow">Why this UI</p>
            <ul className="explanation-list compact">
              <li>Large tap targets for field use.</li>
              <li>English-first copy with Urdu helper text.</li>
              <li>Comparison card to build trust instead of blind automation.</li>
            </ul>
          </article>
        </aside>
      </main>

      {result ? <ResultPanel result={result} form={form} onRefreshSeasonal={handleSeasonalRefresh} /> : null}
    </div>
  );
}
