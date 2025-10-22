# app/utils/static_assets.py
"""
Static Assets Manager - Handles loading of CSS, JS, and other static files
This provides a clean way to load external assets instead of hardcoding them
"""

import os
import streamlit as st
from typing import Optional, List
from pathlib import Path

class StaticAssetsManager:
    """Manages loading of static assets (CSS, JS, images)"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the static assets manager
        
        Args:
            base_path: Base path for static assets. If None, uses project root/static
        """
        if base_path is None:
            # Get the project root directory (two levels up from this file)
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            self.base_path = project_root / "static"
        else:
            self.base_path = Path(base_path)
        
        self.css_path = self.base_path / "css"
        self.js_path = self.base_path / "js"
        self.assets_path = self.base_path / "assets"
    
    def load_css_file(self, filename: str) -> bool:
        """
        Load a CSS file into Streamlit
        
        Args:
            filename: Name of the CSS file (e.g., 'main.css')
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        css_file_path = self.css_path / filename
        
        if not css_file_path.exists():
            st.warning(f"CSS file not found: {css_file_path}")
            return False
        
        try:
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            return True
        except Exception as e:
            st.error(f"Error loading CSS file {filename}: {e}")
            return False
    
    def load_js_file(self, filename: str) -> bool:
        """
        Load a JavaScript file into Streamlit
        
        Args:
            filename: Name of the JS file (e.g., 'main.js')
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        js_file_path = self.js_path / filename
        
        if not js_file_path.exists():
            st.warning(f"JavaScript file not found: {js_file_path}")
            return False
        
        try:
            with open(js_file_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            st.markdown(f"<script>{js_content}</script>", unsafe_allow_html=True)
            return True
        except Exception as e:
            st.error(f"Error loading JavaScript file {filename}: {e}")
            return False
    
    def load_multiple_css_files(self, filenames: List[str]) -> int:
        """
        Load multiple CSS files
        
        Args:
            filenames: List of CSS filenames
            
        Returns:
            int: Number of files successfully loaded
        """
        loaded_count = 0
        for filename in filenames:
            if self.load_css_file(filename):
                loaded_count += 1
        return loaded_count
    
    def load_multiple_js_files(self, filenames: List[str]) -> int:
        """
        Load multiple JavaScript files
        
        Args:
            filenames: List of JS filenames
            
        Returns:
            int: Number of files successfully loaded
        """
        loaded_count = 0
        for filename in filenames:
            if self.load_js_file(filename):
                loaded_count += 1
        return loaded_count
    
    def load_core_assets(self) -> bool:
        """
        Load core assets (main.css and main.js)
        
        Returns:
            bool: True if all core assets loaded successfully
        """
        css_loaded = self.load_css_file("main.css")
        js_loaded = self.load_js_file("main.js")
        
        return css_loaded and js_loaded
    
    def get_asset_path(self, filename: str, asset_type: str = "assets") -> str:
        """
        Get the full path to an asset file
        
        Args:
            filename: Name of the asset file
            asset_type: Type of asset ('css', 'js', 'assets')
            
        Returns:
            str: Full path to the asset file
        """
        if asset_type == "css":
            return str(self.css_path / filename)
        elif asset_type == "js":
            return str(self.js_path / filename)
        elif asset_type == "assets":
            return str(self.assets_path / filename)
        else:
            return str(self.base_path / filename)
    
    def asset_exists(self, filename: str, asset_type: str = "assets") -> bool:
        """
        Check if an asset file exists
        
        Args:
            filename: Name of the asset file
            asset_type: Type of asset ('css', 'js', 'assets')
            
        Returns:
            bool: True if asset exists
        """
        asset_path = self.get_asset_path(filename, asset_type)
        return Path(asset_path).exists()
    
    def list_available_assets(self, asset_type: str = "assets") -> List[str]:
        """
        List all available assets of a given type
        
        Args:
            asset_type: Type of assets to list ('css', 'js', 'assets')
            
        Returns:
            List[str]: List of available asset filenames
        """
        if asset_type == "css":
            path = self.css_path
        elif asset_type == "js":
            path = self.js_path
        elif asset_type == "assets":
            path = self.assets_path
        else:
            path = self.base_path
        
        if not path.exists():
            return []
        
        return [f.name for f in path.iterdir() if f.is_file()]
