# CEO Briefing Design System

**This is the base design for all pages in ceo-briefing.vercel.app**

## Colors
```css
--bg: #fafaf9;           /* Page background */
--surface: #ffffff;       /* Cards, headers */
--text: #1a1a1a;         /* Primary text */
--text-secondary: #555;   /* Secondary text */
--text-muted: #888;       /* Muted text */
--border: #e8e5e1;        /* Borders */
--green: #16a34a;         /* Positive */
--red: #dc2626;           /* Negative */
--yellow: #ca8a04;        /* Caution */
```

## Typography
- **Headlines:** Playfair Display, 800 weight, serif
- **Body:** Inter, 400-700 weight, sans-serif
- **Base size:** 16px
- **Line height:** 1.65

## Components

### Cards
- Background: white (#ffffff)
- Border: 1px solid #e8e5e1
- Border-radius: 8px
- Shadow: 0 1px 3px rgba(0,0,0,0.04)
- Padding: 1.25rem 1.5rem
- Featured cards: 4px left border in accent color

### Section Headers
- Icon: 40x40px rounded square with tinted background
- Title: Playfair Display, 1.35rem, 700 weight
- Border-bottom: 2px solid #e8e5e1

### Tables
- Header: 0.65rem uppercase, #888 color
- Rows: 0.9rem, border-bottom 1px
- Positive values: #16a34a
- Negative values: #dc2626

### Navigation
- Top nav: centered links, 2px bottom border on active
- Section pills: rounded buttons for in-page nav

## Layout
- Max-width: 900px
- Container padding: 2rem 1.5rem
- Section margin-bottom: 3rem

## Accent Colors by Section
- Market: #0d6e4f (green)
- Japan: #c23b22 (red)
- Global/Geo: #1e3a5f (blue)
- Tech: #6c3ea0 (purple)
- Predictions: #b45309 (amber)

---

**All new pages must follow this design system.**
