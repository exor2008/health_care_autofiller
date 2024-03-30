let proc = ps | where name =~ ".*health-care-autofiller.*" | length

if $proc == 0 {
  echo "Runing health autofiller."
  /home/pi/.local/bin/poetry run python /home/pi/health_care_autofiller/main.py
} 

