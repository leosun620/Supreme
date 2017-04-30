#!/usr/bin/python
import os, sys, json, time, requests, urllib2, threading, ConfigParser, types, functools
from datetime import datetime

global stopPoll
global mobileStockJson

rootDirectory = os.getcwd()
c = ConfigParser.ConfigParser()
configFilePath = os.path.join(rootDirectory, 'config.cfg')
c.read(configFilePath)

class Config:
    poll=int(c.get('timeComponents','poll'))
    ghostCheckoutPrevention=c.get('timeComponents','ghostCheckoutPrevention')
    billingName=c.get('cardInfo','firstAndLast')
    email=c.get('cardInfo','email')
    phone=c.get('cardInfo','phone')
    streetAddress=c.get('cardInfo','address')
    zipCode=c.get('cardInfo','zip')
    shippingCity=c.get('cardInfo','city')
    shippingState=c.get('cardInfo','state')
    shippingCountry=c.get('cardInfo','country')
    cardType=c.get('cardInfo','cardType')
    cardNumber=c.get('cardInfo','cardNumber')
    cardMonth=c.get('cardInfo','cardMonth')
    cardYear=c.get('cardInfo','cardYear')
    cardCVV=c.get('cardInfo','cardCVV')

def UTCtoEST():
    current=datetime.now()
    return str(current) + ' EST'

def copy_func(f):
    g = types.FunctionType(f.func_code, f.func_globals, name=f.func_name,
                           argdefs=f.func_defaults,
                           closure=f.func_closure)
    g = functools.update_wrapper(g, f)
    return g

def productThread(name, size, color, qty):
    #include sleep and found flag to break in main - try catch fo NULL init handling
    stopPoll = 0
    while 1:
        while not(mobileStockJson):
            pass
        for category in range(0, len(mobileStockJson['products_and_categories'].values())):
            for item in range(0, len(mobileStockJson['products_and_categories'].values()[category])):
                #print mobileStockJson['products_and_categories'].values()[category][item]['name']
                if name in mobileStockJson['products_and_categories'].values()[category][item]['name']:
                    #Retain useful info here like index but mostly the id for add request
                    stopPoll = 1
                    listedProductName = mobileStockJson['products_and_categories'].values()[category][item]['name']
                    productID = mobileStockJson['products_and_categories'].values()[category][item]['id']
                    print
                    print UTCtoEST(),'::',listedProductName, productID, 'found ( MATCHING ITEM DETECTED )'
                    print
        if (stopPoll != 1): 
            print UTCtoEST(),':: Reloading and reparsing page...'
            time.sleep(user_config.poll)
        else:
            #Item found continue to add and checkout
            foundItemColor = 0
            foundItemSize = 0
            atcSession = requests.session()
            print UTCtoEST(),':: Selecting',listedProductName,'(',productID,')'
            productItemData = atcSession.get('http://www.supremenewyork.com/shop/'+str(productID)+'.json',headers={'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Mobile/11D257'}).json()
            for listedProductColors in productItemData['styles']:
                if color in listedProductColors['name']:
                    foundItemColor = 1
                    colorProductId = listedProductColors['id']
                    for listedProductSizes in listedProductColors['sizes']:
                        if size in listedProductSizes['name']:
                            foundItemSize = 1
                            sizeProductId = listedProductSizes['id']
                            print UTCtoEST(),':: Selecting size:', size,'(',color,')','(',sizeProductId,')'
                            break
            if (foundItemColor == 0 or foundItemSize == 0):
                #couldn't find user desired selection of color and size. picking defaults
                print UTCtoEST(),':: Selecting default colorway:',productItemData['styles'][0]['name']
                selectedDefaultSize = str(productItemData['styles'][0]['sizes'][len(productItemData['styles'][0]['sizes'])-1]['name'])
                sizeProductId = str(productItemData['styles'][0]['sizes'][len(productItemData['styles'][0]['sizes'])-1]['id'])
                selectedDefaultColor = productItemData['styles'][0]['name']
                colorProductId = productItemData['styles'][0]['id']
                print UTCtoEST(),':: Selecting default size:',sizeName,'(',variant,')'


            break

if __name__ == '__main__':
    stopPoll = 0
    mobileStockJson = None
    user_config = Config()
    assert len(c.options('productName')) == len(c.options('productSize')) == len(c.options('productColor')) == len(c.options('productQty')),'Assertion Error: Product section lengths unmatched'
    for enumerableItem in range(0, len(c.options('productName'))):
        itemName = c.get('productName',c.options('productName')[enumerableItem]).title()
        itemSize = c.get('productSize',c.options('productSize')[enumerableItem]).title()
        itemColor = c.get('productColor',c.options('productColor')[enumerableItem]).title()
        itemQty = c.get('productQty',c.options('productQty')[enumerableItem])
        exec('productThread'+str(enumerableItem+1) + " = copy_func(productThread)")
        myThreadFunc = 'productThread'+str(enumerableItem+1)+'("'+itemName+'","'+itemSize+'","'+itemColor+'","'+itemQty+'")'
        myThreadFunc = eval('productThread'+str(enumerableItem+1))
        print itemName, itemSize, itemColor, itemQty,'Thread initialized!'
        t = threading.Thread(target=myThreadFunc, args=(itemName, itemSize, itemColor, itemQty,))
        #t = threading.Thread(target=exec(myThreadFunc), args=(itemName, user_config.poll, itemColor, itemSize, itemQty, user_config.ghostCheckoutPrevention,))
        t.start()

    mobileStockPollSession = requests.session()
    headers = {
        'Host':              'www.supremenewyork.com',
        'Accept-Encoding':   'gzip, deflate',
        'Connection':        'keep-alive',
        'Proxy-Connection':  'keep-alive',
        'Accept':            'application/json',
        'User-Agent':        'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13G34',
        'Referer':           'http://www.supremenewyork.com/mobile',
        'Accept-Language':   'en-us',
        'X-Requested-With':  'XMLHttpRequest'
    }

    while 1:
        if (stopPoll != 1):
            mobileStockJson = mobileStockPollSession.get('http://www.supremenewyork.com/mobile_stock.json', headers=headers).json()
            time.sleep(user_config.poll)
        else:
            #Item/s found! wait for thread completion
            pass 