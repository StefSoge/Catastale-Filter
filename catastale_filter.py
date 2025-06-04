from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QLabel, QAction,
                                QLineEdit, QPushButton, QComboBox,
                                QMessageBox, QHBoxLayout)
from qgis.core import QgsProject, QgsVectorLayer, Qgis
from qgis.PyQt.QtCore import QTimer
from qgis.utils import iface
from qgis.PyQt.QtGui import QIcon
import os

class CatastaleFilterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.prepare_action = None
    
    def initGui(self):
        # Azione principale esistente
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        self.action = QAction(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), 
                            "Filtro Catastale", 
                            self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        # Nuova azione per preparazione layer
        prepare_icon = os.path.join(os.path.dirname(__file__), 'resources', 'prepare.png')
        self.prepare_action = QAction(
            QIcon(prepare_icon) if os.path.exists(prepare_icon) else QIcon(),
            "Prepara layers _ple",
            self.iface.mainWindow()
        )
        self.prepare_action.triggered.connect(self.run_prepare_layers)
        
        # Aggiungi entrambe le azioni al menu e alla toolbar
        self.iface.addToolBarIcon(self.action)
        self.iface.addToolBarIcon(self.prepare_action)
        self.iface.addPluginToMenu("&Catasto Filter", self.action)
        self.iface.addPluginToMenu("&Catasto Filter", self.prepare_action)

    def run_prepare_layers(self):
        """Esegue lo script di preparazione layer"""
        try:
            from .prepara_layers_ple import main
            success, message, needs_reload = main()

            if success:
                iface.messageBar().pushMessage("Elaborazione in corso ...", message, level=Qgis.Success)
                if needs_reload:
                    from qgis.utils import plugins, reloadPlugin
                    try:
                        reloadPlugin('catastale_filter')
                        iface.messageBar().pushMessage("Info", "Plugin ricaricato", level=Qgis.Info)
                    except Exception as e:
                        iface.messageBar().pushMessage("Errore", f"Errore nel reload: {str(e)}", level=Qgis.Critical)
                else:
                    iface.messageBar().pushMessage("Info", message, level=Qgis.Info)
                    
        except Exception as e:
            iface.messageBar().pushMessage("Errore", f"Errore durante l'esecuzione: {str(e)}", level=Qgis.Critical)

    def unload(self):
        """Pulizia migliorata"""
        self.iface.removePluginMenu("&Catasto Filter", self.action)
        self.iface.removePluginMenu("&Catasto Filter", self.prepare_action)
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.prepare_action)
        if self.dialog:
            self.dialog.close()

    def run(self):
        if not self.dialog:
            self.dialog = CatastaleFilterDialog(self.iface.mainWindow())
        self.dialog.show()

def classFactory(iface):
    return CatastaleFilterPlugin(iface)

class BlinkSelectionManager:
    def __init__(self):
        self.timer = None
        self.counter = 0
        self.max_blinks = 6
        self.selected_feature_ids = []
        self.current_layer = None
    
    def blink_selection(self):
        if not self.current_layer or self.counter >= self.max_blinks * 2:
            if self.timer:
                self.timer.stop()
            if self.current_layer and self.selected_feature_ids:
                self.current_layer.selectByIds(self.selected_feature_ids)
            return
        
        if self.counter % 2 == 0:
            self.current_layer.selectByIds([])
        else:
            self.current_layer.selectByIds(self.selected_feature_ids)
        
        self.counter += 1
    
    def start_blinking(self, layer, feature_ids):
        self.stop_blinking()
        self.current_layer = layer
        self.selected_feature_ids = feature_ids
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.blink_selection)
        self.timer.start(300)
    
    def stop_blinking(self):
        if self.timer:
            self.timer.stop()
        if self.current_layer and self.selected_feature_ids:
            self.current_layer.selectByIds(self.selected_feature_ids)

class CatastaleFilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 Filtro Catastale Avanzato")
        self.setMinimumWidth(350)
        
        self.blink_manager = BlinkSelectionManager()
        self.current_layer = None
        self.original_renderer = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Dropdown layer
        layout.addWidget(QLabel("Layer da filtrare:"))
        self.combo_layer = QComboBox()
        self.combo_layer.addItem("")  # Voce vuota iniziale
        
        # Aggiungi solo layer vettoriali che hanno almeno uno dei campi richiesti
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                fields = [field.name() for field in layer.fields()]
                if any(f.endswith('_LABEL') for f in fields) and 'LABEL' in fields:
                    self.combo_layer.addItem(layer.name())
        
        layout.addWidget(self.combo_layer)
        
        # Campi filtro
        layout.addWidget(QLabel("Foglio catastale (valore esatto in [layer]_map_LABEL):"))
        self.txt_foglio = QLineEdit()
        self.txt_foglio.setPlaceholderText("Es: F12 - lascia vuoto per ignorare")
        layout.addWidget(self.txt_foglio)
        
        layout.addWidget(QLabel("Particella (valore esatto in LABEL):"))
        self.txt_particella = QLineEdit()
        self.txt_particella.setPlaceholderText("Es: 0045 - lascia vuoto per ignorare")
        layout.addWidget(self.txt_particella)
        
        # Pulsanti
        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("Applica Filtro")
        self.btn_apply.clicked.connect(self.filter_layer)
        self.btn_reset = QPushButton("Reset Filtro")
        self.btn_reset.clicked.connect(self.reset_filter)
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_reset)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_foglio_field_name(self, layer_name):
        """Restituisce il nome corretto del campo foglio, provando entrambe le varianti"""
        # Primo tentativo: con replace
        foglio_field = f"{layer_name.replace('_ple','_map')}_LABEL"
        
        # Verifica se esiste nel layer o nei join
        if self.current_layer:
            all_fields = self.get_all_available_fields()
            if foglio_field in all_fields:
                return foglio_field
        
        # Secondo tentativo: semplice map_LABEL
        return "map_LABEL"
    
    def get_all_available_fields(self):
        """Restituisce tutti i campi disponibili (layer + join)"""
        if not self.current_layer:
            return []
            
        field_names = [field.name() for field in self.current_layer.fields()]
        joined_fields = []
        
        # Ottieni tutti i campi dai join
        for join in self.current_layer.vectorJoins():
            join_layer = join.joinLayer()
            if join_layer:
                prefix = join.prefix() if hasattr(join, 'prefix') else ""
                joined_fields.extend([f"{prefix}{field.name()}" 
                                   for field in join_layer.fields()])
        
        return field_names + joined_fields
    
    def filter_layer(self):
        try:
            self.blink_manager.stop_blinking()
            
            layer_name = self.combo_layer.currentText()
            foglio = self.txt_foglio.text().strip()
            particella = self.txt_particella.text().strip()
            
            if not layer_name:
                QMessageBox.warning(self, "Attenzione", "Seleziona un layer!")
                return
                
            layers = QgsProject.instance().mapLayersByName(layer_name)
            if not layers:
                QMessageBox.critical(self, "Errore", f"Layer {layer_name} non trovato!")
                return
                
            self.current_layer = layers[0]
            
            # Attiva il layer selezionato
            iface.setActiveLayer(self.current_layer)
            
            if not foglio and not particella:
                self.reset_filter()
                return
            
            # Ottieni il nome corretto del campo foglio
            foglio_field = self.get_foglio_field_name(layer_name)
            all_fields = self.get_all_available_fields()
            
            expression_parts = []
            if foglio:
                if foglio_field not in all_fields:
                    QMessageBox.warning(self, "Campo non trovato", 
                                      f"Il campo {foglio_field} non esiste nel layer o nei join!")
                    return
                expression_parts.append(f'"{foglio_field}" = \'{foglio}\'')
            
            if particella:
                if 'LABEL' not in all_fields:
                    QMessageBox.warning(self, "Campo non trovato", 
                                      "Il campo 'LABEL' non esiste nel layer o nei join!")
                    return
                expression_parts.append(f'"LABEL" = \'{particella}\'')
            
            expression = ' AND '.join(expression_parts)
            
            # Usa selectByExpression
            self.current_layer.removeSelection()
            self.current_layer.selectByExpression(expression)
            
            selected_feature_ids = self.current_layer.selectedFeatureIds()
            
            feature_count = len(selected_feature_ids)
            if feature_count == 0:
                QMessageBox.information(self, "Risultati", 
                                      "Nessun risultato trovato con questi criteri")
            else:
                iface.mapCanvas().zoomToSelected(self.current_layer)
                iface.messageBar().pushMessage("Successo", 
                                             f"Trovate {feature_count} feature", 
                                             level=0, duration=5)
                
                # Avvia l'effetto lampeggiante
                self.blink_manager.start_blinking(self.current_layer, selected_feature_ids)
                
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
    
    def reset_filter(self):
        self.blink_manager.stop_blinking()
        
        try:
            if self.current_layer:
                if self.original_renderer:
                    self.current_layer.setRenderer(self.original_renderer)
                    self.current_layer.triggerRepaint()
                self.current_layer.removeSelection()
                iface.messageBar().pushMessage("Filtro resettato", 
                                             "Tutti i record sono visibili", 
                                             level=0, duration=3)
        except Exception as e:
            iface.messageBar().pushMessage("Errore", 
                                         f"Errore durante il reset: {str(e)}", 
                                         level=2, duration=5)
    
    def closeEvent(self, event):
        """Pulizia quando la finestra viene chiusa"""
        self.blink_manager.stop_blinking()
        super().closeEvent(event)