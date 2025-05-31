from qgis.core import QgsProject, QgsField, QgsVectorLayerJoinInfo, edit, Qgis
from PyQt5.QtCore import QVariant
from qgis.utils import iface

def has_existing_join(ple_layer, map_layer):
    """Controlla se esiste già un join tra i layer"""
    for join in ple_layer.vectorJoins():
        if join.joinLayerId() == map_layer.id():
            return True
    return False

def update_id_map(ple_layer):
    """Aggiorna ID_MAP con l'espressione richiesta"""
    with edit(ple_layer):
        # Crea campo se non esiste - NUOVA SINTASSI
        if ple_layer.fields().indexFromName('ID_MAP') == -1:
            field = QgsField('ID_MAP', QVariant.String, 'text', 255, 0)
            ple_layer.addAttribute(field)
            iface.messageBar().pushMessage("Info", f"Creato campo ID_MAP in {ple_layer.name()}", level=Qgis.Info)
        
        # Aggiornamento diretto e sicuro
        for feature in ple_layer.getFeatures():
            try:
                inspire_id = feature['INSPIREID_LOCALID']
                if inspire_id:
                    # Rimuovi tutto dopo l'ultimo punto e sostituisci PLA con MAP
                    new_value = inspire_id.rsplit('.', 1)[0].replace('PLA', 'MAP')
                    feature['ID_MAP'] = new_value
                    ple_layer.updateFeature(feature)
            except Exception as e:
                iface.messageBar().pushMessage("Errore", f"Errore su feature {feature.id()}: {str(e)}", level=Qgis.Warning)

def run_script():
    project = QgsProject.instance()
    join_creato = False
    
    # Trova tutte le coppie _ple e _map
    ple_layers = {}
    map_layers = {}
    
    for layer in project.mapLayers().values():
        if layer.name().endswith('_ple'):
            parts = layer.name().rsplit('_', 2)
            key = (parts[0], parts[1])
            ple_layers[key] = layer
        elif layer.name().endswith('_map'):
            parts = layer.name().rsplit('_', 2)
            key = (parts[0], parts[1])
            map_layers[key] = layer

    # Processa ogni coppia
    for key in ple_layers:
        if key not in map_layers:
            iface.messageBar().pushMessage("Info", f"Manca layer MAP per {key} - saltato", level=Qgis.Info)
            continue
            
        ple_layer = ple_layers[key]
        map_layer = map_layers[key]

        if has_existing_join(ple_layer, map_layer):
            iface.messageBar().pushMessage("Info", f"Join già esistente per {ple_layer.name()} - saltato", level=Qgis.Info)
            continue

        # 1. Aggiorna ID_MAP
        iface.messageBar().pushMessage("Info", f"Aggiorno {ple_layer.name()}", level=Qgis.Info)
        update_id_map(ple_layer)
        
        # 2. Crea join
        join_info = QgsVectorLayerJoinInfo()
        join_info.setJoinFieldName('INSPIREID_LOCALID')
        join_info.setTargetFieldName('ID_MAP')
        join_info.setJoinLayerId(map_layer.id())
        join_info.setUsingMemoryCache(True)
        join_info.setJoinLayer(map_layer)
        join_info.setPrefix('map_')
        
        ple_layer.addJoin(join_info)
        join_creato = True
        iface.messageBar().pushMessage("Successo", f"Creato join tra {ple_layer.name()} e {map_layer.name()}", level=Qgis.Success)

    if join_creato:
        return True, "Operazione completata con successo! Il plugin verrà ricaricato.", True
    else:
        return True, "Operazione completata con successo! Nessun nuovo join creato.", False

def main():
    try:
        success, message, needs_reload = run_script()
        return success, message, needs_reload
    except Exception as e:
        return False, f"Errore durante l'esecuzione: {str(e)}", False