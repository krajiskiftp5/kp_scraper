from bs4 import BeautifulSoup
from csvsort import csvsort
import requests
import csv
import time
import datetime
import json

j = open('config.json')
config = json.load(j)

proxies = {"https":config["proxy"]}
l = [config["link_structure"][0]["part1"],config["link_structure"][1]["part1"]]
l2 = [config["link_structure"][0]["part2"],config["link_structure"][1]["part2"]]
toPrice = config["link_structure"][2]["part3"]
end = config["link_structure"][3]["part4"]

abs_start_time = time.time()

computer_type = input("Tip racunara: 0 - pc; 1 - laptop: ")
lowEuro = input("Unesi donju granicu cene: ")
highEuro = input("Unesi gornju granicu cene: ")
brStranicaZaObradu = int(input("Broj stranica za obradu: "))
leastPowerFullCPU = input("Not weaker than: ")
deepSearch = input("Deep search on?: ")

procesori = []

def get_cpu_list():
    procesori.append([])
    procesori.append([])

    with open('cpu_list.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            final = str(row['Model']).lower()
            procesori[0].append(final)
            final = str(row['Benchmark'])
            procesori[1].append(final)

    line = len(procesori[0])
    for i in range(len(procesori[0])):
        if leastPowerFullCPU == procesori[0][i]:
            line = i + 1
            print("line found")
            break

    procesori[0][0:line]
    procesori[1][0:line]

class Laptop:
    def __init__(self, id, name, url,price,benchmark,score,cpu):
        self.name = name
        self.id = id

        self.url = url
        self.price = price
        self.benchmark = benchmark
        self.score = score
        self.cpu = cpu

    def __lt__(self, other):
        return self.score < other.score

def cpuFoundId(name):
    max = 0
    index = -1

    for i in range(len(procesori[0])):
        at = name.find(procesori[0][i])
        if at != -1:
            if len(procesori[0][i]) > max:
                max = len(procesori[0][i])
                index = i

    return index


def rtj(link):
    laptop = requests.get(link).text
    print(laptop)
    lapSoup = BeautifulSoup(laptop,'lxml')
    opis = str(lapSoup.find_all(class_ = 'oglas-description')).lower()
    print(opis)
    return cpuFoundId(opis)

get_cpu_list()

lnk = l[int(computer_type)] + str(1) + l2[int(computer_type)]  + lowEuro + toPrice + highEuro + end
sajt = requests.get(lnk, proxies= proxies).text
soup = BeautifulSoup(sajt, 'lxml')
br = soup.find('ul',class_ = 'pagesList clearfix')
euro = soup.find(class_ = 'nbs-widget squareBorder')
euro = float(str(euro).split('style="text-align:left; font-size: 12px;font-weight: bold;color: #023569;">\n')[2][5:-26].replace(",","."))

print("Kurs evra je: " + str(euro) + " RSD")

maxStrana = 0
for b in br:
    sts = str(b).split("this,'")
    if len(sts) > 1:
        if int(sts[1].split("\'")[0]) > maxStrana:
            maxStrana = int(sts[1].split("\'")[0])

print("Broj dostupnih strana u zadatom opsegu je: " + str(maxStrana))
count = 0

with open("output.txt","w") as f,open('names.csv', 'w', newline='') as csvfile: 
    fieldnames = ['name','link','cpuID','cpuName','cpuScore', 'price','totalScore']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for brStr in range(min(brStranicaZaObradu,maxStrana)):
        start_time = time.time()
        sajt = requests.get(l[int(computer_type)] + str(brStr) + l2[int(computer_type)]  + lowEuro + toPrice + highEuro + end, proxies= proxies).text

        print("BS4 je radila: " + str(time.time() - start_time) + "s\n")

        soup = BeautifulSoup(sajt, 'lxml')
        sales = soup.find_all(class_ = 'adName')
        prices = soup.find_all(class_ = 'adPrice')
        description = soup.find_all(class_ = 'adDescription descriptionHeight')

        print("Obrada BS4 je radila: " + str(time.time() - start_time) + "s\n")

        for i in range(len(sales)):
            sal = str(sales[i])
            s = sal.split('"')

            link = 'https://www.kupujemprodajem.com' + s[3]         
            name = s[3].split("/")[3].replace("-"," ")
            opis = str(description[i])[62:-18]
            print(opis)
            price = str(prices[i])
            price = price[29:-13]

            p = price.replace("€","din")
            if p != price:
                p = float(p[0:-4].replace(",",".")) * euro
            else:
                p = float(price[0:-4].replace(".",""))
            price = p
            print(price)

            opis = opis.lower().replace("-"," ")

            testableText = []
            testableText.append(name)
            testableText.append(opis)

            for txt in testableText:
                cpu = cpuFoundId(txt)
                if cpu != -1:
                    break       

            totalScore = float(procesori[1][cpu]) / price
                
            f.write(link + "\n")
            f.write(name + "\n")
            f.write(str(price) + "\n")
            f.write(procesori[0][cpu] + "\n")
            
            if cpu == -1 and deepSearch == "1":
                print("Dublja potraga na: " + name)
                laptop = requests.get(link, proxies= proxies).text
                lapSoup = BeautifulSoup(laptop,'lxml')
                opis = str(lapSoup.find_all(class_ = 'oglas-description')).lower().replace("-"," ")
                cpu = cpuFoundId(opis)
                if cpu != -1:
                    print("SUCCESS")
                    print(procesori[0][cpu])
                    count = count + 1
                else:
                    print("FAIL")
            else:
                print(procesori[0][cpu])
                count = count + 1

            writer.writerow({'name': name, 'link': link, 'cpuID': cpu,'cpuName': procesori[0][cpu],
            'cpuScore': procesori[1][cpu],'price': price, 'totalScore': totalScore})

        print("Ova stranica se obradjivala ukupno: " + str(time.time() - start_time) + "s\n")
        
outName = lowEuro + "-" + highEuro + "-" + str(min(brStranicaZaObradu,maxStrana)) + "-" + str(datetime.datetime.now()) + ".csv"
csvsort('names.csv', [6],output_filename=outName)

rate = float(count) / float(min(brStranicaZaObradu,maxStrana) * 30) * 100

print("Uspešnost imena je: " + str(rate) + "%")
print("Prosečno vreme po stranici: " + str((time.time() - abs_start_time) / min(brStranicaZaObradu,maxStrana))  + "s ")
print("Program radio: " + str(time.time() - abs_start_time)  + "s ")













