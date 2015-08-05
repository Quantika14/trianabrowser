#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import gtk
from gtk import Notebook
import gtk.gdk
import urllib
from urlparse import urlparse
from bs4 import BeautifulSoup
import time
import urllib2
#you need to import webkit and gobject, gobject is needed for threads
import webkit
import gobject
from gtkcodebuffer import CodeBuffer, SyntaxLoader
import os
import dircache

default_site = "http://duckduckgo.com"


class Tab(gtk.VBox):
    ''' Definimos la clase tab, la cual instanciaremos en cada tab que se abra ''' 
    def __init__(self, *args, **kwargs):
        super(Tab, self).__init__(*args, **kwargs)

        ''' lista que contiene los filtros a ser aplicados para div id'''
        self.filters = set()
        ''' lista que contiene los filtros a ser aplicados para div class'''
        self.filters_class = set()
        ''' instancia de la vista web ''' 
        self.web_view = webkit.WebView()
        self.open_page(default_site)

        ''' calbacks de la vista web ''' 
        self.web_view.connect("load-progress-changed", self.changeprogress)
        self.web_view.connect("load-started", self.loadstarted)
        self.web_view.connect("load-finished", self.remove_div)
        self.web_view.connect("load_committed", self.update_buttons)
        
        ''' Barra de herramientas ''' 
        self.toolbar = gtk.HBox()

        self.back_button = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.back_button.connect("clicked", self.go_back)
        self.forward_button = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.forward_button.connect("clicked", self.go_forward)

        self.add_button = gtk.ToolButton(gtk.STOCK_ADD)
        self.add_button.connect("clicked", self.add)        

        self.refresh_button = gtk.ToolButton(gtk.STOCK_REFRESH)
        self.refresh_button.connect("clicked", self.refresh)

        ''' Metemos la vista web en una ventana con scroll''' 
        self.scroll_window = gtk.ScrolledWindow()
        self.scroll_window.add(self.web_view)

        self.url_bar = gtk.Entry()
        self.url_bar.connect("activate", self.on_active)

        self.toolbar.pack_start(self.back_button, False,False, 0)
        self.toolbar.pack_start(self.forward_button, False,False, 0)
        self.toolbar.pack_start(self.refresh_button, False,False, 0)
        self.toolbar.pack_start(self.url_bar, True, True, 0)
        self.toolbar.pack_start(self.add_button, False,False, 0)

        self.pack_start(self.toolbar, False, True, 0)
        self.pack_end(self.scroll_window, True, True, 0)

        self.show_all()

        def delete_event(self, widget, event, data=None):
            return False

        def destroy(self, widget, data=None):
            gtk.main_quit()        

    def loadstarted(self, webview, frame):
        ''' Calback que se ejecuta cuando empieza la carga de la pagina '''
        # self.browser.show_refreshbutton(False)
            # self.browser.show_stopbutton(True)
            #       self.set_progress(0)
        ''' Ponemos el dibijo de progreso de la barra a 0''' 
        self.url_bar.set_progress_fraction(0)



    def set_progress(self, progress):
        ''' Pintamos el progreso en la barra de la url ''' 
        self.url_bar.set_progress_fraction(progress)

    def changeprogress(self, webview, amount):
        ''' Para calcular el progreso de la carga de la vista web''' 
        progress = amount / 100.0        
        self.set_progress(progress)


    def on_active(self, widge, data=None):
        ''' Cuando pulsamos enter en el input de url''' 
        url = self.url_bar.get_text()

        ''' Vemos url empieza por http://, si no, se lo agregamos.
        Si nos es una url valida entonces abrimos una pagina de 
        consulta a google con el texto de la entrada ''' 
        try:
            if not "://" in url:
                url = "http://" + url
                self.open_page(url)

        '''FIX ME!!!!!!!!!!. Actualmente no funciona''' 
        except HTTPConnectivityException():
            url = "https://www.google.es/#q=" + url
            
        self.open_page(url)

    def go_back(self, widget, data=None):
        self.web_view.go_back()

    def go_forward(self, widget, data=None):
        self.web_view.go_forward()

    def add(self, widget, data=None):
        ''' Ventana de agregar filtros ''' 
        self.answerwin = gtk.Window()
        self.answerwin.set_position(gtk.WIN_POS_CENTER)
        self.answerwin.set_size_request(600, 200)
        self.answerwin.set_keep_above(True)
        self.answerwin.set_title("Creacion de filtros")
        self.answerwin.show()

        vbox = gtk.VBox(False, 0)
        vbox.set_homogeneous(True)

        ''' Inputs ''' 
        box = gtk.HBox()
        box.pack_start(gtk.Label('URL: '), False, 5, 5)
        self.entry = gtk.Entry()
        self.entry.set_max_length(50)
        box.pack_end(self.entry)
        vbox.pack_start(box, True, True, 0)


        box2 = gtk.HBox()
        box2.pack_start(gtk.Label('id / class: '), False, 5, 5)
        self.entry2 = gtk.Entry()
        self.entry2.set_max_length(50)
        box2.pack_end(self.entry2)
        vbox.pack_start(box2, True, True, 0)

        box3 = gtk.HBox()
        box3.pack_start(gtk.Label('HTML: '), False, 5, 5)
        self.entry3 = gtk.Entry()
        self.entry3.set_max_length(-1)
        box3.pack_end(self.entry3, True, True, 3)
        vbox.pack_start(box3, True, True, 0)

        ''' Boton ''' 
        button = gtk.Button("Agregar filtro")
        button.connect("clicked", self.submit, self.entry)
        vbox.pack_end(button, False, False, 1)
        
        self.answerwin.add(vbox)
        vbox.show_all()


    def submit(self, widget, data=None):
        ''' Callback que se ejecuta cuando pulsamos Agregar filtro '''
        
        ''' Obtenemos la url del primer input ''' 
        url = self.entry.get_text()
        ''' Obtenemos el id/class del segundo  ''' 
        self.div = self.entry2.get_text()
        ''' Obtenemos el html para reemplazar del tercero ''' 
        self.div_c = self.entry3.get_text()
        ''' Destruimos la ventana ''' 
        self.answerwin.destroy()

        ''' Guardamos los datos a ficheros '''
        hostname = urlparse(url).hostname
        filename = 'filtros/' + hostname + '.txt'
        f = open('filtros/hosts.txt', 'ab')
        f.write(hostname + ' ' + filename + '\n')
        f.close
        
        g = open(filename, 'ab')
        g.write(self.div + '$$' + self.div_c + '$$\n')
        g.close
    
        ''' Por ultimo abrimos la url ''' 
        self.open_page(url)
        ''' Y refrescamos la vista '''
        self.refresh()
        
    def open_page(self, url):
        ''' Asi abrimos las paginas, primero la abrimos de forma normal 
        como se haria con pywebkit y despues los agregamos al conjunto 
        (no hay repeticiones) global. COntruimos dos fliltros, uno para
        remplazar divs segun su id y otro segun el nombre de la clase 
        js y js_c, respectivamente '''
        self.web_view.open(url)

        ''' Lectura de los filtros segun han sido almacenados ''' 
        if os.path.isfile('filtros/hosts.txt'): 
            f = open('filtros/hosts.txt', 'r')
            lines = f.readlines()
            for l in lines:
                host = l.split()[0]
                if host in url:
                    with open( 'filtros/' + host +'.txt', 'r') as g:
                        llines = g.readlines() 
                        for lol in llines:
                            div = lol.split('$$')[0] 
                            div_c = lol.split('$$')[1]

                            ''' Composicion de las cadenas javascript  que aplicaran los filtros '''
                            js = "document.getElementById('" + div + "').innerHTML = '" + div_c + "';"
                            js_c = "document.getElementsByClassName('"+div+"')[0].innerHTML = '"+ div_c+ "';"
                            self.filters.add(js)
                            self.filters_class.add(js_c)                            
                    g.close()
            f.close()

    def refresh(self, widget, data=None):
        ''' Callback para el boton de refrescar''' 
        self.web_view.reload()

    def update_buttons(self, widget, data=None):
        print 'pagechange';
        self.url_bar.set_text( widget.get_main_frame().get_uri() )
        self.back_button.set_sensitive(self.web_view.can_go_back())
        self.forward_button.set_sensitive(self.web_view.can_go_forward())

    def remove_div(self, web_view, frame):
        ''' Callback que se ejecuta cuando la pagina se termina de cargan
        Aqui se ejecutan los filtros mediante execute_script, que hace uso 
        del motor javascript que trae webkit '''

        # self.browser.show_refreshbutton(True)
        # self.browser.show_stopbutton(False)
        
        self.url_bar.set_progress_fraction(0)

        for js in self.filters:
            self.web_view.execute_script(js)

        for jss in self.filters_class:
            self.web_view.execute_script(jss)


class Browser(gtk.Window):
    ''' Esta sera el objeto de la ventena principal ''' 
    def __init__(self, *args, **kwargs):
        super(Browser, self).__init__(*args, **kwargs)

        ''' Le decimos a gtk que use hilos ''' 
        gobject.threads_init()

        ''' Definimos algunas propiedades de la ventana principal ''' 

        self.set_title('Triana Browser')
        self.set_icon_from_file('./iconn.png')
        self.connect("destroy", gtk.main_quit)
        self.maximize()

	''' Instanciamos un objeto notebook que es el que nos permite menejar varias tabs '''
	self.notebook = gtk.Notebook()
        # self.notebook.set_property('show-tabs', False) 
	self.notebook.set_scrollable(True)

        ''' Para mantener la lista de tab abiertas ''' 
        self.tabs = []
	self.set_size_request(400,400)


        ''' HBox viene de Horizontal Box, y es el tipo de caja que hemos decido usar para meter 
        la cabecera de cada tab del notebook ''' 
        hbox = gtk.HBox(False, 0)

        ''' Boton de cerrar tab''' 
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        image_w, image_h = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)

        label = gtk.Label("Nuevo Tab")
        hbox.pack_start(label, False, False)

        btn = gtk.Button()
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        btn.add(close_image)
        btn.connect('clicked', self._close_current_tab)
        hbox.pack_end(btn, False, False)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        btn.modify_style(style)

        hbox.show_all()

        ''' Para empezar creamos una tab vacia  ''' 
        self.tabs.append((self._create_tab(), hbox))
        self.notebook.append_page(*self.tabs[0])
        
        ''' La caja principal donde lo metemos todo, de momento solo 
        tenemos el notebook '''  
        box = gtk.VBox()
        box.pack_start(self.notebook)

        ''' Agragamos la caja a la ventana principal ''' 
        self.add(box)
        
        ''' Eventos que queremos manejar 
        Primero el evento producido por presionar alguna/s tecla/s ''' 
        # self.connect("key-press-event", self._key_pressed)
        
        ''' El evento producido al cambiar de tab, le pasamos la funcion 
        _tab_changed cada vez que se produzca''' 
        self.notebook.connect("switch-page", self._tab_changed)

        ''' Lo mostramos todo ''' 
        self.show_all()


    def _tab_changed(self, notebook, current_page, index):
        ''' Funcion que se llama cada vez que cambiamos de tab '''  
        if not index:
            return
        title = self.tabs[index][0].web_view.get_title()
        if title:
            self.set_title(title)

    def _title_changed(self, web_view, frame, title):
        ''' Cada vez que cambia el title de la pagina, se ejecuta esta callback '''  
        current_page = self.notebook.get_current_page()

        counter = 0
        ''' La lista tab es una lista de pares de la forma 
        ((instancia de la clase tab),(hbox, caja de la cabecera del tab))'''
        for tab, hbox in self.tabs:
            ''' Si la vista del tab es la misma que la pasada a la callback ''' 
            if tab.web_view is web_view:
                ''' Modificamos el titulo, que esta dentro de la caja de la cabecera del tab''' 
                label = hbox.get_children()[0]
                label.set_text(title)
                if counter == current_page:
                    self._tab_changed(None, None, counter)
                break
            counter += 1
            

    def _create_tab(self):
        ''' Creacion de tabs '''
        
        ''' Instanciamos el objeto tab que creamos arriba ''' 
        tab = Tab()
        ''' Agregamos las callbacks para el cambio de titulo y el menu del boton derecho ''' 
        tab.web_view.connect("title-changed", self._title_changed)
        tab.web_view.connect("populate-popup", self._populate_page_popup)

        return tab
    
    def _create_source_view(self):
        ''' Creacion de las pestanas que mostraran el codigo fuente de las paginas
        TODO: Obtener el html a traves del webview y no con urllib '''

        ''' obtenemos la url que esta mostrando la pestana actual ''' 
        url = self.tabs[self.notebook.get_current_page()][0].url_bar.get_text()
        ''' Pedimos la pagina con urllib ''' 
        response = urllib2.urlopen(url)
        page = response.read()
        soup = BeautifulSoup(page)
        ''' La ponemos bonita con bs4''' 
        html = soup.prettify()

        ''' Ahora hacemos uso de la libreria pygtkcodebuffer para mostrar el 
        codigo que acabamos de obtener 
        Primero establecemos el lenguaje que estamos usando para colorear el codigo ''' 
        lang = SyntaxLoader("html")

        ''' Creamos el buffer '''
        buff = CodeBuffer(lang=lang)

        ''' Lo metemos dentro de una ventana con scroll ''' 
        scr = gtk.ScrolledWindow()
        scr.add(gtk.TextView(buff))

        ''' Y lo mostramos ''' 
        buff.set_text(html)
        return url, scr
    
    def _reload_tab(self):
        ''' Recargando la pagina!!! ''' 
        self.tabs[self.notebook.get_current_page()][0].web_view.reload()

    def _close_current_tab(self, widget, data=None):
        ''' Para cerrar el tab actual '''
        if self.notebook.get_n_pages() == 1:
            gtk.main_quit()
        page = self.notebook.get_current_page()
        current_tab = self.tabs.pop(page)
        self.notebook.remove(current_tab[0])

    def _open_new_tab(self, widget, data=None):
        ''' Callback para abrir un nuevo tab ''' 

        ''' hacemos una caja horizontal donde meteremos el titulo y el boton de cerrar
        tab '''
        hbox = gtk.HBox(False, 0)

        ''' Titulo ''' 
        label = gtk.Label("New Tab")
        hbox.pack_start(label, False, False)

        ''' Boton de cerrar ''' 
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        image_w, image_h = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
        btn = gtk.Button()
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        btn.add(close_image)
        btn.connect('clicked', self._close_current_tab)
        hbox.pack_end(btn, False, False)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        btn.modify_style(style)

        hbox.show_all()

        current_page = self.notebook.get_current_page()
        page_tuple = (self._create_tab(), hbox)
        self.tabs.insert(current_page+1, page_tuple)
        self.notebook.insert_page(page_tuple[0], page_tuple[1], current_page+1)
        self.notebook.set_current_page(current_page+1)       

    def _focus_url_bar(self):
        ''' Obtenemos el foco de la barra de url para poder escribir y mandar la peticion ''' 
        current_page = self.notebook.get_current_page()
        self.tabs[current_page][0].url_bar.grab_focus()

    # def _raise_find_dialog(self):
    #     current_page = self.notebook.get_current_page()
    #     self.tabs[current_page][0].find_box.show_all()
    #     self.tabs[current_page][0].find_entry.grab_focus()
    
    def _populate_page_popup(self, view, menu):
        ''' Anadimos los campos al menu del boton derecho con sus correspondientes callbacks ''' 
         source = gtk.MenuItem("Ver codigo fuente")
         source.connect("activate", self._open_source_tab, view)
         new_tab = gtk.MenuItem("Nuevo Tab")
         new_tab.connect("activate", self._open_new_tab, view)
         menu.insert(source, -1)
         menu.insert(new_tab, -1)
         menu.show_all()

    def _open_source_tab(self, menuitem, view):
        ''' Creacion del tab que contendra el codigo fuente. Es practicamente igual que la del tab 
        para el view source ''' 
        
        hbox = gtk.HBox(False, 0)

        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        image_w, image_h = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)

        url, w = self._create_source_view()
        hostname =  urlparse(url).hostname
        label = gtk.Label('source-view: '+hostname)
        hbox.pack_start(label, False, False)

        btn = gtk.Button()
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        btn.add(close_image)
        btn.connect('clicked', self._close_current_tab)
        hbox.pack_end(btn, False, False)
        
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        btn.modify_style(style)

        hbox.show_all()

        current_page = self.notebook.get_current_page()
        page_tuple = (w, hbox)
        self.tabs.insert(current_page+1, page_tuple)
        self.notebook.insert_page(page_tuple[0], page_tuple[1], current_page+1)
        self.show_all()
        self.notebook.set_current_page(current_page+1)

    def _key_pressed(self, widget, event):
        modifiers = gtk.accelerator_get_default_mod_mask()
        mapping = {gtk.gdk.KEY_r: self._reload_tab,
                   gtk.gdk.KEY_w: self._close_current_tab,
                   gtk.gdk.KEY_t: self._open_new_tab,
                   gtk.gdk.KEY_l: self._focus_url_bar,
                   gtk.gdk.KEY_f: self._raise_find_dialog,
                   gtk.gdk.KEY_q: gtk.main_quit}

        if event.state & modifiers == gdk.ModifierType.CONTROL_MASK \
          and event.keyval in mapping:
            mapping[event.keyval]()

if __name__ == "__main__":

    class ConnectivityException(Exception): pass
    
    class HTTPConnectivityException(ConnectivityException): pass
    
    class FTPConnectivityException(ConnectivityException): pass

    browser = Browser()
    gtk.main()
