module.exports = {
  env: {
    node: true,
    es2021: true,
    commonjs: true
  },
  extends: [
    'standard'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  rules: {
    // Отключаем некоторые строгие правила для удобства разработки
    'no-console': 'off',
    'no-unused-vars': ['error', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_'
    }],
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'error',
    'prefer-template': 'error',
    'template-curly-spacing': ['error', 'never'],
    'arrow-spacing': 'error',
    'comma-dangle': ['error', 'never'],
    semi: ['error', 'always'],
    quotes: ['error', 'single', { avoidEscape: true }],
    indent: ['error', 2],
    'no-trailing-spaces': 'error',
    'eol-last': 'error',
    'no-multiple-empty-lines': ['error', { max: 1 }],
    'space-before-function-paren': ['error', 'never'],
    'keyword-spacing': 'error',
    'space-infix-ops': 'error',
    'space-before-blocks': 'error',
    'brace-style': ['error', '1tbs'],
    curly: ['error', 'all'],
    eqeqeq: ['error', 'always'],
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-func': 'error',
    'no-script-url': 'error',
    'no-alert': 'error',
    'no-debugger': 'error',
    'no-duplicate-imports': 'error',
    'no-useless-rename': 'error',
    'prefer-destructuring': ['error', {
      array: false,
      object: true
    }]
  },
  globals: {
    // Глобальные переменные для Node.js
    process: 'readonly',
    Buffer: 'readonly',
    console: 'readonly',
    global: 'readonly',
    module: 'readonly',
    require: 'readonly',
    exports: 'readonly',
    __dirname: 'readonly',
    __filename: 'readonly'
  }
};
