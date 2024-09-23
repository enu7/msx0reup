import kivy
kivy.require('2.1.0')
import asyncio
from kivy.app import async_runTouchApp
from kivy.lang import Builder

from kivy.utils import platform
import logging
from jnius import autoclass
from kivy.config import ConfigParser
from kivy.config import Config
#from PyQt5.QtWidgets import QApplication
import sys
import traceback
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
from kivy.utils import platform
import os

Config.set('kivy', 'default_font_size', '6')

from msx0reup import MSX0RemoteUploader
from kivy.app import App

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ.update({
    'KIVY_NO_CONSOLELOG': '1',
    'KIVY_LOG_LEVEL': 'debug'
})

try:
    from android.activity import bind as activity_bind
    logger.debug("Successfully imported android.activity.bind")
except ImportError as e:
    logger.error(f"Failed to import android.activity.bind: {e}")

class ReupApp(App):
    def build(self):
        logger.debug("Build method called")
        self.icon = './icon/msx0reup_icon.png'
        self.config = self.load_config()
        self.uploader = MSX0RemoteUploader(config=self.config)

        if platform == 'android':
            self.setup_android()
        else:
            logger.debug("Not running on Android. Skipping intent handling setup.")
        
        return self.uploader
    
    def setup_android(self):
        logger.debug("Android platform detected. Setting up intent handling.")
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            currentActivity = PythonActivity.mActivity
            intent = currentActivity.getIntent()
            self.handle_intent(intent)
            activity_bind(on_new_intent=self.on_new_intent)
            logger.debug("Intent handling set up successfully.")
        except Exception as e:
            logger.error(f"Failed to set up intent handling: {str(e)}")

    async def async_run(self, async_lib=None):
        await super().async_run(async_lib=async_lib)

    def on_stop(self):
        self.config.write()

    def load_config(self):
        config = ConfigParser()
        config_file = './msx0reup_settings.ini'
        config.read(config_file)
        if not config.has_section('General') or not config.has_section('Advanced'):
            self.create_default_config(config)
        return config

    def create_default_config(self, config):
        default_settings = {
            'General': {
                'temp_folder': './msx0reup_temp',
                'default_url': 'https://enu7.sakura.ne.jp/msx/',
                'default_msx0_ip': '192.168.0.11'
            },
            'Advanced': {
                'basic_program_path': './default_basic_program.txt'
            }
        }
        for section, settings in default_settings.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in settings.items():
                config.set(section, key, value)
        config.write()

    def handle_intent(self, intent):
        logger.debug("handle_intent called")
        if intent:
            action = intent.getAction()
            logger.debug(f"Initial intent action: {action}")
            self.on_new_intent(intent)
        else:
            logger.debug("Initial intent is None")

    def __init__(self, **kwargs):
        super(ReupApp, self).__init__(**kwargs)
        self.title = "MSX0 Remote Uploader"
        self.config = None
        logger.debug("ReupApp initialized")

    def on_new_intent(self, intent):
        logger.debug("on_new_intent called")
        logger.debug(f"Intent action: {intent.getAction()}")
        logger.debug(f"Intent extras: {intent.getExtras().keySet()}")
        
        if intent.getAction() == 'android.intent.action.SEND':
            logger.debug("SEND action detected")
            if intent.getType() == 'text/plain':
                logger.debug("text/plain type detected")
                url = intent.getStringExtra('android.intent.extra.TEXT')
                logger.debug(f"Received URL: {url}")
                if url:
                    self.uploader.process_shared_url(url)
                else:
                    logger.warning("Received empty URL")
            else:
                logger.warning(f"Unexpected intent type: {intent.getType()}")
        else:
            logger.warning(f"Unexpected intent action: {intent.getAction()}")

if __name__ == '__main__':
    import platform

    # プラットフォーム固有の設定
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    elif platform.system() == 'Linux':
        # Linux（AndroidもLinuxベース）用の設定
        import os
        if os.name == 'posix':
            import asyncio
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
            
    font_path = os.path.join(os.path.dirname(__file__), "font", "NotoSansJP-Regular.ttf")
    resource_add_path(os.path.dirname(font_path))
    LabelBase.register(DEFAULT_FONT, font_path)
    
    logger.debug("Starting ReupApp")
    loop = asyncio.get_event_loop()
    app = ReupApp()
    loop.run_until_complete(app.async_run())
    loop.close()