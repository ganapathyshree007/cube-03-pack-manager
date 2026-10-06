const ALLOWED_TENANTS = new Set(['org_demo_alpha', 'org_demo_bravo']);

module.exports = (req, res, next) => {
  // Extract tenant from authorization context (simulated via header for demo)
  // In a real app, this would come from a verified JWT or session token.

  const tenantId = req.headers['x-tenant-id'];

  if (!tenantId) {
    return res.status(401).json({
      error: 'Unauthorized: Missing tenant context'
    });
  }

  if (!ALLOWED_TENANTS.has(tenantId)) {
    return res.status(403).json({
      error: 'Forbidden: Invalid tenant context'
    });
  }

  // Attach validated tenant context to the request
  req.tenant = tenantId;

  next();
};