import { readFileSync, writeFileSync } from "fs";
import { join } from "path";

/**
 * DEMO-ONLY single-user token storage.
 *
 * There's no auth/DB yet (see docs/api-and-model-plan.md §1), so this just
 * writes the Sandbox access_token to a gitignored file instead of a
 * per-user row in a database. Once real accounts exist, this whole file
 * gets replaced by a `plaid_items` table keyed on user id.
 */
const TOKEN_FILE = join(process.cwd(), ".plaid-sandbox-token.json");

export function saveAccessToken(accessToken: string): void {
  writeFileSync(TOKEN_FILE, JSON.stringify({ accessToken }), "utf-8");
}

export function loadAccessToken(): string | null {
  try {
    const raw = readFileSync(TOKEN_FILE, "utf-8");
    return (JSON.parse(raw).accessToken as string) ?? null;
  } catch {
    return null;
  }
}
