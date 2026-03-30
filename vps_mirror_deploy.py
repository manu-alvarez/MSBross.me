import ftplib
import os

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
    # Hub and API
    (f"{LOCAL_ROOT}/index.html", f"{REMOTE_BASE}/index.html"),
    (f"{LOCAL_ROOT}/api.php", f"{REMOTE_BASE}/api.php"),
    (f"{LOCAL_ROOT}/api.php", f"{REMOTE_BASE}/traductor/api.php"),
    
    # Standalone Apps (Web Dist)
    (f"{LOCAL_ROOT}/web_dist/nikolina.html", f"{REMOTE_BASE}/nikolina.html"),
    (f"{LOCAL_ROOT}/web_dist/nikolina.html", f"{REMOTE_BASE}/nikolina/index.html"),
    (f"{LOCAL_ROOT}/web_dist/admin", f"{REMOTE_BASE}/admin"),
    (f"{LOCAL_ROOT}/web_dist/dev", f"{REMOTE_BASE}/dev"),
    (f"{LOCAL_ROOT}/web_dist/taskflow", f"{REMOTE_BASE}/taskflow"),
    (f"{LOCAL_ROOT}/web_dist/dohler", f"{REMOTE_BASE}/dohler"),
    (f"{LOCAL_ROOT}/web_dist/logisearch", f"{REMOTE_BASE}/logisearch"),
    (f"{LOCAL_ROOT}/web_dist/iaputa", f"{REMOTE_BASE}/iaputa"),
    
    # Moko-Translate (Traductor Neural)
    (f"{LOCAL_ROOT}/Traductor/client/dist", f"{REMOTE_BASE}/moko"),
    (f"{LOCAL_ROOT}/Traductor/client/dist", f"{REMOTE_BASE}/traductor"),
    
    # Legacy / Backups
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

def main():
    print(f"🚀 Iniciando despliegue en {FTP_HOST}...")
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)

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
