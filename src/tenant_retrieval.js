// Synthetic, read-only retrieval fixture for the n8n Code node.
// Filter by tenant and publication state before scoring any document.
const request = $input.first()?.json ?? {};
const tenantId = request.tenant_id;
const query = request.query;
const allowedTenants = new Set(['demo-a', 'demo-b']);

if (
  !allowedTenants.has(tenantId) ||
  typeof query !== 'string' ||
  query.trim().length === 0 ||
  query.length > 120
) {
  return [{ json: { status: 'rejected', reason: 'invalid_sample_scope' } }];
}

const documents = [
  { id: 'A-001', tenant_id: 'demo-a', published: true, title: 'Shipping guide', text: 'Sample shipping policy and delivery windows.' },
  { id: 'A-002', tenant_id: 'demo-a', published: false, title: 'Draft shipping policy', text: 'Unpublished sample document.' },
  { id: 'A-003', tenant_id: 'demo-a', published: true, title: 'Returns guide', text: 'Sample returns and exchanges.' },
  { id: 'B-001', tenant_id: 'demo-b', published: true, title: 'Shipping guide', text: 'Different sample shipping policy.' },
];

const terms = [...new Set(query.toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean))];
const results = documents
  .filter((document) => document.tenant_id === tenantId && document.published)
  .map((document) => {
    const searchable = `${document.title} ${document.text}`.toLowerCase();
    const score = terms.reduce((total, term) => total + Number(searchable.includes(term)), 0);
    return { id: document.id, title: document.title, score };
  })
  .filter((document) => document.score > 0)
  .sort((left, right) => right.score - left.score || left.id.localeCompare(right.id))
  .slice(0, 3);

return [{ json: { status: 'ok', tenant_id: tenantId, results } }];
