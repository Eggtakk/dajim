import { Configuration, PlaidApi, PlaidEnvironments } from "plaid";

const PLAID_CLIENT_ID = process.env.PLAID_CLIENT_ID;
const PLAID_SECRET = process.env.PLAID_SECRET;
const PLAID_ENV = process.env.PLAID_ENV ?? "sandbox";

export const plaidConfigured = Boolean(PLAID_CLIENT_ID && PLAID_SECRET);

const configuration = new Configuration({
  basePath: PlaidEnvironments[PLAID_ENV],
  baseOptions: {
    headers: {
      "PLAID-CLIENT-ID": PLAID_CLIENT_ID ?? "",
      "PLAID-SECRET": PLAID_SECRET ?? "",
    },
  },
});

/**
 * Only call this after checking `plaidConfigured` — the client works either
 * way, but every request will fail auth if the env vars are missing.
 */
export const plaidClient = new PlaidApi(configuration);
