const express = require('express');
const db = require('./db');
const { runVisionInspection } = require('./services/vision');
const determineDisposition = require('./services/disposition');
const tenantMiddleware = require('./middleware/tenant');

const router = express.Router();

// Reload endpoint — no tenant required, reloads return-images.json into memory
router.post('/reload', (req, res) => {
  const result = db.reloadSeedData();
  res.json({ message: 'Data reloaded', ...result });
});

// Status endpoint — reports whether AI mode is active
router.get('/status', (req, res) => {
  res.json({ aiMode: !!process.env.GEMINI_API_KEY });
});

// All routes below are strictly tenant-isolated
router.use(tenantMiddleware);

router.get('/returns', (req, res) => {
  const returns = db.getReturns(req.tenant);
  res.json(returns);
});

router.get('/returns/:id', (req, res) => {
  const ret = db.getReturn(req.tenant, req.params.id);
  if (!ret) return res.status(404).json({ error: "Return not found" });
  res.json(ret);
});

router.post('/returns/inspect', async (req, res) => {
  const { record_id, subject, sku, images = [] } = req.body;
  
  if (!record_id || !subject) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  // Get catalogue context
  const catalogueItem = db.getCatalogueItem(sku);

  // Run AI Inspection
  const checks = await runVisionInspection(images, catalogueItem);
  
  // Deterministic engine
  const outcome = determineDisposition(checks);
  
  // Construct evidence record exactly mapping to schema
  const evidenceRecord = {
    record_id,
    schema_version: "1.0",
    organization_id: req.tenant,
    client_id: "returns-manager-agent-01",
    agent: "Returns Manager",
    subject,
    captured_at: new Date().toISOString(),
    operator_label: "auto-agent",
    images,
    checks,
    outcome,
    overrides: [],
    status: outcome === 'pending_review' ? 'pending_review' : 'completed',
    content_hash: "" // Populated by db save
  };

  try {
    const saved = db.saveEvidenceRecord(req.tenant, evidenceRecord);
    res.json(saved);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post('/returns/:id/override', (req, res) => {
  const { revised_verdict, reason, operator_id } = req.body;
  
  if (!revised_verdict || !reason || !operator_id) {
    return res.status(400).json({ error: "Missing override details" });
  }
  
  const record = db.getReturn(req.tenant, req.params.id);
  if (!record) {
    return res.status(404).json({ error: "Record not found" });
  }

  const overrideData = {
    original_verdict: record.outcome,
    revised_verdict,
    reason,
    operator_id,
    timestamp: new Date().toISOString()
  };

  try {
    const updated = db.saveOverride(req.tenant, req.params.id, overrideData);
    // Note: The outcome itself can be updated for workflow purposes, but the original outcome
    // is preserved inside the overrides array, and checks array is untouched.
    updated.outcome = revised_verdict;
    db.saveEvidenceRecord(req.tenant, updated);
    
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
