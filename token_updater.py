import requests
import uuid


def query_gigachat():
    GigaChatKey = 'MjI2YzEzYWItODliMC00MTc0LTk0MWItNDMzZDBjZWVkNDUzOjAzMTIzNTAzLTE5YjAtNDY2Ni04NmNlLThiY2Q5ODg3ODIzMg=='
    rq_uid = str(uuid.uuid4())

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = {
        'scope': 'GIGACHAT_API_PERS'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {GigaChatKey}'
    }

    response = requests.request("POST", url, headers=headers, data=payload,
                                verify=False)  # verify=False Отключает проверку наличия сертификатов НУЦ Минцифры
    giga_token = response.json()['access_token']
    print(giga_token)
    return giga_token

