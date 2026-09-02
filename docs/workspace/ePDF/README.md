# ePDF - Browser-Based PDF Editor

A lightweight, mobile-friendly PDF editor that runs entirely in your browser. Edit text directly, add watermarks and signatures, manage pages, and download your changes.

## Privacy First

**Your files never leave your device.** All PDF processing happens 100% client-side in your browser:
- No uploads to any server
- No cloud storage
- No tracking or analytics
- Complete privacy for sensitive documents

## Features

### Text Editing
- **Direct Text Editing**: Click any text to edit it directly on the PDF
- **Text Normalization**: Darkens light gray text for better readability
- **Font Scaling**: Text properly scales with zoom level
- **Edit Preservation**: Edited text survives page switching and zoom operations

### Watermarks
- **Text Watermarks**: Add custom text watermarks with adjustable opacity
- **Diagonal Positioning**: Watermarks appear prominently across the page
- **Customizable**: Set your own watermark text before adding

### Signatures
- **Draw Signatures**: Freehand drawing pad for natural signatures
- **Upload Signatures**: Import signature images from your device
- **Movable & Resizable**: Position signatures anywhere on the page
- **Persistent**: Signatures survive zoom and page navigation

### Page Management
- **Multi-page Navigation**: Prev/next controls with page counter
- **Page State Preservation**: All edits saved when switching between pages
- **Auto-save**: Changes auto-saved 5 seconds after editing (debounced)

### Zoom Controls
- **Zoom In/Out**: 0.5x to 3x zoom range in 0.25x increments
- **Edit Preservation on Zoom**: User-added content (watermarks, signatures, edited text) scales correctly
- **Fresh Render**: PDF re-renders cleanly at each zoom level

### Image Manipulation
- **Drag to Reposition**: Move images anywhere on the page
- **Select and Delete**: Remove unwanted images
- **Resize**: Scale images using corner handles

### Undo/Redo
- **Keyboard Shortcuts**: Ctrl+Z (undo), Ctrl+Y or Ctrl+Shift+Z (redo)
- **50-state History**: Up to 50 undo levels per page

### Export Options
- **Download as PDF**: Export edited document as PDF using pdf-lib
- **Download as Image**: Export current page as PNG
- **Multi-page PDF Export**: All pages included in PDF download

### Additional Features
- **Mobile Friendly**: Touch-optimized for tablet and phone editing
- **100% Client-Side**: Files never leave your browser - complete privacy
- **Offline Capable**: Works entirely in the browser after initial load
- **No CDN Dependencies**: PDF.js worker bundled locally for VPS deployment
- **Zero Backend Required**: Static file hosting is all you need

## Quick Start

### Development
```bash
cd ePDF
npm install
npm run dev
```

Open http://localhost:5173

## Tech Stack

- **Frontend**: React + Vite + TypeScript
- **PDF Rendering**: PDF.js (v5.4.530, bundled locally)
- **Canvas Editing**: Fabric.js v6
- **PDF Export**: pdf-lib
- **Backend**: Express.js (optional - static hosting works too)
- **Storage**: In-browser only (100% client-side)

## Deployment

Since all PDF processing is client-side, you only need static file hosting:

### Option 1: Static Hosting (Recommended)
```bash
npm run build
# Serve the dist/ folder with any static host (Nginx, Cloudflare Pages, Netlify, etc.)
```

### Option 2: Node.js Server
```bash
npm run build
NODE_ENV=production npm start  # Serves on port 3001
```

## Project Structure

```
ePDF/
├── client/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PDFEditor.tsx    # Main editor with Fabric.js canvas
│   │   │   └── UploadZone.tsx   # Drag-and-drop file selector
│   │   ├── App.tsx
│   │   └── index.css
│   ├── public/
│   │   └── pdf.worker.min.mjs   # PDF.js worker (bundled)
│   └── index.html
├── server/
│   └── index.ts                 # Optional Express server (static hosting works)
├── dist/                        # Production build (deploy this folder)
└── package.json
```

## How It Works

1. **Select File**: Browser reads PDF directly from your device (never uploaded)
2. **Render**: PDF.js renders each page, extracting text positions and images
3. **Overlay**: Fabric.js creates editable text boxes over extracted text
4. **Edit**: Modify text, add watermarks/signatures, move images
5. **Save State**: Page states saved in memory, preserved across navigation
6. **Export**: Download as PDF (using pdf-lib) or PNG image

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+Shift+Z | Redo |
| Delete/Backspace | Delete selected object |

## License

MIT
