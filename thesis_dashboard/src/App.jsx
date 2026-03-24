import React, { useEffect, useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Droplets,
  MonitorPlay,
  Search,
  TableProperties
} from 'lucide-react';

const METRIC_COLORS = {
  'rollout/ep_rew_mean': '#10b981',
  'rollout/ep_len_mean': '#f59e0b',
  deterministic_return: '#22c55e',
  stochastic_return_mean: '#14b8a6',
  stochastic_return_std: '#eab308',
  pak_holdout_return: '#a855f7',
  mean_reward: '#6366f1',
  mean_ep_length: '#fb7185',
  n_kg: '#1d4ed8',
  p_kg: '#ea580c',
  k_kg: '#16a34a',
  blocked_npk_kg: '#dc2626',
  applied_total_npk_kg: '#06b6d4',
  requested_total_npk_kg: '#a16207',
  reward: '#84cc16',
  cost_total: '#ef4444'
};

const FALLBACK_COLORS = ['#38bdf8', '#f97316', '#34d399', '#f43f5e', '#818cf8', '#facc15', '#2dd4bf', '#fb7185'];

function parseCsvLine(line) {
  const cells = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      cells.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  cells.push(current);
  return cells;
}

function coerceCsvValue(raw) {
  if (raw === undefined || raw === null) return null;
  const value = String(raw).trim();
  if (!value) return null;
  if (/^(true|false)$/i.test(value)) return value.toLowerCase() === 'true';
  if (/^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(value)) return Number(value);
  return value;
}

function parseCSV(text) {
  if (!text || text.trim().startsWith('<')) return [];
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = parseCsvLine(lines[0]).map(h => h.trim());
  return lines.slice(1).map(line => {
    const values = parseCsvLine(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header] = coerceCsvValue(values[index]);
    });
    return row;
  });
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatValue(value, maxFractionDigits = 2) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString(undefined, { maximumFractionDigits: maxFractionDigits });
  }
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  return String(value);
}

function prettyLabel(key) {
  return String(key).replaceAll('/', ' / ').replaceAll('_', ' ').replace(/\s+/g, ' ').trim();
}

function numericColumns(rows) {
  const keys = new Set();
  rows.forEach(row => {
    Object.entries(row).forEach(([key, value]) => {
      if (isFiniteNumber(value)) keys.add(key);
    });
  });
  return Array.from(keys);
}

function latestNumeric(rows, key) {
  for (let i = rows.length - 1; i >= 0; i -= 1) {
    if (isFiniteNumber(rows[i]?.[key])) return rows[i][key];
  }
  return null;
}

function metricRange(rows, key) {
  const values = rows.map(row => row[key]).filter(isFiniteNumber);
  if (!values.length) return null;
  return {
    min: Math.min(...values),
    max: Math.max(...values),
    mean: values.reduce((sum, item) => sum + item, 0) / values.length
  };
}

function getMetricColor(metric, index) {
  return METRIC_COLORS[metric] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

function StatCard({ icon, label, value, color }) {
  const Icon = icon;
  return (
    <div className="glass-panel p-4 flex flex-col gap-2 relative overflow-hidden group hover:border-[var(--color-dash-text)] transition-colors">
      <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity" style={{ color }}>
        <Icon size={76} />
      </div>
      <div className="flex items-center gap-2 text-[var(--color-dash-muted)] font-medium text-sm">
        <Icon size={16} /> {label}
      </div>
      <div className="text-3xl font-light text-white tracking-tight">{formatValue(value, 3)}</div>
    </div>
  );
}

function MetricToggleGroup({ label, options, selected, onToggle, maxSelections = 8 }) {
  if (!options.length) {
    return <p className="text-xs text-gray-500">No numeric metrics available.</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-[var(--color-dash-muted)]">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map(metric => {
          const isActive = selected.includes(metric);
          const canSelect = isActive || selected.length < maxSelections;
          return (
            <button
              key={metric}
              type="button"
              disabled={!canSelect}
              onClick={() => onToggle(metric)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                isActive
                  ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                  : 'border-[var(--color-dash-border)] text-gray-300 hover:bg-white/5'
              } ${!canSelect ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {prettyLabel(metric)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function DataTableSection({ title, rows }) {
  const [limit, setLimit] = useState(50);
  const columns = useMemo(() => {
    const set = new Set();
    rows.forEach(row => Object.keys(row).forEach(key => set.add(key)));
    return Array.from(set);
  }, [rows]);

  if (!rows.length) {
    return (
      <div className="glass-panel p-5">
        <h4 className="text-sm font-medium text-white mb-2">{title}</h4>
        <p className="text-sm text-gray-400">No rows available.</p>
      </div>
    );
  }

  const visibleRows = rows.slice(0, limit);
  return (
    <div className="glass-panel p-5 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 className="text-sm font-medium text-white">{title}</h4>
        <div className="flex items-center gap-2 text-xs text-gray-300">
          <span>Rows:</span>
          <select
            value={limit}
            onChange={event => setLimit(Number(event.target.value))}
            className="bg-[rgba(0,0,0,0.45)] border border-[var(--color-dash-border)] rounded-md px-2 py-1"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
          <span className="text-[var(--color-dash-muted)]">
            Showing {visibleRows.length} / {rows.length}
          </span>
        </div>
      </div>
      <div className="overflow-auto max-h-[420px] border border-[var(--color-dash-border)] rounded-lg">
        <table className="w-full text-xs border-collapse">
          <thead className="sticky top-0 bg-zinc-900/95">
            <tr>
              <th className="text-left p-2 border-b border-[var(--color-dash-border)]">#</th>
              {columns.map(column => (
                <th key={column} className="text-left p-2 border-b border-[var(--color-dash-border)] min-w-[140px]">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, rowIndex) => (
              <tr key={`${title}-${rowIndex}`} className="odd:bg-white/[0.02]">
                <td className="p-2 border-b border-[var(--color-dash-border)] text-gray-400">{rowIndex + 1}</td>
                {columns.map(column => (
                  <td key={`${title}-${rowIndex}-${column}`} className="p-2 border-b border-[var(--color-dash-border)] text-gray-200 align-top break-all">
                    {formatValue(row[column], 4)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function App() {
  const [runs, setRuns] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedRun, setSelectedRun] = useState(null);
  const [runData, setRunData] = useState({ history: [], npk: [], evals: [] });
  const [loadedRunSlug, setLoadedRunSlug] = useState(null);

  const [datasetFilter, setDatasetFilter] = useState('all');
  const [methodFilter, setMethodFilter] = useState('all');
  const [weatherFilter, setWeatherFilter] = useState('all');

  const [historyMetrics, setHistoryMetrics] = useState([]);
  const [historyXKey, setHistoryXKey] = useState('global_step');
  const [evalMetric, setEvalMetric] = useState('mean_reward');
  const [npkMetrics, setNpkMetrics] = useState([]);
  const [npkXKey, setNpkXKey] = useState('num_timesteps');

  useEffect(() => {
    fetch('/data/runs_index.json')
      .then(response => response.json())
      .then(data => setRuns(Array.isArray(data) ? data : []))
      .catch(error => console.error('Failed to load run index:', error));
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    const { dataset, run_slug: runSlug } = selectedRun;
    const basePath = `/data/${dataset}/${runSlug}`;
    let cancelled = false;

    Promise.all([
      fetch(`${basePath}__history_selected.csv`).then(response => (response.ok ? response.text() : '')),
      fetch(`${basePath}__weekly_npk_log.csv`).then(response => (response.ok ? response.text() : '')),
      fetch(`${basePath}__checkpoint_eval_curves.csv`).then(response => (response.ok ? response.text() : ''))
    ])
      .then(([historyCsv, npkCsv, evalCsv]) => {
        if (cancelled) return;
        setRunData({ history: parseCSV(historyCsv), npk: parseCSV(npkCsv), evals: parseCSV(evalCsv) });
        setLoadedRunSlug(runSlug);
      })
      .catch(error => {
        if (cancelled) return;
        console.error('Failed to load run payload:', error);
        setRunData({ history: [], npk: [], evals: [] });
        setLoadedRunSlug(runSlug);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRun]);

  const datasetOptions = useMemo(() => Array.from(new Set(runs.map(run => run.dataset))).sort(), [runs]);
  const methodOptions = useMemo(() => Array.from(new Set(runs.map(run => run.method))).sort(), [runs]);
  const weatherOptions = useMemo(() => Array.from(new Set(runs.map(run => run.weather_label))).sort(), [runs]);

  const filteredRuns = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return runs.filter(run => {
      if (datasetFilter !== 'all' && run.dataset !== datasetFilter) return false;
      if (methodFilter !== 'all' && run.method !== methodFilter) return false;
      if (weatherFilter !== 'all' && run.weather_label !== weatherFilter) return false;
      if (!needle) return true;
      return (
        run.run_slug.toLowerCase().includes(needle) ||
        run.group_key.toLowerCase().includes(needle) ||
        run.method.toLowerCase().includes(needle)
      );
    });
  }, [runs, search, datasetFilter, methodFilter, weatherFilter]);

  const historyNumericColumns = useMemo(() => numericColumns(runData.history), [runData.history]);
  const evalNumericColumns = useMemo(() => numericColumns(runData.evals), [runData.evals]);
  const npkNumericColumns = useMemo(() => numericColumns(runData.npk), [runData.npk]);

  const historyXOptions = useMemo(() => {
    const preferred = ['global_step', '_step', '_runtime'];
    const available = preferred.filter(key => historyNumericColumns.includes(key));
    return available.length ? available : [];
  }, [historyNumericColumns]);

  const evalMetricOptions = useMemo(() => {
    return evalNumericColumns.filter(column => column !== 'timestep');
  }, [evalNumericColumns]);

  const npkXOptions = useMemo(() => {
    const preferred = ['num_timesteps', 'operation_year', 'year', 'doy'];
    return preferred.filter(column => npkNumericColumns.includes(column));
  }, [npkNumericColumns]);

  const defaultHistoryMetrics = useMemo(() => {
    const preferred = [
      'rollout/ep_rew_mean',
      'rollout/ep_len_mean',
      'deterministic_return',
      'stochastic_return_mean',
      'pak_holdout_return'
    ];
    const defaults = preferred.filter(metric => historyNumericColumns.includes(metric));
    return defaults.length ? defaults : historyNumericColumns.slice(0, 5);
  }, [historyNumericColumns]);

  const resolvedHistoryMetrics = useMemo(() => {
    const existing = historyMetrics.filter(metric => historyNumericColumns.includes(metric));
    return existing.length ? existing : defaultHistoryMetrics;
  }, [historyMetrics, historyNumericColumns, defaultHistoryMetrics]);

  const resolvedHistoryXKey = useMemo(() => {
    if (historyXOptions.includes(historyXKey)) return historyXKey;
    return historyXOptions[0] || 'index';
  }, [historyXKey, historyXOptions]);

  const defaultEvalMetric = useMemo(() => {
    const preferred = ['mean_reward', 'std_reward', 'mean_ep_length'];
    return preferred.find(metric => evalMetricOptions.includes(metric)) || evalMetricOptions[0] || 'mean_reward';
  }, [evalMetricOptions]);

  const resolvedEvalMetric = evalMetricOptions.includes(evalMetric) ? evalMetric : defaultEvalMetric;

  const defaultNpkMetrics = useMemo(() => {
    const preferred = [
      'n_kg',
      'p_kg',
      'k_kg',
      'blocked_npk_kg',
      'applied_total_npk_kg',
      'requested_total_npk_kg',
      'cost_total',
      'reward'
    ];
    const defaults = preferred.filter(metric => npkNumericColumns.includes(metric));
    return defaults.length ? defaults.slice(0, 6) : npkNumericColumns.slice(0, 6);
  }, [npkNumericColumns]);

  const resolvedNpkMetrics = useMemo(() => {
    const existing = npkMetrics.filter(metric => npkNumericColumns.includes(metric));
    return existing.length ? existing : defaultNpkMetrics;
  }, [npkMetrics, npkNumericColumns, defaultNpkMetrics]);

  const resolvedNpkXKey = useMemo(() => {
    if (npkXOptions.includes(npkXKey)) return npkXKey;
    return npkXOptions[0] || 'index';
  }, [npkXKey, npkXOptions]);

  const loading = Boolean(selectedRun && loadedRunSlug !== selectedRun.run_slug);

  const summaryStats = useMemo(() => {
    return {
      primaryReturn: selectedRun?.primary_metric_value ?? null,
      deterministicReturn: latestNumeric(runData.history, 'deterministic_return'),
      stochasticMean: latestNumeric(runData.history, 'stochastic_return_mean'),
      holdoutReturn: latestNumeric(runData.history, 'pak_holdout_return'),
      historyRows: runData.history.length,
      evalRows: runData.evals.length,
      npkRows: runData.npk.length
    };
  }, [selectedRun, runData]);

  const historyOption = useMemo(() => {
    if (!runData.history.length || !resolvedHistoryMetrics.length) return null;
    const useXKey = resolvedHistoryXKey !== 'index' ? resolvedHistoryXKey : null;
    const series = resolvedHistoryMetrics.map((metric, seriesIndex) => {
      const points = runData.history
        .map((row, rowIndex) => {
          const y = row[metric];
          if (!isFiniteNumber(y)) return null;
          const x = useXKey && isFiniteNumber(row[useXKey]) ? row[useXKey] : rowIndex + 1;
          return [x, y];
        })
        .filter(Boolean);
      return {
        name: metric,
        type: 'line',
        data: points,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 2, color: getMetricColor(metric, seriesIndex) },
        itemStyle: { color: getMetricColor(metric, seriesIndex) }
      };
    });
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { type: 'scroll', top: 8, textStyle: { color: '#d4d4d8' } },
      grid: { left: 56, right: 28, top: 56, bottom: 56 },
      xAxis: {
        type: 'value',
        name: useXKey ? prettyLabel(useXKey) : 'Index',
        nameTextStyle: { color: '#a1a1aa' },
        axisLabel: { color: '#cbd5e1' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: { color: '#cbd5e1' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 8, textStyle: { color: '#cbd5e1' } }],
      series
    };
  }, [runData.history, resolvedHistoryMetrics, resolvedHistoryXKey]);

  const evalOption = useMemo(() => {
    if (!runData.evals.length || !resolvedEvalMetric) return null;
    const groups = Array.from(
      new Set(runData.evals.map(row => row.checkpoint_name).filter(value => typeof value === 'string' && value.length > 0))
    );
    const series = groups.map((group, groupIndex) => {
      const points = runData.evals
        .filter(row => row.checkpoint_name === group)
        .map((row, rowIndex) => {
          const y = row[resolvedEvalMetric];
          if (!isFiniteNumber(y)) return null;
          const x = isFiniteNumber(row.timestep) ? row.timestep : rowIndex + 1;
          return [x, y];
        })
        .filter(Boolean);
      return {
        name: group,
        type: 'line',
        data: points,
        showSymbol: true,
        symbolSize: 6,
        lineStyle: { width: 2, color: getMetricColor(group, groupIndex) },
        itemStyle: { color: getMetricColor(group, groupIndex) }
      };
    });
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: { trigger: 'axis', axisPointer: { type: 'line' } },
      legend: { type: 'scroll', top: 8, textStyle: { color: '#d4d4d8' } },
      grid: { left: 56, right: 28, top: 56, bottom: 56 },
      xAxis: {
        type: 'value',
        name: 'Timestep',
        nameTextStyle: { color: '#a1a1aa' },
        axisLabel: { color: '#cbd5e1' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      yAxis: {
        type: 'value',
        scale: true,
        name: prettyLabel(resolvedEvalMetric),
        nameTextStyle: { color: '#a1a1aa' },
        axisLabel: { color: '#cbd5e1' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      series
    };
  }, [runData.evals, resolvedEvalMetric]);

  const npkOption = useMemo(() => {
    if (!runData.npk.length || !resolvedNpkMetrics.length) return null;
    const useXKey = resolvedNpkXKey !== 'index' ? resolvedNpkXKey : null;
    const series = resolvedNpkMetrics.map((metric, metricIndex) => {
      const points = runData.npk
        .map((row, rowIndex) => {
          const y = row[metric];
          if (!isFiniteNumber(y)) return null;
          const x = useXKey && isFiniteNumber(row[useXKey]) ? row[useXKey] : rowIndex + 1;
          return [x, y];
        })
        .filter(Boolean);
      const isBar = metric.includes('blocked') || metric.includes('requested_total') || metric.includes('applied_total');
      return {
        name: metric,
        type: isBar ? 'bar' : 'line',
        data: points,
        showSymbol: !isBar,
        smooth: !isBar,
        barMaxWidth: 12,
        itemStyle: { color: getMetricColor(metric, metricIndex), opacity: isBar ? 0.75 : 1 },
        lineStyle: { width: 2, color: getMetricColor(metric, metricIndex) }
      };
    });
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { type: 'scroll', top: 8, textStyle: { color: '#d4d4d8' } },
      grid: { left: 56, right: 28, top: 56, bottom: 56 },
      xAxis: {
        type: 'value',
        name: useXKey ? prettyLabel(useXKey) : 'Index',
        nameTextStyle: { color: '#a1a1aa' },
        axisLabel: { color: '#cbd5e1' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: { color: '#cbd5e1' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 8, textStyle: { color: '#cbd5e1' } }],
      series
    };
  }, [runData.npk, resolvedNpkMetrics, resolvedNpkXKey]);

  const onHistoryMetricToggle = metric => {
    setHistoryMetrics(current => {
      const base = current.length ? current : resolvedHistoryMetrics;
      return base.includes(metric) ? base.filter(item => item !== metric) : [...base, metric];
    });
  };
  const onNpkMetricToggle = metric => {
    setNpkMetrics(current => {
      const base = current.length ? current : resolvedNpkMetrics;
      return base.includes(metric) ? base.filter(item => item !== metric) : [...base, metric];
    });
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="w-[420px] flex-shrink-0 glass-panel m-4 flex flex-col rounded-2xl overflow-hidden border-r-0">
        <div className="p-5 border-b border-[var(--color-dash-border)] space-y-4">
          <h1 className="text-xl font-semibold text-white flex items-center gap-2">
            <MonitorPlay size={20} className="text-blue-500" /> Thesis Dashboard
          </h1>
          <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-500" size={16} />
            <input
              type="text"
              placeholder={`Search ${runs.length} runs...`}
              className="w-full bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-lg py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              value={search}
              onChange={event => setSearch(event.target.value)}
            />
          </div>
          <div className="grid grid-cols-1 gap-2">
            <select
              value={datasetFilter}
              onChange={event => setDatasetFilter(event.target.value)}
              className="bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-md px-3 py-1.5 text-xs"
            >
              <option value="all">All datasets</option>
              {datasetOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            <select
              value={methodFilter}
              onChange={event => setMethodFilter(event.target.value)}
              className="bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-md px-3 py-1.5 text-xs"
            >
              <option value="all">All methods</option>
              {methodOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            <select
              value={weatherFilter}
              onChange={event => setWeatherFilter(event.target.value)}
              className="bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-md px-3 py-1.5 text-xs"
            >
              <option value="all">All weather modes</option>
              {weatherOptions.map(option => (
                <option key={option} value={option}>{option.replaceAll('_', ' ')}</option>
              ))}
            </select>
          </div>
          <p className="text-xs text-[var(--color-dash-muted)]">Showing {filteredRuns.length} runs</p>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {filteredRuns.map(run => (
            <button
              key={run.run_slug}
              onClick={() => setSelectedRun(run)}
              className={`w-full text-left p-4 rounded-xl border transition-all ${
                selectedRun?.run_slug === run.run_slug
                  ? 'bg-[rgba(59,130,246,0.12)] border-blue-500'
                  : 'border-transparent hover:bg-[rgba(255,255,255,0.05)]'
              }`}
            >
              <div className="text-xs text-blue-400 font-mono mb-1">
                {run.method.toUpperCase()} | {String(run.weather_label).replaceAll('_', ' ')}
              </div>
              <div className="text-sm font-medium text-white">{run.run_slug}</div>
              <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                  <Activity size={12} /> {formatValue(run.primary_metric_value, 1)}
                </span>
                <span>{run.dataset}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col p-4 pl-0 overflow-y-auto">
        {!selectedRun ? (
          <div className="h-full flex items-center justify-center text-gray-500 flex-col gap-4">
            <Activity size={48} className="opacity-20" />
            Select a run to inspect all available training, evaluation, and NPK details.
          </div>
        ) : (
          <div className="max-w-[1400px] w-full mx-auto space-y-6 pb-20">
            <div className="glass-panel p-7">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold tracking-wide uppercase">
                  {selectedRun.dataset} | {selectedRun.method}
                </span>
                <span className="px-3 py-1 rounded-full bg-sky-500/20 text-sky-300 text-xs font-semibold tracking-wide uppercase">
                  {String(selectedRun.weather_label).replaceAll('_', ' ')}
                </span>
                {selectedRun.ent_coef !== null && (
                  <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold tracking-wide uppercase">
                    Ent: {selectedRun.ent_coef}
                  </span>
                )}
                {selectedRun.cost_weight !== null && (
                  <span className="px-3 py-1 rounded-full bg-orange-500/20 text-orange-300 text-xs font-semibold tracking-wide uppercase">
                    CostW: {selectedRun.cost_weight}
                  </span>
                )}
              </div>
              <h2 className="text-2xl font-light text-white mb-1 break-all">{selectedRun.run_slug}</h2>
              <p className="text-sm text-gray-400 font-mono">GROUP: {selectedRun.group_key}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              <StatCard icon={CheckCircle2} label="Primary Return" value={summaryStats.primaryReturn} color="#22c55e" />
              <StatCard icon={BarChart3} label="Latest Deterministic" value={summaryStats.deterministicReturn} color="#14b8a6" />
              <StatCard icon={Activity} label="Latest Stochastic Mean" value={summaryStats.stochasticMean} color="#f59e0b" />
              <StatCard icon={Droplets} label="Latest Holdout Return" value={summaryStats.holdoutReturn} color="#8b5cf6" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="glass-panel p-4">
                <p className="text-xs text-[var(--color-dash-muted)] mb-1">History Rows</p>
                <p className="text-xl text-white">{summaryStats.historyRows}</p>
                <p className="text-xs text-gray-400 mt-1">{historyNumericColumns.length} numeric metrics detected</p>
              </div>
              <div className="glass-panel p-4">
                <p className="text-xs text-[var(--color-dash-muted)] mb-1">Evaluation Rows</p>
                <p className="text-xl text-white">{summaryStats.evalRows}</p>
                <p className="text-xs text-gray-400 mt-1">{evalMetricOptions.length} evaluation metrics detected</p>
              </div>
              <div className="glass-panel p-4">
                <p className="text-xs text-[var(--color-dash-muted)] mb-1">NPK Rows</p>
                <p className="text-xl text-white">{summaryStats.npkRows}</p>
                <p className="text-xs text-gray-400 mt-1">{npkNumericColumns.length} NPK numeric metrics detected</p>
              </div>
            </div>

            <div className="glass-panel p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                  <MonitorPlay size={18} /> Training Metrics Explorer
                </h3>
                {loading && <span className="text-blue-300 text-sm animate-pulse">Loading run data...</span>}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <label className="text-xs text-gray-300">X-axis</label>
                <select
                  value={resolvedHistoryXKey}
                  onChange={event => setHistoryXKey(event.target.value)}
                  className="bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-md px-3 py-1.5 text-xs"
                >
                  {historyXOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>
              <MetricToggleGroup
                label="Select up to 8 history metrics"
                options={historyNumericColumns.filter(column => !historyXOptions.includes(column))}
                selected={resolvedHistoryMetrics}
                onToggle={onHistoryMetricToggle}
                maxSelections={8}
              />
              {historyOption ? (
                <div className="h-[460px] w-full">
                  <ReactECharts option={historyOption} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge />
                </div>
              ) : (
                <p className="text-sm text-gray-400">No training history available for this run.</p>
              )}
            </div>

            <div className="glass-panel p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                  <BarChart3 size={18} /> Checkpoint Evaluation Curves
                </h3>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-300">Metric</label>
                  <select
                    value={resolvedEvalMetric}
                    onChange={event => setEvalMetric(event.target.value)}
                    className="bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-md px-3 py-1.5 text-xs"
                  >
                    {evalMetricOptions.map(option => (
                      <option key={option} value={option}>{prettyLabel(option)}</option>
                    ))}
                  </select>
                </div>
              </div>
              {evalOption ? (
                <div className="h-[400px] w-full">
                  <ReactECharts option={evalOption} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge />
                </div>
              ) : (
                <p className="text-sm text-gray-400">No checkpoint evaluation file found for this run.</p>
              )}
            </div>

            <div className="glass-panel p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                  <Droplets size={18} /> Weekly NPK / Budget / Reward Explorer
                </h3>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-300">X-axis</label>
                  <select
                    value={resolvedNpkXKey}
                    onChange={event => setNpkXKey(event.target.value)}
                    className="bg-[rgba(0,0,0,0.5)] border border-[var(--color-dash-border)] rounded-md px-3 py-1.5 text-xs"
                  >
                    {npkXOptions.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>
              </div>
              <MetricToggleGroup
                label="Select up to 8 NPK metrics"
                options={npkNumericColumns.filter(column => !npkXOptions.includes(column))}
                selected={resolvedNpkMetrics}
                onToggle={onNpkMetricToggle}
                maxSelections={8}
              />
              {npkOption ? (
                <div className="h-[420px] w-full">
                  <ReactECharts option={npkOption} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge />
                </div>
              ) : (
                <p className="text-sm text-gray-400">No weekly NPK log available for this run.</p>
              )}
            </div>

            <div className="glass-panel p-5 space-y-4">
              <h3 className="text-lg font-medium text-white flex items-center gap-2">
                <TableProperties size={18} /> Raw Data Tables (All Columns)
              </h3>
              <DataTableSection title="History Selected CSV" rows={runData.history} />
              <DataTableSection title="Checkpoint Eval Curves CSV" rows={runData.evals} />
              <DataTableSection title="Weekly NPK Log CSV" rows={runData.npk} />
            </div>

            <div className="glass-panel p-5 space-y-3">
              <h3 className="text-sm font-medium text-white">Metric Snapshot</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {resolvedHistoryMetrics.slice(0, 6).map(metric => {
                  const range = metricRange(runData.history, metric);
                  return (
                    <div key={metric} className="border border-[var(--color-dash-border)] rounded-lg p-3 bg-white/[0.02]">
                      <p className="text-xs text-blue-300 mb-1">{prettyLabel(metric)}</p>
                      {range ? (
                        <p className="text-xs text-gray-300 leading-6">
                          Min: {formatValue(range.min, 3)} | Mean: {formatValue(range.mean, 3)} | Max: {formatValue(range.max, 3)}
                        </p>
                      ) : (
                        <p className="text-xs text-gray-500">No numeric values.</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
