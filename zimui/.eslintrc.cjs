module.exports = {
  root: true,
  parser: 'vue-eslint-parser',
  parserOptions: {
    sourceType: 'module',
    ecmaVersion: 'latest',
    parser: '@typescript-eslint/parser',
  },
  extends: [
    'eslint:recommended',
    // '@vue/eslint-config-standard',
    // '@vue/eslint-config-prettier/skip-formatting',
    'plugin:vue/vue3-recommended',
    // '@vue/typescript/recommended',
    '@vue/eslint-config-typescript/recommended',
    'prettier',
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': 'warn',
    'no-debugger': 'error',
    'vue/multi-word-component-names': 'warn',
    'vue/no-reserved-component-names': 'warn',
    'vue/require-explicit-emits': 'warn',
  },
  overrides: [
    {
      files: ['*.cjs'],
      env: { node: true },
    },
  ],
}
