# Static Assets Directory

This directory contains all static assets (CSS, JavaScript, images, etc.) for the Polo GGB Research Assistant application.

## Directory Structure

```
static/
├── css/                    # CSS stylesheets
│   └── main.css           # Main application styles
├── js/                    # JavaScript files
│   └── main.js            # Main application JavaScript
├── assets/                # Other static assets (images, fonts, etc.)
├── config/                # Configuration files
│   └── assets_config.yaml # Asset loading configuration
└── README.md              # This file
```

## Architecture Benefits

### ✅ **Separation of Concerns**
- **CSS**: Styling separated from Python logic
- **JavaScript**: Client-side functionality separated from backend
- **Configuration**: Asset loading behavior configurable

### ✅ **Maintainability**
- Easy to modify styles without touching Python code
- Version control friendly for CSS/JS changes
- Clear file organization

### ✅ **Performance**
- Assets can be cached by browsers
- Minification and compression possible
- CDN deployment ready

### ✅ **Development Experience**
- Syntax highlighting for CSS/JS files
- Better debugging capabilities
- IDE support for web technologies

## Usage

### Loading Assets in Python

```python
from utils.static_assets import StaticAssetsManager

# Initialize assets manager
assets_manager = StaticAssetsManager()

# Load core assets (main.css + main.js)
assets_manager.load_core_assets()

# Load specific files
assets_manager.load_css_file("main.css")
assets_manager.load_js_file("main.js")

# Load multiple files
assets_manager.load_multiple_css_files(["main.css", "themes/dark.css"])
```

### Adding New Assets

1. **CSS Files**: Add to `static/css/` directory
2. **JavaScript Files**: Add to `static/js/` directory
3. **Other Assets**: Add to `static/assets/` directory
4. **Update Configuration**: Modify `static/config/assets_config.yaml` if needed

### Asset Loading Order

Assets are loaded in the order specified in the configuration file:
1. Core CSS files (in order)
2. Core JavaScript files (in order)
3. Optional assets (if enabled)

## File Descriptions

### `css/main.css`
Contains all the main application styling including:
- Button styles and animations
- Loading overlay styles
- Layout and responsive design
- Streamlit component overrides

### `js/main.js`
Contains JavaScript functionality including:
- Loading overlay management
- UI interaction handlers
- Utility functions
- Event listeners

### `config/assets_config.yaml`
Configuration file that defines:
- Which assets to load
- Loading order
- Asset loading behavior
- Development settings

## Deployment Considerations

### For Streamlit Cloud
- All assets are bundled with the application
- No external CDN needed
- Assets loaded from local filesystem

### For Custom Deployment
- Assets can be served from a CDN
- Static file serving can be optimized
- Caching headers can be set appropriately

## Development Guidelines

1. **CSS**: Use consistent naming conventions and organize by component
2. **JavaScript**: Keep functions modular and well-documented
3. **Assets**: Optimize images and use appropriate formats
4. **Configuration**: Keep asset config simple and maintainable

## Migration from Hardcoded Assets

The application has been refactored from hardcoded CSS/JS in Python files to external asset files. This provides:

- **Better maintainability**: Styles and scripts in dedicated files
- **Improved performance**: Assets can be cached and optimized
- **Enhanced development experience**: Proper syntax highlighting and tooling
- **Deployment flexibility**: Assets can be served from CDN or bundled

## Troubleshooting

### Assets Not Loading
1. Check file paths in `StaticAssetsManager`
2. Verify files exist in correct directories
3. Check file permissions
4. Review error messages in Streamlit logs

### Styling Issues
1. Verify CSS syntax is correct
2. Check for conflicting styles
3. Use browser developer tools to debug
4. Ensure CSS selectors match Streamlit components

### JavaScript Errors
1. Check browser console for errors
2. Verify JavaScript syntax
3. Ensure functions are properly defined
4. Check for timing issues with DOM loading
