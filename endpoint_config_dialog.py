"""
Endpoint Configuration UI Dialog
Provides a user interface for managing translation endpoints
"""

import json
import logging
from typing import Dict, Any, Optional
from PySide6 import QtWidgets, QtCore, QtGui

logger = logging.getLogger('Lorebook_Gemini_Translator')


class EndpointConfigDialog(QtWidgets.QDialog):
    """Dialog for configuring translation endpoints"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Translation Endpoints")
        self.setModal(True)
        self.resize(800, 600)
        
        # Load current configuration
        self.config = self.load_config()
        self.endpoints = self.config.get('endpoints', {})
        self.active_endpoint = self.config.get('active_endpoint', 'gemini')
        
        self.setup_ui()
        self.load_endpoints_to_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Endpoint selector
        selector_layout = QtWidgets.QHBoxLayout()
        selector_layout.addWidget(QtWidgets.QLabel("Active Endpoint:"))
        
        self.endpoint_combo = QtWidgets.QComboBox()
        self.endpoint_combo.currentTextChanged.connect(self.on_endpoint_changed)
        selector_layout.addWidget(self.endpoint_combo)
        
        self.add_endpoint_btn = QtWidgets.QPushButton("Add New")
        self.add_endpoint_btn.clicked.connect(self.add_new_endpoint)
        selector_layout.addWidget(self.add_endpoint_btn)
        
        self.remove_endpoint_btn = QtWidgets.QPushButton("Remove")
        self.remove_endpoint_btn.clicked.connect(self.remove_endpoint)
        selector_layout.addWidget(self.remove_endpoint_btn)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Configuration area
        self.config_widget = QtWidgets.QWidget()
        self.config_layout = QtWidgets.QFormLayout(self.config_widget)
        
        # Name
        self.name_edit = QtWidgets.QLineEdit()
        self.config_layout.addRow("Name:", self.name_edit)
        
        # Type
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["gemini", "openai"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.config_layout.addRow("Type:", self.type_combo)
        
        # Base URL
        self.base_url_edit = QtWidgets.QLineEdit()
        self.config_layout.addRow("Base URL:", self.base_url_edit)
        
        # Auth Type
        self.auth_combo = QtWidgets.QComboBox()
        self.auth_combo.addItems(["none", "api_key", "custom"])
        self.config_layout.addRow("Authentication:", self.auth_combo)
        
        # Models
        models_label = QtWidgets.QLabel("Available Models:")
        self.config_layout.addRow(models_label)
        
        # Models list widget for selection
        self.models_list = QtWidgets.QListWidget()
        self.models_list.setMaximumHeight(100)
        self.models_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.models_list.itemClicked.connect(self.on_model_selected)
        self.config_layout.addRow(self.models_list)
        
        # Selected model display
        self.selected_model_edit = QtWidgets.QLineEdit()
        self.selected_model_edit.setPlaceholderText("Selected model (click from list or type manually)")
        self.config_layout.addRow("Active Model:", self.selected_model_edit)
        
        # Models text edit for manual entry
        self.models_edit = QtWidgets.QTextEdit()
        self.models_edit.setMaximumHeight(60)
        self.models_edit.setPlaceholderText("Additional models (one per line)")
        self.config_layout.addRow("Manual Models:", self.models_edit)
        
        # Test connection button
        self.test_btn = QtWidgets.QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.config_layout.addRow("", self.test_btn)
        
        # Advanced settings
        advanced_group = QtWidgets.QGroupBox("Advanced Settings")
        advanced_layout = QtWidgets.QFormLayout()
        
        # Temperature
        self.temp_spin = QtWidgets.QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)
        advanced_layout.addRow("Temperature:", self.temp_spin)
        
        # Max tokens
        self.max_tokens_spin = QtWidgets.QSpinBox()
        self.max_tokens_spin.setRange(1, 32000)
        self.max_tokens_spin.setValue(4096)
        advanced_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Custom headers
        self.headers_edit = QtWidgets.QTextEdit()
        self.headers_edit.setMaximumHeight(80)
        self.headers_edit.setPlaceholderText("JSON format: {\"Header-Name\": \"value\"}")
        advanced_layout.addRow("Custom Headers:", self.headers_edit)
        
        advanced_group.setLayout(advanced_layout)
        self.config_layout.addRow(advanced_group)
        
        layout.addWidget(self.config_widget)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def on_model_selected(self, item):
        """Handle model selection from list"""
        if item:
            self.selected_model_edit.setText(item.text())
            logger.info(f"Selected model: {item.text()}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            from translation_providers import ProviderFactory
            return ProviderFactory.load_endpoints_config()
        except Exception as e:
            logger.error(f"Error loading endpoints config: {e}")
            return {"endpoints": {}, "active_endpoint": "gemini"}
    
    def load_endpoints_to_ui(self):
        """Load endpoints into the UI"""
        self.endpoint_combo.clear()
        for key in self.endpoints.keys():
            self.endpoint_combo.addItem(key)
        
        # Set active endpoint
        index = self.endpoint_combo.findText(self.active_endpoint)
        if index >= 0:
            self.endpoint_combo.setCurrentIndex(index)
    
    def on_endpoint_changed(self, endpoint_key: str):
        """Handle endpoint selection change"""
        if endpoint_key and endpoint_key in self.endpoints:
            endpoint = self.endpoints[endpoint_key]
            
            # Load values
            self.name_edit.setText(endpoint.get('name', ''))
            self.type_combo.setCurrentText(endpoint.get('type', 'openai'))
            self.base_url_edit.setText(endpoint.get('base_url', ''))
            self.auth_combo.setCurrentText(endpoint.get('auth_type', 'none'))
            
            # Models
            models = endpoint.get('models', [])
            self.models_list.clear()
            self.models_list.addItems(models)
            
            # Active model
            active_model = endpoint.get('active_model', '')
            if not active_model and models:
                active_model = models[0]
            self.selected_model_edit.setText(active_model)
            
            # Additional models in text edit
            additional_models = endpoint.get('additional_models', [])
            self.models_edit.setPlainText('\n'.join(additional_models))
            
            # Advanced settings
            params = endpoint.get('default_params', {})
            self.temp_spin.setValue(params.get('temperature', 0.7))
            self.max_tokens_spin.setValue(params.get('max_tokens', 4096))
            
            # Headers
            headers = endpoint.get('headers', {})
            if headers:
                self.headers_edit.setPlainText(json.dumps(headers, indent=2))
            else:
                self.headers_edit.clear()
    
    def on_type_changed(self, provider_type: str):
        """Handle provider type change"""
        # Update UI based on provider type
        if provider_type == 'gemini':
            self.base_url_edit.setText("https://generativelanguage.googleapis.com")
            self.base_url_edit.setEnabled(False)
            self.auth_combo.setCurrentText("api_key")
        else:
            self.base_url_edit.setEnabled(True)
            if not self.base_url_edit.text():
                self.base_url_edit.setText("http://localhost:11434/v1")
    
    def add_new_endpoint(self):
        """Add a new endpoint"""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Endpoint", "Enter endpoint key (e.g., 'my_local_llm'):"
        )
        
        if ok and name:
            if name in self.endpoints:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"Endpoint '{name}' already exists!"
                )
                return
            
            # Create new endpoint
            self.endpoints[name] = {
                "name": f"New {name} Endpoint",
                "type": "openai",
                "base_url": "http://localhost:11434/v1",
                "models": [],
                "auth_type": "none",
                "headers": {},
                "default_params": {
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
            }
            
            self.load_endpoints_to_ui()
            self.endpoint_combo.setCurrentText(name)
    
    def remove_endpoint(self):
        """Remove current endpoint"""
        current = self.endpoint_combo.currentText()
        
        if current == 'gemini':
            QtWidgets.QMessageBox.warning(
                self, "Error", "Cannot remove the default Gemini endpoint!"
            )
            return
        
        if current in self.endpoints:
            reply = QtWidgets.QMessageBox.question(
                self, "Confirm", f"Remove endpoint '{current}'?"
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                del self.endpoints[current]
                self.load_endpoints_to_ui()
    
    def test_connection(self):
        """Test connection to current endpoint"""
        current = self.endpoint_combo.currentText()
        if not current:
            return
        
        # Save current settings to endpoint
        self.save_current_endpoint()
        
        # Get API key if needed
        api_key = None
        if self.auth_combo.currentText() == 'api_key':
            api_key, ok = QtWidgets.QInputDialog.getText(
                self, "API Key", "Enter API key for testing:", 
                QtWidgets.QLineEdit.Password
            )
            if not ok:
                return
        
        # Test connection
        try:
            from translation_providers import ProviderFactory
            
            endpoint_config = self.endpoints[current]
            provider = ProviderFactory.create_provider(endpoint_config)
            
            models = provider.list_models(api_key)
            
            if models:
                QtWidgets.QMessageBox.information(
                    self, "Success", 
                    f"Connection successful!\n\nFound {len(models)} models"
                )
                
                # Update models list
                self.models_list.clear()
                self.models_list.addItems(models)
                
                # Auto-select first model if none selected
                if not self.selected_model_edit.text() and models:
                    self.selected_model_edit.setText(models[0])
                    
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", 
                    "Connection successful but no models found.\n"
                    "You may need to manually add model names."
                )
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Connection failed:\n{str(e)}"
            )
    
    def save_current_endpoint(self):
        """Save current endpoint settings"""
        current = self.endpoint_combo.currentText()
        if not current:
            return
        
        # Parse headers
        headers = {}
        headers_text = self.headers_edit.toPlainText().strip()
        if headers_text:
            try:
                headers = json.loads(headers_text)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in headers field")
        
        # Parse models from list widget
        models = []
        for i in range(self.models_list.count()):
            models.append(self.models_list.item(i).text())
        
        # Parse additional models from text edit
        additional_models = [m.strip() for m in self.models_edit.toPlainText().split('\n') 
                           if m.strip()]
        
        # Get selected model
        active_model = self.selected_model_edit.text().strip()
        
        # Update endpoint
        self.endpoints[current] = {
            "name": self.name_edit.text(),
            "type": self.type_combo.currentText(),
            "base_url": self.base_url_edit.text(),
            "models": models,
            "additional_models": additional_models,
            "active_model": active_model,
            "auth_type": self.auth_combo.currentText(),
            "headers": headers,
            "default_params": {
                "temperature": self.temp_spin.value(),
                "max_tokens": self.max_tokens_spin.value()
            }
        }
    
    def save_config(self):
        """Save all configuration"""
        # Save current endpoint
        self.save_current_endpoint()
        
        # Update active endpoint
        self.active_endpoint = self.endpoint_combo.currentText()
        
        # Save to file
        config = {
            "endpoints": self.endpoints,
            "active_endpoint": self.active_endpoint
        }
        
        try:
            with open("endpoints_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info("Endpoints configuration saved")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to save configuration:\n{str(e)}"
            )
