import os
import wx
import time
import shutil
import threading
import requests
import numpy as np
import concurrent.futures
from pubsub import pub
from PIL import Image, ImageFilter
from selenium import webdriver
import glob

count = 0
img_urls = []
display_list = []
size = (360, 280)


# return the search links to images
def get_links():
    global img_urls
    imgs = open('links.txt', 'r')
    img_urls = [line.rstrip('\n') for line in imgs.readlines()]
    return img_urls

# return list of scraped jpgs
def get_imlist(path):
    image_list = []
    image_list = [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.jpg')]
    [x.lstrip('scraped_photos\\') for x in image_list]
    return [x.lstrip('scraped_photos\\') for x in image_list]

# return list of processed jps for display
def get_imlist_alt(path):
    return [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.jpg')]

# apply blur to images and save
def blur_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}') 
    img = img.filter(ImageFilter.GaussianBlur(10))

    img.thumbnail(size)
    img.save(f'processed_photos/blur/{img_name}')
    
# apply maximum filter to images and save
def max_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.MaxFilter)

    img.thumbnail(size)
    img.save(f'processed_photos/max/{img_name}')  

# apply medium filter to images and save
def med_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.MedianFilter)

    img.thumbnail(size)
    img.save(f'processed_photos/med/{img_name}')

# apply minimum filter to images and save
def min_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.MinFilter)

    img.thumbnail(size)
    img.save(f'processed_photos/min/{img_name}') 
    
# apply mode filter to images and save
def mode_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.ModeFilter)

    img.thumbnail(size)
    img.save(f'processed_photos/mode/{img_name}')   

# apply negative filter to images and save
def negative_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    for i in range(0, img.size[0]-1):
        for j in range(0, img.size[1]-1):
            # Get pixel value at (x,y) position of the image
            pixelColorVals = img.getpixel((i,j));
            # Invert color
            redPixel    = 255 - pixelColorVals[0]; # Negate red pixel
            greenPixel  = 255 - pixelColorVals[1]; # Negate green pixel
            bluePixel   = 255 - pixelColorVals[2]; # Negate blue pixel        
            # Modify the image with the inverted pixel values
            img.putpixel((i,j),(redPixel, greenPixel, bluePixel));

    img.thumbnail(size)
    img.save(f'processed_photos/negative/{img_name}')  

# apply sharpen filter to images and save
def sharpen_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.SHARPEN)

    img.thumbnail(size)
    img.save(f'processed_photos/sharpen/{img_name}')

# apply smoothen filter to images and save
def smoothen_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.SMOOTH_MORE)

    img.thumbnail(size)
    img.save(f'processed_photos/smoothen/{img_name}')

# enhance image edges and save
def edgeenhance_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)

    img.thumbnail(size)
    img.save(f'processed_photos/edgeenhance/{img_name}')

# detect image edges and save
def edgedetect_image(img_name): 
    img = Image.open(f'scraped_photos/{img_name}')
    img = img.filter(ImageFilter.FIND_EDGES)

    img.thumbnail(size)
    img.save(f'processed_photos/edgedetect/{img_name}')
    print(f'{img_name} was processed...')
   
    
def download_image(img_url):
    img_bytes = requests.get(img_url).content
    
    img_name = img_url.split('/')[4]
    img_name = f'scraped_photos/{img_name}.jpg'
    with open(img_name, 'wb') as img_file:
      img_file.write(img_bytes)
      print(f'{img_name} was downloaded...')

# threading panel
class TIPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size = wx.Size(540, 500))
        self.parent = parent
        
        self.SetBackgroundColour(wx.Colour(250, 255, 230))
        
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        self.inputsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.outputsizer = wx.BoxSizer(wx.VERTICAL)
        
        self.searchphotos = wx.TextCtrl(self, 0, size=wx.Size(335, 25),style=wx.BORDER_SUNKEN|wx.TE_PROCESS_ENTER)
        self.searchphotos.Bind(wx.EVT_TEXT_ENTER, self.getSearchResult)
        self.searchphotos.SetFont(font)
        self.searchphotos.SetForegroundColour(wx.Colour(0, 0, 0, alpha=wx.ALPHA_OPAQUE))
        self.inputsizer.Add(self.searchphotos, 0)

        self.searchbutton = wx.Button(self, id=wx.ID_ANY, label='SEARCH', size = (105,25))
        self.searchbutton.Bind(wx.EVT_BUTTON, self.search)
        self.inputsizer.Add(self.searchbutton, 0, wx.LEFT, 10)
        self.outputsizer.Add(self.inputsizer, 0, wx.ALIGN_CENTER|wx.TOP, 20)
        
        self.text = wx.StaticText(self, -1, 'SEARCH RESULTS')
        self.outputsizer.Add(self.text, 0, wx.ALIGN_CENTER|wx.TOP, 20)

        self.searchresult_scroller = wx.TextCtrl(self, -1, size=wx.Size(450, 350),style= wx.TE_MULTILINE|wx.BORDER_SUNKEN|wx.TE_READONLY)
        self.outputsizer.Add(self.searchresult_scroller, 0, wx.ALIGN_CENTER|wx.TOP, 10)

        self.clear_button = wx.Button(self, 0, "CLEAR", size = (100,25))
        self.clear_button.SetToolTip(wx.ToolTip('Clear search results'))
        self.clear_button.Bind(wx.EVT_BUTTON, self.clearSearch)

        self.getimages_button = wx.Button(self, 0, "SCRAPE", size = (100,25))
        self.getimages_button.SetToolTip(wx.ToolTip('Multithreaded image download'))
        self.getimages_button.Bind(wx.EVT_BUTTON, self.multithread_scrape)

        self.bottomsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomsizer.Add(self.getimages_button, 0, wx.ALIGN_CENTER|wx.RIGHT, 20)
        self.bottomsizer.Add(self.clear_button, 0, wx.ALIGN_CENTER)
        
        self.outputsizer.Add(self.bottomsizer, 0, wx.ALIGN_CENTER|wx.TOP, 15)
      
        self.SetSizer(self.outputsizer)
        self.outputsizer.Fit(self)
        self.Layout()
        
        self.Show()

    # clear button pressed
    def clearSearch(self, event):
        self.searchresult_scroller.SetValue('')
        self.searchphotos.SetValue('')
        pub.sendMessage('change_statusbar1', msg='Scrape Time :')
        return

    # enter pressed on txtcrl
    def getSearchResult(self, event):
        check = self.searchphotos.GetValue()
        if check != '':
          self.search(self)
        else:
          self.searchresult_scroller.SetValue("Please enter a search query")

    # search button pressed - search url with user defined search term
    def search(self, event):
        search_term = self.searchphotos.GetValue()
        if search_term != '':      
            self.searchresult_scroller.SetValue('')
            browser = webdriver.Firefox()
            url = "https://unsplash.com/search/photos/" + search_term
            browser.get(url)
            complete = False
            os.remove("links.txt")
            # we will open the file in apend mode
            link_file = open("links.txt", mode="a+")
            while not complete:
              try:
                  elem1 = browser.find_elements_by_tag_name('a')
              except:
                  print('some error occured')
              try:
                  for elem in elem1:
                      if elem.get_attribute('title') == 'Download photo':
                          print(elem.get_attribute('href'), file=link_file)
              except:
                  print("No data in Element")
              complete = True

            # Closing the file to save in drive
            link_file.close()

            with open("links.txt") as fp:
              for cnt, line in enumerate(fp):   
                self.searchresult_scroller.WriteText(line)
        else:
          self.searchresult_scroller.SetValue("Please enter a search query")

    # scraped the images and saves them to a local folder
    def multithread_scrape(self, event):
        check = self.searchresult_scroller.GetValue()
        if check != '':
            folder = 'scraped_photos'
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    self.searchresult_scroller.WriteText('Failed to delete %s. Reason: %s'%(file_path, e))
                    
            t1 = time.perf_counter()

            with concurrent.futures.ThreadPoolExecutor() as executor:
              executor.map(download_image, get_links())

            t2 = time.perf_counter()
            pub.sendMessage('change_statusbar1', msg=f'Multi-threaded scrape time : {round(t2-t1, 2)} seconds')
        else:
          self.searchresult_scroller.SetValue("Please enter a search query")
        

# multiprocessing panel
class MIPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size = wx.Size(540, 500))

        self.SetBackgroundColour(wx.Colour(217, 255, 217))
        
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        self.buttonsizer = wx.BoxSizer(wx.VERTICAL)
        self.outputsizer = wx.BoxSizer(wx.VERTICAL)
        self.outputbuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        lblList = ['1', '2', '4']     
        self.rbox = wx.RadioBox(self,label = 'Number of Processes', pos = (80,10), choices = lblList ,
                                majorDimension = 1, style = wx.RA_SPECIFY_ROWS)
        self.rbox.SetSelection(2)
        self.rbox.Bind(wx.EVT_RADIOBOX,self.onRadioBox)
        self.buttonsizer.Add(self.rbox, 0, wx.LEFT|wx.TOP, 10)
        
        self.blur_button = wx.Button(self, 0, "BLUR", size = (100,25))
        self.blur_button.Bind(wx.EVT_BUTTON, self.blur)
        self.buttonsizer.Add(self.blur_button, 0, wx.LEFT|wx.TOP, 15)
      
        self.max_button = wx.Button(self, 0, "MAXIMUM", size = (100,25))
        self.max_button.Bind(wx.EVT_BUTTON, self.maximum)
        self.buttonsizer.Add(self.max_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.median_button = wx.Button(self, 0, "MEDIAN", size = (100,25))
        self.median_button.Bind(wx.EVT_BUTTON, self.median)
        self.buttonsizer.Add(self.median_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.minimum_button = wx.Button(self, 0, "MINIMUM", size = (100,25))
        self.minimum_button.Bind(wx.EVT_BUTTON, self.minimum)
        self.buttonsizer.Add(self.minimum_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.mode_button = wx.Button(self, 0, "MODE", size = (100,25))
        self.mode_button.Bind(wx.EVT_BUTTON, self.mode)
        self.buttonsizer.Add(self.mode_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.negative_button = wx.Button(self, 0, "NEGATIVE", size = (100,25))
        self.negative_button.Bind(wx.EVT_BUTTON, self.negative)
        self.buttonsizer.Add(self.negative_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.sharpen_button = wx.Button(self, 0, "SHARPEN", size = (100,25))
        self.sharpen_button.Bind(wx.EVT_BUTTON, self.sharpen)
        self.buttonsizer.Add(self.sharpen_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.smoothen_button = wx.Button(self, 0, "SMOOTH", size = (100,25))
        self.smoothen_button.Bind(wx.EVT_BUTTON, self.smoothen)
        self.buttonsizer.Add(self.smoothen_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.subtract_button = wx.Button(self, 0, "EDGE ENHANCE", size = (100,25))
        self.subtract_button.Bind(wx.EVT_BUTTON, self.edge_enhance)
        self.buttonsizer.Add(self.subtract_button, 0, wx.LEFT|wx.TOP, 15)
        
        self.threshold_button = wx.Button(self, 0, "EDGE DETECT", size = (100,25))
        self.threshold_button.Bind(wx.EVT_BUTTON, self.edge_detect)
        self.buttonsizer.Add(self.threshold_button, 0, wx.LEFT|wx.TOP, 15)

        img = wx.Image(360,280)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(img))
        self.outputsizer.Add(self.imageCtrl, 0, wx.LEFT|wx.TOP, 20)

        self.backward_button = wx.Button(self, 0, "<----", size = (100,25))
        self.backward_button.Bind(wx.EVT_BUTTON, self.backwardsearch)
        self.outputbuttonsizer.Add(self.backward_button, 0, wx.ALIGN_CENTER|wx.LEFT, 20)
        
        self.forward_button = wx.Button(self, 0, "---->", size = (100,25))
        self.forward_button.Bind(wx.EVT_BUTTON, self.forwardsearch)
        self.outputbuttonsizer.Add(self.forward_button, 0, wx.LEFT, 20)
        self.outputsizer.Add(self.outputbuttonsizer, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 10)

        self.filterresults_scroller = wx.TextCtrl(self, -1, size=wx.Size(360, 95),style= wx.TE_MULTILINE|wx.BORDER_SUNKEN|wx.TE_READONLY)
        self.bottomsizer.Add(self.filterresults_scroller, 0, wx.BOTTOM, 10)

        self.clear_button = wx.Button(self, 0, "CLEAR", size = (100,25))
        self.clear_button.SetToolTip(wx.ToolTip('Clear results'))
        self.clear_button.Bind(wx.EVT_BUTTON, self.clearSearch)
        self.bottomsizer.Add(self.clear_button, 0, wx.ALIGN_CENTER)

        self.outputsizer.Add(self.bottomsizer, 0, wx.LEFT, 20)
        
        self.mainSizer.Add(self.buttonsizer, 0, wx.TOP, 10)
        self.mainSizer.Add(self.outputsizer, 0, wx.TOP, 10)
        
        self.SetSizer(self.mainSizer)
        self.mainSizer.Fit(self)
        self.Layout()
        
        self.Show()

    # select number or processes - default 4
    def onRadioBox(self, event): 
        return self.rbox.GetStringSelection()

    # clear button pressed to clear display and reset arrays   
    def clearSearch(self, event):
        global display_list, count 
        count = 0
        display_list = []
        img = wx.Image(360,280)
        self.imageCtrl.SetBitmap(wx.Bitmap(img))
        self.filterresults_scroller.SetValue('')
        pub.sendMessage('change_statusbar1', msg='')
        
    # move to next processed image in display
    def forwardsearch(self, event):
        global display_list, count

        if count < len(display_list)-1:
            count += 1
        if len(display_list) == 0:
            return
        img = wx.Image(display_list[count], wx.BITMAP_TYPE_ANY)
        # scale the image, preserving the aspect ratio
        self.imageCtrl.SetBitmap(wx.Bitmap(img))
        self.Refresh()

    # move to previous processed image in display
    def backwardsearch(self, event):
        global display_list, count
        
        if count > 0:
            count -= 1
        if len(display_list) == 0:
            return
        img = wx.Image(display_list[count], wx.BITMAP_TYPE_ANY)
        # scale the image, preserving the aspect ratio
        self.imageCtrl.SetBitmap(wx.Bitmap(img))
        self.Refresh()

    # display the processed images    
    def displayImages(self, filepath):
        global display_list, count
        display_list = get_imlist_alt(filepath)
        count = 0
        img = wx.Image(display_list[count], wx.BITMAP_TYPE_ANY)
        # scale the image, preserving the aspect ratio
        self.imageCtrl.SetBitmap(wx.Bitmap(img))
        self.Refresh()
        
    # blur button pressed  - applies multiprocessing
    def blur(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(blur_image, img_names)
        t2 = time.perf_counter()
        self.filterresults_scroller.WriteText('Batch processing with BLUR filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')
        
        self.displayImages('processed_photos/blur')

    # maimu button pressed  - applies multiprocessing
    def maximum(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(max_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with MAXIMUM filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')
        
        self.displayImages('processed_photos/max')
        
    # median button pressed  - applies multiprocessing
    def median(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(med_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with MEDIUM filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')
        
        self.displayImages('processed_photos/med')
        
    # minimum button pressed  - applies multiprocessing
    def minimum(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(min_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with MINIMUM filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/min')
        
    # mode button pressed  - applies multiprocessing
    def mode(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(mode_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with MODE filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/mode')
        
    # negative button pressed - applies multiprocessing
    def negative(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(negative_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with NEGATIVE filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/negative')
        
    # sharpen button pressed  - applies multiprocessing
    def sharpen(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(sharpen_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with SHARPEN filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/sharpen')
        
    # smoothen button pressed  - applies multiprocessing
    def smoothen(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(smoothen_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with SMOOTHEN filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/smoothen')
        
    # edge enhance button pressed  - applies multiprocessing
    def edge_enhance(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(edgeenhance_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with EDGE ENHANCE filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/edgeenhance')
        
    # edge detect button pressed  - applies multiprocessing
    def edge_detect(self, event):
        pub.sendMessage('change_statusbar1', msg='')
        img_names = get_imlist('scraped_photos')
        num_processes = int(self.onRadioBox(self))

        t1 = time.perf_counter()
        #By default, the ProcessPoolExecutor creates one subprocess per CPU
        with concurrent.futures.ProcessPoolExecutor(num_processes) as executor:  
            executor.map(edgedetect_image, img_names)
        t2 = time.perf_counter()

        self.filterresults_scroller.WriteText('Batch processing with EDGE DETECT filter\n')
        self.filterresults_scroller.WriteText(f'Number of processes: {num_processes} \n')
        self.filterresults_scroller.WriteText(f'Parallel processing finished in {round(t2-t1,2)} seconds\n\n')

        self.displayImages('processed_photos/edgedetect')
        
# set up of application frame and status bar
class MyFrame(wx.Frame):    
    def __init__(self):

        sys_menu = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        super().__init__(parent = None, title= '  The Image Magician',style = sys_menu)
       
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("multiprocessing.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        # A Statusbar in the bottom of the window
        self.statusbar = self.CreateStatusBar(2)
        self.statusbar.SetBackgroundColour(wx.Colour(230, 230, 230, alpha=wx.ALPHA_OPAQUE))

        pub.subscribe(self.change_statusbar0, 'change_statusbar0')
        pub.subscribe(self.change_statusbar1, 'change_statusbar1')

        self.statusbar.SetStatusWidths([200, 340])
        self.SetStatusText('  Developed by Mario Manitta',0)
        #self.SetStatusText('  Scrape Time : ',1)
          
        self.Center() 
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
        self.panel = wx.Panel(self, style=wx.BORDER_SUNKEN)
        self.nb = wx.Notebook(self.panel)
        
        # Create the tab windows
        tab1 = TIPanel(self.nb)
        tab2 = MIPanel(self.nb)

        # Add the windows to tabs and name them.
        self.nb.AddPage(tab1, "Multi-Threaded Image Scraping")
        self.nb.AddPage(tab2, "Multi-Process Image Filtering")
        self.nb.SetSelection(0)
        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.page_changed)
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.nb,1,wx.BOTTOM|wx.EXPAND, 5)
        self.panel.SetSizer(self.mainSizer)
        self.mainSizer.Fit(self)
        #self.SetSize(wx.Size(600, 400))
        self.panel.Layout()   
        self.Show()


    def start_over(self, event):
        self.panel.Refresh()
        self.mainSizer.Fit(self)
        self.panel.Layout()   
        

    def page_changed(self, event):
        global panel_count
        panel_count = self.nb.GetSelection()
        self.start_over(self)
        
        

    def on_close(self, event):
        global online
        dlg = wx.MessageDialog(self, 'Are you sure you want to quit?', 'Close application',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            online = False
            self.Destroy()
                
        else:
            return
        
    def change_statusbar0(self, msg):
        self.SetStatusText(msg, 0)

    def change_statusbar1(self, msg):
        self.SetStatusText(msg, 1)
        


if __name__ == '__main__':

    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
  
