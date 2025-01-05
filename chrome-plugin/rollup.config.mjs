import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import copy from 'rollup-plugin-copy';

export default [
  {
    input: 'static/index.js',
    output: {
      dir: 'dist/static',
      format: 'iife',
    },
    plugins: [
      commonjs(),
      nodeResolve(),
      copy({
        targets: [
          {
            src: ['manifest.json', 'background.js', 'static'],
            dest: 'dist'
          }
        ]
      })
    ]
  },
  {
    input: 'scripts/content.js',
    output: {
      dir: 'dist/scripts',
      format: 'es'
    },
    plugins: [
      commonjs(),
      nodeResolve(),
    ]
  }
];
