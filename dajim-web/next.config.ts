import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Lets the dev server serve its JS/HMR assets when you open it via a LAN
  // IP instead of localhost (e.g. testing from a phone on the same wifi, or
  // a teammate hitting your machine directly). Next.js blocks this by
  // default. Add your own IP here if you hit the same "Blocked cross-origin
  // request" error in the terminal.
  allowedDevOrigins: ["192.168.0.77"],
};

export default nextConfig;
