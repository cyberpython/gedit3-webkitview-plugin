# coding=UTF-8
'''
Copyright (C) 2011 Georgios Migdos <cyberpython@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
from gi.repository import GObject, Gtk, Gedit, WebKit
import os.path

MENU_XML = """<ui>
<menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_3">
        <menuitem name="WebkitViewAction" action="WebkitViewAction"/>
        <menuitem name="WebkitReloadAction" action="WebkitReloadAction"/>
      </placeholder>
    </menu>
</menubar>
</ui>"""

UNSAVED_DOC_HTML_ERROR_PAGE_MSG = "Oh snap! You should save the active document before loading it in the preview window."

UNSAVED_DOC_HTML_ERROR_PAGE = """<!DOCTYPE html/>
<html>
    <head>
        <title>Unsaved Document Error!</title>
        <style>
        /* Taken from Twitter's Bootstrap: https://github.com/twitter/bootstrap */
        .alert-message.error {
          color: #ffffff;
        }
        .alert-message {
          position: relative;
          padding: 7px 15px;
          margin-bottom: 18px;
          color: #404040;
          background-color: #eedc94;
          background-repeat: repeat-x;
          background-image: linear-gradient(top, #fceec1, #eedc94);
          text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
          border-color: #eedc94 #eedc94 #e4c652;
          border-color: rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.25);
          text-shadow: 0 1px 0 rgba(255, 255, 255, 0.5);
          border-width: 1px;
          border-style: solid;
          border-radius: 4px;
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
        }
        .alert-message.error {
          background-color: #c43c35;
          background-repeat: repeat-x;
          background-image: linear-gradient(top, #ee5f5b, #c43c35);
          text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
          border-color: #c43c35 #c43c35 #882a25;
          border-color: rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.25);
        }
        .alert-message p {
          margin: 0;
          text-align: center;
        }
        .alert-message div {
          margin-top: 5px;
          margin-bottom: 2px;
          line-height: 28px;
        }
        </style>
    </head>
    <body>
        <div class="alert-message error">
            <p>"""+UNSAVED_DOC_HTML_ERROR_PAGE_MSG+"""</p>
        </div>
    </body>
</html>
"""


class WebkitViewPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "WebkitViewPlugin"
    window = GObject.property(type=Gedit.Window)
   
    def __init__(self):
        GObject.Object.__init__(self)
    
    def _add_ui(self):
        self._add_menuitem()
        self._add_side_panel()
   
    def _add_side_panel(self):
        self.default_url = 'http://www.google.com'
        icon = Gtk.Image()
        #icon.set_from_icon_name("gnome-mime-text-html", Gtk.IconSize.MENU)
        iconpath = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'gedit-webkitview.svg')
        icon.set_from_file(iconpath)
        vbox = Gtk.VBox(homogeneous=False)
        hbox = Gtk.HBox(homogeneous=False)
        self.url_edit = Gtk.Entry()
        self.url_edit.connect("activate", self._on_entry_activate)
        self.load_btn = Gtk.Button("Load active document")
        self.load_btn.connect("clicked", self.on_load_button_clicked)
        self._webkit_view =  WebKit.WebView()
        self._webkit_view.connect("navigation-policy-decision-requested",self._nav_request_policy_decision_cb)
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.add(self._webkit_view)
        hbox.pack_start(self.url_edit, True, True, 0)
        hbox.pack_start(self.load_btn, False, True, 0)
        vbox.pack_start(hbox, False, True, 0)
        vbox.pack_start(self._scrolled_window, True, True, 0);
        panel = self.window.get_side_panel()
        panel.add_item(vbox, "WebkitViewPanel", "Webkit view", icon)
        panel.activate_item(vbox)
        vbox.show_all()
        
    def _nav_request_policy_decision_cb(self,view,frame,net_req,nav_act,pol_dec):
        uri = net_req.get_uri()
        self.url_edit.set_text(uri)
        return False
        
    def _on_entry_activate(self, entry):
        uri = self.url_edit.get_text()
        if(self._webkit_view):
            self._webkit_view.open(uri)
    
    def _add_menuitem(self):
        manager = self.window.get_ui_manager()
        self._actions = Gtk.ActionGroup("WebkitViewActions")
        self._actions.add_actions([
                ('WebkitViewAction', Gtk.STOCK_INFO, "Load active document in webkit view", 
                '<CTRL>l', "Load the active document in the webkit view.", 
                self.on_load_content_action_activate),
                ('WebkitReloadAction', Gtk.STOCK_INFO, "Refresh webkit view", 
                '<CTRL>r', "Refreshes the webkit view's content.", 
                self.on_reload_content_action_activate)
        ]);
        manager.insert_action_group(self._actions)
        self._ui_merge_id = manager.add_ui_from_string(MENU_XML)
        manager.ensure_update()
        
    def do_activate(self):
        self._add_ui()

    def do_deactivate(self):
        self._remove_ui()

    def do_update_state(self):
        pass
        
    def on_load_button_clicked(self, button):
        self.load_active_document()
    
    def on_load_content_action_activate(self, action, data=None):
        self.load_active_document()
                    
    def load_active_document(self):
        document = self.window.get_active_document()
        if (document):
            location = document.get_location()
            if(location):
                uri = location.get_uri()
                if(self._webkit_view):
                    self._webkit_view.open(uri)
                    self.url_edit.set_text(uri)
            else:
                if(self._webkit_view):
                    self._webkit_view.load_string(UNSAVED_DOC_HTML_ERROR_PAGE, 'text/html', 'UTF-8', '')
                    self.url_edit.set_text('')
                
    def on_reload_content_action_activate(self, action, data=None):
        if(self._webkit_view):
            self._webkit_view.reload()
            
        
    def _remove_ui(self):
        manager = self.window.get_ui_manager()
        manager.remove_ui(self._ui_merge_id)
        manager.remove_action_group(self._actions)
        manager.ensure_update()
        
        panel = self.window.get_bottom_panel()
        panel.remove_item(self._webkit_view)


