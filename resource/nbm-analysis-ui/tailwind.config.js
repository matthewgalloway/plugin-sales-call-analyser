/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'navy': {
          800: '#1e3a5f',
          900: '#0f1f3d',
        },
      },
    },
  },
  plugins: [],
}
