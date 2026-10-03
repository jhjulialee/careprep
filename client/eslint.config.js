import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
export default [{ignores:['dist']},{files:['**/*.{js,jsx}'],languageOptions:{ecmaVersion:2022,sourceType:'module',globals:globals.browser},plugins:{'react-hooks':reactHooks},rules:{...js.configs.recommended.rules,...reactHooks.configs.recommended.rules,'no-unused-vars':['error',{argsIgnorePattern:'^_'}]}}]
