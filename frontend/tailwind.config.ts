import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#14171F", // page background
          surface: "#1B1F29", // cards, rail, docked player
          raised: "#232838", // hover / elevated surface
          hairline: "#2C3140", // borders
        },
        paper: {
          DEFAULT: "#EDEAE2", // primary text (warm off-white)
          muted: "#8B8F9C", // secondary text
          faint: "#5B5F6C", // tertiary / disabled text
        },
        lamp: {
          50: "#FBF2E2",
          200: "#F3D19A",
          400: "#E8A33D", // primary accent
          600: "#B87A22",
          900: "#513008",
        },
        ribbon: {
          50: "#E3F3EA",
          200: "#9FD6B6",
          400: "#4FA37D", // progress / bookmark accent
          600: "#337758",
          900: "#123322",
        },
        danger: {
          400: "#D8654F",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jbmono)", "monospace"],
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        docked: "0 -1px 0 0 #2C3140",
      },
    },
  },
  plugins: [],
};

export default config;
