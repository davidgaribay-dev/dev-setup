import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['esm'],
  platform: 'node',
  target: 'node20',
  outDir: 'dist',
  clean: true,
  sourcemap: true,
  // Bundle the shared package, but keep external dependencies external
  noExternal: [/@rewind\/shared/],
  // Don't bundle node_modules (they have native bindings, etc.)
  external: ['neo4j-driver', '@hono/node-server', 'hono'],
});
