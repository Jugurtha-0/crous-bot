import requests

TOKEN = "8988887991:AAEsocx4SddEiyXkc_ORHdMUEtqdcGTp0gc"

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

response = requests.get(url)

print(response.json())
