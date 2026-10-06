const { GoogleGenerativeAI } = require('@google/generative-ai');
const fs = require('fs');
const path = require('path');

/**
 * Intelligent mock that uses image count and product context to vary results.
 * Instead of always returning 0% confidence, uses heuristics so the demo
 * looks realistic even without an API key.
 */
function getMockResponse(catalogueItem, imageUrls) {
  const hasImages = imageUrls && imageUrls.length > 0;
  const productName = catalogueItem ? catalogueItem.product_name : null;
  const expectedParts = catalogueItem ? catalogueItem.expected_parts : [];
  const latency = Math.floor(Math.random() * 30) + 20;

  if (!hasImages) {
    return [
      { check_key: "identity", verdict: "UNCERTAIN", confidence: 0.1, detail: "No evidence images provided. Cannot verify product identity.", model_version: "mock_demo", latency_ms: latency },
      { check_key: "completeness", verdict: "UNCERTAIN", confidence: 0.1, detail: "No images available to verify parts: " + (expectedParts.join(', ') || 'unknown'), model_version: "mock_demo", latency_ms: latency },
      { check_key: "condition", verdict: "UNCERTAIN", confidence: 0.1, detail: "No images available to assess condition.", model_version: "mock_demo", latency_ms: latency }
    ];
  }

  // Seeded mock: vary verdicts based on product name hash for consistent demo
  const seed = productName ? productName.charCodeAt(0) % 3 : 1;
  
  const scenarios = [
    // Scenario 0: Good return - restock
    [
      { check_key: "identity", verdict: "PASS", confidence: 0.92, detail: `Visual evidence matches expected ${productName || 'product'} profile.`, model_version: "mock_demo", latency_ms: latency },
      { check_key: "completeness", verdict: "PASS", confidence: 0.88, detail: `All expected parts visible: ${expectedParts.join(', ')}.`, model_version: "mock_demo", latency_ms: latency },
      { check_key: "condition", verdict: "PASS", confidence: 0.85, detail: "Used - Like New. No visible damage or wear.", model_version: "mock_demo", latency_ms: latency }
    ],
    // Scenario 1: Damaged - refurbish/liquidate
    [
      { check_key: "identity", verdict: "PASS", confidence: 0.90, detail: `Product identified as ${productName || 'returned item'}.`, model_version: "mock_demo", latency_ms: latency },
      { check_key: "completeness", verdict: "FAIL", confidence: 0.78, detail: `Missing parts detected. Expected: ${expectedParts.join(', ')}. One or more parts not visible.`, model_version: "mock_demo", latency_ms: latency },
      { check_key: "condition", verdict: "FAIL", confidence: 0.82, detail: "Used - Acceptable. Visible wear and minor damage observed.", model_version: "mock_demo", latency_ms: latency }
    ],
    // Scenario 2: Wrong item
    [
      { check_key: "identity", verdict: "FAIL", confidence: 0.80, detail: `Returned item does not visually match expected ${productName || 'product'} SKU.`, model_version: "mock_demo", latency_ms: latency },
      { check_key: "completeness", verdict: "UNCERTAIN", confidence: 0.3, detail: "Cannot verify completeness until identity is confirmed.", model_version: "mock_demo", latency_ms: latency },
      { check_key: "condition", verdict: "UNCERTAIN", confidence: 0.3, detail: "Cannot assess condition of unexpected item.", model_version: "mock_demo", latency_ms: latency }
    ]
  ];

  return scenarios[seed];
}

/**
 * Fetch an image URL and return as base64 inline data part for Gemini.
 */
async function urlToImagePart(url) {
  if (url.startsWith('data:')) {
    const mimeType = url.split(';')[0].split(':')[1];
    const base64Data = url.split(',')[1];
    return { inlineData: { data: base64Data, mimeType } };
  }

  if (url.startsWith('fixtures/')) {
    const filePath = path.join(__dirname, '..', 'data', url);
    if (fs.existsSync(filePath)) {
      const buffer = fs.readFileSync(filePath);
      const ext = path.extname(filePath).toLowerCase();
      const mimeType = ext === '.png' ? 'image/png' : 'image/jpeg';
      return { inlineData: { data: buffer.toString('base64'), mimeType } };
    }
    return null;
  }

  if (url.startsWith('http')) {
    try {
      const resp = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
      if (resp.ok) {
        const arrayBuffer = await resp.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        const mimeType = (resp.headers.get('content-type') || 'image/jpeg').split(';')[0];
        return { inlineData: { data: buffer.toString('base64'), mimeType } };
      }
    } catch (e) {
      console.warn('Image fetch failed:', url, e.message);
    }
  }
  return null;
}

/**
 * Parse Gemini response text into a checks array.
 */
function parseChecks(text, latency) {
  // Strip markdown code fences
  let jsonStr = text.trim();
  const md = jsonStr.match(/```(?:json)?\n?([\s\S]*?)\n?```/);
  if (md) jsonStr = md[1].trim();

  // Find JSON array
  const arrStart = jsonStr.indexOf('[');
  const arrEnd = jsonStr.lastIndexOf(']');
  if (arrStart !== -1 && arrEnd !== -1) {
    jsonStr = jsonStr.substring(arrStart, arrEnd + 1);
  }

  const checks = JSON.parse(jsonStr);
  return checks.map(c => ({
    ...c,
    model_version: 'gemini-2.5-flash',
    latency_ms: latency
  }));
}

/**
 * Call Gemini with exponential backoff retry on overload.
 */
async function callGeminiWithRetry(model, contents, maxRetries = 3) {
  let lastError;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await model.generateContent(contents);
      return result.response.text();
    } catch (err) {
      lastError = err;
      const isOverloaded = err.message && (
        err.message.includes('overloaded') ||
        err.message.includes('503') ||
        err.message.includes('429') ||
        err.message.includes('RESOURCE_EXHAUSTED')
      );
      if (isOverloaded && attempt < maxRetries - 1) {
        const delay = Math.pow(2, attempt) * 1500; // 1.5s, 3s, 6s
        console.log(`Gemini overloaded, retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})...`);
        await new Promise(r => setTimeout(r, delay));
      } else {
        throw err;
      }
    }
  }
  throw lastError;
}

async function runVisionInspection(imageUrls, catalogueItem) {
  const apiKey = process.env.GEMINI_API_KEY;
  const start = Date.now();

  if (!apiKey) {
    console.log('No API key found. Running in MOCK/DEMO mode.');
    return getMockResponse(catalogueItem, imageUrls);
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    // Use an available model for this API key
    const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

    const prompt = `You are a returns inspection AI agent. Analyze the evidence images of a returned product.

Product Information:
- SKU: ${catalogueItem ? catalogueItem.sku : 'Unknown'}
- Product Name: ${catalogueItem ? catalogueItem.product_name : 'Unknown'}
- Expected Parts: ${catalogueItem ? catalogueItem.expected_parts.join(', ') : 'Unknown'}
- Description: ${catalogueItem ? catalogueItem.description : 'Unknown'}

Instructions:
1. IDENTITY check: Does the returned item visually match the expected product?
2. COMPLETENESS check: Are all expected parts visible in the images?
3. CONDITION check: Is the physical condition acceptable? (Use PASS if acceptable, FAIL if damaged). In the detail field, provide the grade using ONLY this scale: New, Renewed, Used - Like New, Used - Very Good, Used - Good, Used - Acceptable, Unacceptable.

Rules:
- Verdict must be exactly PASS, FAIL, or UNCERTAIN
- confidence is a decimal from 0.0 to 1.0
- If no images or unclear images, use UNCERTAIN with low confidence
- Be specific in the detail field about what you observe

Respond with ONLY a valid JSON array, no other text:
[
  { "check_key": "identity", "verdict": "PASS|FAIL|UNCERTAIN", "confidence": 0.0-1.0, "detail": "what you observed" },
  { "check_key": "completeness", "verdict": "PASS|FAIL|UNCERTAIN", "confidence": 0.0-1.0, "detail": "which parts visible or missing" },
  { "check_key": "condition", "verdict": "PASS|FAIL|UNCERTAIN", "confidence": 0.0-1.0, "detail": "condition grade and observations" }
]`;

    // Load image parts
    const imageParts = [];
    for (const url of (imageUrls || [])) {
      const part = await urlToImagePart(url).catch(e => { console.warn('urlToImagePart failed:', e.message); return null; });
      if (part) imageParts.push(part);
    }

    const contents = imageParts.length > 0 ? [prompt, ...imageParts] : [prompt];
    console.log(`Running Gemini inspection with ${imageParts.length} image(s)...`);

    const text = await callGeminiWithRetry(model, contents);
    console.log('Gemini raw response:', text.substring(0, 200));

    const latency = Date.now() - start;
    return parseChecks(text, latency);

  } catch (error) {
    console.error('Vision API Error:', error.message);
    const latency = Date.now() - start;
    const detail = error.message.includes('overloaded')
      ? 'Gemini API temporarily overloaded. Please retry in a moment.'
      : 'API Error: ' + error.message;
    return [
      { check_key: 'identity', verdict: 'UNCERTAIN', confidence: 0, detail, model_version: 'fail_open', latency_ms: latency },
      { check_key: 'completeness', verdict: 'UNCERTAIN', confidence: 0, detail, model_version: 'fail_open', latency_ms: latency },
      { check_key: 'condition', verdict: 'UNCERTAIN', confidence: 0, detail, model_version: 'fail_open', latency_ms: latency }
    ];
  }
}

module.exports = { runVisionInspection };
