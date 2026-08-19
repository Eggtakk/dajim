"use client";

import { useCallback, useEffect, useState } from "react";
import { usePlaidLink } from "react-plaid-link";

/**
 * Wraps the Plaid Link flow (fetch link_token -> open Link -> exchange
 * public_token) behind a single `connect()` call.
 *
 * If PLAID_CLIENT_ID/PLAID_SECRET aren't set (see .env.local.example),
 * /api/plaid/create-link-token responds 501 and `connect()` just calls
 * `onConnected` directly — the rest of the app keeps working on mock data,
 * Plaid is additive, not a hard requirement.
 */
export function usePlaidConnect(onConnected: () => void) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [available, setAvailable] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/plaid/create-link-token", { method: "POST" })
      .then(async (res) => ({ ok: res.ok, body: await res.json() }))
      .then(({ ok, body }) => {
        if (cancelled) return;
        if (ok && body.linkToken) {
          setLinkToken(body.linkToken);
        } else {
          setAvailable(false);
        }
      })
      .catch(() => {
        if (!cancelled) setAvailable(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { open, ready } = usePlaidLink({
    token: linkToken ?? "",
    onSuccess: (publicToken) => {
      fetch("/api/plaid/exchange-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ publicToken }),
      })
        .catch((error) => console.error("Plaid token exchange failed", error))
        .finally(onConnected);
    },
  });

  const connect = useCallback(() => {
    if (available && linkToken && ready) {
      open();
    } else {
      onConnected();
    }
  }, [available, linkToken, ready, open, onConnected]);

  return { connect };
}
