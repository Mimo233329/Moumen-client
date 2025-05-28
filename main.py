import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QGraphicsOpacityEffect,
    QSizePolicy, QComboBox, QMessageBox, QFormLayout, QLineEdit, QCheckBox,
    QScrollArea, QDialog, QDialogButtonBox, QFileDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer, QUrl,QRect, pyqtSignal # Added pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QPainter, QBrush, QPixmap, QDesktopServices, QFont, QFontDatabase
import smtplib
from email.mime.text import MIMEText
import string
import random
import socket
import requests # type: ignore
from datetime import datetime

# --- Global Data Fetching --- (No changes here)
def get_device_name():
    return socket.gethostname()

def get_current_time_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def Generate_Password(num):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(num))

def get_location_info():
    try:
        response = requests.get("https://ipinfo.io", timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "IP": data.get("ip", "N/A"), "City": data.get("city", "N/A"),
            "Region": data.get("region", "N/A"), "Country": data.get("country", "N/A"),
            "Location (lat,long)": data.get("loc", "N/A"), "Organization": data.get("org", "N/A")
        }
    except requests.exceptions.RequestException as e:
        print(f"Error getting location: {e}")
        return {
            "IP": "N/A", "City": "N/A", "Region": "N/A", "Country": "N/A",
            "Location (lat,long)": "N/A", "Organization": "N/A", "error": str(e)
        }

HTML_CONTENT_TEMPLATE = """
<html><head><style>body{{font-family:Arial,sans-serif;color:#333}}.container{{background-color:#f9f9f9;padding:20px;border-radius:8px;max-width:600px;margin:auto;border:1px solid #ddd}}.footer{{font-size:12px;color:#888;margin-top:20px}}</style></head><body><div class="container"><h2>Moumen Client - Verification Code</h2><p>Hello,</p><p>We noticed a sign-in attempt to your account on Moumen Client:</p><ul><li><strong>Date & Time:</strong> {time}</li><li><strong>IP Address:</strong> {ip}</li><li><strong>Location:</strong> {city}, {country}</li><li><strong>Device:</strong> {device_name}</li></ul><p>If this was you, please enter this verification code on Moumen Client. Your code is: <strong>{verification_code}</strong></p><p>If this wasn't you, you can safely ignore this email.</p><p>Cheers,<br>Moumen Team</p><div class="footer">This is an automated message. Please do not reply.</div></div></body></html>
"""

def send_verification_email(to_email: str, verification_code: str):
    sender = "moumen.mahmoud2014@gmail.com"
    app_password = "evaonebzdwoklnmc" 
    location_data = get_location_info()
    body_html = HTML_CONTENT_TEMPLATE.format(
        time=get_current_time_str(), ip=location_data["IP"], city=location_data["City"],
        country=location_data["Country"], device_name=get_device_name(),
        verification_code=verification_code)
    msg = MIMEText(body_html, "html")
    msg['Subject'] = "Your Moumen Client Verification Code"; msg['From'] = sender; msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, app_password); smtp_server.sendmail(sender, to_email, msg.as_string())
        print(f"Verification email sent to {to_email}"); return True
    except smtplib.SMTPAuthenticationError: print("SMTP AuthError"); return False
    except smtplib.SMTPException as e: print(f"SMTP Error: {e}"); return False
    except Exception as e: print(f"General email error: {e}"); return False

CONFIG_FILE = "config.json"; TRANSLATIONS_FILE = "translations.json"; ACCOUNTS_FILE = "account.json"
GAMES_FILE = "games.json" 

def create_placeholder_icon(open_eye=True, size=QSize(22,22), color_name="gray"):
    color=QColor(color_name);pixmap=QPixmap(size);pixmap.fill(Qt.transparent);painter=QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing);pen=painter.pen();pen.setColor(color);pen.setWidthF(1.5)
    painter.setPen(pen);eye_rect=QRect(2,size.height()//2-5,size.width()-4,10);painter.drawEllipse(eye_rect)
    if open_eye:painter.setBrush(color);ps=4;painter.drawEllipse(size.width()//2-ps//2,size.height()//2-ps//2,ps,ps)
    else:painter.drawLine(4,size.height()-6,size.width()-4,6)
    painter.end();return QIcon(pixmap)

class AnimatedStackedWidget(QStackedWidget): # No changes here
    def __init__(self,parent=None):super().__init__(parent);self.m_speed=300;self.m_animation_type=QEasingCurve.InOutCubic;self.m_active_animation=None
    def _create_opacity_effect(self,w):
        if not w:return None
        ef=w.graphicsEffect()
        if isinstance(ef,QGraphicsOpacityEffect):return ef
        ef=QGraphicsOpacityEffect(w);w.setGraphicsEffect(ef);return ef
    def switch_to_index(self,idx):
        ci=self.currentIndex()
        if ci==idx:
            w=self.widget(ci)
            if w:ef=self._create_opacity_effect(w)
            if w and ef and ef.opacity()!=1.0:ef.setOpacity(1.0)
            return
        if self.m_active_animation and self.m_active_animation.state()==QPropertyAnimation.Running:self.m_active_animation.stop()
        wo=self.widget(ci);wi=self.widget(idx)
        if not wi:return
        self.setCurrentIndex(idx);wi.show()
        ei=self._create_opacity_effect(wi)
        if ei:ei.setOpacity(0.0)
        if wo:
            eo=self._create_opacity_effect(wo)
            if eo:
                ao=QPropertyAnimation(eo,b"opacity");ao.setDuration(self.m_speed//2)
                ao.setStartValue(eo.opacity());ao.setEndValue(0.0);ao.setEasingCurve(self.m_animation_type)
                ao.finished.connect(lambda w=wo,e=ei:self._fade_out_finished(w,e))
                self.m_active_animation=ao;ao.start(QPropertyAnimation.DeleteWhenStopped);return
        self._start_fade_in(ei)
    def _fade_out_finished(self,wo,ei):
        if wo:wo.hide();self._start_fade_in(ei)
    def _start_fade_in(self,ei):
        if ei:
            ai=QPropertyAnimation(ei,b"opacity");ai.setDuration(self.m_speed)
            ai.setStartValue(0.0);ai.setEndValue(1.0);ai.setEasingCurve(self.m_animation_type)
            ai.finished.connect(self._animation_fully_finished)
            self.m_active_animation=ai;ai.start(QPropertyAnimation.DeleteWhenStopped)
    def _animation_fully_finished(self):
        cw=self.currentWidget()
        if cw:ef=self._create_opacity_effect(cw)
        if cw and ef:ef.setOpacity(1.0)
        self.m_active_animation=None

class AddGameDialog(QDialog): # No changes here
    def __init__(self, tr_func, parent=None):
        super().__init__(parent)
        self._tr = tr_func
        self.setWindowTitle(self._tr("add_game_dialog_title", "Add New Game"))
        self.setMinimumWidth(400)
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self._tr("game_name_placeholder_dialog", "Enter game name"))
        self.form_layout.addRow(self._tr("game_name_label_dialog", "Game Name:"), self.name_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText(self._tr("game_desc_placeholder_dialog", "Enter game description"))
        self.desc_edit.setFixedHeight(100)
        self.form_layout.addRow(self._tr("game_desc_label_dialog", "Description:"), self.desc_edit)

        self.cover_path_edit = QLineEdit()
        self.cover_path_edit.setPlaceholderText(self._tr("game_cover_placeholder_dialog", "Path to cover image"))
        self.cover_path_edit.setReadOnly(True)
        self.browse_button = QPushButton(self._tr("browse_button_dialog", "Browse..."))
        self.browse_button.clicked.connect(self.browse_cover)
        cover_layout = QHBoxLayout()
        cover_layout.addWidget(self.cover_path_edit)
        cover_layout.addWidget(self.browse_button)
        self.form_layout.addRow(self._tr("game_cover_label_dialog", "Cover Image:"), cover_layout)

        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(self._tr("dialog_ok_button", "OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(self._tr("dialog_cancel_button", "Cancel"))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def browse_cover(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 
                                                 self._tr("select_cover_dialog_title", "Select Cover Image"), "", 
                                                 self._tr("image_files_filter_dialog", "Image Files (*.png *.jpg *.jpeg *.bmp)"))
        if file_name:
            self.cover_path_edit.setText(file_name)

    def get_data(self):
        name = self.name_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        cover_path = self.cover_path_edit.text().strip()

        if not name:
            QMessageBox.warning(self, self._tr("game_add_fail_title", "Input Error"), self._tr("game_add_fail_message_name", "Game name cannot be empty."))
            return None
        return {
            "name": name,
            "description": description,
            "cover_path": cover_path
        }

# --- MODIFIED GameItemWidget ---
class GameItemWidget(QFrame):
    delete_requested = pyqtSignal(str) # Signal to emit when delete is clicked, carries game name

    def __init__(self, game_data, tr_func, parent=None): # Added tr_func
        super().__init__(parent)
        self.setObjectName("gameItem")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(120)
        self._tr = tr_func # Store translation function
        self.game_name = game_data.get("name", "N/A") # Store game name for the signal

        main_layout = QHBoxLayout(self) # Changed to main_layout to add button column
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Content Layout (Cover + Text) ---
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0,0,0,0) # No margin for this inner layout

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(100, 100) 
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;") 

        pixmap = QPixmap(game_data.get("cover_path", ""))
        if pixmap.isNull() or not game_data.get("cover_path"):
            ph_pixmap = QPixmap(100, 100)
            ph_pixmap.fill(QColor("lightGray")) 
            painter = QPainter(ph_pixmap)
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(ph_pixmap.rect(), Qt.AlignCenter, "No Cover")
            painter.end()
            self.cover_label.setPixmap(ph_pixmap)
        else:
            self.cover_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        content_layout.addWidget(self.cover_label)

        text_widget = QWidget() 
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(10,0,0,0) 
        
        self.name_label = QLabel(self.game_name) # Use stored game_name
        self.name_label.setObjectName("gameNameLabel") 
        self.name_label.setWordWrap(True)
        font = self.name_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2) 
        self.name_label.setFont(font)

        self.desc_label = QLabel(game_data.get("description", "N/A"))
        self.desc_label.setObjectName("gameDescLabel") 
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch() 
        content_layout.addWidget(text_widget, 1)
        
        main_layout.addWidget(content_widget, 1) # Content takes most space

        # --- Delete Button Column ---
        delete_button_layout = QVBoxLayout()
        delete_button_layout.setAlignment(Qt.AlignTop | Qt.AlignRight) # Align button to top-right of its column
        
        self.delete_button = QPushButton(self._tr("game_delete_button", "Delete")) # Use _tr
        self.delete_button.setObjectName("deleteGameButton") # For specific styling if needed
        self.delete_button.setFixedSize(QSize(80, 30)) # Adjust size as needed
        self.delete_button.setIcon(QIcon.fromTheme("edit-delete", QIcon(create_placeholder_icon(False, QSize(16,16), "red")))) # Example icon
        self.delete_button.clicked.connect(self.on_delete_clicked)
        
        delete_button_layout.addWidget(self.delete_button)
        delete_button_layout.addStretch() # Push button to the top

        main_layout.addLayout(delete_button_layout) # Add delete button column to main layout

    def on_delete_clicked(self):
        self.delete_requested.emit(self.game_name) # Emit signal with game name
# --- END MODIFIED GameItemWidget ---

class MoumenClient(QMainWindow):
    def __init__(self, default_nav_bar_position="left"):
        super().__init__()
        self.default_nav_bar_position = default_nav_bar_position
        self.translations = {}
        
        self.font_en_path = "fonten.ttf"
        self.font_ar_path = "fontar.ttf"

        self.is_logged_in = False
        self.current_user_details = None
        
        self.load_translations()
        self.load_settings() 

        self.set_global_font()

        self.setWindowTitle(self._tr("app_title", "Moumen Client"))
        self.setGeometry(100, 100, 1000, 700)
        self.icon_path = "ico.png" 
        self.sun_icon_path = "sun.png" 
        self.moon_icon_path = "moon.png" 
        self.bg_image_path_light = "code light.jpg" 
        self.bg_image_path_dark = "code dark.jpg" 
        
        self.nav_icon_bases = {
            "nav_home": "home", "nav_projects": "projects", 
            "nav_games": "games", # Changed from "games" to "gamepad" to match common icon names
            "nav_contact": "contact",
            "nav_courses": "courses", "nav_account": "account", "nav_settings": "settings"
        }
        self.nav_icons = {}
        self.accounts_data = {}
        self.games_data = [] 
        self.pending_verification_email = None
        self.current_verification_code = None
        
        self.setup_icon()
        self.load_theme_icons()
        self.load_extra_icons() 
        self.load_nav_icons()   
        self.load_accounts_data()
        self.load_games_data() 
        
        self.current_nav_button = None
        self.nav_buttons = []
        self.page_elements_for_translation = {} 
        
        self.init_ui() 
        self.apply_theme_and_styles() 
        self.theme_button.setChecked(self.current_theme == "Dark") 
        
        if hasattr(self, 'account_page_stack'): 
            self.update_account_page_view()

        if self.nav_buttons:
            QTimer.singleShot(50, lambda: self.nav_buttons[0].click())

    def set_global_font(self): # No changes
        font_path = ""
        if self.current_language == "English": 
            font_path = self.font_en_path
        else: 
            font_path = self.font_ar_path

        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1: 
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font_family_name = font_families[0]
                    app_font = QFont(font_family_name, 10) 
                    QApplication.instance().setFont(app_font)
                    print(f"Global font set to: {font_family_name} from {font_path}")
                else:
                    print(f"Warning: Could not retrieve font family name for {font_path} (ID: {font_id})")
            else:
                print(f"Warning: Could not load font {font_path}. QFontDatabase.addApplicationFont returned -1.")
        else:
            print(f"Warning: Font file not found: {font_path}. Using system default font.")

    def _tr(self, key, default_text=""): return self.translations.get(self.current_language, {}).get(key, default_text if default_text else key)
    
    def load_translations(self): # No changes
        try:
            if os.path.exists(TRANSLATIONS_FILE):
                with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f: self.translations = json.load(f)
            else: self.translations = {"English": {}} 
        except (IOError, json.JSONDecodeError) as e: print(f"Error loading translations: {e}"); self.translations = {"English": {}}

    def load_settings(self): # No changes
        self.settings = {
            "nav_bar_position": self.default_nav_bar_position,
            "theme": "Light",
            "language": "English", 
            "is_logged_in": False, 
            "current_user_email": None, 
            "current_user_displayName": None
        }
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f: self.settings.update(json.load(f))
        except (IOError, json.JSONDecodeError) as e: print(f"Error loading config: {e}")

        self.nav_bar_position = self.settings.get("nav_bar_position", self.default_nav_bar_position).lower()
        self.current_theme = self.settings.get("theme", "Light")
        self.current_language = self.settings.get("language", "English") 
        if self.current_language not in self.translations: 
            print(f"Warning: Language '{self.current_language}' not found in translations. Defaulting to English.")
            self.current_language = "English"

        loaded_is_logged_in = self.settings.get("is_logged_in", False)
        if loaded_is_logged_in:
            email = self.settings.get("current_user_email")
            displayName = self.settings.get("current_user_displayName")
            if email: 
                self.is_logged_in = True
                self.current_user_details = {"email": email, "displayName": displayName if displayName else f"User_{email.split('@')[0]}"}
            else:
                self.is_logged_in = False 
                self.current_user_details = None
        else:
            self.is_logged_in = False
            self.current_user_details = None

    def save_settings(self): # No changes
        if hasattr(self, 'nav_bar_position_combo'): self.settings["nav_bar_position"] = self.nav_bar_position_combo.currentText().lower()
        if hasattr(self, 'language_combo'): self.settings["language"] = self.language_combo.currentText()
        self.settings["theme"] = self.current_theme

        self.settings["is_logged_in"] = self.is_logged_in
        if self.is_logged_in and self.current_user_details:
            self.settings["current_user_email"] = self.current_user_details.get("email")
            self.settings["current_user_displayName"] = self.current_user_details.get("displayName")
        else:
            self.settings["current_user_email"] = None
            self.settings["current_user_displayName"] = None
            
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(self.settings, f, indent=4)
        except IOError as e: print(f"Error saving config: {e}")

    def setup_icon(self): # No changes
        try: self.setWindowIcon(QIcon(self.icon_path))
        except Exception as e: print(f"Window Icon Error: {e}")
    def load_theme_icons(self): self.sun_icon = QIcon(self.sun_icon_path); self.moon_icon = QIcon(self.moon_icon_path)
    def load_extra_icons(self):
        tc = "#A6B0C3" if self.current_theme=="Dark" else "#555"
        self.eye_open_icon=create_placeholder_icon(True,color_name=tc);self.eye_closed_icon=create_placeholder_icon(False,color_name=tc)
    def load_nav_icons(self): # No changes
        self.nav_icons={"light":{},"dark":{}}
        for k,bn in self.nav_icon_bases.items():
            light_icon_path = f"{bn}_light.png"
            dark_icon_path = f"{bn}_dark.png"
            self.nav_icons["light"][k]=QIcon(light_icon_path)
            self.nav_icons["dark"][k]=QIcon(dark_icon_path)
            if self.nav_icons["dark"][k].isNull(): 
                self.nav_icons["dark"][k]=self.nav_icons["light"][k]
            if self.nav_icons["light"][k].isNull(): 
                print(f"Warning: Icon for '{k}' ({light_icon_path}/{dark_icon_path}) not found. Using placeholder.")
    def get_nav_icon(self,k):return self.nav_icons.get("dark" if self.current_theme=="Dark" else "light",{}).get(k,QIcon())
    
    def load_accounts_data(self): # No changes
        try:
            if os.path.exists(ACCOUNTS_FILE):
                with open(ACCOUNTS_FILE,'r',encoding='utf-8') as f:self.accounts_data=json.load(f)
            else:self.accounts_data={"user@example.com":{"email":"user@example.com","displayName":"Test User","lastVerified":None}};self.save_accounts_data()
        except (IOError,json.JSONDecodeError) as e:print(f"Acc load err:{e}");self.accounts_data={}
    def save_accounts_data(self): # No changes
        try:
            with open(ACCOUNTS_FILE,'w',encoding='utf-8') as f:json.dump(self.accounts_data,f,indent=4)
        except IOError as e:print(f"Acc save err:{e}")

    def load_games_data(self): # No changes
        try:
            if os.path.exists(GAMES_FILE):
                with open(GAMES_FILE, 'r', encoding='utf-8') as f:
                    self.games_data = json.load(f)
            else:
                self.games_data = []
                self.save_games_data() 
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading games data: {e}")
            self.games_data = []

    def save_games_data(self): # No changes
        try:
            with open(GAMES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.games_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving games data: {e}")

    def init_ui(self): # No changes except nav_item_keys
        self.central_frame=QFrame();self.central_frame.setObjectName("centralWidget");self.setCentralWidget(self.central_frame)
        self.nav_item_keys=["nav_home","nav_projects","nav_games","nav_contact","nav_courses","nav_account","nav_settings"]
        ml_dir=QVBoxLayout if self.nav_bar_position=="top" else QHBoxLayout
        ml=ml_dir(self.central_frame);ml.setContentsMargins(0,0,0,0);ml.setSpacing(0)
        self.nav_bar=QFrame();self.nav_bar.setObjectName("navBar")
        nbl_dir=QHBoxLayout if self.nav_bar_position=="top" else QVBoxLayout
        nbl=nbl_dir(self.nav_bar)
        if self.nav_bar_position=="top":nbl.setContentsMargins(15,5,15,5);nbl.setSpacing(10);nbl.setAlignment(Qt.AlignLeft);self.nav_bar.setFixedHeight(60)
        else:nbl.setContentsMargins(5,15,5,15);nbl.setSpacing(10);nbl.setAlignment(Qt.AlignTop);self.nav_bar.setFixedWidth(200)
        self.nav_buttons=[]
        for i,ik in enumerate(self.nav_item_keys):
            b=QPushButton(self._tr(ik));b.setObjectName("navButton");b.setCheckable(True);b.setMinimumHeight(45)
            b.setIconSize(QSize(24,24));b.setIcon(self.get_nav_icon(ik));b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            if self.nav_bar_position=="top":b.setMinimumWidth(130)
            b.clicked.connect(lambda c,idx=i:self.switch_page(idx));nbl.addWidget(b);self.nav_buttons.append(b)
        nbl.addStretch(1)
        self.theme_button=QPushButton();self.theme_button.setObjectName("themeButton");self.theme_button.setCheckable(True);self.theme_button.setFixedSize(36,36)
        self.theme_button.setIconSize(QSize(24,24));self.theme_button.clicked.connect(self.toggle_theme);nbl.addWidget(self.theme_button)
        self.stacked_widget=AnimatedStackedWidget();self.stacked_widget.setObjectName("contentStack")
        self.create_pages()
        ml.addWidget(self.nav_bar);ml.addWidget(self.stacked_widget,1)
        self._store_translatable_page_elements() 

    def _get_content_wrapper(self,alignment=Qt.AlignTop|Qt.AlignHCenter): # No changes
        cw=QWidget();il=QVBoxLayout(cw);il.setContentsMargins(25,25,25,25);il.setSpacing(15);il.setAlignment(alignment);return cw,il

    def create_pages(self): # No changes (order of page creation remains)
        while self.stacked_widget.count()>0:w=self.stacked_widget.widget(0);self.stacked_widget.removeWidget(w);w.deleteLater()
        # Home Page
        hp=QWidget();hp.setObjectName("contentPage");hpml=QVBoxLayout(hp);hpml.setAlignment(Qt.AlignCenter);hpml.setContentsMargins(0,0,0,0)
        hcw,hil=self._get_content_wrapper(Qt.AlignTop|Qt.AlignLeft)
        self.home_title=QLabel(self._tr("home_page_main_title"));self.home_title.setObjectName("pageTitleLabel");self.home_title.setAlignment(Qt.AlignCenter);self.home_title.setWordWrap(True)
        self.who_am_i_title=QLabel(self._tr("home_who_am_i_title"));self.who_am_i_title.setObjectName("subHeadingLabel");self.who_am_i_title.setAlignment(Qt.AlignLeft)
        self.who_am_i_content=QLabel(self._tr("home_who_am_i_content"));self.who_am_i_content.setObjectName("pageContentLabel");self.who_am_i_content.setWordWrap(True);self.who_am_i_content.setAlignment(Qt.AlignLeft)
        self.how_i_started_title=QLabel(self._tr("home_how_started_title"));self.how_i_started_title.setObjectName("subHeadingLabel");self.how_i_started_title.setAlignment(Qt.AlignLeft)
        self.how_i_started_content=QLabel(self._tr("home_how_started_content"));self.how_i_started_content.setObjectName("pageContentLabel");self.how_i_started_content.setWordWrap(True);self.how_i_started_content.setAlignment(Qt.AlignLeft)
        self.techniques_title=QLabel(self._tr("home_techniques_title"));self.techniques_title.setObjectName("subHeadingLabel");self.techniques_title.setAlignment(Qt.AlignLeft)
        self.techniques_content=QLabel(self._tr("home_techniques_content"));self.techniques_content.setObjectName("pageContentLabel");self.techniques_content.setWordWrap(True);self.techniques_content.setAlignment(Qt.AlignLeft)
        hil.addWidget(self.home_title);hil.addSpacing(20);hil.addWidget(self.who_am_i_title);hil.addWidget(self.who_am_i_content);hil.addSpacing(15)
        hil.addWidget(self.how_i_started_title);hil.addWidget(self.how_i_started_content);hil.addSpacing(15);hil.addWidget(self.techniques_title);hil.addWidget(self.techniques_content);hil.addStretch(1)
        hpml.addStretch(1);hpml.addWidget(hcw);hpml.addStretch(1);self.stacked_widget.addWidget(hp)
        
        # Projects Page
        pp=QWidget();pp.setObjectName("contentPage");ppml=QVBoxLayout(pp);ppml.setAlignment(Qt.AlignCenter);ppml.setContentsMargins(0,0,0,0)
        pcw,pil=self._get_content_wrapper()
        self.projects_title=QLabel(self._tr("projects_page_title"));self.projects_title.setObjectName("pageTitleLabel");self.projects_title.setAlignment(Qt.AlignCenter)
        self.project1_title=QLabel(self._tr("project1_title"));self.project1_title.setObjectName("subHeadingLabel")
        self.project1_desc=QLabel(self._tr("project1_desc"));self.project1_desc.setObjectName("pageContentLabel");self.project1_desc.setWordWrap(True);self.project1_desc.setAlignment(Qt.AlignCenter)
        self.project1_button=QPushButton(self._tr("project1_button"));self.project1_button.setObjectName("linkButton");self.project1_button.clicked.connect(lambda:QDesktopServices.openUrl(QUrl("https://mimo-code.itch.io/mimo-browser")))
        self.project2_title=QLabel(self._tr("project2_title"));self.project2_title.setObjectName("subHeadingLabel")
        self.project2_desc=QLabel(self._tr("project2_desc"));self.project2_desc.setObjectName("pageContentLabel");self.project2_desc.setWordWrap(True);self.project2_desc.setAlignment(Qt.AlignCenter)
        self.project2_button=QPushButton(self._tr("project2_button"));self.project2_button.setObjectName("linkButton");self.project2_button.setEnabled(False)
        pil.addWidget(self.projects_title);pil.addWidget(self.project1_title);pil.addWidget(self.project1_desc);pil.addWidget(self.project1_button,alignment=Qt.AlignHCenter);pil.addSpacing(25)
        pil.addWidget(self.project2_title);pil.addWidget(self.project2_desc);pil.addWidget(self.project2_button,alignment=Qt.AlignHCenter);pil.addStretch(1)
        ppml.addStretch(1);ppml.addWidget(pcw);ppml.addStretch(1);self.stacked_widget.addWidget(pp)

        self.create_games_page() 

        # Contact Page
        cp=QWidget();cp.setObjectName("contentPage");cpml=QVBoxLayout(cp);cpml.setAlignment(Qt.AlignCenter);cpml.setContentsMargins(0,0,0,0)
        ccw,cil=self._get_content_wrapper()
        self.contact_title_label=QLabel(self._tr("contact_page_title"));self.contact_title_label.setObjectName("pageTitleLabel");self.contact_title_label.setAlignment(Qt.AlignCenter)
        self.facebook_button=QPushButton(self._tr("contact_facebook_button"));self.facebook_button.setObjectName("linkButton");self.facebook_button.clicked.connect(lambda:QDesktopServices.openUrl(QUrl("https://web.facebook.com/moumen.mahmoud.5815")))
        self.github_contact_button=QPushButton(self._tr("contact_github_button"));self.github_contact_button.setObjectName("linkButton");self.github_contact_button.clicked.connect(lambda:QDesktopServices.openUrl(QUrl("https://github.com/Mimo233329")))
        self.instagram_button=QPushButton(self._tr("contact_instagram_button"));self.instagram_button.setObjectName("linkButton");self.instagram_button.clicked.connect(lambda:QDesktopServices.openUrl(QUrl("https://www.instagram.com/moamenhre/")))
        self.email_contact_label=QLabel(self._tr("contact_email_label"));self.email_contact_label.setObjectName("pageContentLabel");self.email_contact_label.setAlignment(Qt.AlignCenter)
        cil.addWidget(self.contact_title_label);cil.addSpacing(10);cil.addWidget(self.facebook_button,alignment=Qt.AlignHCenter);cil.addWidget(self.github_contact_button,alignment=Qt.AlignHCenter);cil.addWidget(self.instagram_button,alignment=Qt.AlignHCenter);cil.addSpacing(15);cil.addWidget(self.email_contact_label);cil.addStretch(1)
        cpml.addStretch(1);cpml.addWidget(ccw);cpml.addStretch(1);self.stacked_widget.addWidget(cp)
        
        # Courses Page
        crp=QWidget();crp.setObjectName("contentPage");crpml=QVBoxLayout(crp);crpml.setAlignment(Qt.AlignCenter);crpml.setContentsMargins(0,0,0,0)
        crcw,cril=self._get_content_wrapper()
        self.courses_title_label=QLabel(self._tr("courses_page_title"));self.courses_title_label.setObjectName("pageTitleLabel");self.courses_title_label.setAlignment(Qt.AlignCenter)
        self.game_dev_course_title=QLabel(self._tr("course_game_dev_title"));self.game_dev_course_title.setObjectName("subHeadingLabel")
        self.game_dev_course_desc=QLabel(self._tr("course_game_dev_desc"));self.game_dev_course_desc.setObjectName("pageContentLabel");self.game_dev_course_desc.setWordWrap(True);self.game_dev_course_desc.setAlignment(Qt.AlignCenter)
        self.view_course_button=QPushButton(self._tr("course_view_button"));self.view_course_button.setObjectName("linkButton");self.view_course_button.setEnabled(False)
        cril.addWidget(self.courses_title_label);cril.addWidget(self.game_dev_course_title);cril.addWidget(self.game_dev_course_desc);cril.addWidget(self.view_course_button,alignment=Qt.AlignHCenter);cril.addStretch(1)
        crpml.addStretch(1);crpml.addWidget(crcw);crpml.addStretch(1);self.stacked_widget.addWidget(crp)
        
        self.create_account_page() 
        
        # Settings Page
        sp=QWidget();sp.setObjectName("contentPage");spml=QVBoxLayout(sp);spml.setAlignment(Qt.AlignCenter);spml.setContentsMargins(0,0,0,0)
        scw,sil=self._get_content_wrapper()
        self.settings_title_label=QLabel(self._tr("settings_page_title"));self.settings_title_label.setObjectName("pageTitleLabel");self.settings_title_label.setAlignment(Qt.AlignCenter);sil.addWidget(self.settings_title_label)
        fl=QFormLayout();fl.setSpacing(10);fl.setLabelAlignment(Qt.AlignRight)
        self.language_label=QLabel(self._tr("settings_language_label"));self.language_combo=QComboBox();self.language_combo.addItems(list(self.translations.keys())if self.translations else["English"]);self.language_combo.setCurrentText(self.current_language);fl.addRow(self.language_label,self.language_combo)
        self.nav_bar_label=QLabel(self._tr("settings_nav_bar_label"));self.nav_bar_position_combo=QComboBox();self.nav_bar_position_combo.addItems(["Left","Top"]);self.nav_bar_position_combo.setCurrentText(self.nav_bar_position.capitalize());fl.addRow(self.nav_bar_label,self.nav_bar_position_combo)
        sil.addLayout(fl);sil.addSpacing(15)
        self.apply_settings_button=QPushButton(self._tr("settings_save_button"));self.apply_settings_button.setObjectName("actionButton");self.apply_settings_button.clicked.connect(self.apply_and_save_settings);sil.addWidget(self.apply_settings_button,alignment=Qt.AlignHCenter)
        self.restart_label=QLabel(self._tr("settings_restart_info"));self.restart_label.setObjectName("infoLabel");self.restart_label.setWordWrap(True);self.restart_label.hide();sil.addWidget(self.restart_label,alignment=Qt.AlignCenter);sil.addStretch(1)
        spml.addStretch(1);spml.addWidget(scw);spml.addStretch(1);self.stacked_widget.addWidget(sp)
        
        for i in range(self.stacked_widget.count()):
            self.stacked_widget._create_opacity_effect(self.stacked_widget.widget(i))
            if i!=self.stacked_widget.currentIndex():self.stacked_widget.widget(i).hide()
            else:self.stacked_widget.widget(i).show();ef=self.stacked_widget._create_opacity_effect(self.stacked_widget.widget(i));_=ef.setOpacity(1.0)if ef else None

    def create_games_page(self): # No changes here
        self.games_page_widget = QWidget()
        self.games_page_widget.setObjectName("contentPage")
        
        page_layout = QVBoxLayout(self.games_page_widget)
        page_layout.setContentsMargins(20, 20, 20, 20) 
        page_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        self.games_page_title = QLabel(self._tr("games_page_title", "My Games Collection"))
        self.games_page_title.setObjectName("pageTitleLabel")
        header_layout.addWidget(self.games_page_title, 1, Qt.AlignLeft) 

        self.add_game_button = QPushButton(self._tr("add_game_button", "Add Game"))
        self.add_game_button.setObjectName("actionButton") 
        self.add_game_button.setIcon(QIcon.fromTheme("list-add", QIcon(create_placeholder_icon(color_name="#FFF")))) 
        self.add_game_button.clicked.connect(self.handle_add_game_button_clicked)
        header_layout.addWidget(self.add_game_button, 0, Qt.AlignRight) 
        page_layout.addLayout(header_layout)

        self.games_scroll_area = QScrollArea()
        self.games_scroll_area.setWidgetResizable(True)
        self.games_scroll_area.setObjectName("gamesScrollArea") 
        self.games_scroll_area.setStyleSheet("QScrollArea#gamesScrollArea { border: none; background-color: transparent; }")

        scroll_content_widget = QWidget() 
        scroll_content_widget.setStyleSheet("background-color: transparent;")
        self.games_list_layout = QVBoxLayout(scroll_content_widget) 
        self.games_list_layout.setSpacing(10)
        self.games_list_layout.setAlignment(Qt.AlignTop)
        
        self.games_scroll_area.setWidget(scroll_content_widget)
        page_layout.addWidget(self.games_scroll_area, 1) 

        self.populate_games_list_widget() 
        self.stacked_widget.addWidget(self.games_page_widget)

    # --- MODIFIED populate_games_list_widget ---
    def populate_games_list_widget(self):
        if not hasattr(self, 'games_list_layout'): 
            return

        while self.games_list_layout.count():
            child = self.games_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.games_data:
            no_games_label = QLabel(self._tr("no_games_message", "No games added yet. Click 'Add Game' to start!"))
            no_games_label.setAlignment(Qt.AlignCenter)
            no_games_label.setObjectName("pageContentLabel") 
            self.games_list_layout.addWidget(no_games_label)
        else:
            for game_data in self.games_data:
                item_widget = GameItemWidget(game_data, self._tr) # Pass self._tr
                item_widget.delete_requested.connect(self.handle_delete_game_request) # Connect signal
                self.games_list_layout.addWidget(item_widget)
    # --- END MODIFIED populate_games_list_widget ---

    def handle_add_game_button_clicked(self): # No changes
        dialog = AddGameDialog(self._tr, self)
        if dialog.exec_() == QDialog.Accepted:
            game_data = dialog.get_data()
            if game_data:
                self.games_data.append(game_data)
                self.save_games_data()
                self.populate_games_list_widget() 
                QMessageBox.information(self, 
                                        self._tr("game_add_success_title", "Game Added"), 
                                        self._tr("game_add_success_message", f"'{game_data['name']}' has been added successfully."))

    # --- NEW handle_delete_game_request method ---
    def handle_delete_game_request(self, game_name_to_delete):
        reply = QMessageBox.question(self, 
                                     self._tr("game_delete_confirm_title", "Confirm Delete"),
                                     self._tr("game_delete_confirm_message", f"Are you sure you want to delete '{game_name_to_delete}'?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            game_found = False
            for i, game in enumerate(self.games_data):
                if game.get("name") == game_name_to_delete:
                    del self.games_data[i]
                    game_found = True
                    break
            
            if game_found:
                self.save_games_data()
                self.populate_games_list_widget() # Refresh the UI
                QMessageBox.information(self, 
                                        self._tr("game_delete_success_title", "Game Deleted"),
                                        self._tr("game_delete_success_message", f"'{game_name_to_delete}' has been deleted."))
            else:
                QMessageBox.warning(self, 
                                    self._tr("game_delete_fail_title", "Error"),
                                    self._tr("game_delete_fail_message_not_found", f"Could not find '{game_name_to_delete}' to delete."))
    # --- END NEW handle_delete_game_request method ---

    def create_account_page(self): # No changes
        self.account_page_widget=QWidget();self.account_page_widget.setObjectName("contentPage")
        apml=QVBoxLayout(self.account_page_widget);apml.setAlignment(Qt.AlignCenter);apml.setContentsMargins(0,0,0,0)
        self.account_page_stack=AnimatedStackedWidget();self.account_page_stack.setObjectName("accountContentStack")
        sv_container=QWidget();svcl=QVBoxLayout(sv_container);svcl.setAlignment(Qt.AlignCenter);svcl.addStretch(1)
        sfw,sl=self._get_content_wrapper()
        self.account_page_title=QLabel(self._tr("account_page_signin_title"));self.account_page_title.setObjectName("pageTitleLabel");sl.addWidget(self.account_page_title)
        self.email_prompt_label=QLabel(self._tr("account_email_label"));self.email_input=QLineEdit();self.email_input.setPlaceholderText(self._tr("account_email_placeholder"))
        sl.addWidget(self.email_prompt_label);sl.addWidget(self.email_input)
        self.recaptcha_checkbox=QCheckBox(self._tr("account_recaptcha_label"));sl.addWidget(self.recaptcha_checkbox,alignment=Qt.AlignHCenter)
        self.signin_button=QPushButton(self._tr("account_signin_button"));self.signin_button.setObjectName("actionButton");self.signin_button.clicked.connect(self.handle_send_verification_code_request);sl.addWidget(self.signin_button,alignment=Qt.AlignHCenter)
        
        svcl.addWidget(sfw);svcl.addStretch(1);self.account_page_stack.addWidget(sv_container)
        dv_container=QWidget();dvcl=QVBoxLayout(dv_container);dvcl.setAlignment(Qt.AlignCenter);dvcl.addStretch(1)
        dw,dl=self._get_content_wrapper()
        self.account_details_title=QLabel(self._tr("account_details_title"));self.account_details_title.setObjectName("pageTitleLabel");dl.addWidget(self.account_details_title)
        self.user_email_details_label=QLabel(self._tr("account_details_email"));self.user_email_value_label=QLabel();self.user_email_value_label.setObjectName("pageContentLabel");self.user_email_value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.user_display_name_details_label=QLabel(self._tr("account_details_display_name"));self.user_display_name_value_label=QLabel();self.user_display_name_value_label.setObjectName("pageContentLabel");self.user_display_name_value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        df=QFormLayout();df.addRow(self.user_email_details_label,self.user_email_value_label);df.addRow(self.user_display_name_details_label,self.user_display_name_value_label);dl.addLayout(df)
        self.logout_button=QPushButton(self._tr("account_logout_button"));self.logout_button.setObjectName("actionButton");self.logout_button.clicked.connect(self.handle_logout);dl.addWidget(self.logout_button,alignment=Qt.AlignHCenter)
        dvcl.addWidget(dw);dvcl.addStretch(1);self.account_page_stack.addWidget(dv_container)
        vv_container=QWidget();vvcl=QVBoxLayout(vv_container);vvcl.setAlignment(Qt.AlignCenter);vvcl.addStretch(1)
        vw,vl=self._get_content_wrapper()
        self.verify_title_label=QLabel(self._tr("account_verify_title"));self.verify_title_label.setObjectName("pageTitleLabel");vl.addWidget(self.verify_title_label)
        self.verify_prompt_label=QLabel(self._tr("account_verify_prompt"));self.verify_prompt_label.setWordWrap(True);self.verify_prompt_label.setAlignment(Qt.AlignCenter);vl.addWidget(self.verify_prompt_label)
        self.verification_code_input=QLineEdit();self.verification_code_input.setPlaceholderText(self._tr("account_verify_code_placeholder"));self.verification_code_input.setAlignment(Qt.AlignCenter);vl.addWidget(self.verification_code_input)
        self.verify_code_button=QPushButton(self._tr("account_verify_button"));self.verify_code_button.setObjectName("actionButton");self.verify_code_button.clicked.connect(self.handle_verify_code);vl.addWidget(self.verify_code_button,alignment=Qt.AlignHCenter)
        self.cancel_verification_button=QPushButton(self._tr("account_cancel_verify_button"));self.cancel_verification_button.setObjectName("linkButton");self.cancel_verification_button.clicked.connect(self.cancel_verification_process);vl.addWidget(self.cancel_verification_button,alignment=Qt.AlignHCenter)
        vvcl.addWidget(vw);vvcl.addStretch(1);self.account_page_stack.addWidget(vv_container)
        apml.addWidget(self.account_page_stack);self.stacked_widget.addWidget(self.account_page_widget)
        for i in range(self.account_page_stack.count()):
            self.account_page_stack._create_opacity_effect(self.account_page_stack.widget(i))
            if i!=self.account_page_stack.currentIndex():self.account_page_stack.widget(i).hide()

    def handle_send_verification_code_request(self): # No changes
        ea=self.email_input.text().strip().lower()
        if not ea or "@" not in ea or "." not in ea.split("@")[-1]:QMessageBox.warning(self,self._tr("signin_error_title"),self._tr("signin_invalid_email_error"));return
        if not self.recaptcha_checkbox.isChecked():QMessageBox.warning(self,self._tr("signin_error_title"),self._tr("signin_recaptcha_error"));return
        self.current_verification_code=Generate_Password(6);self.pending_verification_email=ea
        self.signin_button.setEnabled(False);self.signin_button.setText(self._tr("account_sending_code_button"));QApplication.processEvents()
        es=send_verification_email(ea,self.current_verification_code)
        self.signin_button.setEnabled(True);self.signin_button.setText(self._tr("account_signin_button"))
        if es:
            self.verify_prompt_label.setText(self._tr("account_verify_prompt_dynamic",f"An email has been sent to {ea}. Please enter the code:"))
            self.account_page_stack.switch_to_index(2);self.verification_code_input.clear();self.verification_code_input.setFocus()
        else:QMessageBox.critical(self,self._tr("email_error_title"),self._tr("email_send_error_message"));self.current_verification_code=None;self.pending_verification_email=None
    
    def handle_verify_code(self): # No changes
        ec=self.verification_code_input.text().strip()
        if not ec:QMessageBox.warning(self,self._tr("verify_error_title"),self._tr("verify_empty_code_error"));return
        if self.current_verification_code and ec==self.current_verification_code:
            self.is_logged_in=True;ue=self.pending_verification_email
            dn=self.accounts_data.get(ue,{}).get("displayName",f"User_{ue.split('@')[0]}")
            self.current_user_details={"email":ue,"displayName":dn}
            if ue not in self.accounts_data:self.accounts_data[ue]={}
            self.accounts_data[ue].update({"email":ue,"displayName":dn,"lastVerified":get_current_time_str()});self.save_accounts_data()
            self.save_settings() 
            QMessageBox.information(self,self._tr("verify_success_title"),self._tr("verify_success_message"));self.update_account_page_view()
            self.current_verification_code=None;self.pending_verification_email=None;self.verification_code_input.clear()
        else:QMessageBox.warning(self,self._tr("verify_error_title"),self._tr("verify_incorrect_code_error"));self.verification_code_input.selectAll();self.verification_code_input.setFocus()

    def cancel_verification_process(self): # No changes
        self.current_verification_code=None;self.pending_verification_email=None;self.verification_code_input.clear()
        self.account_page_stack.switch_to_index(0);self.email_input.setFocus()

    def handle_logout(self): # No changes
        self.is_logged_in=False;self.current_user_details=None
        self.save_settings() 
        self.update_account_page_view()
        QMessageBox.information(self,self._tr("logout_title"),self._tr("logout_message"))

    def update_account_page_view(self): # No changes
        if not hasattr(self,'account_page_stack'):return 
        if self.is_logged_in and self.current_user_details:
            self.user_email_value_label.setText(self.current_user_details.get("email","N/A"))
            self.user_display_name_value_label.setText(self.current_user_details.get("displayName","N/A"))
            self.account_page_stack.switch_to_index(1)
        else:
            self.account_page_stack.switch_to_index(0)
            if hasattr(self, 'email_input'): self.email_input.clear() 
            if hasattr(self, 'recaptcha_checkbox'): self.recaptcha_checkbox.setChecked(False)

    def _store_translatable_page_elements(self): # No changes
        self.page_elements_for_translation={
            "app_title":self.setWindowTitle,"home_page_main_title":self.home_title,"home_who_am_i_title":self.who_am_i_title,
            "home_who_am_i_content":self.who_am_i_content,"home_how_started_title":self.how_i_started_title,
            "home_how_started_content":self.how_i_started_content,"home_techniques_title":self.techniques_title,
            "home_techniques_content":self.techniques_content,"projects_page_title":self.projects_title,
            "project1_title":self.project1_title,"project1_desc":self.project1_desc,"project1_button":self.project1_button,
            "project2_title":self.project2_title,"project2_desc":self.project2_desc,"project2_button":self.project2_button,
            "contact_page_title":self.contact_title_label,"contact_facebook_button":self.facebook_button,
            "contact_github_button":self.github_contact_button,"contact_instagram_button":self.instagram_button,
            "contact_email_label":self.email_contact_label,"courses_page_title":self.courses_title_label,
            "course_game_dev_title":self.game_dev_course_title,"course_game_dev_desc":self.game_dev_course_desc,
            "course_view_button":self.view_course_button, 
            "settings_page_title":self.settings_title_label, 
            "settings_language_label":self.language_label,"settings_nav_bar_label":self.nav_bar_label,
            "settings_save_button":self.apply_settings_button,"settings_restart_info":self.restart_label,
            "games_page_title": self.games_page_title if hasattr(self, 'games_page_title') else lambda t: None,
            "add_game_button": self.add_game_button if hasattr(self, 'add_game_button') else lambda t: None,
        }
        if hasattr(self,'account_page_title'):
            self.page_elements_for_translation.update({
                "account_page_signin_title":self.account_page_title,"account_email_label":self.email_prompt_label,
                "account_signin_button":self.signin_button,
                "account_recaptcha_label":self.recaptcha_checkbox,"account_details_title":self.account_details_title,
                "account_details_email":self.user_email_details_label,"account_details_display_name":self.user_display_name_details_label,
                "account_logout_button":self.logout_button,"account_verify_title":self.verify_title_label,
                "account_verify_prompt":self.verify_prompt_label,"account_verify_button":self.verify_code_button,
                "account_cancel_verify_button":self.cancel_verification_button,
                "account_email_placeholder":lambda t:self.email_input.setPlaceholderText(t),
                "account_verify_code_placeholder":lambda t:self.verification_code_input.setPlaceholderText(t),
                "account_sending_code_button":"account_sending_code_button_key_for_translations_json", 
            })

    def retranslate_ui(self): # No changes
        self.setWindowTitle(self._tr("app_title","Moumen Client"))
        for i,k in enumerate(self.nav_item_keys):
            if i<len(self.nav_buttons):self.nav_buttons[i].setText(self._tr(k));self.nav_buttons[i].setIcon(self.get_nav_icon(k))
        
        for k,wom in self.page_elements_for_translation.items():
            tt=self._tr(k,k) 
            if k == "account_signin_button":
                if hasattr(self, 'signin_button') and self.signin_button.text() != self._tr("account_sending_code_button"):
                    self.signin_button.setText(tt)
            elif callable(wom) and not isinstance(wom, QWidget): 
                try:
                    wom(tt)
                except Exception as e:
                    print(f"Error translating placeholder for {k}: {e}")
            elif isinstance(wom, (QLabel, QPushButton, QCheckBox)):
                wom.setText(tt)
        
        if self.pending_verification_email and hasattr(self,'account_page_stack')and self.account_page_stack.currentIndex()==2:
             self.verify_prompt_label.setText(self._tr("account_verify_prompt_dynamic",f"An email has been sent to {self.pending_verification_email}. Please enter the code:"))
        elif hasattr(self,'verify_prompt_label'):self.verify_prompt_label.setText(self._tr("account_verify_prompt"))

        if hasattr(self, 'populate_games_list_widget'):
            self.populate_games_list_widget() 

        if hasattr(self,'language_combo'):
            cs=self.language_combo.currentText();self.language_combo.clear();self.language_combo.addItems(list(self.translations.keys())if self.translations else["English"])
            self.language_combo.setCurrentText(cs if self.language_combo.findText(cs)!=-1 else "English")
        
        self.load_extra_icons();self.apply_theme_and_styles();self.update()


    def switch_page(self,idx): # No changes
        self.stacked_widget.switch_to_index(idx)
        if self.current_nav_button:self.current_nav_button.setChecked(False)
        if 0<=idx<len(self.nav_buttons):
            self.current_nav_button=self.nav_buttons[idx];self.current_nav_button.setChecked(True)
            if self.nav_item_keys[idx] == "nav_account" and hasattr(self, 'update_account_page_view'):
                self.update_account_page_view()
            elif self.nav_item_keys[idx] == "nav_games" and hasattr(self, 'populate_games_list_widget'):
                 self.populate_games_list_widget()


    def toggle_theme(self): # No changes
        self.current_theme="Dark"if self.current_theme=="Light"else"Light";self.settings["theme"]=self.current_theme
        self.theme_button.setChecked(self.current_theme=="Dark");self.load_extra_icons();self.apply_theme_and_styles();self.save_settings()

    def apply_and_save_settings(self): # No changes
        onp=self.nav_bar_position;nnp=self.nav_bar_position_combo.currentText().lower()
        ol=self.current_language;nl=self.language_combo.currentText()
        
        language_changed = (ol != nl)

        self.settings["nav_bar_position"]=nnp;self.settings["language"]=nl
        self.current_language=nl;self.nav_bar_position=nnp
        
        self.save_settings()

        if language_changed:
            self.set_global_font() 
            self.retranslate_ui() 
        else:
            self.apply_theme_and_styles()

        QMessageBox.information(self,self._tr("settings_saved_message_title"),self._tr("settings_saved_message_body"))
        if onp!=nnp:
            self.restart_label.setText(self._tr("settings_restart_info_full"));self.restart_label.show()
            QMessageBox.information(self,self._tr("settings_restart_required_title"),self._tr("settings_restart_required_body"))
        else:self.restart_label.hide()

    # --- MODIFIED apply_theme_and_styles ---
    def apply_theme_and_styles(self):
        id=self.current_theme=="Dark";bi=self.bg_image_path_dark if id else self.bg_image_path_light
        mbg="#1E1E1E"if id else"#F0F2F5";nbbg="#2D3A4A"if id else"#2C3E50";nbbc="#252F3B"if id else"#22303F"
        nbtxt="#A6B0C3"if id else"#ECF0F1";nbh="#394B5F"if id else"#3E5771";nbcbg="#007ACC"if id else"#1ABC9C"
        nbctxt="#FFF";pbgra="rgba(40,40,40,0.92)"if id else"rgba(255,255,255,0.96)";ptxt="#E0E0E0"if id else"#2C3E50"
        pctxt="#C0C0C0"if id else"#444";shtxt="#D0D0D0"if id else"#3A506B";lbbg=nbcbg;lbtxt=nbctxt;lbh="#005C9E"if id else"#16A085"
        itxt="#A0A0A0"if id else"#666";cbg=nbbg if id else"#FFF";ctxt=nbtxt if id else ptxt;cbdr=nbh if id else"#BDC3C7"
        fltxt=nbtxt if id else ptxt;lebg="#252526"if id else"#FFF";letxt=ptxt;lebdr="#3E3E42"if id else"#ABADB3";chktxt=pctxt
        
        game_item_bg = "rgba(50, 50, 50, 0.8)" if id else "rgba(245, 245, 245, 0.9)"
        game_item_border = "#444" if id else "#ddd"
        game_name_color = ptxt
        game_desc_color = pctxt
        delete_button_bg = "rgba(200, 50, 50, 0.7)" if id else "rgba(255, 100, 100, 0.8)" # Reddish
        delete_button_hover_bg = "rgba(230, 70, 70, 0.9)" if id else "rgba(255, 130, 130, 1.0)"
        delete_button_text_color = "#FFF"


        self.theme_button.setIcon(self.sun_icon if id else self.moon_icon)
        for i,k in enumerate(self.nav_item_keys):
            if i<len(self.nav_buttons):self.nav_buttons[i].setIcon(self.get_nav_icon(k))
        nbs='bottom'if self.nav_bar_position=="top"else'right';nss=f"QFrame#navBar{{border-{nbs}:2px solid {nbbc};}}"
        nss+=f"QPushButton#navButton{{text-align:center;padding-left:10px;padding-right:10px;}}"
        if self.nav_bar_position=="left":nss+="QPushButton#navButton::indicator{display:none;}"
        
        ss=f"""QMainWindow{{background-color:{mbg};}}
            QFrame#centralWidget{{background-image:url('{bi.replace("\\","/")}');background-repeat:no-repeat;background-position:center;background-attachment:fixed;background-size:cover;}}
            QFrame#navBar{{background-color:{nbbg};}}{nss}
            QPushButton#navButton{{background-color:transparent;color:{nbtxt};border:none;font-size:14px;font-weight:500;border-radius:6px;padding-top:8px;padding-bottom:8px;}}
            QPushButton#navButton:hover{{background-color:{nbh};}}QPushButton#navButton:checked{{background-color:{nbcbg};color:{nbctxt};font-weight:bold;}}
            QPushButton#themeButton{{background-color:transparent;border:1px solid {nbtxt};border-radius:18px;}}QPushButton#themeButton:hover{{background-color:{nbh};}}
            QStackedWidget#contentStack,QStackedWidget#accountContentStack{{background-color:transparent;}}
            QWidget#contentPage{{background-color:{pbgra};border-radius:8px;}}
            QLabel#pageTitleLabel{{font-size:28px;color:{ptxt};font-weight:bold;padding-bottom:10px;qproperty-alignment:AlignCenter;}}
            QLabel#subHeadingLabel{{font-size:20px;color:{shtxt};font-weight:bold;padding-top:10px;padding-bottom:5px;qproperty-alignment:AlignCenter;}}
            QLabel#pageContentLabel{{font-size:15px;color:{pctxt};line-height:1.5;qproperty-wordWrap:true;}}
            QLabel#infoLabel{{font-size:13px;color:{itxt};font-style:italic;margin-top:10px;qproperty-alignment:AlignCenter;}}
            QPushButton#linkButton,QPushButton#actionButton,QPushButton#ssoButton{{background-color:{lbbg};color:{lbtxt};border:none;border-radius:5px;padding:10px 20px;font-size:14px;margin:5px 0;min-width:180px;max-width:350px;}}
            QPushButton#linkButton:hover,QPushButton#actionButton:hover,QPushButton#ssoButton:hover{{background-color:{lbh};}}
            QPushButton#linkButton:disabled,QPushButton#actionButton:disabled{{background-color:gray;color:lightgray;}}
            QLineEdit{{background-color:{lebg};color:{letxt};border:1px solid {lebdr};border-radius:4px;padding:8px;font-size:14px;min-height:24px;}}
            QCheckBox{{color:{chktxt};font-size:14px;spacing:5px;}}QCheckBox::indicator{{width:15px;height:15px;}}
            QComboBox{{background-color:{cbg};color:{ctxt};border:1px solid {cbdr};border-radius:4px;padding:6px;min-height:22px;}}
            QComboBox QAbstractItemView{{border:1px solid {cbdr};background-color:{cbg};color:{ctxt};selection-background-color:{nbh};}}
            QFormLayout QLabel{{font-size:14px;color:{fltxt};padding-top:6px;}}
            QScrollArea, QScrollArea QWidget {{ background-color: transparent; border: none; }}
            QFrame#gameItem {{ 
                background-color: {game_item_bg}; 
                border: 1px solid {game_item_border}; 
                border-radius: 6px; 
                padding: 8px; 
            }}
            QLabel#gameNameLabel {{ color: {game_name_color}; font-size: 16px; font-weight: bold; }}
            QLabel#gameDescLabel {{ color: {game_desc_color}; font-size: 14px; }}
            QPushButton#deleteGameButton {{
                background-color: {delete_button_bg};
                color: {delete_button_text_color};
                border: 1px solid rgba(150,20,20,0.8);
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }}
            QPushButton#deleteGameButton:hover {{
                background-color: {delete_button_hover_bg};
            }}
            AddGameDialog QLineEdit, AddGameDialog QTextEdit {{ /* Style for dialog inputs if needed */ }}
            """
        self.setStyleSheet(ss);self.update();[w.style().polish(w)for w in self.findChildren(QWidget)]
    # --- END MODIFIED apply_theme_and_styles ---

    def resizeEvent(self,e):super().resizeEvent(e) # No changes
    def closeEvent(self,e):self.save_settings();super().closeEvent(e) # No changes

# --- MODIFIED __main__ for new translation keys ---
if __name__=="__main__":
    app=QApplication(sys.argv) 
    
    if not os.path.exists(TRANSLATIONS_FILE):
        dt={"English":{
            "app_title":"Moumen Client",
            "nav_home":"Home","nav_projects":"Projects","nav_games":"Games","nav_contact":"Contact","nav_courses":"Courses","nav_account":"Account","nav_settings":"Settings",
            "home_page_main_title":"Welcome!","home_who_am_i_title":"Who Am I?","home_who_am_i_content":"...","home_how_started_title":"How I Started","home_how_started_content":"...","home_techniques_title":"Techniques","home_techniques_content":"...",
            "projects_page_title":"My Projects","project1_title":"Mimo Browser","project1_desc":"...","project1_button":"View","project2_title":"AI Client","project2_desc":"...","project2_button":"View (Soon)",
            
            "games_page_title": "My Games Collection", "add_game_button": "Add Game",
            "no_games_message": "No games added yet. Click 'Add Game' to start!",
            "add_game_dialog_title": "Add New Game",
            "game_name_label_dialog": "Game Name:", "game_name_placeholder_dialog": "Enter game name",
            "game_desc_label_dialog": "Description:", "game_desc_placeholder_dialog": "Enter game description",
            "game_cover_label_dialog": "Cover Image:", "game_cover_placeholder_dialog": "Path to cover image",
            "browse_button_dialog": "Browse...", "select_cover_dialog_title": "Select Cover Image",
            "image_files_filter_dialog": "Image Files (*.png *.jpg *.jpeg *.bmp)",
            "dialog_ok_button": "OK", "dialog_cancel_button": "Cancel",
            "game_add_success_title": "Game Added", "game_add_success_message": "'{game_name}' has been added successfully.",
            "game_add_fail_title": "Input Error", "game_add_fail_message_name": "Game name cannot be empty.",
            "game_add_fail_message_cover": "Cover image path cannot be empty.",
            "game_delete_button": "Delete", # New
            "game_delete_confirm_title": "Confirm Delete", # New
            "game_delete_confirm_message": "Are you sure you want to delete '{game_name}'?", # New
            "game_delete_success_title": "Game Deleted", # New
            "game_delete_success_message": "'{game_name}' has been deleted.", # New
            "game_delete_fail_title": "Delete Error", # New
            "game_delete_fail_message_not_found": "Could not find '{game_name}' to delete.", # New


            "contact_page_title":"Connect","contact_facebook_button":"Facebook","contact_github_button":"GitHub","contact_instagram_button":"Instagram","contact_email_label":"Email: ...",
            "courses_page_title":"Courses","course_game_dev_title":"Game Dev","course_game_dev_desc":"...","course_view_button":"Soon", 
            "settings_page_title":"Settings","settings_language_label":"Language:","settings_nav_bar_label":"Nav Bar:","settings_save_button":"Save",
            "settings_restart_info":"Restart needed.","settings_restart_info_full":"Restart for nav changes.","settings_saved_message_title":"Saved","settings_saved_message_body":"Settings saved.","settings_restart_required_title":"Restart","settings_restart_required_body":"Restart for nav.",
            "account_page_signin_title":"Sign In","account_email_label":"Email:","account_email_placeholder":"your@email.com","account_recaptcha_label":"I'm not a robot",
            "account_signin_button":"Send Code","account_sending_code_button":"Sending...",
            "account_details_title":"Account","account_details_email":"Email:","account_details_display_name":"Name:","account_logout_button":"Log Out",
            "account_verify_title":"Verify Code","account_verify_prompt":"Email sent. Enter code:","account_verify_prompt_dynamic":"Email to {email}. Enter code:",
            "account_verify_code_placeholder":"6-digit code","account_verify_button":"Verify","account_cancel_verify_button":"Cancel",
            "signin_error_title":"Error","signin_invalid_email_error":"Valid email needed.","signin_recaptcha_error":"Prove not robot.",
            "email_error_title":"Email Error","email_send_error_message":"Could not send.","verify_error_title":"Verify Error","verify_empty_code_error":"Enter code.",
            "verify_success_title":"Success","verify_success_message":"Signed in!","verify_incorrect_code_error":"Incorrect code.",
            "logout_title":"Logged Out","logout_message":"Logged out."
            },
            "Arabic":{ 
                "app_title":"عميل مؤمن","nav_home":"الرئيسية", "nav_games": "الألعاب", "settings_page_title":"الإعدادات",
                "games_page_title": "مجموعة ألعابي", "add_game_button": "إضافة لعبة",
                "no_games_message": "لم يتم إضافة ألعاب بعد. انقر 'إضافة لعبة' للبدء!",
                "add_game_dialog_title": "إضافة لعبة جديدة",
                 "game_name_label_dialog": "اسم اللعبة:", "game_name_placeholder_dialog": "أدخل اسم اللعبة",
                "game_desc_label_dialog": "الوصف:", "game_desc_placeholder_dialog": "أدخل وصف اللعبة",
                "game_cover_label_dialog": "صورة الغلاف:", "game_cover_placeholder_dialog": "مسار صورة الغلاف",
                "browse_button_dialog": "تصفح...", "select_cover_dialog_title": "اختر صورة الغلاف",
                "image_files_filter_dialog": "ملفات الصور (*.png *.jpg *.jpeg *.bmp)",
                "dialog_ok_button": "موافق", "dialog_cancel_button": "إلغاء",
                "game_add_success_title": "تمت إضافة اللعبة", "game_add_success_message": "تمت إضافة '{game_name}' بنجاح.",
                "game_delete_button": "حذف", # New
                "game_delete_confirm_title": "تأكيد الحذف", # New
                "game_delete_confirm_message": "هل أنت متأكد أنك تريد حذف '{game_name}'؟", # New
                "game_delete_success_title": "تم حذف اللعبة", # New
                "game_delete_success_message": "تم حذف '{game_name}'.", # New
                "game_delete_fail_title": "خطأ في الحذف", # New
                "game_delete_fail_message_not_found": "لم يتم العثور على '{game_name}' للحذف." # New
            }}
        try:
            with open(TRANSLATIONS_FILE,'w',encoding='utf-8')as f:json.dump(dt,f,indent=4,ensure_ascii=False)
            print(f"Created dummy '{TRANSLATIONS_FILE}'")
        except IOError as e:print(f"Could not create dummy translations: {e}")
    
    if not os.path.exists(GAMES_FILE):
        try:
            with open(GAMES_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4) 
            print(f"Created empty '{GAMES_FILE}'")
        except IOError as e:
            print(f"Could not create empty games file: {e}")

    client=MoumenClient()
    client.show()
    sys.exit(app.exec_())
# --- END MODIFIED __main__ ---