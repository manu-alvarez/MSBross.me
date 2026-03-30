import ftplib
import os
import subprocess

FTP_HOST = os.getenv('FTP_HOST', 'msbros.ftp.tb-hosting.com')
FTP_USER = os.getenv('FTP_USER', 'msbrossme@msbrossme')
FTP_PASS = os.getenv('FTP_PASS')

if not FTP_PASS:
    raise SystemExit('FTP_PASS environment variable is required for deployment')

# Local directories with the corrected files
LOCAL_ROOT = os.getenv('LOCAL_ROOT', '/Users/manu/Desktop/msbross.me')
VPS_BACKUP = os.getenv('VPS_BACKUP', '/Users/manu/Desktop/msbross.me/vps_backup')
REMOTE_BASE = os.getenv('REMOTE_BASE', '/www')

# Deployment mapping: (local_source, remote_dest)
DEPLOY_LIST = [
    # Hub and API Gateway (The Brain)
    (f"{LOCAL_ROOT}/index.html", f"{REMOTE_BASE}/index.html"),
    (f"{LOCAL_ROOT}/api.php", f"{REMOTE_BASE}/api.php"),
    
    # Nikolina AI (Voice Assistant)
    (f"{LOCAL_ROOT}/livekit-frontend/dist", f"{REMOTE_BASE}/nikolina"),
    
    # IAPuta OS (Cognitive System)
    (f"{LOCAL_ROOT}/IAPutaOS/frontend/dist", f"{REMOTE_BASE}/iaputa"),
    
    # Moko-Translate (Neural Translation)
    (f"{LOCAL_ROOT}/Traductor/client/dist", f"{REMOTE_BASE}/traductor"),
    (f"{LOCAL_ROOT}/Traductor/client/dist", f"{REMOTE_BASE}/moko"),
    
    # DOHLER (Task Architecture)
    (f"{LOCAL_ROOT}/dohler_src/frontend/dist", f"{REMOTE_BASE}/dohler"),
    
    # TaskFlow Pro & Legacy
    (f"{LOCAL_ROOT}/taskflow_pro_src/dist", f"{REMOTE_BASE}/taskflow"),
    (f"{VPS_BACKUP}/COMBIPRO", f"{REMOTE_BASE}/combipro"),
]

def upload_file(ftp, local_path, remote_path):
    print(f"  Subiendo: {remote_path}...")
    try:
        with open(local_path, 'rb') as f:
            ftp.storbinary(f"STOR {remote_path}", f)
    except Exception as e:
        print(f"  ❌ Error subiendo {remote_path}: {e}")

def ensure_dir(ftp, remote_dir):
    parts = remote_dir.split('/')
    path = ""
    for part in parts:
        if not part: continue
        path += "/" + part
        try:
            ftp.mkd(path)
            print(f"Creado directorio: {path}")
        except:
            pass

def build_projects():
    print("🔨 Construyendo proyectos React/Vite para Cache-Busting y sincronización...")
    build_commands = [
        (f"{LOCAL_ROOT}/IAPutaOS/frontend", "npm run build"),
        (f"{LOCAL_ROOT}/livekit-frontend", "npm run build"),
        (f"{LOCAL_ROOT}/Traductor/client", "npm run build"),
        (f"{LOCAL_ROOT}/dohler_src/frontend", "npm run build"),
        (f"{LOCAL_ROOT}/taskflow_pro_src", "npm run build")
    ]
    
    for d, cmd in build_commands:
        if os.path.exists(d):
            print(f"  👉 Construyendo en {d}...")
            try:
                subprocess.run(cmd, cwd=d, shell=True, check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(f"  ❌ Error construyendo {d}")
        else:
            print(f"  ⚠️ Ignorando {d} (No existe)")

def main():
    build_projects()
    print(f"\n🚀 Iniciando despliegue en {FTP_HOST}...")
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
    except Exception as e:
        print(f"❌ Error de conexión FTP: {e}")
        return

    for local_source, remote_dest in DEPLOY_LIST:
        print(f"\nProcesando: {os.path.basename(local_source)} -> {remote_dest}")
        
        if os.path.isfile(local_source):
            ensure_dir(ftp, os.path.dirname(remote_dest))
            upload_file(ftp, local_source, remote_dest)
        else:
            ensure_dir(ftp, remote_dest)
            for root, dirs, files in os.walk(local_source):
                # Skip node_modules and .git to be serverless/lightweight
                if "node_modules" in root or ".git" in root:
                    continue
                    
                rel_path = os.path.relpath(root, local_source)
                remote_dir = remote_dest if rel_path == "." else f"{remote_dest}/{rel_path.replace(os.sep, '/')}"
                
                ensure_dir(ftp, remote_dir)
                for file in files:
                    local_file = os.path.join(root, file)
                    remote_file = f"{remote_dir}/{file}"
                    
                    # Rename CombiPro main file to index.html if needed
                    if file == "generador-combis-pro.html":
                        remote_file = f"{remote_dir}/index.html"
                        
                    upload_file(ftp, local_file, remote_file)

    ftp.quit()
    print("\n✅ DESPLIEGUE COMPLETO. Todos los sistemas operativos y serverless en msbross.me")

if __name__ == "__main__":
    main()
