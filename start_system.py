"""
Script de inicio rápido del sistema
Inicia todos los componentes principales
"""
import subprocess
import sys
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def print_header(text):
    """Imprime encabezado decorado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print_header("Verificando Dependencias")
    
    try:
        import kafka
        print("✓ kafka-python instalado")
    except ImportError:
        print("✗ kafka-python no encontrado")
        return False
    
    try:
        import pymongo
        print("✓ pymongo instalado")
    except ImportError:
        print("✗ pymongo no encontrado")
        return False
    
    try:
        import flask
        print("✓ Flask instalado")
    except ImportError:
        print("✗ Flask no encontrado")
        return False
    
    print("\n✅ Todas las dependencias están instaladas")
    return True


def start_producer():
    """Inicia el Kafka producer"""
    print_header("Iniciando Kafka Producer")
    
    producer_script = PROJECT_ROOT / "streaming" / "producer.py"
    
    if not producer_script.exists():
        print(f"✗ No se encontró {producer_script}")
        return None
    
    process = subprocess.Popen(
        [sys.executable, str(producer_script)]
    )
    
    print(f"✓ Producer iniciado (PID: {process.pid})")
    return process


def start_alert_service():
    """Inicia el servicio de alertas"""
    print_header("Iniciando Alert Service")
    
    alerts_script = PROJECT_ROOT / "streaming" / "alerts.py"
    
    if not alerts_script.exists():
        print(f"✗ No se encontró {alerts_script}")
        return None
    
    process = subprocess.Popen(
        [sys.executable, str(alerts_script)]
    )
    
    print(f"✓ Alert Service iniciado (PID: {process.pid})")
    return process


def start_flask_app():
    """Inicia la aplicación Flask"""
    print_header("Iniciando Flask Web App")
    
    flask_script = PROJECT_ROOT / "flask_web_app" / "app.py"
    
    if not flask_script.exists():
        print(f"✗ No se encontró {flask_script}")
        return None
    
    process = subprocess.Popen(
        [sys.executable, str(flask_script)]
    )
    
    print(f"✓ Flask App iniciada (PID: {process.pid})")
    print("  Acceder a: http://localhost:5000")
    return process


def main():
    """Función principal"""
    print_header("🚀 Sistema de Análisis de Acciones - Inicio Rápido")
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ Instala las dependencias primero:")
        print("   pip install -r requirements.txt")
        return
    
    # Lista de procesos
    processes = []
    
    try:
        # Esperar un poco para que se inicien
        time.sleep(2)
        
        # Iniciar producer
        producer = start_producer()
        if producer:
            processes.append(("Producer", producer))
        
        time.sleep(2)
        
        # Iniciar alert service
        alerts = start_alert_service()
        if alerts:
            processes.append(("Alerts", alerts))
        
        time.sleep(2)
        
        # Iniciar Flask
        flask_app = start_flask_app()
        if flask_app:
            processes.append(("Flask", flask_app))
        
        print_header("✅ Sistema Iniciado")
        print("Componentes activos:")
        for name, proc in processes:
            print(f"  - {name}: PID {proc.pid}")
        
        print("\n📊 Accesos:")
        print("  - Web App: http://localhost:5000")
        print("  - Grafana: http://localhost:3000")
        print("  - Kibana: http://localhost:5601")
        print("  - Airflow: http://localhost:8080")
        
        print("\n⚠️  Para detener el sistema, presiona Ctrl+C")
        
        # Esperar señal de interrupción
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        
        for name, proc in processes:
            print(f"  Deteniendo {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        
        print("✅ Sistema detenido correctamente")


if __name__ == "__main__":
    main()
