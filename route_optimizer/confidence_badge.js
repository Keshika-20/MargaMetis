/**
 * confidence_badge.js
 * -------------------
 * MārgaMetis — Frontend confidence display
 * Contribution by: [Your Name]
 *
 * Plug this into the existing route card render logic.
 * Takes the ConfidenceResult dict (returned from backend)
 * and injects a confidence badge + ETA range into each route card.
 *
 * Usage (inside your existing route display JS):
 *   import { renderConfidenceBadge, renderETARange } from './confidence_badge.js';
 *
 *   // After your existing route cards are rendered:
 *   routes.forEach((route, i) => {
 *     const card = document.getElementById(`route-card-${i}`);
 *     card.appendChild(renderConfidenceBadge(route.confidence_result));
 *     card.appendChild(renderETARange(route.confidence_result));
 *   });
 */


/**
 * Returns a styled confidence badge element.
 *
 * @param {Object} result - ConfidenceResult from backend
 * @param {number} result.confidence     - 0–100
 * @param {string} result.risk_level     - 'Low' | 'Medium' | 'High'
 * @param {Object} result.breakdown      - sub-scores
 * @param {Array}  result.warnings       - string[]
 * @returns {HTMLElement}
 */
export function renderConfidenceBadge(result) {
  const { confidence, risk_level, breakdown, warnings } = result;

  // Color scheme per risk level
  const colors = {
    Low:     { bg: '#e1f5ee', text: '#085041', bar: '#1D9E75' },
    Medium:  { bg: '#faeeda', text: '#633806', bar: '#EF9F27' },
    High:    { bg: '#faece7', text: '#712B13', bar: '#D85A30' },
    Unknown: { bg: '#f1efe8', text: '#444441', bar: '#888780' },
  };
  const c = colors[risk_level] || colors.Unknown;

  const wrapper = document.createElement('div');
  wrapper.style.cssText = `
    background: ${c.bg};
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 10px;
    font-family: inherit;
  `;

  // ── Header row ──────────────────────────────────────
  const header = document.createElement('div');
  header.style.cssText = 'display:flex; align-items:center; gap:10px; margin-bottom:8px;';

  const label = document.createElement('span');
  label.style.cssText = `
    font-size: 12px;
    font-weight: 500;
    color: ${c.text};
    letter-spacing: 0.02em;
  `;
  label.textContent = `${risk_level} risk`;

  const scoreText = document.createElement('span');
  scoreText.style.cssText = `
    font-size: 18px;
    font-weight: 500;
    color: ${c.text};
    margin-left: auto;
  `;
  scoreText.textContent = `${confidence.toFixed(0)}% confidence`;

  header.appendChild(label);
  header.appendChild(scoreText);
  wrapper.appendChild(header);

  // ── Progress bar ────────────────────────────────────
  const barTrack = document.createElement('div');
  barTrack.style.cssText = `
    background: rgba(0,0,0,0.08);
    border-radius: 4px;
    height: 6px;
    width: 100%;
    margin-bottom: 10px;
    overflow: hidden;
  `;
  const barFill = document.createElement('div');
  barFill.style.cssText = `
    background: ${c.bar};
    height: 100%;
    width: ${confidence}%;
    border-radius: 4px;
    transition: width 0.6s ease;
  `;
  barTrack.appendChild(barFill);
  wrapper.appendChild(barTrack);

  // ── Sub-score breakdown ─────────────────────────────
  const breakdown_items = [
    { label: 'Speed consistency', key: 'speed_consistency' },
    { label: 'Road quality',      key: 'road_quality'      },
    { label: 'Time-of-day risk',  key: 'time_risk'         },
  ];

  const breakdownGrid = document.createElement('div');
  breakdownGrid.style.cssText = `
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
    margin-bottom: 8px;
  `;

  breakdown_items.forEach(({ label: blabel, key }) => {
    const cell = document.createElement('div');
    cell.style.cssText = `
      text-align: center;
      font-size: 11px;
      color: ${c.text};
      opacity: 0.85;
    `;
    const val = document.createElement('div');
    val.style.cssText = 'font-size:15px; font-weight:500; margin-bottom:2px;';
    val.textContent = `${breakdown[key].toFixed(0)}%`;
    const lbl = document.createElement('div');
    lbl.textContent = blabel;
    cell.appendChild(val);
    cell.appendChild(lbl);
    breakdownGrid.appendChild(cell);
  });

  wrapper.appendChild(breakdownGrid);

  // ── Warnings ────────────────────────────────────────
  if (warnings && warnings.length > 0) {
    warnings.forEach(w => {
      const warn = document.createElement('div');
      warn.style.cssText = `
        font-size: 11px;
        color: ${c.text};
        opacity: 0.75;
        padding: 3px 0;
        display: flex;
        align-items: center;
        gap: 5px;
      `;
      warn.innerHTML = `<span style="font-size:13px">⚠</span> ${w}`;
      wrapper.appendChild(warn);
    });
  }

  return wrapper;
}


/**
 * Returns an ETA range element showing best-case / worst-case.
 *
 * @param {Object} result
 * @param {number} result.eta_minutes
 * @param {Array}  result.eta_range   - [optimistic, pessimistic]
 * @returns {HTMLElement}
 */
export function renderETARange(result) {
  const { eta_minutes, eta_range } = result;
  const [best, worst] = eta_range;

  const el = document.createElement('div');
  el.style.cssText = `
    font-size: 12px;
    color: var(--color-text-secondary, #666);
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  `;

  el.innerHTML = `
    <span style="font-weight:500; color:var(--color-text-primary, #222)">
      ETA: ${eta_minutes.toFixed(0)} min
    </span>
    <span style="opacity:0.6">
      (best ${best.toFixed(0)} – worst ${worst.toFixed(0)} min)
    </span>
  `;

  return el;
}