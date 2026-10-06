import { useState, useEffect, useMemo } from 'react'
import './index.css'

const API_BASE = 'http://localhost:3001/api';

function useAiMode() {
  const [aiMode, setAiMode] = useState(null);
  useEffect(() => {
    fetch(`${API_BASE}/status`)
      .then(r => r.json())
      .then(d => setAiMode(d.aiMode))
      .catch(() => setAiMode(false));
  }, []);
  return aiMode;
}

// ─── ICONS ────────────────────────────────────────────────────────────────────
const Icon = ({ name }) => {
  const icons = {
    dashboard: '▦',
    analytics: '◈',
    returns:   '↩',
    settings:  '⚙',
    help:      '?',
    tenant:    '🏢',
    back:      '←',
    inspect:   '🔍',
    override:  '✏',
    check:     '✓',
    arrow:     '↗',
  };
  return <span style={{fontSize:'1rem'}}>{icons[name] || '•'}</span>;
};

// ─── HELPERS ──────────────────────────────────────────────────────────────────
const countBy = (arr, key, val) => arr.filter(r => r[key] === val).length;

function dispositionColor(d) {
  if (!d) return '#f59e0b';
  if (d === 'restock') return '#3dd68c';
  if (d === 'refurbish') return '#38bdf8';
  if (d === 'liquidate' || d === 'dispose') return '#ef4444';
  return '#f59e0b';
}

// ─── DONUT SVG ────────────────────────────────────────────────────────────────
function DonutChart({ segments, size = 130, thickness = 28 }) {
  const r = (size - thickness) / 2;
  const cx = size / 2, cy = size / 2;
  const circumference = 2 * Math.PI * r;
  const total = segments.reduce((s, seg) => s + seg.value, 0) || 1;
  let offset = 0;
  return (
    <svg width={size} height={size} className="donut-svg" style={{transform:'rotate(-90deg)'}}>
      {segments.map((seg, i) => {
        const dashArray = (seg.value / total) * circumference;
        const dashOffset = circumference - offset;
        offset += dashArray;
        return (
          <circle
            key={i}
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke={seg.color}
            strokeWidth={thickness}
            strokeDasharray={`${dashArray} ${circumference - dashArray}`}
            strokeDashoffset={-circumference + (circumference - (dashOffset - dashArray))}
            strokeLinecap="butt"
            style={{transition:'stroke-dasharray 0.8s ease'}}
          />
        );
      })}
      <circle cx={cx} cy={cy} r={r - thickness/2 - 2} fill="var(--bg-card)" />
    </svg>
  );
}

// ─── BAR CHART ────────────────────────────────────────────────────────────────
function BarChart({ data, height = 160 }) {
  const max = Math.max(...data.map(d => d.value), 1);
  return (
    <div className="bar-chart" style={{height}}>
      {data.map((d, i) => (
        <div className="bar-group" key={i}>
          <div className="bar-wrap" style={{height: height - 30}}>
            <div
              className={`bar ${d.color || 'green'}`}
              style={{height: `${(d.value / max) * 100}%`, width: '100%'}}
              data-val={d.value}
            />
          </div>
          <div className="bar-label">{d.label}</div>
        </div>
      ))}
    </div>
  );
}

// ─── PROGRESS ROW ─────────────────────────────────────────────────────────────
function ProgressRow({ label, value, max, color }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="progress-row">
      <div className="progress-header">
        <span className="name">{label}</span>
        <span className="pct">{value} <span style={{color:'var(--text-dim)',fontWeight:400}}>({pct}%)</span></span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{width: `${pct}%`, background: color || 'var(--green-bright)'}} />
      </div>
    </div>
  );
}

// ─── STAT CARD ────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, icon, highlight }) {
  return (
    <div className={`stat-card${highlight ? ' highlight' : ''} animate-in`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

// ─── ANALYTICS PAGE ───────────────────────────────────────────────────────────
function AnalyticsPage({ returns }) {
  const total = returns.length;
  const completed = countBy(returns, 'status', 'completed');
  const pending = countBy(returns, 'status', 'pending_review');
  const restock = countBy(returns, 'outcome', 'restock');
  const refurbish = countBy(returns, 'outcome', 'refurbish');
  const liquidate = countBy(returns, 'outcome', 'liquidate');
  const dispose = countBy(returns, 'outcome', 'dispose');
  const noOutcome = total - restock - refurbish - liquidate - dispose;

  // Returns by SKU
  const bySku = useMemo(() => {
    const map = {};
    returns.forEach(r => {
      map[r.ordered_sku] = (map[r.ordered_sku] || 0) + 1;
    });
    return Object.entries(map)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([sku, count]) => ({ label: sku.replace('SKU-', ''), value: count, color: 'green' }));
  }, [returns]);

  // Returns by date (last 7 unique captured_at days)
  const byDate = useMemo(() => {
    const map = {};
    returns.forEach(r => {
      if (r.captured_at) {
        const day = new Date(r.captured_at).toLocaleDateString('en-US', { month:'short', day:'numeric' });
        map[day] = (map[day] || 0) + 1;
      }
    });
    return Object.entries(map)
      .slice(-7)
      .map(([label, value]) => ({ label, value, color: 'green-light' }));
  }, [returns]);

  const dispositionSegments = [
    { label: 'Restock',   value: restock,   color: '#3dd68c' },
    { label: 'Refurbish', value: refurbish,  color: '#38bdf8' },
    { label: 'Liquidate', value: liquidate,  color: '#f59e0b' },
    { label: 'Dispose',   value: dispose,    color: '#ef4444' },
    { label: 'Pending',   value: noOutcome,  color: '#334155' },
  ].filter(s => s.value > 0);

  const statusSegments = [
    { label: 'Completed', value: completed, color: '#22a84a' },
    { label: 'Pending',   value: pending,   color: '#f59e0b' },
  ];

  const recoveryRate = total > 0 ? Math.round(((restock + refurbish) / total) * 100) : 0;

  return (
    <div className="animate-in">
      {/* KPI Row */}
      <div className="stats-grid mb-6">
        <StatCard highlight label="Total Returns" value={total} icon="📦" sub={<span>All tenants combined</span>} />
        <StatCard label="Inspected" value={completed} icon="✅" sub={<span className="up">↑ {total > 0 ? Math.round((completed/total)*100) : 0}% completion rate</span>} />
        <StatCard label="Pending Review" value={pending} icon="⏳" sub={<span className="down">Awaiting AI analysis</span>} />
        <StatCard label="Recovery Rate" value={`${recoveryRate}%`} icon="♻" sub={<span className="up">Restock + Refurbish</span>} />
      </div>

      {/* Charts Row 1 */}
      <div className="charts-grid mb-6">
        {/* Returns by SKU */}
        <div className="card">
          <div className="chart-title">Returns by Product SKU</div>
          <div className="chart-sub">Volume of returns per product category</div>
          <BarChart data={bySku.length > 0 ? bySku : [{label:'No data',value:0,color:'green'}]} height={180} />
        </div>

        {/* Disposition Donut */}
        <div className="card">
          <div className="chart-title">Disposition Breakdown</div>
          <div className="chart-sub">AI-assigned outcomes</div>
          <div className="donut-container" style={{marginTop:'0.5rem'}}>
            <DonutChart segments={dispositionSegments.length > 0 ? dispositionSegments : [{value:1,color:'#1e3a27'}]} size={130} thickness={26} />
            <div className="donut-legend">
              {[
                {label:'Restock', value: restock, color:'#3dd68c'},
                {label:'Refurbish', value: refurbish, color:'#38bdf8'},
                {label:'Liquidate', value: liquidate, color:'#f59e0b'},
                {label:'Dispose', value: dispose, color:'#ef4444'},
                {label:'Pending', value: noOutcome, color:'#4d7a5e'},
              ].map((item, i) => (
                <div className="donut-legend-item" key={i}>
                  <div className="legend-dot" style={{background: item.color}} />
                  <span className="legend-label">{item.label}</span>
                  <span className="legend-value">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="charts-grid-3 mb-6">
        {/* Status Breakdown */}
        <div className="card">
          <div className="chart-title">Inspection Status</div>
          <div className="chart-sub">Completed vs pending review</div>
          <div className="donut-container" style={{marginTop:'0.5rem', justifyContent:'center', flexDirection:'column', alignItems:'center', gap:'1rem'}}>
            <DonutChart segments={statusSegments.length > 0 ? statusSegments : [{value:1,color:'#1e3a27'}]} size={110} thickness={22} />
            <div className="donut-legend" style={{width:'100%'}}>
              {statusSegments.map((s,i) => (
                <div className="donut-legend-item" key={i}>
                  <div className="legend-dot" style={{background:s.color}} />
                  <span className="legend-label">{s.label}</span>
                  <span className="legend-value">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Returns by Date */}
        <div className="card">
          <div className="chart-title">Returns Over Time</div>
          <div className="chart-sub">Daily return volume</div>
          <BarChart data={byDate.length > 0 ? byDate : [{label:'No data',value:0,color:'green-light'}]} height={160} />
        </div>

        {/* SKU Progress */}
        <div className="card">
          <div className="chart-title">Top SKU Distribution</div>
          <div className="chart-sub">Share of returns per product</div>
          <div style={{marginTop:'0.75rem'}}>
            {bySku.slice(0,5).map((d, i) => (
              <ProgressRow
                key={i}
                label={d.label}
                value={d.value}
                max={total}
                color={['#22a84a','#3dd68c','#38bdf8','#f59e0b','#ef4444'][i]}
              />
            ))}
            {bySku.length === 0 && <div className="text-muted text-sm">No data available.</div>}
          </div>
        </div>
      </div>

      {/* Recent Returns Table */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <div className="chart-title">Recent Returns</div>
            <div className="chart-sub">Latest 10 return records</div>
          </div>
        </div>
        <div className="table-container" style={{border:'none', borderRadius:0}}>
          <table>
            <thead>
              <tr>
                <th>Record ID</th>
                <th>SKU</th>
                <th>Status</th>
                <th>Disposition</th>
                <th>Captured</th>
              </tr>
            </thead>
            <tbody>
              {returns.slice(0,10).map(r => (
                <tr key={r.record_id}>
                  <td style={{fontWeight:600, color:'var(--green-glow)'}}>{r.record_id}</td>
                  <td className="text-muted">{r.ordered_sku}</td>
                  <td><span className={`badge ${r.status}`}>{r.status?.replace('_',' ')}</span></td>
                  <td>
                    {r.outcome
                      ? <span className={`badge ${r.outcome}`}>{r.outcome}</span>
                      : <span className="text-muted text-xs">—</span>}
                  </td>
                  <td className="text-sm text-muted">
                    {r.captured_at ? new Date(r.captured_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
              {returns.length === 0 && (
                <tr><td colSpan="5" style={{textAlign:'center',padding:'2rem',color:'var(--text-dim)'}}>No data available.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── DASHBOARD PAGE ───────────────────────────────────────────────────────────
function DashboardPage({ returns, onView }) {
  const total = returns.length;
  const completed = countBy(returns, 'status', 'completed');
  const pending = countBy(returns, 'status', 'pending_review');
  const restock = countBy(returns, 'outcome', 'restock');

  return (
    <div className="animate-in">
      <div className="stats-grid mb-6">
        <StatCard highlight label="Total Returns" value={total}     icon="📦" sub={<span>All records loaded</span>} />
        <StatCard label="Inspected"      value={completed} icon="✅" sub={<span className="up">↑ {total > 0 ? Math.round((completed/total)*100) : 0}% complete</span>} />
        <StatCard label="Pending Review" value={pending}   icon="⏳" sub={<span>Awaiting inspection</span>} />
        <StatCard label="Restockable"    value={restock}   icon="🔄" sub={<span className="up">↑ {total > 0 ? Math.round((restock/total)*100) : 0}% recovery</span>} />
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Record ID</th>
              <th>Unit ID</th>
              <th>SKU</th>
              <th>Status</th>
              <th>Disposition</th>
              <th>Captured</th>
            </tr>
          </thead>
          <tbody>
            {returns.map(r => (
              <tr key={r.record_id} onClick={() => onView(r.record_id)}>
                <td style={{fontWeight:600, color:'var(--green-glow)'}}>{r.record_id}</td>
                <td className="text-muted">{r.unit_id}</td>
                <td>{r.ordered_sku}</td>
                <td>
                  <span className={`badge ${r.status === 'pending_review' ? 'pending_review' : 'pass'}`}>
                    {r.status || 'pending'}
                  </span>
                </td>
                <td>
                  {r.outcome
                    ? <span className={`badge ${r.outcome}`}>{r.outcome.replace('_',' ')}</span>
                    : <span className="text-muted">—</span>}
                </td>
                <td className="text-sm text-muted">
                  {r.captured_at ? new Date(r.captured_at).toLocaleDateString() : '—'}
                </td>
              </tr>
            ))}
            {returns.length === 0 && (
              <tr>
                <td colSpan="6" style={{textAlign:'center',padding:'3rem',color:'var(--text-dim)'}}>
                  No returns found for this organization.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── INSPECTION PAGE ──────────────────────────────────────────────────────────
function InspectionPage({ recordId, tenantId, onBack }) {
  const [record, setRecord] = useState(null);
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideVerdict, setOverrideVerdict] = useState('restock');
  const [loading, setLoading] = useState(false);

  const fetchRecord = () => {
    fetch(`${API_BASE}/returns/${recordId}`, { headers: { 'x-tenant-id': tenantId } })
      .then(r => r.json()).then(setRecord).catch(console.error);
  };

  useEffect(() => { fetchRecord(); }, [recordId, tenantId]);

  const handleInspect = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/returns/inspect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': tenantId },
        body: JSON.stringify({
          record_id: record.record_id,
          subject: record.unit_id,
          sku: record.ordered_sku,
          images: record.photo_refs ? record.photo_refs.split(';') : []
        })
      });
      setRecord(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleOverride = async () => {
    if (!overrideReason) return alert('Reason required for override');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/returns/${recordId}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': tenantId },
        body: JSON.stringify({ revised_verdict: overrideVerdict, reason: overrideReason, operator_id: 'op_demo_user' })
      });
      setRecord(await res.json());
      setOverrideReason('');
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  if (!record) return <div className="text-muted" style={{padding:'2rem'}}>Loading record…</div>;

  const outcomeColor = dispositionColor(record.outcome);

  return (
    <div className="animate-in">
      <button className="secondary mb-4" onClick={onBack}>← Back to Dashboard</button>

      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 style={{fontSize:'1.6rem', fontWeight:700, color:'var(--green-glow)'}}>{record.record_id}</h2>
          <div className="text-muted text-sm mt-2">
            Unit: <strong style={{color:'var(--text-main)'}}>{record.unit_id || '—'}</strong>&ensp;|&ensp;
            Order: <strong style={{color:'var(--text-main)'}}>{record.order_id || '—'}</strong>
          </div>
        </div>
        <div>
          {record.outcome && record.outcome !== 'pending_review' ? (
            <span className={`badge ${record.outcome}`} style={{fontSize:'0.85rem', padding:'0.4rem 1rem'}}>
              Disposition: {record.outcome.replace('_',' ').toUpperCase()}
            </span>
          ) : (
            <div style={{display:'flex', gap:'1rem', alignItems:'center'}}>
              {record.outcome === 'pending_review' && (
                <span className={`badge ${record.outcome}`} style={{fontSize:'0.85rem', padding:'0.4rem 1rem'}}>
                  Disposition: PENDING REVIEW
                </span>
              )}
              <button onClick={handleInspect} disabled={loading} className="pulse">
                {loading ? '⏳ Analyzing…' : (record.outcome === 'pending_review' ? '🔄 Retry AI Inspection' : '🔍 Run AI Inspection')}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="inspection-grid">
        <div>
          {/* Product Context */}
          <div className="card mb-4">
            <div className="chart-title mb-2">Product Context</div>
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'1rem'}}>
              <div>
                <div className="text-xs text-muted mb-2" style={{textTransform:'uppercase',letterSpacing:'0.6px'}}>SKU</div>
                <div style={{fontWeight:600}}>{record.ordered_sku || '—'}</div>
              </div>
              <div>
                <div className="text-xs text-muted mb-2" style={{textTransform:'uppercase',letterSpacing:'0.6px'}}>ASIN</div>
                <div style={{fontWeight:600}}>{record.ordered_asin || '—'}</div>
              </div>
              <div>
                <div className="text-xs text-muted mb-2" style={{textTransform:'uppercase',letterSpacing:'0.6px'}}>Expected Parts</div>
                <div style={{fontWeight:600}}>{record.parts_list || '—'}</div>
              </div>
            </div>
          </div>

          {/* Evidence Images */}
          <div className="card mb-4">
            <div className="chart-title mb-4">Evidence Images</div>
            <div className="flex gap-2" style={{flexWrap:'wrap'}}>
              {record.photo_refs ? record.photo_refs.split(';').map((img, idx) => {
                const isUrl = img.startsWith('http') || img.startsWith('data:') || img.startsWith('fixtures/');
                const imgSrc = img.startsWith('fixtures/') ? `http://localhost:3001/${img}` : img;
                return (
                  <div key={idx} style={{
                    width:'120px', height:'120px',
                    background:'var(--bg-hover)',
                    borderRadius:'var(--radius)',
                    display:'flex', alignItems:'center', justifyContent:'center',
                    border:'1px dashed var(--border)', overflow:'hidden',
                    transition:'all 0.2s ease'
                  }}>
                    {isUrl ? (
                      <img
                        src={imgSrc}
                        alt="Evidence"
                        referrerPolicy="no-referrer"
                        style={{width:'100%', height:'100%', objectFit:'cover'}}
                        onError={e => {
                          e.target.style.display = 'none';
                          e.target.parentNode.innerHTML = '<span style="font-size:0.7rem;color:var(--text-dim);text-align:center;padding:0.5rem">Image unavailable</span>';
                        }}
                      />
                    ) : (
                      <span className="text-muted text-sm" style={{textAlign:'center', padding:'0.5rem'}}>
                        {img.split('/').pop()}
                      </span>
                    )}
                  </div>
                );
              }) : (
                <div className="text-muted text-sm">No evidence images uploaded.</div>
              )}
            </div>
          </div>

          {/* AI Checks */}
          {record.checks && record.checks.length > 0 && (
            <div className="card mb-4">
              <div className="chart-title mb-4">AI Inspection Verdicts</div>
              {record.checks.map((chk, idx) => (
                <div key={idx} style={{
                  padding:'1rem',
                  borderRadius:'var(--radius)',
                  background:'var(--bg-hover)',
                  marginBottom: idx < record.checks.length - 1 ? '0.75rem' : 0,
                  border:'1px solid var(--border)'
                }}>
                  <div className="flex justify-between items-center mb-2">
                    <strong style={{textTransform:'capitalize', fontSize:'0.9rem'}}>{chk.check_key}</strong>
                    <span className={`badge ${chk.verdict.toLowerCase()}`}>{chk.verdict}</span>
                  </div>
                  <div className="text-muted text-sm mb-2">{chk.detail}</div>
                  <div className="flex items-center gap-2">
                    <div style={{flex:1, height:'5px', background:'var(--bg-main)', borderRadius:'999px', overflow:'hidden'}}>
                      <div style={{
                        height:'100%', borderRadius:'999px',
                        width: `${(chk.confidence || 0) * 100}%`,
                        background: chk.verdict === 'PASS' ? 'var(--green-bright)' :
                                    chk.verdict === 'FAIL' ? 'var(--danger)' : 'var(--warning)',
                        transition:'width 0.8s ease'
                      }} />
                    </div>
                    <span className="text-xs text-muted">{Math.round((chk.confidence || 0) * 100)}% confidence</span>
                  </div>
                  {chk.model_version && (
                    <div className="text-xs" style={{color:'var(--text-dim)', marginTop:'0.4rem'}}>
                      Model: {chk.model_version} · {chk.latency_ms}ms
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Side Panel */}
        <div>
          <div className="card mb-4">
            <div className="chart-title mb-4">Human Override</div>
            <p className="text-sm text-muted mb-3" style={{lineHeight:'1.5'}}>
              {record.outcome === 'pending_review'
                ? '⚠️ AI could not reach a confident decision. Please review manually.'
                : '✅ AI has made a decision. Override below if you disagree.'}
            </p>
            {record.outcome ? (
              <div>
                <select value={overrideVerdict} onChange={e => setOverrideVerdict(e.target.value)}>
                  <option value="restock">Restock</option>
                  <option value="refurbish">Refurbish</option>
                  <option value="liquidate">Liquidate</option>
                  <option value="dispose">Dispose</option>
                  <option value="pending_review">Pending Review</option>
                </select>
                <textarea
                  placeholder="Reason for override…"
                  value={overrideReason}
                  onChange={e => setOverrideReason(e.target.value)}
                  rows={3}
                />
                <button onClick={handleOverride} disabled={loading} style={{width:'100%'}}>
                  Apply Override
                </button>
              </div>
            ) : (
              <div className="text-muted text-sm">Run AI inspection first to unlock overrides.</div>
            )}
          </div>

          <div className="card">
            <div className="chart-title mb-4">Evidence Trace</div>
            {record.overrides && record.overrides.length > 0 ? (
              <div className="timeline">
                {record.overrides.map((ov, idx) => (
                  <div key={idx} className="timeline-item text-sm">
                    <strong>Override Applied</strong> by {ov.operator_id}<br/>
                    <span className="text-muted">{new Date(ov.timestamp).toLocaleString()}</span><br/>
                    <span style={{textDecoration:'line-through', color:'var(--text-dim)'}}>{ov.original_verdict}</span>
                    {' → '}
                    <strong style={{color:'var(--green-glow)'}}>{ov.revised_verdict}</strong><br/>
                    <em style={{color:'var(--text-muted)'}}>"{ov.reason}"</em>
                  </div>
                ))}
              </div>
            ) : record.checks ? (
              <div className="text-sm text-muted">Original decision intact. No overrides.</div>
            ) : (
              <div className="text-muted text-sm">No evidence captured yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [returns, setReturns] = useState([]);
  const [activeTenant, setActiveTenant] = useState('org_demo_alpha');
  const aiMode = useAiMode();

  useEffect(() => {
    fetch(`${API_BASE}/returns`, { headers: { 'x-tenant-id': activeTenant } })
      .then(r => r.json()).then(setReturns).catch(console.error);
  }, [activeTenant, activeTab]);

  const viewInspection = (id) => {
    setSelectedRecordId(id);
    setActiveTab('inspection');
  };

  const handleTenantSwitch = (e) => {
    setActiveTenant(e.target.value);
    if (activeTab === 'inspection') setActiveTab('dashboard');
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard',  icon: '▦', badge: returns.length },
    { id: 'analytics', label: 'Analytics',  icon: '◈' },
  ];

  const pageTitle = {
    dashboard:  { title: 'Returns Dashboard', sub: 'Manage and inspect all return records' },
    analytics:  { title: 'Analytics',         sub: 'Visual insights into return patterns' },
    inspection: { title: selectedRecordId,    sub: 'AI-powered return inspection report' },
  }[activeTab] || {};

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">RM</div>
          <span>Returns AI</span>
        </div>

        <div className="sidebar-section">Menu</div>
        {navItems.map(item => (
          <button
            key={item.id}
            className={`sidebar-nav-item${activeTab === item.id ? ' active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span style={{fontSize:'1rem'}}>{item.icon}</span>
            {item.label}
            {item.badge !== undefined && (
              <span className="nav-badge">{item.badge}</span>
            )}
          </button>
        ))}

        <div className="sidebar-section" style={{marginTop:'1.5rem'}}>General</div>
        <button className="sidebar-nav-item">
          <span>⚙</span> Settings
        </button>
        <button className="sidebar-nav-item">
          <span>?</span> Help
        </button>

        {/* Tenant switcher */}
        <div className="tenant-section">
          <div className="tenant-label">Tenant Context</div>
          <select value={activeTenant} onChange={handleTenantSwitch} style={{marginBottom:0}}>
            <option value="org_demo_alpha">org_demo_alpha</option>
            <option value="org_demo_bravo">org_demo_bravo</option>
          </select>
        </div>
      </aside>

      {/* MAIN */}
      <div className="main-content">
        <header className="topbar">
          <div className="topbar-title">
            <h2>{pageTitle.title}</h2>
            <p>{pageTitle.sub}</p>
          </div>
          <div className="topbar-actions">
            {activeTab === 'inspection' && (
              <button className="secondary" onClick={() => setActiveTab('dashboard')}>
                ← Back
              </button>
            )}
            {aiMode !== null && (
              <div style={{
                background: aiMode ? 'rgba(34,168,74,0.12)' : 'rgba(239,68,68,0.12)',
                border: `1px solid ${aiMode ? 'var(--border-bright)' : '#7f1d1d'}`,
                borderRadius:'var(--radius)',
                padding:'0.35rem 0.75rem',
                fontSize:'0.75rem',
                color: aiMode ? 'var(--green-glow)' : '#fca5a5',
                fontWeight:600,
                display:'flex', alignItems:'center', gap:'0.4rem'
              }}>
                <span style={{width:8,height:8,borderRadius:'50%',display:'inline-block',background: aiMode ? 'var(--green-bright)' : '#ef4444'}} />
                {aiMode ? 'AI LIVE' : 'MOCK MODE'}
              </div>
            )}
          </div>
        </header>

        <main className="page-content">
          {activeTab === 'dashboard' && (
            <DashboardPage returns={returns} onView={viewInspection} />
          )}
          {activeTab === 'analytics' && (
            <AnalyticsPage returns={returns} />
          )}
          {activeTab === 'inspection' && (
            <InspectionPage
              recordId={selectedRecordId}
              tenantId={activeTenant}
              onBack={() => setActiveTab('dashboard')}
            />
          )}
        </main>
      </div>
    </div>
  );
}
