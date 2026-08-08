"use client";

import { useCallback, useSyncExternalStore } from "react";
import { DEFAULT_GOAL } from "./goal";
import type { GoalSettings } from "./types";

const STORAGE_KEY = "dajim:goal-settings";

export { DEFAULT_GOAL };

/**
 * A tiny external store backed by localStorage, read via
 * useSyncExternalStore so the server snapshot (always DEFAULT_GOAL) and the
 * client snapshot (localStorage, once mounted) never fight over hydration —
 * React reconciles the two automatically instead of us juggling setState
 * inside an effect.
 */
let cache: GoalSettings = DEFAULT_GOAL;
let cacheLoaded = false;
const listeners = new Set<() => void>();

function readStoredGoal(): GoalSettings {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_GOAL;
    return { ...DEFAULT_GOAL, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_GOAL;
  }
}

function subscribe(onStoreChange: () => void) {
  listeners.add(onStoreChange);
  return () => listeners.delete(onStoreChange);
}

function getSnapshot(): GoalSettings {
  if (!cacheLoaded) {
    cache = readStoredGoal();
    cacheLoaded = true;
  }
  return cache;
}

function getServerSnapshot(): GoalSettings {
  return DEFAULT_GOAL;
}

function writeGoal(next: GoalSettings) {
  cache = next;
  cacheLoaded = true;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // storage unavailable (private mode, quota) — state still works in-memory
  }
  listeners.forEach((notify) => notify());
}

/**
 * Persists the user's goal-setting selections to localStorage so they
 * survive reloads and navigation. No backend yet — once the model/API is
 * ready this is the natural spot to sync goal changes to it as well.
 */
export function useGoalSettings() {
  const goal = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setGoal = useCallback((next: Partial<GoalSettings>) => {
    writeGoal({ ...getSnapshot(), ...next });
  }, []);

  const resetGoal = useCallback(() => {
    writeGoal(DEFAULT_GOAL);
  }, []);

  return { goal, setGoal, resetGoal };
}
