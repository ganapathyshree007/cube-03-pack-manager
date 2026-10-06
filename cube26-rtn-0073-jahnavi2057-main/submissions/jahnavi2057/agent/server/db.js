const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const catalogue = require('./data/catalogue.json');
const returnImagesPath = path.join(__dirname, './data/return-images.json');
function getReturnImages() {
  try { return JSON.parse(fs.readFileSync(returnImagesPath, 'utf8')); }
  catch (e) { return {}; }
}

const returnsDb = new Map(); // record_id -> return object
const overridesDb = new Map(); // record_id -> array of overrides

// Load seed data if empty (simulate DB setup)
function loadSeedData() {
  const seedPath = path.join(__dirname, '../../../../data/returns_sample.csv');
  if (fs.existsSync(seedPath)) {
    const csv = fs.readFileSync(seedPath, 'utf8');
    const lines = csv.split('\n').filter(l => l.trim().length > 0);
    const headers = lines[0].split(',');
    
    for (let i = 1; i < lines.length; i++) {
      const vals = lines[i].split(',');
      if (vals.length < headers.length) continue;
      
      const record = {};
      headers.forEach((h, idx) => {
        record[h.trim()] = vals[idx].trim();
      });
      
      // Override photo_refs with URLs from return-images.json (read fresh each time)
      const returnImages = getReturnImages();
      if (Object.prototype.hasOwnProperty.call(returnImages, record.record_id)) {
        // Key exists: use the URLs list (even if empty, overrides CSV paths)
        const imageUrls = returnImages[record.record_id];
        const validUrls = imageUrls.filter(u => u && !u.includes('PASTE_IMAGE_URL'));
        record.photo_refs = validUrls.join(';');
      }
      // If key not in return-images.json at all, keep the original CSV photo_refs value

      // Seed record wrapper
      returnsDb.set(record.record_id, {
        ...record,
        org_id: record.org_id // Crucial for tenant isolation
      });
    }
  }
}

loadSeedData();

module.exports = {
  // Call this to reload images without restarting the server
  reloadSeedData: () => {
    returnsDb.clear();
    loadSeedData();
    return { reloaded: returnsDb.size };
  },

  getReturns: (tenantId) => {
    const results = [];
    for (const record of returnsDb.values()) {
      if (record.org_id === tenantId) {
        results.push(record);
      }
    }
    return results;
  },
  
  getReturn: (tenantId, recordId) => {
    const record = returnsDb.get(recordId);
    if (record && record.org_id === tenantId) return record;
    return null;
  },
  
  getCatalogueItem: (sku) => {
    return catalogue.find(c => c.sku === sku) || null;
  },
  
  saveEvidenceRecord: (tenantId, evidenceRecord) => {
    // Generate content hash
    const hash = crypto.createHash('sha256').update(JSON.stringify(evidenceRecord)).digest('hex');
    evidenceRecord.content_hash = hash;
    
    // In a real system, this would save to a separate evidence table
    // For this implementation, we append/update the main record
    const existing = returnsDb.get(evidenceRecord.record_id) || {};
    
    if (existing.org_id && existing.org_id !== tenantId) {
      throw new Error("Unauthorized tenant access during save");
    }
    
    returnsDb.set(evidenceRecord.record_id, {
      ...existing,
      ...evidenceRecord,
      org_id: tenantId // Ensure strict tenant boundary
    });
    
    return evidenceRecord;
  },
  
  saveOverride: (tenantId, recordId, overrideData) => {
    const record = returnsDb.get(recordId);
    if (!record || record.org_id !== tenantId) {
      throw new Error("Record not found or unauthorized");
    }
    
    if (!record.overrides) record.overrides = [];
    record.overrides.push(overrideData);
    
    // Hash update
    const hash = crypto.createHash('sha256').update(JSON.stringify(record)).digest('hex');
    record.content_hash = hash;
    
    returnsDb.set(recordId, record);
    return record;
  }
};
