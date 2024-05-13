from PIL import Image
import requests
from bs4 import BeautifulSoup as bs
import json


class get_license_details:
    def __init__(self, url:str, license_number:str, date_of_birth:str):
        self.url = url
        self.license_number = license_number
        dob = date_of_birth.split('-')
        dob.reverse()
        self.date_of_birth = '-'.join(dob)
        self.form_input= {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': "form_rcdl:j_idt44",
            'javax.faces.partial.execute': "@all",
            'javax.faces.partial.render': ['form_rcdl:pnl_show','form_rcdl:pg_show','form_rcdl:rcdl_pnl'],
            'form_rcdl:j_idt44': "form_rcdl:j_idt44",
            'form_rcdl': 'form_rcdl',
            'form_rcdl:j_idt34:CaptchaID': '',
            'form_rcdl:tf_dlNO': self.license_number, 
            'form_rcdl:tf_dob_input': self.date_of_birth,
            'javax.faces.ViewState': None
        }
 

    def check_status(self):
        response = requests.get(self.url)
        if response.status_code == 200:  
            return True
        return False

    def send_input(self):
        error_message = ''
        with requests.Session() as session:
            resp =  session.get(self.url)
            if resp.status_code == 200:
                data = resp.content
                parsedData = bs(data, 'html.parser')
                form_data = parsedData.find('form')

                param = parsedData.find('input', attrs={"name": 'javax.faces.ViewState'})
                self.form_input['javax.faces.ViewState'] = param["value"]
        
                image = form_data.find(attrs={'id':'form_rcdl:j_idt34:j_idt39'})
                image_link = 'https://parivahan.gov.in' + image.get('src')
                captcha = Image.open(requests.get(image_link, stream=True).raw)
                captcha.show()

                cap = input('Enter the captcha: ') 
                next_url = 'https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml'

                self.form_input['form_rcdl:j_idt34:CaptchaID'] = cap        
        
                resp_data = session.post(next_url, data=self.form_input)
                received = resp_data.content
                parsedReceived = bs(received, "lxml")
                error_message = parsedReceived.find('span', attrs={"class" : "ui-messages-error-summary"})
        
        if error_message:
            print("Error:", error_message.text)
            exit()
        else:
            return parsedReceived

    def parse_data(self, parsed_received):
        data = {}
        validity = {}
        class_of_vehicles = []
        for row in parsed_received.select('table tr'):
            row_data = row.find_all('td')
            cells = [cell.text.strip() for cell in row_data]
            if len(cells) == 2:
                data[cells[0]] = cells[1]
            elif 'Transport' in cells or 'Non-Transport' in cells:
                valid_from = cells[1].split(':')
                valid_to = cells[2].split(':')
                validity[cells[0]] = {'Valid_from' : valid_from[1], 'Valid_to' : valid_to[1]}
            elif 'TR' in cells or 'NT' in cells:
                class_of_vehicles.append({'cov_category': cells[0], 'class_of_vehicle': cells[1], 'cov_issue_date': cells[2]})
                        
        data['driving_license_validity_details'] = validity
        data['class_of_vehicle_details'] = class_of_vehicles

        return json.dumps(data, indent=4)        


def main():
    url = 'https://parivahan.gov.in/rcdlstatus/?pur_cd=101'
    license_num = input('Enter your License Number:')
    dob = input('Enter you Date of Birth in YYYY-MM-DD format:')
    
    login_object = get_license_details(url, license_num, dob)

    if login_object.check_status():
        response_received = login_object.send_input()
        parsed = login_object.parse_data(response_received)
        print(parsed)
    else:
        print('Some Error Occurred.')


if __name__ == "__main__":
    main()