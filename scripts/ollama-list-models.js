#!/usr/bin/env node
/**
 * Lists models served by an Ollama-compatible API.
 *
 * Defaults to local Ollama: http://localhost:11434/api/tags
 *
 * Env vars:
 * - OLLAMA_HOST or OLLAMA_BASE_URL: e.g. http://localhost:11434
 * - OLLAMA_API_KEY: optional; sent as "Authorization: Bearer <key>"
 *
 * Args:
 * - --json: print the raw JSON response
 */

const baseUrl = (process.env.OLLAMA_BASE_URL || process.env.OLLAMA_HOST || "http://localhost:11434")
  .replace(/\/+$/, "");
const apiKey = process.env.OLLAMA_API_KEY;

function headerValuePreview(value) {
  if (!value) return "";
  // Avoid leaking secrets in logs.
  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

async function main() {
  const url = `${baseUrl}/api/tags`;

  const headers = { Accept: "application/json" };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;

  let res;
  try {
    res = await fetch(url, { method: "GET", headers });
  } catch (err) {
    console.error(`Request failed: ${err?.message || String(err)}`);
    console.error(`URL: ${url}`);
    if (apiKey) console.error(`Auth: Bearer ${headerValuePreview(apiKey)}`);
    process.exitCode = 1;
    return;
  }

  const text = await res.text();
  if (!res.ok) {
    console.error(`HTTP ${res.status} ${res.statusText}`);
    console.error(`URL: ${url}`);
    if (apiKey) console.error(`Auth: Bearer ${headerValuePreview(apiKey)}`);
    if (text) console.error(text);
    process.exitCode = 1;
    return;
  }

  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    console.error("Response was not valid JSON.");
    console.error(`URL: ${url}`);
    if (text) console.error(text);
    process.exitCode = 1;
    return;
  }

  const args = new Set(process.argv.slice(2));
  if (args.has("--json")) {
    process.stdout.write(JSON.stringify(data, null, 2) + "\n");
    return;
  }

  const models = Array.isArray(data?.models) ? data.models : [];
  if (models.length === 0) {
    console.log("No models found.");
    return;
  }

  for (const m of models) {
    // Ollama returns "name" like "llama3:latest".
    if (m?.name) console.log(m.name);
  }
}

main();

