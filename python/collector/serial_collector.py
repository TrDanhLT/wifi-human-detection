import argparse,csv,serial
from datetime import datetime
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--port',required=True); p.add_argument('--baud',type=int,default=115200); p.add_argument('--output',default='data/raw/live/csi_recording.csv'); a=p.parse_args()
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); ser=serial.Serial(a.port,a.baud,timeout=1)
print(f'Listening on {a.port}');
with out.open('a',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    try:
        while True:
            line=ser.readline().decode('utf-8',errors='ignore').strip()
            if line: w.writerow([datetime.now().timestamp(),line]); f.flush(); print(line)
    except KeyboardInterrupt: pass
    finally: ser.close()
