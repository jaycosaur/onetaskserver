import sys
import multiprocessing
import time
import cv2
import urllib.request
import numpy as np 
from pydarknet import Detector, Image
import urllib.request
from harvesters.core import Harvester

thresh = 0.5
hier_thresh = 0.2

#darknet_path = '/home/server/Projects/pyyolo/darknet'
datacfg = '/home/server/Projects/YOLO3-4-Py/cfg/coco.data'
cfgfile = '/home/server/Projects/YOLO3-4-Py/cfg/yolov3.cfg'
weightfile = '/home/server/Projects/YOLO3-4-Py/weights/yolov3.weights'
#cfgfile = 'tiny-yolo/yolov2-tiny.cfg'
#weightfile = 'tiny-yolo/yolov2-tiny.weights'

TRIGGER_FAR_URL = 'http://192.168.1.100:8000/trigger-far'
TRIGGER_CLOSE_URL = 'http://192.168.1.100:8000/trigger-close'
TRIGGER_TRUCK_URL = 'http://192.168.1.100:8000/trigger-truck'
TRIGGER_FAR_FLASH_URL = 'http://192.168.1.100:8000/trigger-far-flash'
TRIGGER_CLOSE_FLASH_URL = 'http://192.168.1.100:8000/trigger-close-flash'
TRIGGER_TRUCK_FLASH_URL = 'http://192.168.1.100:8000/trigger-truck-flash'

CTI_FILE = '/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti'

LOG = True

CAM_CONFIG = {
    'CAM_1': {
        'name': 'QG0170070015',
        'window': 'UPROAD-TRIGGER',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070015',
        'rotate': False
    },
    'CAM_2': {
        'name': 'QG0170070016',
        'window': 'WIDE-TRIGGER',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070016',
        'rotate': True
    },
}

def worker(camId):   

    # declare Detector in isolation from Camera object for reinitiation of Camera under failure.
    #  
    net = Detector(bytes(cfgfile, encoding="utf-8"), bytes(weightfile, encoding="utf-8"), 0,
                   bytes(datacfg, encoding="utf-8"))

    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']
    h = Harvester()
    h.add_cti_file(CTI_FILE)
    h.update_device_info_list()


    try:
        cam = h.create_image_acquisition_manager(serial_number=CAM_NAME)
        print ("Camera found")

    except:
        print ("Camera Not Found")
        exit ()

    cam.start_image_acquisition()

    #variable declarations

    lastTime = time.time()
    transposeTime = 0
    i = 0
    numberCars = 0
    lastSnapshot = None
    cv2.namedWindow(WINDOW_NAME, flags=0)

    carColor = (255,0,0)
    busColor = (0,255,0)
    truckColor = (0,0,255)
    phoneColor = (0,255,255)
    baseColor = (255,255,255)

    baseRes = 400
    scale = 800/1920

    #as percentages

    uproadThresh = 295
    truckThresh = 230
    closeThresh = 180
    extraThresh = 50
    leftBound = 50
    leftBound2 = 70
    rightBound = 125
    rightBound2 = 125
    marginOfError = 20

    
    factor = baseRes/320
    uproadThresh = int(uproadThresh*factor)
    truckThresh = int(truckThresh*factor)
    closeThresh = int(closeThresh*factor )
    extraThresh = int(50*factor )
    leftBound = int(leftBound*factor )
    leftBound2 = int(leftBound2*factor )
    rightBound = int(125*factor )
    rightBound2 = int(125*factor )

    showLines = False
    showYolo = False

    triggerDelay = 0.250
    uproadLastTrigger = time.time()
    truckLastTrigger = time.time()
    closeLastTrigger = time.time()

    while(True):
        buffer = cam.fetch_buffer() #cam fails here often!
        payload = buffer.payload.components
        if LOG:
            print(payload)
        if(payload):
            image = payload[0].data
            if LOG:
                print(image)
            small = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
            rgb = cv2.cvtColor(small, cv2.COLOR_BayerRG2RGB)
            img = np.rot90(rgb,1)
            c, h1, w1 = rgb.shape[2], rgb.shape[1], rgb.shape[0]

            img2 = Image(img)
            results = net.detect(img2)
            if LOG:
                print(results)
            k = cv2.waitKey(1)

            if k==113:    # Esc key to stop
                showLines = True
            elif k==97:
                showLines = False
            elif k==122:
                showYolo = True
            elif k==120:
                showYolo = False
                

            if showLines and camId=='CAM_2':
                    cv2.line(rgb, (uproadThresh,0), (uproadThresh, w1), (255,255,0), 1)
                    cv2.line(rgb, (uproadThresh+marginOfError,0), (uproadThresh+marginOfError, w1), (255,0,0), 1)
                    cv2.line(rgb, (uproadThresh-marginOfError,0), (uproadThresh-marginOfError, w1), (255,0,0), 1)
                    cv2.putText(rgb, 'Up-Road', (uproadThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(rgb, (truckThresh,0), (truckThresh, w1), (255,255,0), 1)
                    cv2.line(rgb, (truckThresh+marginOfError,0), (truckThresh+marginOfError, w1), (255,0,0), 1)
                    cv2.line(rgb, (truckThresh-marginOfError,0), (truckThresh-marginOfError, w1), (255,0,0), 1)
                    cv2.putText(rgb, 'Truck', (truckThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(rgb, (closeThresh,0), (closeThresh, w1), (255,255,0), 1)
                    cv2.line(rgb, (closeThresh+marginOfError,0), (closeThresh+marginOfError, w1), (255,0,0), 1)
                    cv2.line(rgb, (closeThresh-marginOfError,0), (closeThresh-marginOfError, w1), (255,0,0), 1)
                    cv2.putText(rgb, 'Close', (closeThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(rgb, (0,rightBound), (h1, rightBound), (255,255,255), 1)
                    cv2.line(rgb, (0,leftBound2), (h1, leftBound2), (255,255,255), 1)
                    cv2.line(rgb, (0,leftBound), (h1, leftBound), (255,255,255), 1)

            if showLines and camId=='CAM_1':
                cv2.line(rgb, (extraThresh,0), (extraThresh, w1), (255,255,0), 1)
                cv2.putText(rgb, 'Up-Road', (extraThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                #cv2.line(rgb, (0,rightBound2), (h1, rightBound2), (255,255,255), 1)

            bounds = 100

            for cat, score, bounds in results:
                    x, y, w, h = bounds
                    x, y = (h1-int(y), int(x))
                    x1,y1,x2,y2 = [int(x-h/2),int(y-w/2),int(x+h/2),int(y+w/2)]

                    type = str(cat.decode("utf-8"))
                    color = baseColor
                    if (type == 'car'):
                        color = carColor
                    if (type == 'bus'):
                        color = busColor
                    if (type == 'truck'):
                        color = truckColor
                    if (type == 'phone'):
                        color = phoneColor
                    #x1,y1,x2,y2 = [int(x+w/2),int(y+h/2),int(x-w/2),int(y-h/2)]
                    #cv2.rectangle(rgb, (int(x-w/2),int(y-h/2)),(int(x+w/2),int(y+h/2)),(255,0,0))
                    #cv2.line(rgb, (x1,y1), (x1, y2), color, 2)
                    if showYolo and h>5:
                        #cv2.rectangle(rgb, (x1,y1),(x2,y2),color)
                        #cv2.putText(rgb, str(cat.decode("utf-8")), (int(x), int(y)), cv2.FONT_HERSHEY_COMPLEX, 1, color)
                        cv2.circle(rgb, (int(x), int(y)), int(2),
                            (0, 255, 0), 3)

                    currentTime = time.time()

                    if y <= rightBound and camId=='CAM_2' and h>10 and w>10:
                        if x>=uproadThresh-10 and x<=uproadThresh+10 and y>=leftBound2 and (currentTime-uproadLastTrigger)>triggerDelay:
                            urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                            if LOG:
                                print('FAR TRIG')
                            uproadLastTrigger = currentTime
                        #if x1<=truckThresh and x2>=truckThresh and (currentTime-truckLastTrigger)>triggerDelay:
                        if x>=truckThresh-marginOfError and x<=truckThresh+marginOfError and y>=leftBound and (currentTime-truckLastTrigger)>triggerDelay:
                            urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                            if LOG:
                                print('TRUCK TRIG')
                            numberCars += 1
                            truckLastTrigger = currentTime
                        #if x1<=closeThresh and x2>=closeThresh and (currentTime-closeLastTrigger)>triggerDelay:
                        if x>=closeThresh-marginOfError*2 and x<=closeThresh+marginOfError*2 and y>=leftBound and (currentTime-closeLastTrigger)>triggerDelay:
                            urllib.request.urlopen(TRIGGER_CLOSE_URL).read()
                            if LOG:
                                print('CLOSE TRIG')
                            closeLastTrigger = currentTime
                    
                    if camId=='CAM_1':
                        if y1<=rightBound2   and y2>=rightBound2 and False :
                            urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                            numberCars += 1
                    

            '''predictions = []
            for output in predictions:
                left, right, top, bottom, what, prob = output['left'],output['right'],output['top'],output['bottom'],output['class'],output['prob']
                #print(output)
                #lastSnapshot = snapshot.copy()
                #cv2.imshow("Snapshots", lastSnapshot)
                if( what == 'car' ):
                    print(output)
                    numberCars += 1
                    cv2.rectangle(rgb, (50,50), (100,150), (255, 255, 255), 20)
                    if ( camId =="CAM_2" ):
                        urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                        urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                        urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()'''

            if IS_ROTATE:
                cv2.imshow(WINDOW_NAME, np.rot90(rgb))
            else:
                cv2.imshow(WINDOW_NAME, rgb)

            cv2.waitKey(1)
            buffer.queue()
            
            print("Count: ", numberCars, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime))
            lastTime = time.time()
            i += 1

    cam.stop_image_acquisition()
    cam.destroy()

if __name__ == '__main__':
    camIds = ['CAM_2','CAM_1']
    #camIds = ['CAM_1']
    for i in camIds:
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()