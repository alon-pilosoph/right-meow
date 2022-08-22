/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../templates/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require("daisyui")
  ],
  daisyui: {
    styled: true,
    themes: [
      {
        mytheme: {
          "primary": "#4338ca",
          "primary-content": "#ffffff",
          "secondary": "#d946ef",
          "accent": "#4b5563",
          "accent-content": "#ffffff",
          "neutral": "#e5e7eb",
          "base-100": "#FFFFFF",
          "info": "#3ABFF8",
          "success": "#36D399",
          "warning": "#FBBD23",
          "error": "#f43f5e",
        },
      },
    ],
  }
}
