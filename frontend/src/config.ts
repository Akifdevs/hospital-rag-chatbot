/**
 * The global document-set version the chat widget queries.
 *
 * Global versions are semantic labels such as "1", "1.1", or "2".
 * A newly ingested snapshot is READY immediately; there is no
 * confirmation/publish step.
 *
 * Update this value when you want the standalone widget build to
 * query a different READY snapshot. Embedded widgets can override
 * it with the script tag's `version` attribute.
 */
export const ACTIVE_VERSION = "1";
