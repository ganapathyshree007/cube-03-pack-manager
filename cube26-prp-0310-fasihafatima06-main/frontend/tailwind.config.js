/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        odoo: {
          purple: "#714B67",
          purpleHover: "#5B3B53",
          purpleLight: "#F3EDF2",
          purpleBorder: "#E4D6E2",
          teal: "#00A09D",
          tealHover: "#008B88",
          tealLight: "#E6F6F6",
          tealBorder: "#BCE7E6",
          dark: "#1F2937",
          bg: "#F8F9FA",
        },
        cube: {
          bg: "#F8F9FA",
          dark: "#1F2937",
          card: "#FFFFFF",
          cardHover: "#F9FAFB",
          border: "#E5E7EB",
          borderHover: "#CBD5E1",
          indigo: "#714B67",
          violet: "#00A09D",
          amber: "#D97706",
          pass: "#00A09D",
          fail: "#E11D48",
          uncertain: "#D97706",
          text: "#1F2937",
          muted: "#6B7280",
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
