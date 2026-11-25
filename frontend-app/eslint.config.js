import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import {defineConfig,globalIgnores} from 'eslint/config';
export default defineConfig([
  globalIgnores(['dist','.migration-baseline','test-results','playwright-report']),
  {files:['**/*.{js,jsx}'],extends:[js.configs.recommended],languageOptions:{globals:{...globals.browser,...globals.node},parserOptions:{ecmaFeatures:{jsx:true}}}},
  {files:['**/*.{ts,tsx}'],extends:[tseslint.configs.recommended],languageOptions:{globals:{...globals.browser,...globals.node}}},
  {files:['src/**/*.{jsx,tsx}'],extends:[reactHooks.configs.flat.recommended,reactRefresh.configs.vite]},
]);
