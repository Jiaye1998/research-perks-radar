/** @type {import('next').NextConfig} */

// For GitHub Pages project sites, the app is served from
// https://<user>.github.io/<repo>/  — so basePath must be the repo name.
// The workflow sets NEXT_PUBLIC_BASE_PATH; locally it's empty.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig = {
  output: "export",
  basePath,
  images: { unoptimized: true },
  trailingSlash: true,
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
};

module.exports = nextConfig;
