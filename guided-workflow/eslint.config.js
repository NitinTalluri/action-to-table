import js from "@eslint/js";
import pluginQuery from "@tanstack/eslint-plugin-query";
import reactDom from "eslint-plugin-react-dom";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

import reactX from "eslint-plugin-react-x";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "**/cisco/*", "amplify/**"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        project: ["./tsconfig.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "react-x": reactX,
      "react-dom": reactDom,
      "@tanstack/query": pluginQuery,
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      ...reactHooks.configs["recommended-latest"].rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      ...reactX.configs["recommended-typescript"].rules,
      ...reactDom.configs.recommended.rules,

      "@tanstack/query/exhaustive-deps": "error",

      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",

      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
          ignoreRestSiblings: true,
        },
      ],
      "@typescript-eslint/no-unused-expressions": [
        "error",
        { allowShortCircuit: true, allowTernary: true },
      ],
      "@typescript-eslint/ban-ts-comment": [
        "error",
        { "ts-ignore": "allow-with-description", "ts-expect-error": false },
      ],
    },
    settings: {
      "import/resolver": {
        typescript: true,
      },
    },
    linterOptions: {
      reportUnusedDisableDirectives: "error",
    },
  },
);
