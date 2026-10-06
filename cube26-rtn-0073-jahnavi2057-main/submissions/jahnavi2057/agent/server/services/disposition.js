module.exports = function determineDisposition(checks) {
  const identity    = checks.find(c => c.check_key === 'identity');
  const completeness = checks.find(c => c.check_key === 'completeness');
  const condition   = checks.find(c => c.check_key === 'condition');

  // Only UNCERTAIN means AI genuinely cannot decide — escalate to human
  if (!identity    || identity.verdict    === 'UNCERTAIN') return 'pending_review';
  if (!completeness || completeness.verdict === 'UNCERTAIN') return 'pending_review';
  if (!condition   || condition.verdict   === 'UNCERTAIN')  return 'pending_review';

  // AI has a definitive answer on every check — make a decision
  const condText = (condition.detail || '').toLowerCase();

  // Wrong item returned — dispose regardless of condition
  if (identity.verdict === 'FAIL') {
    return 'dispose';
  }

  // Correct item but missing parts
  if (completeness.verdict === 'FAIL') {
    // If condition is still good enough, send for refurbishment to add missing parts
    if (condText.includes('new') || condText.includes('like new') || condText.includes('very good')) {
      return 'refurbish';
    }
    // Otherwise liquidate — not worth refurbishing incomplete + worn
    return 'liquidate';
  }

  // Identity PASS, completeness PASS — decide purely on condition
  if (condText.includes('unacceptable')) return 'dispose';
  if (condText.includes('used - acceptable') || condText.includes('used - good')) return 'liquidate';
  if (condText.includes('used - very good') || condText.includes('used - like new') || condText.includes('renewed')) return 'refurbish';
  if (condText.includes('new')) return 'restock';

  // Fallback: condition text not recognised but AI gave PASS — default to refurbish
  return 'refurbish';
};
