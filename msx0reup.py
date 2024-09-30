import os
import requests
import html2text
import telnetlib
import threading
import logging
import zipfile
import shutil
import json
import struct
import lhafile 
import traceback
import socket
import ssl
import time
import mimetypes
import platform
import re
import certifi
import asyncio
import chardet
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty,ListProperty,ObjectProperty,BooleanProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.modalview import ModalView
from kivy.uix.dropdown import DropDown
from kivy.uix.settings import SettingsWithNoMenu
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from msx0babaput import msx0babaput
from kivy.uix.spinner import Spinner
from kivy.properties import NumericProperty


from kivy.uix.label import Label as KivyLabel
from kivy.uix.button import Button as KivyButton
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle

class Label(KivyLabel):
    def __init__(self, **kwargs):
        super(Label, self).__init__(**kwargs)
        self.font_size = 14 # デフォルトのフォントサイズを設定

class Button(KivyButton):
    def __init__(self, **kwargs):
        super(Button, self).__init__(**kwargs)
        self.font_size = 14  # デフォルトのフォントサイズを設定

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logging()

class UIComponents:
    class LoadingSpinner(ModalView):
        def __init__(self, **kwargs):
            super(UIComponents.LoadingSpinner, self).__init__(**kwargs)
            self.size_hint = (None, None)
            self.size = (100, 100)
            self.auto_dismiss = False
            self.background_color = [0, 0, 0, 0.5]

            self.spinner_image = Image(
                source='./icon/spinner.gif',
                size_hint=(None, None),
                size=(50, 50),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            self.spinner_image.anim_delay = 0.1
            self.spinner_image.anim_loop = 0
            self.add_widget(self.spinner_image)

            self.pos = ((Window.width - self.width) / 2, (Window.height - self.height) / 2)

    class UploadSpinner(ModalView):
        def __init__(self, **kwargs):
            super(UIComponents.UploadSpinner, self).__init__(**kwargs)
            self.size_hint = (None, None)
            self.size = (300, 200)
            self.auto_dismiss = False
            
            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            
            self.spinner_image = Image(
                source='./icon/spinner.gif',
                size_hint=(None, None),
                size=(50, 50),
                pos_hint={'center_x': 0.5}
            )
            self.spinner_image.anim_delay = 0.1
            self.spinner_image.anim_loop = 0
            layout.add_widget(self.spinner_image)
            
            self.progress_bar = ProgressBar(max=100, value=0)
            layout.add_widget(self.progress_bar)
            
            self.progress_label = Label(text="Uploading: 0%")
            layout.add_widget(self.progress_label)
            
            self.cancel_button = Button(text="Cancel", size_hint=(None, None), size=(100, 40), pos_hint={'center_x': 0.5})
            layout.add_widget(self.cancel_button)
            
            self.add_widget(layout)

        def update_progress(self, value):
            self.progress_bar.value = value
            self.progress_label.text = f"Uploading: {int(value)}%"
            logger.debug(f"UploadSpinner:update_progress:{self.progress_label.text}")


class Utils:
    @staticmethod
    def read_until_timeout(tn, expected, timeout):
        def _read_thread(tn, result):
            try:
                logger.debug(f"_read_thread:{expected}{timeout}")
                result.append(tn.read_until(expected, timeout))
            except EOFError:
                result.append(None)

        result = []
        thread = threading.Thread(target=_read_thread, args=(tn, result))
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            tn.close()
            raise TimeoutError("Operation timed out")
        if not result:
            raise TimeoutError("Operation timed out")
        return result[0]
    
    @staticmethod
    def change_to_basic_mode(tn,timeout):
        try:
            tn.write(b'\r\n')
            response = tn.read_until(b'A>', 2)
            if b'A>' in response:
                tn.write(b'basic\r\n')
                Utils.read_until_timeout(tn, b'Ok', timeout)
            return response
        
        except TimeoutError as e:
            error_message = f"Error Change to basic mode {str(e)}"
            logger.error(error_message)
            raise e

    @staticmethod
    def change_to_dos_mode(tn,timeout):
        try:
            tn.write(b'\r\n')
            response = tn.read_until(b'A>', 2)
            if b'A>' not in response:
                logger.debug("_execute_command_thread:_system")
                tn.write(b'_system\r\n')
                response = Utils.read_until_timeout(tn, b'A>', timeout)
            return response
        except TimeoutError as e:
            error_message = f"Error Change to dos mode {str(e)}"
            logger.error(error_message)
            raise e
    


class LinkedLabel(RecycleDataViewBehavior, Label):
    index = None

    def on_touch_down(self, touch):
        logger.debug("LinkedLabel:on_touch_down")
        if self.collide_point(*touch.pos):
            logger.debug(f"LinkedLabel:on_touch_down:collide_point:{str(touch.pos)}")
            return self.parent.parent.on_label_touch(self, touch)
        return super(LinkedLabel, self).on_touch_down(touch)

class IconButton(ButtonBehavior, Image):
    inverted = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(IconButton, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (24, 24)
        self.allow_stretch = True
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.bind(inverted=self.update_canvas)

    def on_press(self):
        self.inverted = True

    def on_release(self):
        self.inverted = False

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.inverted:
                Color(1, 1, 1, 1)  # 白色
            else:
                Color(0, 0, 0, 0)  # 透明
            Rectangle(pos=self.pos, size=self.size)

        if self.inverted:
            self.color = [0, 0, 0, 1]  # 黒色
        else:
            self.color = [1, 1, 1, 1]  # 白色

class AsyncTextBrowser(RecycleView):
    text = StringProperty('')
    base_url = StringProperty('')
    links = ListProperty([])

    def __init__(self, **kwargs):
        super(AsyncTextBrowser, self).__init__(**kwargs)
        self.viewclass = 'LinkedLabel'
        self.data = []
        self.site_configs = self.load_site_configs()

    def load_site_configs(self):
        logger.debug(f"load_site_configs:")
        try:
            with open('site_configs.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("site_configs.json not found. No custom content extraction will be applied.")
            return {}

    def extract_content(self, html, url):
        logger.debug(f"extract_content:")
        domain = urlparse(url).netloc
        config = self.site_configs.get(domain)
        
        if not config:
            return html

        start_marker = config['start_marker']
        end_marker = config['end_marker']

        start_index = html.find(start_marker)
        end_index = html.find(end_marker, start_index)

        if start_index != -1 and end_index != -1:
            return html[start_index:end_index + len(end_marker)]
        else:
            logger.warning(f"Markers not found for {url}. Returning full content.")
            return html

    def on_text(self, instance, value):
        logger.debug(f"AsyncTextBrowser:on_text")
        Clock.schedule_once(lambda dt: self.process_text(value))

    def process_text(self, text):
        logger.debug(f"AsyncTextBrowser:process_text")
        lines = text.split('\n')
        processed_lines = []
        for i, line in enumerate(lines):
            processed_line = self.format_links(line)
            processed_lines.append({
                'text': processed_line,
                'markup': True,
                'halign': 'left',
                'text_size': (self.width, None),
                'index': i
            })
        self.data = processed_lines

    def format_links(self, text):
        def repl(match):
            full_match = match.group(0)
            text = match.group(1)
            logger.debug(f"AsyncTextBrowser:format_links:full_match:{full_match}")
            url = match.group(2)
            # 相対URLを絶対URLに変換
            absolute_url = urljoin(self.base_url, url)
            link_id = f"link_{len(self.links)}"
            self.links.append((link_id, absolute_url)) 
            def display_edges(text):
                if len(text) <= 20:
                    return text
                else:
                    return text[:10] + "..." + text[-10:]
            logger.debug(f"AsyncTextBrowser:format_links:url:{display_edges(url)}")
            return f'[ref={link_id}][color=0000ff]{text}({display_edges(url)})[/color][/ref]'

        pattern = r'\[(.*?)\]\((.*?)(\s+".*?")?\)'
        url_text=re.sub(pattern, repl, text)
        logger.debug(f"AsyncTextBrowser:format_links:{url_text}")
        return url_text

    def on_label_touch(self, label, touch):
        logger.debug("AsyncTextBrowser:on_label_touch:")
        logger.debug(f"AsyncTextBrowser:on_label_touch:label:{str(label)}")
        if hasattr(label, 'refs') and label.refs:
            logger.debug(f"AsyncTextBrowser:on_label_touch:label.rfs:true")
            for ref in label.refs:
                logger.debug(f"AsyncTextBrowser:on_label_touch:ref:{str(ref)}")
                if label.collide_point(*touch.pos):
                    link_id = ref
                    for id, url in self.links:
                        if id == link_id:
                            logger.debug(f"AsyncTextBrowser:on_label_touch:url:{str(url)}")
                            self.parent.parent.parent.parent.parent.on_link_click(url)
                            return True
        return False

    async def async_load_url(self, url, max_redirects=10):
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: session.get(url, verify=certifi.where(), allow_redirects=True)
            )
            response.raise_for_status()

            # エンコーディングの検出と設定
            if response.encoding is None:
                detected = chardet.detect(response.content)
                response.encoding = detected['encoding']

            logger.debug(f"async_load_url:encoding:{response.encoding}")

            # HTMLのメタタグからエンコーディングを取得
            soup = BeautifulSoup(response.content, 'html.parser')
            meta_charset = soup.find('meta', charset=True)
            meta_content_type = soup.find('meta', {'http-equiv': 'Content-Type'})
            logger.debug(f"async_load_url:meta_charset:{meta_charset}\nmeta_content_type:{meta_content_type}")
            if meta_charset:
                response.encoding =  meta_charset['charset']
            elif meta_content_type:
                content = meta_content_type['content'].lower()
                if 'charset=' in content:
                    response.encoding =  content.split('charset=')[-1]
            # x-sjisをShift_JISに変換
            if response.encoding  and response.encoding.lower() == 'x-sjis':
                response.encoding  = 'shift_jis'


            logger.debug(f"async_load_url:encoding:{response.encoding}")
            html_content = response.text
            final_url = response.url  # 最終的なURL（リダイレクト後）

            # コンテンツの抽出
            extracted_content = self.extract_content(html_content, final_url)

            # HTMLをテキストに変換
            h = html2text.HTML2Text()
            h.ignore_images = True
            h.unicode_snob = True
            h.body_width = 0
            h.ignore_links = False
            h.inline_links = True
            h.use_automatic_links = False
            text = h.handle(extracted_content)

            # 相対URLを絶対URLに変換
            text = self.convert_relative_urls(text, final_url)

            Clock.schedule_once(lambda dt: self.update_text_browser(final_url, text))
        except Exception as e:
            error_message = f"Error loading URL: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            Clock.schedule_once(lambda dt: self.update_text_browser(url, error_message))
    def convert_relative_urls(self, text, base_url):
        def replace_url(match):
            url = match.group(2)
            return f'[{match.group(1)}]({urljoin(base_url, url)})'
        # Markdownリンクの正規表現パターン
        pattern = r'\[(.*?)\]\((.*?)\)'
        return re.sub(pattern, replace_url, text)

    def update_text_browser(self, url, text):
        logger.debug(f"update_text_browser:")
        self.base_url = url
        self.text = text
        self.reset_scroll()

    def reset_scroll(self):
        self.scroll_y = 1

class DiskSelectionDialog(Popup):
    def __init__(self, current_disk, available_disks, on_select, **kwargs):
        super(DiskSelectionDialog, self).__init__(**kwargs)

        self.title = "Select Disk"
        self.size_hint = (0.8, 0.8)
        
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Current disk info
        current_disk_label = Label(text=f"Current Disk: {current_disk}", size_hint_y=None, height=30)
        layout.add_widget(current_disk_label)
        
        # Available disks list with radio buttons
        scroll_view = ScrollView(size_hint=(1, 1))
        grid_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))
        
        self.radio_buttons = []
        for disk in available_disks:
            rb = RadioButton(text=disk, group='disk_selection', size_hint_y=None, height=30)
            self.radio_buttons.append(rb)
            grid_layout.add_widget(rb)
        
        scroll_view.add_widget(grid_layout)
        layout.add_widget(scroll_view)
        
        # Buttons
        button_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        select_button = Button(text="Select")
        select_button.bind(on_press=self.on_select_press)
        cancel_button = Button(text="Cancel")
        cancel_button.bind(on_press=self.dismiss)
        
        button_layout.add_widget(select_button)
        button_layout.add_widget(cancel_button)
        layout.add_widget(button_layout)
        
        self.content = layout
        self.on_select = on_select

    def on_select_press(self, instance):
        selected_disk = next((rb.label.text for rb in self.radio_buttons if rb.active), None)
        if selected_disk:
            self.on_select(selected_disk)
            self.dismiss()
        else:
            # 選択されていない場合のエラーメッセージなどを表示
            pass


class RadioButton(BoxLayout):
    def __init__(self, text, group, **kwargs):
        super(RadioButton, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 30
        self.spacing = 10  # チェックボックスとラベルの間隔

        self.checkbox = CheckBox(group=group, size_hint=(None, None), width=30, height=30)
        self.label = Label(text=text, halign='left', valign='middle', text_size=(None, 30))
        
        # レイアウトの調整
        self.add_widget(Widget(size_hint_x=None, width=200))  # 左側の余白
        self.add_widget(self.checkbox)
        self.add_widget(self.label)
        self.add_widget(Widget())  # 右側の余白（伸縮可能）

    @property
    def active(self):
        return self.checkbox.active
    
class MSX0InfoLayout(GridLayout):
    def __init__(self, msx0_host, **kwargs):
        super().__init__(**kwargs)
        self.msx0_host = msx0_host
        self.cols = 1
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))

class MSX0RemoteUploader(BoxLayout):
    sort_options = [
        ('name', True, 'Name↑'),
        ('name', False, 'Name↓'),
        ('date', True, 'Date↑'),
        ('date', False, 'Date↓'),
        ('size', True, 'Size↑'),
        ('size', False, 'Size↓'),
    ]
    main_color = ListProperty([0.9, 0.70, 0.75, 1])
    secondary_color = ListProperty([0.8, 0.25, 0.3, 1])
    tertiary_color = ListProperty([0.2, 0.05, 0.05, 1])
    def __init__(self, config, **kwargs):
        logger.debug("MSX0RemoteUploader:init")
        super().__init__(**kwargs)
        self.config = config
        self.spinner = UIComponents.LoadingSpinner()
        self.upload_spinner = UIComponents.UploadSpinner()
        self.settings = SettingsWithNoMenu()
        self.settings_popup = None
        self.temp_folder_path = './msx0reup_temp'
        self.uploader = FileUploader(config)
        # self.msx0_list = []
        self.active_threads = 0
        self.progress_bar = None
        self.progress_label = None
        self.upload_threads = {}
        self.upload_cancel_flag = threading.Event()
        self.all_checked = False
        self.url_history = []
        self.current_url_index = -1

        self.loop = asyncio.get_event_loop()
        self.text_browser = AsyncTextBrowser()
        self.executor = ThreadPoolExecutor(max_workers=5)

        self.upload_start_time = 0 
        self.successful_uploads = 0

        self.msx0_layouts = {} 

        Clock.schedule_once(self.post_init, 0)
        self.load_settings()
        self.apply_settings()

        self.current_sort = ('date', True)  # (sort_key, is_ascending)

        self.load_color_settings()

    def load_color_settings(self):
        color_theme = self.config.get('General', 'color_theme')
        if color_theme == 'Red':
            self.main_color = [0.9, 0.70, 0.75, 1]
            self.secondary_color = [0.8, 0.25, 0.3, 1]
            self.tertiary_color = [0.2, 0.05, 0.05, 1]
        else:  # Blue
            self.main_color = [0.4, 0.86, 0.94, 1]
            self.secondary_color = [0.2, 0.25, 0.6, 1]
            self.tertiary_color = [0.1, 0.1, 0.4, 1]

    def post_init(self, dt):
        self.temp_refresh_button = self.ids.temp_refresh_button
        self.msx0_refresh_button = self.ids.msx0_refresh_button
        self.populate_file_list()
        if hasattr(self.ids, 'server_ip_input'):
            self.ids.server_ip_input.text = self.config.get('General', 'default_msx0_ip')
        Clock.schedule_once(self.add_text_browser, 0)

    def add_text_browser(self, dt):
        logger.debug("Adding TextBrowser")
        try:
            self.ids.preview_container.add_widget(self.text_browser)
            logger.debug("TextBrowser added")
            url=self.ids.url_input.text
            self.url_history.append(url)
            self.current_url_index = len(self.url_history) - 1
            asyncio.create_task(self.load_url_with_spinner(url))
            logger.debug("add_text_brower:load_url")
        except Exception as e:
            logger.error(f"Exception in add_text_browser: {str(e)}")
            logger.error(traceback.format_exc())

    def show_spinner(self):
        logger.debug("show_spinner:start")
        self.spinner.open()
        logger.debug("show_spinner:end")

    def hide_spinner(self):
        logger.debug("hide_spinner:start")
        self.spinner.dismiss()
        logger.debug("hide_spinner:end")

    def on_link_click(self, url):
        logger.debug("on_link_click:")
        mime_type, _ = mimetypes.guess_type(url)
        logger.debug(f"on_link_click:{mime_type}")

        if mime_type and not mime_type.startswith('text'):
             self.confirm_download(url)
        else:
            self.ids.url_input.text = url
            self.load_url()

    def load_url(self):
        url = self.ids.url_input.text
        if url:
            logger.debug(f"Loading URL: {url}")
            self.show_spinner()
            self.url_history.append(url)
            self.current_url_index = len(self.url_history) - 1
            asyncio.create_task(self.load_url_with_spinner(url))
            # Schedule the cursor position update
            Clock.schedule_once(lambda dt: self.reset_url_input_cursor(), 0)

    async def load_url_with_spinner(self, url):
        try:
            await self.text_browser.async_load_url(url)
        finally:
            self.hide_spinner()

    def reset_url_input_cursor(self):
        self.ids.url_input.cursor = (0, 0)  # Move cursor to the start
        self.ids.url_input.scroll_x = 0  # Scroll to the start

    def go_back(self):
        if self.current_url_index > 0:
            self.current_url_index -= 1
            previous_url = self.url_history[self.current_url_index]
            self.ids.url_input.text = previous_url
            self.load_url()
        else:
            self.show_info_popup("No previous URL in history")

    def confirm_download(self, url):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f'Download this file?\n{url}'))
        buttons = BoxLayout()
        yes_button = Button(text='Yes')
        no_button = Button(text='No')
        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)
        content.add_widget(buttons)

        popup = Popup(title='Confirm Download', content=content, size_hint=(0.9, 0.4))
        
        yes_button.bind(on_press=lambda x: self.download_file_fromView(url, popup))
        no_button.bind(on_press=popup.dismiss)

        popup.open()


    def local_copy(self):
        content = BoxLayout(orientation='vertical')

        # ドライブ選択用のボックスレイアウト
        drives_layout = BoxLayout(size_hint_y=None, height=40)
        drives_layout.add_widget(Label(text="Select Drive:"))
        
        def change_drive(instance):
            file_chooser.path = instance.text

        # 利用可能なドライブを取得
        available_drives = self.get_available_drives()
        for drive in available_drives:
            btn = Button(text=drive, size_hint_x=None, width=40)
            btn.bind(on_release=change_drive)
            drives_layout.add_widget(btn)
        content.add_widget(drives_layout)

        file_chooser = FileChooserListView(path=os.path.expanduser("~"))
        content.add_widget(file_chooser)

        button_layout = BoxLayout(size_hint_y=None, height=40)
        select_button = Button(text='Select')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(select_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)

        popup = Popup(title="Choose a file to copy", content=content, size_hint=(0.9, 0.9))

        def select(instance):
            if file_chooser.selection:
                source_path = file_chooser.selection[0]
                file_name = os.path.basename(source_path)
                dest_path = os.path.join(self.temp_folder_path, file_name)
                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"File copied: {file_name}")
                    self.populate_file_list()  # Refresh the file list
                except Exception as e:
                    print(f"Error copying file: {e}")
            popup.dismiss()

        select_button.bind(on_press=select)
        cancel_button.bind(on_press=popup.dismiss)

        popup.open()

    def get_available_drives(self):
        if os.name == 'nt':  # Windows
            import win32api
            drives = win32api.GetLogicalDriveStrings()
            return [d.rstrip('\\') for d in drives.split('\000') if d]
        elif os.name == 'posix':  # Linux/Mac
            return ['/']  # Linuxの場合はルートディレクトリのみ
        else:
            return []  # その他のOSの場合は空リストを返す

    def load_settings(self):
        settings_json = '''
        [
            {
                "type": "path",
                "title": "Temporary Folder",
                "desc": "Location of the local temporary folder",
                "section": "General",
                "key": "temp_folder"
            },
            {
                "type": "string",
                "title": "Default Download URL",
                "desc": "Default URL for file downloads",
                "section": "General",
                "key": "default_url"
            },
            {
                "type": "string",
                "title": "Default MSX0 IP",
                "desc": "Default IP address for MSX0",
                "section": "General",
                "key": "default_msx0_ip"
            },
            {
                "type": "options",
                "title": "Color Theme",
                "desc": "Choose the color theme for the application",
                "section": "General",
                "key": "color_theme",
                "options": ["Blue", "Red"]
            },
            {
                "type": "path",
                "title": "BASIC Program Path",
                "desc": "Path to the BASIC program file",
                "section": "Advanced",
                "key": "basic_program_path"
            }
        ]
        '''
        self.settings.add_json_panel('MSX0 Remote Uploader Settings', self.config, data=settings_json)
        self.settings.bind(on_config_change=self.on_config_change)

    def apply_settings(self):
        self.temp_folder_path = self.config.get('General', 'temp_folder')
        self.ids.url_input.text = self.config.get('General', 'default_url')
        self.ids.server_ip_input.text = self.config.get('General', 'default_msx0_ip')
        #self.uploader.timeout = self.config.getint('Advanced', 'upload_timeout')
        self.uploader.load_basic_program()
        self.load_color_settings()  # 色設定を適用

    def open_settings(self):
        if not self.settings_popup:
            content = BoxLayout(orientation='vertical')
            content.add_widget(self.settings)
            
            close_button = Button(
                text='Close',
                size_hint=(1, None),
                height=50
            )
            close_button.bind(on_press=self.close_settings)
            content.add_widget(close_button)

            self.settings_popup = Popup(
                title='Settings',
                content=content,
                size_hint=(0.9, 0.9),
                auto_dismiss=False
            )
        
        self.settings_popup.open()

    def close_settings(self, instance):
        if self.settings_popup:
            self.settings_popup.dismiss()
        self.apply_settings()

    def on_config_change(self, instance, config, section, key, value):
        if section == 'General' and key == 'color_theme':
            self.load_color_settings()
        self.config.set(section, key, value)
        self.config.write()

    def refresh_temp_file_list(self, *args):
        logger.debug("Refreshing temporary file list")
        self.temp_refresh_button.disabled = True
        self.populate_file_list()

    def populate_file_list(self):
        self.ids.temp_file_list.clear_widgets()
        if not os.path.exists(self.temp_folder_path):
            os.makedirs(self.temp_folder_path)
        
        files = []
        for file in os.listdir(self.temp_folder_path):
            file_path = os.path.join(self.temp_folder_path, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                file_timestamp = os.path.getmtime(file_path)
                newline_type = self.detect_newline_type(file_path)
                files.append({
                    'name': file,
                    'size': file_size,
                    'date': file_timestamp,
                    'newline': newline_type,
                    'path': file_path
                })

        self.sort_files(files)

        for file in files:
            file_line = self.create_file_line(file['name'], file['size'], file['newline'], file['path'])
            self.ids.temp_file_list.add_widget(file_line)

        logger.debug("Temporary file list refreshed")
        self.temp_refresh_button.disabled = False
        self.hide_spinner()

    def sort_files(self, files):
        sort_key, is_ascending = self.current_sort
        reverse = not is_ascending
        files.sort(key=lambda x: x[sort_key], reverse=reverse)

    def on_sort_option_select(self, option):
        self.current_sort = (option[0], option[1])
        self.populate_file_list()

    def create_file_line(self, file, file_size, newline_type, file_path):
        file_line = BoxLayout(size_hint_y=None, height=30)
        file_line.add_widget(CheckBox(size_hint_x=None, width=30))
        filename_label = Label(text=file, halign='left')
        filename_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        file_line.add_widget(filename_label)

        name_edit_btn = IconButton(source='./icon/name_edit_btn.png', size_hint_x=None, width=32)
        name_edit_btn.bind(on_press=lambda instance: self.show_rename_dialog(file_path, filename_label))
        file_line.add_widget(name_edit_btn)

        file_line.add_widget(Label(text=f'{file_size} bytes'))
        file_line.add_widget(Label(text=newline_type))
        
        if file.lower().endswith('.dsk'):
            extract_btn = IconButton(source='./icon/extract_btn.png', size_hint_x=None, width=32)
            extract_btn.file_path = file_path
            extract_btn.bind(on_press=self.on_extract_dsk)
            file_line.add_widget(extract_btn)
        elif file.lower().endswith('.zip'):
            unzip_btn = IconButton(source='./icon/unzip_btn.png', size_hint_x=None, width=32)
            unzip_btn.bind(on_press=lambda instance, file_path=file_path: self.unzip_file(file_path))
            file_line.add_widget(unzip_btn)
        elif file.lower().endswith('.lzh'):
            unlzh_btn = IconButton(source='./icon/unzip_btn.png', size_hint_x=None, width=32)
            unlzh_btn.bind(on_press=lambda instance, file_path=file_path: self.extract_lzh(file_path))
            file_line.add_widget(unlzh_btn)
        else:
            if newline_type == 'LF':
                conv_btn = Button(text='CONV\nCR+LF', font_size=10, size_hint_x=None, width=32)
                conv_btn.bind(on_press=lambda instance, fp=file_path: self.on_convert_crlf(instance, fp))
                file_line.add_widget(conv_btn)
            else:
                file_line.add_widget(Widget(size_hint_x=None, width=32))
        delete_btn = IconButton(source='./icon/delete_btn.png', size_hint_x=None, width=32)
        delete_btn.bind(on_press=lambda instance, file_path=file_path, file_line=file_line: self.confirm_delete(file_path, file_line))
        file_line.add_widget(delete_btn)

        return file_line
    
    def show_rename_dialog(self, file_path, filename_label):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        new_name_input = TextInput(text=os.path.basename(file_path), multiline=False)
        content.add_widget(new_name_input)
        
        btn_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        rename_btn = Button(text='Rename')
        cancel_btn = Button(text='Cancel')
        
        btn_layout.add_widget(rename_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Rename File', content=content, size_hint=(None, None), size=(400, 200))
        
        def on_rename(instance):
            new_name = new_name_input.text
            if new_name:
                self.rename_file(file_path, new_name, filename_label)
            popup.dismiss()

        rename_btn.bind(on_press=on_rename)
        cancel_btn.bind(on_press=popup.dismiss)

        popup.open()

    def rename_file(self, old_path, new_name, filename_label):
        dir_path = os.path.dirname(old_path)
        new_path = os.path.join(dir_path, new_name)
        try:
            os.rename(old_path, new_path)
            filename_label.text = new_name
            self.show_info_popup(f"File renamed to {new_name}")
        except Exception as e:
            self.show_error_popup(f"Error renaming file: {str(e)}")

    def detect_newline_type(self, file_path):
        try:
            # OSの判定
            current_os = platform.system()

            if current_os == 'Android':
                # Android環境ではmimetypesを使用
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                is_text = mime_type is not None and mime_type.startswith('text/')
            else:
                # その他の環境ではmagicを使用
                import magic
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(file_path)
                is_text = mime_type.startswith('text/')

            if not is_text:
                return 'Binary'

            # ファイルサイズが0の場合
            if os.path.getsize(file_path) == 0:
                return 'Empty file'

            with open(file_path, 'rb') as file:
                content = file.read(1024)
                if b'\r\n' in content:
                    return 'CR+LF'
                elif b'\n' in content:
                    return 'LF'
                elif b'\r' in content:
                    return 'CR'
                else:
                    return 'No newline'
        except ImportError as ie:
            logger.error(f"Import error: {str(ie)}. Falling back to basic file type detection.")
            # 基本的なファイルタイプ検出にフォールバック
            _, ext = os.path.splitext(file_path)
            if ext.lower() in ['.txt', '.py', '.java', '.c', '.cpp', '.h', '.html', '.css', '.js']:
                return self.detect_newline_type_basic(file_path)
            else:
                return 'Binary'
        except Exception as e:
            logger.error(f"Error detecting newline type: {str(e)}")
            return f'Error: {str(e)}'

    def detect_newline_type_basic(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                content = file.read(1024)
                if b'\0' in content:
                    return 'Binary'
                elif b'\r\n' in content:
                    return 'CR+LF'
                elif b'\n' in content:
                    return 'LF'
                elif b'\r' in content:
                    return 'CR'
                else:
                    return 'No newline'
        except Exception as e:
            logger.error(f"Error in basic newline type detection: {str(e)}")
            return f'Error: {str(e)}'

    def convert_lf_to_crlf(self, file_path):
        with open(file_path, 'rb') as file:
            content = file.read()
        
        content = content.replace(b'\n', b'\r\n').replace(b'\r\r\n', b'\r\n')
        
        with open(file_path, 'wb') as file:
            file.write(content)
        
        logger.debug(f"Converted {file_path} to CR+LF")
        self.populate_file_list()

    def on_convert_crlf(self, instance, file_path):
        self.convert_lf_to_crlf(file_path)

    def unzip_file(self, zip_file_path):
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_folder_path)
            logger.debug(f"Successfully unzipped {zip_file_path}")
            self.populate_file_list()
        except Exception as e:
            logger.error(f"Error unzipping file: {e}")

    def extract_lzh(self, lzh_path):
        try:
            logger.debug(f"extract_lzh:{lzh_path}")
            lzh = lhafile.Lhafile(lzh_path)
            try:
                for info in lzh.infolist():
                    extracted_path = os.path.join(self.temp_folder_path, info.filename)
                    with open(extracted_path, "wb") as f:
                        f.write(lzh.read(info.filename))
                self.show_info_popup(f"Successfully extracted {lzh_path}")
                self.populate_file_list()
            finally:
                lzh.fp.close()
        except lhafile.BadLhafile as e:
            self.show_error_popup(f"Invalid LZH file: {str(e)}")
        except PermissionError as e:
            self.show_error_popup(f"Permission denied: {str(e)}")
        except Exception as e:
            message=f"Error extracting {lzh_path}: {str(e)}"
            logger.error(traceback.format_exc())
            self.show_error_popup(message)

    def confirm_delete(self, file_path, file_line):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Are you sure you want to delete this file?'))
        btn_layout = BoxLayout(size_hint_y=None, height=30)
        btn_layout.add_widget(Button(text='OK', on_press=lambda instance: [self.delete_file(file_path, file_line), popup.dismiss()]))
        btn_layout.add_widget(Button(text='Cancel', on_press=lambda instance: popup.dismiss()))
        content.add_widget(btn_layout)

        popup = Popup(title="Confirm Delete", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def delete_file(self, file_path, file_line):
        try:
            os.remove(file_path)
            self.ids.temp_file_list.remove_widget(file_line)
            logger.debug(f"File deleted: {file_path}")
        except Exception as e:
            self.show_error_popup(f"Error deleting file: {str(e)}")

    def add_msx0_list(self):
        logger.debug("Adding MSX0 to list")
        self.show_spinner()
        new_msx0 = self.ids.server_ip_input.text
        if new_msx0 and new_msx0 not in self.msx0_layouts:
            
            msx0_info_layout = MSX0InfoLayout(new_msx0)
            self.msx0_layouts[new_msx0] = msx0_info_layout
            threading.Thread(target=self.add_msx0_to_list, args=(msx0_info_layout,)).start()
        else:
            self.hide_spinner()
            self.show_error_popup("Invalid IP address or already in the list")
        

    def add_msx0_to_list(self, msx0_info_layout):
        Clock.schedule_once(lambda dt: self.ids.msx0_list_layout.add_widget(msx0_info_layout))
        self.update_file_list_msx0(msx0_info_layout.msx0_host)
        
        Clock.schedule_once(lambda dt: self.hide_spinner())

    def display_msx0_list(self):
        logger.debug("Displaying servers")

        #self.ids.msx0_list_layout.clear_widgets()
        #Clock.schedule_once(lambda dt: self.ids.msx0_list_layout.clear_widgets())
        futures = []
        for msx0_host in list(self.msx0_layouts.keys()):
            future = self.executor.submit(self.update_file_list_msx0, msx0_host)
            futures.append(future)

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                error_msg=f"Error connecting to MSX0: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                Clock.schedule_once(lambda dt: self.show_error_popup(error_msg), 0)

        Clock.schedule_once(lambda dt: self.on_servers_displayed())

    def on_servers_displayed(self):
        logger.debug("MSX0 file list refreshed")
        self.msx0_refresh_button.disabled = False
        self.hide_spinner()

    def update_file_list_msx0(self, msx0_host):
        try:
            logger.debug(f"Updating file list for MSX0: {msx0_host}")
            parsed_files = self.get_file_list_msx0(host=msx0_host)
            if parsed_files[0] is not None:  # チェックを追加
                Clock.schedule_once(lambda dt: self.update_ui_for_msx0(msx0_host, parsed_files))
        except Exception as e:
            error_message = f"Error updating file list for {msx0_host}: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            Clock.schedule_once(lambda dt: self.show_error_popup(error_message))

        # if self.msx0_list and msx0_host == self.msx0_list[-1]:
        #     self.msx0_refresh_button.disabled = False


    def get_file_list_msx0(self, host, existing_connection=None):
        logger.debug(f"Getting file list from: {host}")
        tn = None
        try:
            if existing_connection:
                tn = existing_connection
            else:
                tn = telnetlib.Telnet(host, 2223, timeout=5)
                Utils.change_to_basic_mode(tn,timeout=5)

            # ドライブ情報を取得
            tn.write(b'_IOTGET("msx/u0/drive/a",a$):PRINT a$\r\n')
            result = Utils.read_until_timeout(tn, b"Ok", timeout=10).decode("utf-8")
            logger.debug(result)
            disk_info = result.split("\r\n")[-2].strip()
            logger.debug(f"get_file_list_msx0:{disk_info}")
            tn.write(b'FILES ,L\r\n')
            result = Utils.read_until_timeout(tn, b"Ok", timeout=10).decode("utf-8")
            lines = result.split("\r\n")[1:-1]
            print(lines)
            if "File not found" in lines[1].strip():
                drive_info, current_dir, files = None, None, []
            else:
                drive_info, current_dir, files = self.parse_files_l_output(lines)

            if not existing_connection:
                tn.close()

            return disk_info, drive_info, current_dir, files
        except TimeoutError as e:
            error_message = f"Connection to {host} timed out"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            Clock.schedule_once(lambda dt: self.show_error_popup(error_message))
            return None, None, None, []
        except Exception as e:
            error_message = f"Error connecting to {host}: {str(e)}"
            logger.error(error_message)
            if host in  self.msx0_layouts:
                self.remove_msx0_server(host)
            Clock.schedule_once(lambda dt: self.show_error_popup(error_message))
            return None, None, None, []
        finally:
            if tn and not existing_connection:
                tn.close()


    def parse_files_l_output(self, lines):
        files = []
        drive_info = None
        current_dir = None
        for line in lines:
            if line == "FILES ,L":
                continue
            if ':' in line[:2]:  # ドライブ情報の行
                drive_info =line[:2].strip()
                current_dir = line[3:].strip()
                logger.debug(f"parse_files_l_output:{drive_info}")
                continue
           
            name = line[:8].strip()
            ext = line[9:12].strip()
            attr = line[13:18].strip()
            size = line[18:].strip()

            is_directory = 'd' in attr

            if is_directory:
                files.append({
                    'name': name,
                    'ext': '',
                    'is_directory': True,
                    'attr': attr,
                    'size': int(size) if size.isdigit() else 0
                })
            else:
                files.append({
                    'name': name,
                    'ext': ext,
                    'is_directory': False,
                    'attr': attr,
                    'size': int(size) if size.isdigit() else 0
                })
        return drive_info, current_dir, files

    def update_ui_for_msx0(self, msx0_host, parsed_files):
        logger.debug(f"Updating UI for MSX0: {msx0_host}")
        #self.ids.msx0_list_layout.clear_widgets()  # Clear existing widgets
        
        disk_info, drive_info, current_dir, files = parsed_files
        
        if msx0_host in self.msx0_layouts:
            # 既存のレイアウトを更新
            msx0_info_layout = self.msx0_layouts[msx0_host]
            msx0_info_layout.clear_widgets()
        else:
            # 新しいレイアウトを作成
            msx0_info_layout = MSX0InfoLayout(msx0_host)
            self.msx0_layouts[msx0_host] = msx0_info_layout
            self.ids.msx0_list_layout.add_widget(msx0_info_layout)

        # Add server information line
        info_line = BoxLayout(size_hint_y=None, height=24)
        checkbox = CheckBox(size_hint_x=None, width=30)
        info_line.add_widget(checkbox)

        disk_info =disk_info if disk_info==None or len(disk_info)<=10 else disk_info[:4]+".."+disk_info[-4:]
        info_text = f"{msx0_host}\\{disk_info}\\{drive_info}\\{current_dir}"
        info_label = Label(text=info_text, halign='left')
        info_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        info_line.add_widget(info_label)

        cmd_btn = IconButton(source='./icon/cmd_btn.png', size_hint_x=None, width=32)
        cmd_btn.bind(on_press=lambda instance: self.show_command_dialog(msx0_host))
        info_line.add_widget(cmd_btn)
        disk_change_btn = IconButton(source='./icon/disk_change_btn.png', size_hint_x=None, width=32)
        disk_change_btn.bind(on_press=lambda instance: self.show_disk_change_dialog(msx0_host))
        info_line.add_widget(disk_change_btn)

        reset_btn = IconButton(source='./icon/reset_btn.png', size_hint_x=None, width=32)
        reset_btn.bind(on_press=lambda instance: self.confirm_reset_msx0(msx0_host))
        info_line.add_widget(reset_btn)

        remove_btn = IconButton(source='./icon/remove_btn.png', size_hint_x=None, width=32)
        remove_btn.bind(on_press=lambda instance: self.remove_msx0_server(msx0_host))
        info_line.add_widget(remove_btn)

#        self.ids.msx0_list_layout.add_widget(info_line)
        msx0_info_layout.add_widget(info_line)

        for file_info in files:
            file_line = self.create_file_line_for_msx0(file_info, msx0_host)
            msx0_info_layout.add_widget(file_line)


    def create_file_line_for_msx0(self, file_info, msx0_host):
        file_line = BoxLayout(size_hint_y=None, height=24)
        file_line.add_widget(Label(text="", size_hint_x=None, width=30))
        
        if file_info['is_directory']:
            file_name = f"{file_info['name']}\\"  # ディレクトリ名の最後に「\」を追加
        else:
            file_name = f"{file_info['name']}.{file_info['ext']}" if file_info['ext'] else file_info['name']
        
        file_name_label = Label(text=file_name, halign='left', size_hint_x=0.4)
        file_name_label.bind(size=lambda *args: setattr(file_name_label, 'text_size', (file_name_label.width, None)))
        file_line.add_widget(file_name_label)

        if file_info['is_directory']:
            file_line.add_widget(Widget(size_hint_x=0.2))
        else:
            size_label = Label(text=f"{file_info['size']} bytes", size_hint_x=0.2)
            file_line.add_widget(size_label)

        if file_info['is_directory']:
            change_dir_btn = IconButton(source='./icon/change_dir_btn.png', size_hint_x=None, width=32)
            # change_dir_btn = Button(text='CD', font_size=10, size_hint_x=None, width=32)
            change_dir_btn.bind(on_press=lambda instance: self.change_directory(file_info['name'], msx0_host))
            file_line.add_widget(change_dir_btn)
        elif file_info['ext'].upper() == 'BAS':
            run_btn = IconButton(source='./icon/run_btn.png', size_hint_x=None, width=32)
            #run_btn = Button(text='RUN', font_size=10, size_hint_x=None, width=32)
            run_btn.bind(on_press=lambda instance: self.confirm_run_onMsx0(file_name, file_line, msx0_host))
            file_line.add_widget(run_btn)
        elif file_info['ext'].upper() == 'COM':
            run_btn = IconButton(source='./icon/exec_btn.png', size_hint_x=None, width=32)
            #run_btn = Button(text='EXEC', font_size=10, size_hint_x=None, width=32)
            run_btn.bind(on_press=lambda instance: self.confirm_exec_onMsx0(file_name, file_line, msx0_host))
            file_line.add_widget(run_btn)
        else:
            file_line.add_widget(Widget(size_hint_x=None, width=32))

        #delete_btn = Button(text='DEL\nETE', font_size=10, size_hint_x=None, width=32)
        delete_btn = IconButton(source='./icon/delete_btn.png', size_hint_x=None, width=32)
        delete_btn.bind(on_press=lambda instance: self.confirm_delete_onMsx0(file_name, file_line, msx0_host))
        file_line.add_widget(delete_btn)

        return file_line
    
    def show_command_dialog(self, msx0_host):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        command_input = TextInput(hint_text='Enter command', multiline=False)
        content.add_widget(command_input)
        
        btn_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        ok_button = Button(text='Execute')
        cancel_button = Button(text='Cancel')
        
        btn_layout.add_widget(ok_button)
        btn_layout.add_widget(cancel_button)
        content.add_widget(btn_layout)

        popup = Popup(title=f"Execute Command on {msx0_host}", content=content, size_hint=(None, None), size=(400, 200))
        
        ok_button.bind(on_press=lambda instance: [self.execute_command(msx0_host, command_input.text), popup.dismiss()])
        cancel_button.bind(on_press=popup.dismiss)

        popup.open()

    def execute_command(self, msx0_host, command):
        self.show_spinner()
        threading.Thread(target=self._execute_command_thread, args=(msx0_host, command)).start()

    def _execute_command_thread(self, msx0_host, command):
        logger.debug("_execute_command_thread:start")
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                response = Utils.change_to_dos_mode(tn,timeout=5)
                if b'A>' in response:
                    logger.debug(f"_execute_command_thread:{command.encode('ascii') }")
                    tn.write(command.encode('ascii') + b'\r\n')
                    result = tn.read_until(b'A>', timeout=30).decode('ascii')
                    Clock.schedule_once(lambda dt: self.show_command_result(result), 0)
                else:
                    error_msg = "This server cannot change to DOS mode."
                    Clock.schedule_once(lambda dt: self.show_error_popup(error_msg), 0)
        except Exception as e:
            error_msg = f"Error executing command on {msx0_host}: {str(e)}"
            Clock.schedule_once(lambda dt: self.show_error_popup(error_msg), 0)
        finally:
            Clock.schedule_once(lambda dt: self.hide_spinner())
            logger.debug("_execute_command_thread:end")

    def show_command_result(self, result):
        content = BoxLayout(orientation='vertical')
        scroll_view = ScrollView(size_hint=(1, 1))
        label = Label(text=result, size_hint_y=None, text_size=(400, None))
        label.bind(texture_size=label.setter('size'))
        scroll_view.add_widget(label)
        content.add_widget(scroll_view)
        
        popup = Popup(title="Command Execution Result", content=content, size_hint=(None, None), size=(450, 300))
        popup.open()
    def change_directory(self, dir_name, msx0_host):
        self.show_spinner()
        threading.Thread(target=self._change_directory_thread, args=(dir_name, msx0_host)).start()

    def _change_directory_thread(self, dir_name, msx0_host):
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                Utils.change_to_basic_mode(tn,timeout=5)
                
                change_dir_command = f'_CHDIR("{dir_name}")\r\n'.encode('ascii')
                logger.debug("_change_directory_thread:command_write:start")
                tn.write(change_dir_command)
                logger.debug("_change_directory_thread:command_write:end")
                result = Utils.read_until_timeout(tn, b"Ok", 5).decode("utf-8")
                
                if "Ok" in result:
                    # ディレクトリ変更が成功した場合、ファイルリストを再取得
                    parsed_files = self.get_file_list_msx0(msx0_host,existing_connection=tn)
                    Clock.schedule_once(lambda dt: self.update_ui_for_msx0(msx0_host, parsed_files))
                else:
                    error_message = f"Failed to change directory to {dir_name}"
                    Clock.schedule_once(lambda dt: self.show_error_popup(error_message))
        except Exception as e:
            error_message = f"Error changing directory: {str(e)}"
            Clock.schedule_once(lambda dt: self.show_error_popup(error_message))
        finally:
            Clock.schedule_once(lambda dt: self.hide_spinner())

    def parse_files(self, file_list):
        parsed_files = []
        for line in file_list:
            line_length = len(line)
            num_files = line_length // 13 + 1
            for i in range(num_files):
                file_name = line[i*13 : i*13 + 8].strip()
                extension = line[i*13 + 9 : i*13 + 12].strip()
                if len(file_name) >= 3 and file_name[1:3] == ':\\':
                    continue
                if file_name:
                    parsed_files.append((file_name, extension))
        return parsed_files

    def confirm_reset_msx0(self, ip_address):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f'Are you sure you want to reset MSX0 at {ip_address}?'))
        btn_layout = BoxLayout(size_hint_y=None, height=30)
        
        def do_reset(instance):
            self.reset_msx0(ip_address)
            popup.dismiss()

        btn_layout.add_widget(Button(text='OK', on_press=do_reset))
        btn_layout.add_widget(Button(text='Cancel', on_press=lambda instance: popup.dismiss()))
        content.add_widget(btn_layout)

        popup = Popup(title="Confirm Reset", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def reset_msx0(self, ip_address):
        try:
            server_address = (ip_address, 2224)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(server_address)
                payloads = [
                    "7de600008101",
                    "7de61000f102",
                    "ffffffffffffffffffffffffffffffff",
                    "7de600008103"
                ]
                for payload in payloads:
                    sock.send(bytes.fromhex(payload))
                    time.sleep(0.1)
            self.show_info_popup(f"Reset command sent to MSX0 at {ip_address}")
        except Exception as e:
            error_msg = f"Error resetting MSX0 at {ip_address}: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.show_error_popup(error_msg)

    def confirm_delete_onMsx0(self, file_path, file_line, msx0_host):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Are you sure you want to delete this file?'))
        btn_layout = BoxLayout(size_hint_y=None, height=30)
        btn_layout.add_widget(Button(text='OK', on_press=lambda instance: [self.start_delete_file_onMsx0(file_path, file_line, msx0_host), popup.dismiss()]))
        btn_layout.add_widget(Button(text='Cancel', on_press=lambda instance: popup.dismiss()))
        content.add_widget(btn_layout)

        popup = Popup(title="Confirm Delete", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def start_delete_file_onMsx0(self, file_path, file_line, msx0_host):
        self.show_spinner()
        threading.Thread(target=self.delete_file_onMsx0, args=(file_path, file_line, msx0_host)).start()

    def delete_file_onMsx0(self, file_path, file_line, msx0_host):
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                Utils.change_to_basic_mode(tn,timeout=5)
                tn.write(b'KILL "' + file_path.encode("ascii") + b'"\r\n')
                Utils.read_until_timeout(tn, b"Ok", 5).decode("utf-8")

            Clock.schedule_once(lambda dt: self.update_ui_after_delete(file_line))
            Clock.schedule_once(lambda dt: self.show_info_popup(f"File {file_path} deleted successfully from {msx0_host}"))

        except TimeoutError:
            self.show_error_popup(f"Connection to {msx0_host} timed out while deleting file")
        except Exception as e:
            self.show_error_popup(f"Error deleting file on {msx0_host}: {str(e)}")
        finally:
            Clock.schedule_once(lambda dt: self.hide_spinner())

    def update_ui_after_delete(self, file_line):
        self.ids.msx0_list_layout.remove_widget(file_line)


    def show_disk_change_dialog(self, msx0_host):
        # 改修: LoadingSpinnerを表示
        self.show_spinner()
        
        # ディスク情報の取得を非同期で行う
        threading.Thread(target=self._get_disk_info, args=(msx0_host,)).start()
        
    def _get_disk_info(self, msx0_host):
        current_disk = "Unknown"
        available_disks =  []
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                Utils.change_to_basic_mode(tn,timeout=5)
                tn.write(b'_IOTGET("msx/u0/drive/a",a$):PRINT a$\r\n')
                result = Utils.read_until_timeout(tn, b"Ok", 5).decode("utf-8")
                current_disk = result.split("\r\n")[1].strip()
            
                tn.write(b'CLEAR800:DIM X$(30):_IOTFIND("host/media/dsk",CC):_IOTFIND("host/media/dsk",X$(0),31):FOR I=1 TO CC-1:PRINTX$(I):NEXTI\r\n')
                result = Utils.read_until_timeout(tn, b"Ok", 5).decode("utf-8")
                available_disks = [line.strip() for line in result.split("\r\n")[2:-1]]

        except Exception as e:
            logger.error(f"Error getting disk: {str(e)}")

        finally:
            # UI更新とLoadingSpinner非表示をメインスレッドで行う
            Clock.schedule_once(lambda dt: self._show_disk_dialog(msx0_host, current_disk, available_disks))

    def _show_disk_dialog(self, msx0_host, current_disk, available_disks):
        logger.debug("_show_disk_dialog:start")
        self.hide_spinner()
        
        def on_disk_select(selected_disk):
            self.change_disk(msx0_host, selected_disk)
            self.refresh_msx0_file_list()
        
        dialog = DiskSelectionDialog(current_disk, available_disks, on_disk_select)
        dialog.open()
        logger.debug("_show_disk_dialog:end")

    def change_disk(self, msx0_host, new_disk):
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                Utils.change_to_basic_mode(tn,timeout=5)
                command = f'_IOTPUT("msx/u0/drive/a","{new_disk}"):_IOTGET("msx/u0/drive/a",a$):PRINT a$:_IOTPUT("conf/save",1)\r\n'
                tn.write(command.encode('ascii'))
                result = Utils.read_until_timeout(tn, b"Ok", 5).decode("utf-8")
                changed_disk = result.split("\r\n")[1].strip()
                if changed_disk == new_disk:
                    self.show_info_popup(f"Disk changed to {new_disk}")
                    parsed_files = self.get_file_list_msx0(host=msx0_host,existing_connection=tn)
                    Clock.schedule_once(lambda dt: self.update_ui_for_msx0(msx0_host, parsed_files))
                else:
                    self.show_error_popup(f"Failed to change disk to {new_disk}")
        except Exception as e:
            logger.error(f"Error changing disk: {str(e)}")
            self.show_error_popup(f"Error changing disk: {str(e)}")


    def confirm_run_onMsx0(self, file_path, file_line, msx0_host):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Are you sure you want to run this file?'))
        btn_layout = BoxLayout(size_hint_y=None, height=30)
        btn_layout.add_widget(Button(text='OK', on_press=lambda instance: [self.run_file_onMsx0(file_path, file_line, msx0_host), popup.dismiss()]))
        btn_layout.add_widget(Button(text='Cancel', on_press=lambda instance: popup.dismiss()))
        content.add_widget(btn_layout)

        popup = Popup(title="Confirm RUN", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def run_file_onMsx0(self, file_path, file_line, msx0_host):
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                Utils.change_to_basic_mode(tn,timeout=5)
                tn.write(b'RUN "' + file_path.encode("ascii") + b'"\r\n')
            self.show_info_popup(f"File {file_path} executed on {msx0_host}")
        except TimeoutError:
            self.show_error_popup(f"Connection to {msx0_host} timed out while running file")
        except Exception as e:
            self.show_error_popup(f"Error running file on {msx0_host}: {str(e)}")

    def confirm_exec_onMsx0(self, file_path, file_line, msx0_host):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f'Execute {file_path} on {msx0_host}?'))
        
        options_input = TextInput(hint_text='Enter command line options (optional)', multiline=False)
        content.add_widget(options_input)
        
        no_timeout_layout = BoxLayout(size_hint_y=None, height=30)
        no_timeout_checkbox = CheckBox(size_hint_x=None, width=30)
        no_timeout_label = Label(text='Wait indefinitely (no timeout)')
        no_timeout_layout.add_widget(no_timeout_checkbox)
        no_timeout_layout.add_widget(no_timeout_label)
        content.add_widget(no_timeout_layout)
        
        btn_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        ok_button = Button(text='OK')
        cancel_button = Button(text='Cancel')
        
        btn_layout.add_widget(ok_button)
        btn_layout.add_widget(cancel_button)
        content.add_widget(btn_layout)

        popup = Popup(title="Confirm Execute", content=content, size_hint=(None, None), size=(400, 250))
        
        ok_button.bind(on_press=lambda instance: [self.exec_file_onMsx0(file_path, options_input.text, msx0_host, no_timeout_checkbox.active), popup.dismiss()])
        cancel_button.bind(on_press=popup.dismiss)

        popup.open()

    def exec_file_onMsx0(self, file_path, options, msx0_host, no_timeout):
        self.show_spinner()
        threading.Thread(target=self._exec_file_thread, args=(file_path, options, msx0_host, no_timeout)).start()

    def _exec_file_thread(self, file_path, options, msx0_host, no_timeout):
        try:
            with telnetlib.Telnet(msx0_host, 2223, timeout=5) as tn:
                response = Utils.change_to_dos_mode(tn,timeout=5)
                if b'A>' in response:
                    command = f' {file_path} {options}'.strip().encode('ascii') + b'\r\n'
                    tn.write(command)
                    if no_timeout:
                        result = tn.read_until(b'A>').decode('ascii')
                    else:
                        result = tn.read_until(b'A>', timeout=30).decode('ascii')
                    Clock.schedule_once(lambda dt: self.show_exec_result(result), 0)
                else:
                    error_msg = "This server cannot change to DOS mode."
                    Clock.schedule_once(lambda dt: self.show_error_popup(error_msg), 0)
        except TimeoutError:
            error_msg = f"Connection to {msx0_host} timed out while executing file"
            Clock.schedule_once(lambda dt: self.show_error_popup(error_msg), 0)
        except EOFError:
            result = "Command execution completed. Connection closed by the server."
            Clock.schedule_once(lambda dt: self.show_exec_result(result), 0)
        except Exception as e:
            error_msg = f"Error executing file on {msx0_host}: {str(e)}"
            Clock.schedule_once(lambda dt: self.show_error_popup(error_msg), 0)
        finally:
            Clock.schedule_once(lambda dt: self.hide_spinner())

    def show_exec_result(self, result):
        content = BoxLayout(orientation='vertical')
        scroll_view = ScrollView(size_hint=(1, 1))
        label = Label(text=result, size_hint_y=None, text_size=(400, None))
        label.bind(texture_size=label.setter('size'))
        scroll_view.add_widget(label)
        content.add_widget(scroll_view)
        
        popup = Popup(title="Execution Result", content=content, size_hint=(None, None), size=(450, 300))
        popup.open()

    def upload_file(self):
        selected_files = self.get_selected_files()
        selected_servers = self.get_selected_servers()

        if not selected_files or not selected_servers:
            self.show_error_popup(f"No files or servers selected")
            logger.debug(f"upload_file:files:{selected_files}\nservers:{selected_servers}")
            return

        self.upload_cancel_flag.clear()
        self.upload_spinner.cancel_button.bind(on_press=self.cancel_upload)
        self.upload_spinner.open()

        self.total_uploads = len(selected_files) * len(selected_servers)
        self.uploads_completed = 0

        self.upload_start_time = time.time() 

        for server_ip in selected_servers:
            self.upload_threads[server_ip] = threading.Thread(
                target=self.upload_worker,
                args=(server_ip, selected_files.copy())
            )
            self.upload_threads[server_ip].start()

    def get_selected_files(self):
        selected_files = []
        for child in self.ids.temp_file_list.children:
            if isinstance(child, BoxLayout):
                checkbox = child.children[-1]
                if isinstance(checkbox, CheckBox) and checkbox.active:
                    filename_label = child.children[5]
                    logger.debug(f"get_selected_servers:{filename_label}")
                    file_path = os.path.join(self.temp_folder_path, filename_label.text)
                    selected_files.append(file_path)
        return selected_files

    def get_selected_servers(self):
        selected_servers = []
        for msx0_info_layout in self.ids.msx0_list_layout.children:
            if isinstance(msx0_info_layout, MSX0InfoLayout):
                # サーバー情報行は最初の子要素と仮定
                info_line = msx0_info_layout.children[-1]  # 注意: children リストは逆順
                if isinstance(info_line, BoxLayout):
                    checkbox = info_line.children[-1]  # チェックボックスは最初の子要素と仮定
                    if isinstance(checkbox, CheckBox) and checkbox.active:
                        selected_servers.append(msx0_info_layout.msx0_host)
        return selected_servers

    def upload_worker(self, server_ip, files_to_upload):
        for file_path in files_to_upload:
            if self.upload_cancel_flag.is_set():
                logger.debug(f"Upload cancelled for {server_ip}")
                break
            logger.debug(f"Uploading {file_path} to {server_ip}")
            try:
                result, execution_time = self.uploader.upload_file(server_ip, file_path, self.upload_cancel_flag)
                logger.debug(f"Upload to {server_ip}: {result}")
                logger.debug(f"Execution time: {execution_time} seconds")
                if "Done" in result:
                    self.successful_uploads += 1
            except Exception as e:
                logger.error(f"Error uploading {file_path} to {server_ip}: {e}")
            finally:
                self.uploads_completed += 1
                progress = (self.uploads_completed / self.total_uploads) * 100
                Clock.schedule_once(lambda dt, p=progress: self.update_upload_progress(p))
        del self.upload_threads[server_ip]
        if not self.upload_threads:
            Clock.schedule_once(self.finish_upload)

    def update_upload_progress(self, progress):
        self.upload_spinner.update_progress(progress)

    def finish_upload(self, dt):
        self.display_msx0_list()
        self.upload_spinner.dismiss()
        elapsed_time = time.time() - self.upload_start_time
        self.show_info_popup(f"Upload completed\nSuccessful uploads: {self.successful_uploads}/{self.total_uploads}\nTotal time: {elapsed_time}sec\n")
        self.update_upload_progress(0) 
        self.successful_uploads=0

    def cancel_upload(self, instance):
        self.upload_cancel_flag.set()
        self.show_info_popup("Upload cancelled")

    def show_error_popup(self, message):
        content = Label(text=message)
        popup = Popup(title="Error", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_info_popup(self, message):
        content = Label(text=message)
        popup = Popup(title="Information", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def create_progress_bar(self):
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=30)
        self.progress_label = Label(text="Uploading: 0%", size_hint_y=None, height=30)
        self.ids.upload_status.clear_widgets()
        self.ids.upload_status.add_widget(self.progress_label)
        self.ids.upload_status.add_widget(self.progress_bar)

    def update_progress(self, value):
        if self.progress_bar:
            self.progress_bar.value = value
            self.progress_label.text = f"Uploading: {int(value)}%"

    def reset_progress(self):
        if self.progress_bar:
            self.progress_bar.value = 0
            self.progress_label.text = "Upload complete"
            Clock.schedule_once(self.remove_progress_bar, 3)  # 3秒後にプログレスバーを削除
        self.ids.cancel_button.disabled = True
        self.upload_cancel_flag.clear()

    def remove_progress_bar(self, dt):
        self.ids.upload_status.clear_widgets()

    def download_file_fromView(self, url, popup):
        try:
            filename, _ = self._download_file(url, self.config.get('General', 'temp_folder'))
            self.populate_file_list()
            popup.dismiss()
            logger.info(f"File downloaded: {filename}")
        except ValueError:
            popup.dismiss()
        except Exception as e:
            popup.dismiss()
            self.show_error_popup(f"Download failed: {str(e)}")

    def download_file(self):
        url = self.ids.url_input.text
        try:
            filename, _ = self._download_file(url, self.config.get('General', 'temp_folder'))
            self.populate_file_list()
            logger.info(f"File downloaded: {filename}")
        except ValueError:
            pass
        except Exception as e:
            self.show_error_popup(f"Download failed: {str(e)}")

        # self.add_to_history(url, 'url')

    def _download_file(self, url, save_path, max_redirects=10):
        logger.info(f"Starting download: {url}")
        try:
            self.show_spinner()
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            response = session.get(url, allow_redirects=True, stream=True)
            logger.info(f"Final URL after redirects: {response.url}")

            # Check if the response is HTML
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                raise ValueError(f"Unexpected HTML content at {response.url}")

            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                filename = re.findall("filename=(.+)", content_disposition)[0].strip('"')
            else:
                filename = response.url.split('/')[-1]

            logger.info(f"Downloading file: {filename}")
            file_path = os.path.join(save_path, filename)

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            actual_size = os.path.getsize(file_path)
            logger.info(f"File saved. Actual size on disk: {actual_size} bytes")

            return filename, file_path

        except ValueError as e:
            Clock.schedule_once(lambda dt: self.hide_spinner())
            error_message=f" {str(e)}"
            logger.error(f"Download failed: {str(e)}")
            Clock.schedule_once(lambda dt: self.show_redirect_error(error_message, response.url), 0)
            raise
        except Exception as e:
            Clock.schedule_once(lambda dt: self.hide_spinner())
            logger.error(f"Download failed: {str(e)}", exc_info=True)
            raise

    def show_redirect_error(self, error_message, final_url):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f"Error: {error_message}"))
        # Create a button with the final URL as text
        url_button = Button(
            text=f"Final URL: {final_url}",
            size_hint_y=None,
            height=44
        )
        content.add_widget(url_button)
        
        content.add_widget(Label(text="Click the URL above to access it directly."))
        
        close_button = Button(text="Close", size_hint_y=None, height=44)
        content.add_widget(close_button)
        
        popup = Popup(title="Download Error", content=content, size_hint=(0.9, 0.9))

        def load_url_from_button(popup,url):
            popup.dismiss()
            self.ids.url_input.text = url
            self.load_url()
        url_button.bind(on_press=lambda instance: load_url_from_button(popup,url=final_url))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def toggle_all_checkboxes(self):
        self.all_checked = not self.all_checked  # Toggle the state
        for child in self.ids.temp_file_list.children:
            if isinstance(child, BoxLayout):
                checkbox = child.children[-1]  # Assuming the checkbox is the last child
                if isinstance(checkbox, CheckBox):
                    checkbox.active = self.all_checked

    def delete_selected_files(self):
        files_to_delete = []
        for child in self.ids.temp_file_list.children:
            if isinstance(child, BoxLayout):
                checkbox = child.children[-1]  # Assuming the checkbox is the last child
                if isinstance(checkbox, CheckBox) and checkbox.active:
                    filename_label = child.children[4]  # Assuming the filename label is the 5th child
                    files_to_delete.append(filename_label.text)

        if not files_to_delete:
            self.show_info_popup("No files selected for deletion.")
            return

        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f"Are you sure you want to delete {len(files_to_delete)} selected file(s)?"))
        btn_layout = BoxLayout(size_hint_y=None, height=30)
        
        def confirm_delete(instance):
            for filename in files_to_delete:
                file_path = os.path.join(self.temp_folder_path, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {filename}: {str(e)}")
            self.populate_file_list()  # Refresh the file list
            self.show_info_popup(f"Deleted {len(files_to_delete)} file(s).")
            popup.dismiss()

        btn_layout.add_widget(Button(text='Yes', on_press=confirm_delete))
        btn_layout.add_widget(Button(text='No', on_press=lambda instance: popup.dismiss()))
        content.add_widget(btn_layout)
        popup = Popup(title="Confirm Deletion", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()


    def refresh_msx0_file_list(self, *args):
        self.show_spinner()
        self.msx0_refresh_button.disabled = True
        
        # ファイルリストの更新を非同期で行う
        threading.Thread(target=self._refresh_msx0_file_list_thread).start()

    def _refresh_msx0_file_list_thread(self):
        self.display_msx0_list()
        self.hide_spinner()
        self.msx0_refresh_button.disabled = False
        logger.debug("MSX0 file list refreshed")
        
    def remove_msx0_server(self, server_ip):
        if server_ip in self.msx0_layouts:
            msx0_info_layout = self.msx0_layouts.pop(server_ip)
            Clock.schedule_once(lambda dt: self.ids.msx0_list_layout.remove_widget(msx0_info_layout))
            # if server_ip in self.msx0_layouts:
            #     self.ids.msx0_list_layout.remove_widget(self.msx0_layouts[server_ip])
            #     del self.msx0_layouts[server_ip]
            self.display_msx0_list()
        else:
            self.show_error_popup(f"Server {server_ip} not found in the list")
 
    def parse_msx_dsk(self, filename):
        with open(filename, 'rb') as f:
            # ブートセクターの読み取り
            boot_sector = f.read(0x200)  # 512 bytes

            # ディスク名の取得（MSX_04）
            disk_name = boot_sector[3:9].decode('ascii', errors='ignore').strip()

            # ファイルシステム情報の読み取り
            bytes_per_sector = struct.unpack('<H', boot_sector[0x0B:0x0D])[0]
            sectors_per_cluster = boot_sector[0x0D]
            reserved_sectors = struct.unpack('<H', boot_sector[0x0E:0x10])[0]
            number_of_fats = boot_sector[0x10]
            root_entries = struct.unpack('<H', boot_sector[0x11:0x13])[0]
            total_sectors = struct.unpack('<H', boot_sector[0x13:0x15])[0]
            media_descriptor = boot_sector[0x15]
            sectors_per_fat = struct.unpack('<H', boot_sector[0x16:0x18])[0]

            # ルートディレクトリの位置を計算
            root_dir_start = (reserved_sectors + number_of_fats * sectors_per_fat) * bytes_per_sector

            # ルートディレクトリエントリの読み取り
            f.seek(root_dir_start)
            entries = []
            for _ in range(root_entries):
                entry = f.read(32)
                if entry[0] == 0:  # 未使用エントリ
                    break
                if entry[0] == 0xE5:  # 削除されたファイル
                    continue
                file_name = entry[:8].decode('ascii', errors='ignore').strip()
                file_ext = entry[8:11].decode('ascii', errors='ignore').strip()
                attributes = entry[11]
                start_cluster = struct.unpack('<H', entry[26:28])[0]
                file_size = struct.unpack('<I', entry[28:32])[0]
                entries.append({
                    'name': f"{file_name}.{file_ext}".rstrip('.'),
                    'size': file_size,
                    'attributes': attributes,
                    'start_cluster': start_cluster
                })
        
        return {
            'disk_name': disk_name,
            'bytes_per_sector': bytes_per_sector,
            'sectors_per_cluster': sectors_per_cluster,
            'reserved_sectors': reserved_sectors,
            'number_of_fats': number_of_fats,
            'root_entries': root_entries,
            'total_sectors': total_sectors,
            'media_descriptor': hex(media_descriptor),
            'sectors_per_fat': sectors_per_fat,
            'files': entries
        }

    def extract_files_from_dsk(self, dsk_path):
        dsk_info = self.parse_msx_dsk(dsk_path)
        extracted_files = []

        with open(dsk_path, 'rb') as dsk_file:
            # ルートディレクトリの開始位置を計算
            root_dir_start = (dsk_info['reserved_sectors'] + 
                            dsk_info['number_of_fats'] * dsk_info['sectors_per_fat']) * dsk_info['bytes_per_sector']
            
            # データ領域の開始位置を計算
            data_start = root_dir_start + (dsk_info['root_entries'] * 32)

            for file_info in dsk_info['files']:
                file_name = file_info['name']
                file_size = file_info['size']
                
                # ファイルの開始クラスタを取得（これはparse_msx_dskで追加する必要があります）
                start_cluster = file_info.get('start_cluster', 2)  # デフォルトは2（最初のデータクラスタ）
                
                # ファイルの開始位置を計算
                file_start = data_start + (start_cluster - 2) * dsk_info['sectors_per_cluster'] * dsk_info['bytes_per_sector']
                
                # ファイルの内容を読み取る
                dsk_file.seek(file_start)
                file_content = dsk_file.read(file_size)

                # テンポラリフォルダに抽出したファイルを保存
                output_path = os.path.join(self.temp_folder_path, file_name)
                with open(output_path, 'wb') as output_file:
                    output_file.write(file_content)
                extracted_files.append(file_name)
                
        return extracted_files

    def on_extract_dsk(self, instance):
        dsk_path = instance.file_path
        extracted_files = self.extract_files_from_dsk(dsk_path)
        
        # 抽出結果をポップアップで表示
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f"Extracted {len(extracted_files)} files:"))
        for file in extracted_files:
            content.add_widget(Label(text=file))
        
        popup = Popup(title="Extraction Complete", content=content, size_hint=(0.8, 0.8))
        popup.open()
        
        # ファイルリストを更新
        self.populate_file_list()

class FileUploader:

    def __init__(self, config ):
        self.port = 2223
        self.timeout = 10  # Default timeout value
        self.config = config
        self.load_basic_program()
 
    def load_basic_program(self):
        basic_program_path = self.config.get('Advanced', 'basic_program_path')
        try:
            with open(basic_program_path, 'r') as file:
                lines = file.readlines()
                self.basic_program = ''.join(line.rstrip() + '\r\n' for line in lines)
        except FileNotFoundError as e:
            print(f"BASIC program file not found: {basic_program_path}")
            raise e

    def upload_file(self, server_ip, file_path, cancel_flag):
        print(f"!upload_file:uploading {file_path} to {server_ip}:")
        try:
            result, execution_time = msx0babaput(server_ip, self.basic_program, file_path, cancel_flag, self.timeout)
            print(f"Upload result: {result}")
            print(f"Execution time: {execution_time} seconds")
            return result, execution_time
        except Exception as e:
            error_message = f"Error uploading file: {str(e)}"
            print(error_message)
            return error_message, 0
