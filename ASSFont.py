from tkinterdnd2 import TkinterDnD, DND_ALL
import customtkinter as ctk
import re, json
from functools import partial
import os, sys
import shutil
from fontTools.ttLib import TTFont
from fontTools import subset
import random
import string
from PIL import Image


class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


def hex_to_rgb(hex_color):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return (r, g, b)


def rgb_to_hex(rgb_color):
    return "#{0:02x}{1:02x}{2:02x}".format(*rgb_color)


def opacity(color: str = "#FA4276", opacity: float = 0.0) -> str:
    rgb_color = hex_to_rgb(color)
    new_rgb_color = tuple(int(c * opacity + 255 * (1 - opacity)) for c in rgb_color)
    new_color_str = rgb_to_hex(new_rgb_color)
    return new_color_str


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 开关
class Check(ctk.CTkFrame):
    def __init__(self, master, key: str, label: str, default: bool = False):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.key = key
        self.label = label
        self.default = default

        if key not in master.values:
            master.values[self.key] = self.default
        self.checkbutton = ctk.CTkButton(
            master=self,
            font=master.font,
            text=self.label,
            hover=False,
            fg_color="#333333",
            text_color="#FFFFFF",
            border_color="#FA4276",
            corner_radius=6,
            border_width=2,
            height=18,
            border_spacing=1,
            command=partial(self.toggle, master=master, value=None),
            width=1000,
        )
        self.checkbutton.grid(row=0, column=0, padx=0, pady=0, sticky="nw")
        self.update(master)

    def toggle(self, master, value: bool | None = None):
        master.values[self.key] = (
            not master.values[self.key] if value is None else value
        )
        # print(master.values)
        self.update(master)

    def update(self, master):
        if master.values[self.key]:
            self.checkbutton.configure(fg_color=opacity(opacity=0.7))
        else:
            self.checkbutton.configure(fg_color="#333333")

    def getself(self):
        return self.checkbutton


# 设置选项
class Option(ctk.CTkFrame):
    def __init__(
        self,
        master,
        key: str,
        label: str,
        arg: any = None,
    ):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.key = key
        self.label = label
        self.arg = arg

        self.labelbox = ctk.CTkLabel(
            master=self,
            text=self.label,
            height=24,
            width=1000,
            text_color="#EEEEEE",
            fg_color="#333333",
            font=master.font,
            corner_radius=4,
        )
        self.labelbox.grid(row=0, column=0, padx=(10, 10), pady=(5, 0), sticky="nw")
        self.textvariable = ctk.StringVar(value=master.getconfig(self.key))
        self.inputbox = ctk.CTkEntry(
            master=self,
            textvariable=self.textvariable,
            height=24,
            width=1000,
            text_color="#FFFFFF",
            fg_color="#666666",
            border_color="#EEEEEE",
            font=master.font,
            corner_radius=4,
            border_width=1,
        )
        self.inputbox.grid(row=1, column=0, padx=(10, 10), pady=(0, 5), sticky="nsw")
        self.inputbox.bind("<KeyRelease>", partial(self.update, master=master))

    def update(self, _, master):
        # print(self.inputbox.get())
        master.config[self.key] = self.inputbox.get()
        master.saveconfig()


# 设置窗口加滚动
class ConfigWindowFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.font = master.font
        self.config = master.config
        self.getconfig = master.getconfig
        self.saveconfig = master.saveconfig
        self.grid_columnconfigure([0], weight=1)

        _options = {
            "mkvmerge_path": "mkvmerge路径(安装mkvtoolnix的同目录下)",
            "filename_ext": "混流输出文件的视频属性标识",
            "mkvoutputdir": "混流输出文件的路径(留空则与输入文件同目录)",
            "videotrack_lang": "混流视频轨道的语言设置(中文为zh日文为ja)",
            "videotrack_name": "混流视频轨道的名称",
            "videotrack_resolution": "混流视频轨道的分辨率",
            "audiotrack_lang": "混流音频轨道的语言设置(中文为zh日文为ja)",
            "audiotrack_name": "混流音频轨道的名称",
            "audiotrack_delay": "混流音频轨道的延迟(0则无延迟)",
            "asschsjpntrack_symbol": "混流字幕轨道判定为简中/简日的标识符",
            "asschsjpntrack_lang": "[简中/简日]混流字幕轨道的语言(中文为zh日文为ja)",
            "asschsjpntrack_name": "[简中/简日]混流字幕轨道的名称",
            "asschtjpntrack_symbol": "混流字幕轨道判定为繁中/繁日的标识符",
            "asschtjpntrack_lang": "[繁中/繁日]混流字幕轨道的语言(中文为zh日文为ja)",
            "asschtjpntrack_name": "[繁中/繁日]混流字幕轨道的名称",
            "assjpntrack_symbol": "混流字幕轨道判定为日文的标识符",
            "assjpntrack_lang": "[日本語]混流字幕轨道的语言(中文为zh日文为ja)",
            "assjpntrack_name": "[日本語]混流字幕轨道的名称",
            "asstrackname_separator": "混流字幕轨道名称分割符\n(在字幕文件名有.style.ass时在名称后添加/分割符style/)",
            "assmultistyle_defaulttrack": "混流字幕轨道有多style时判定默认轨道的style名",
            "fontsubset_warning": "子集化字体之后添加的警告标识(作用于字体名称及附件名称)",
        }
        row = 0
        for key, label in _options.items():
            _option = Option(
                self,
                key=key,
                label=label,
            )
            _option.grid(row=row, column=0, padx=(16, 16), pady=(5, 5), sticky=ctk.N)
            row = row + 1


# 设置窗口
class ConfigWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.geometry("600x500")
        self.minsize(600, 500)
        self.title("ASSFont 设置 - KyokuSai")
        self.after(250, lambda: self.iconbitmap(resource_path("favicon.ico")))
        self.font = master.font
        self.config = master.config
        self.getconfig = master.getconfig
        self.saveconfig = master.saveconfig

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.configwindowframe = ConfigWindowFrame(
            master=self, corner_radius=0, fg_color="transparent"
        )
        self.configwindowframe.grid(row=0, column=0, sticky="nsew")
        # print(master.config)
        # self.focus()


class ASSFont:
    def __init__(self):
        super().__init__()
        self.styles = {}
        self.dialogues = []
        self.fonts = {}
        self.filecontent = ""

    # 读取字幕文件
    def readfile(self, assfile: str):
        with open(assfile, "r", encoding="utf-8") as file:
            self.filecontent = file.read()

    # 读取字幕样式
    def readstyles(self):
        styles = re.findall(r"^(Style:.+)$", self.filecontent, re.MULTILINE)
        for style in styles:
            match = re.search(r"^Style: ?([^,]*),([^,]*)", style)
            self.styles[match.group(1)] = match.group(2)
        # print(self.styles)

    # 读取字幕行
    def readdialogues(self):
        dialogues = re.findall(r"^(Dialogue:.+)$", self.filecontent, re.MULTILINE)
        for dialogue in dialogues:
            match = re.search(
                r"^Dialogue: ?[^,]+,[^,]+,[^,]+,([^,]+),[^,]*,[^,]+,[^,]+,[^,]+,[^,]*,(.*)$",  # 固定读取样式名称位置，没有考虑字幕使用其它顺序的情况
                dialogue,
            )
            self.dialogues.append(
                {
                    "style": match.group(1),  # 样式名
                    "content": match.group(2),  # 内容
                }
            )
        # print(self.dialogues)

    # 混合多字幕的字体信息
    def mergefonts(self, fonts: dict):
        for font, content in fonts.items():
            if font not in self.fonts:
                self.fonts[font] = ""
            self.fonts[font] += content

    # 删除重复字符
    def remove_duplicates(self):
        for font, content in self.fonts.items():
            content = f"{content}ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"  # 必需加上大小写英语和数字才能正常显示字体
            if re.search(r"０１２３４５６７８９", content):
                content = f"{content}０１２３４５６７８９"
            unique_chars = set(content)
            self.fonts[font] = "".join(sorted(unique_chars))

    # 添加字体信息
    def addfont(self, fontname: str, content: str):
        content = re.sub(r"\{[^\{]*\}", "", content)  # 去掉特效标签部分
        if len(content) == 0:  # 如果此时已经为空则不添加此信息（避免添加未用到的字体）
            return
        if fontname.startswith("@"):  # 如果使用倒置则去掉倒置符号
            fontname = fontname.lstrip("@")
        if fontname not in self.fonts:
            self.fonts[fontname] = ""
        self.fonts[fontname] += content

    # 清除\p1绘图
    def cleandraw(self, content: str) -> str:
        content = re.sub(r"\\p1[^{}]*}.*?{[^{}]*\\p0", "", content)
        content = re.sub(r"\\p1[^{}]*}.*?$", "}", content)
        return content

    # 对\fn进行分片分析
    def collectfontbypart(self, default_font: str, content: str):
        content = f"{{\\fn{default_font}}}{content}"
        match = re.findall(r"\\fn.*?(?=\\fn|$)", content)
        for part in match:
            font = re.search(r"\\fn([^\\\}]*)", part).group(1)
            if len(font) == 0:
                font = default_font
            part = re.sub(r"^[^\{\}]*\}", "", part)
            part = re.sub(r"\{[^\{\}]*$", "", part)
            self.addfont(font, part)
            # print(f"***{font} /// {part}")

    # 收集字体
    def collectfont(self):
        for dialogue in self.dialogues:
            default_style = dialogue["style"]
            content = dialogue["content"]
            if r"\p1" in content:
                content = self.cleandraw(content)
            # print(content)
            if r"\fn" in content:
                # print(content)
                self.collectfontbypart(self.styles[default_style], content)
                continue
            self.addfont(self.styles[default_style], content)


class App(Tk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        self.geometry("600x500")
        self.minsize(600, 500)
        self.title("ASSFont - KyokuSai")
        self.iconbitmap(resource_path("favicon.ico"))

        self.grid_columnconfigure([0, 1, 2], weight=1)

        self.folder = ""
        if getattr(sys, "frozen", False):
            self.folder = os.path.abspath(os.path.dirname(sys.executable))
        else:
            self.folder = os.path.abspath(os.path.dirname(__file__))
        self.cache = {}
        self.cache_file = os.path.join(self.folder, "data\\cache.json")
        self.config = {}
        self.config_file = os.path.join(self.folder, "data\\config.json")
        self.font = ctk.CTkFont(family="NotoSansSC-Medium", size=18, weight="normal")

        self.mkv = []
        self.mkvbox = ctk.CTkTextbox(
            self,
            height=25,
            text_color="#FFFFFF",
            fg_color="#666666",
            border_color="#FFFFFF",
            scrollbar_button_color="#DDDDDD",
            scrollbar_button_hover_color="#EEEEEE",
            font=self.font,
            wrap="none",
            corner_radius=4,
            border_width=2,
            border_spacing=0,
        )
        self.mkvbox.grid(
            row=0, column=0, padx=16, pady=(10, 5), sticky="ew", columnspan=3
        )
        self.mkvbox.drop_target_register(DND_ALL)
        self.mkvbox.dnd_bind(
            "<<Drop>>",
            partial(
                self.file_drop,
                box=self.mkvbox,
                format="mkv",
                files="mkv",
                multiple=False,
            ),
        )
        self.mkvbox.insert(ctk.END, "拖入mkv文件(如果要混流)")
        self.mkvbox.configure(state="disabled")

        self.files = []
        self.asss = []
        self.filebox = ctk.CTkTextbox(
            self,
            height=175,
            text_color="#FFFFFF",
            fg_color="#666666",
            border_color="#FFFFFF",
            scrollbar_button_color="#DDDDDD",
            scrollbar_button_hover_color="#EEEEEE",
            font=self.font,
            wrap="none",
            corner_radius=4,
            border_width=2,
            border_spacing=0,
        )
        self.filebox.grid(
            row=1, column=0, padx=16, pady=(5, 5), sticky="ew", columnspan=3
        )
        self.filebox.drop_target_register(DND_ALL)
        self.filebox.dnd_bind(
            "<<Drop>>", partial(self.file_drop, box=self.filebox, files="files")
        )
        self.filebox.insert(ctk.END, "拖入字幕文件")
        self.filebox.configure(state="disabled")

        self.values = {}
        _check = Check(self, key="assfix", label="字幕修正", default=False)
        _check.grid(row=2, column=0, padx=(16, 2), pady=(5, 0), sticky=ctk.N)
        _check.getself().configure(state="disabled")
        _check = Check(self, key="subset", label="子集化字体", default=True)
        _check.grid(row=2, column=1, padx=(2, 2), pady=(5, 0), sticky=ctk.N)
        _check = Check(self, key="usecache", label="使用缓存", default=True)
        _check.grid(row=2, column=2, padx=(2, 16), pady=(5, 0), sticky=ctk.N)
        self.cache_check = _check

        self.logbox = ctk.CTkTextbox(
            self,
            height=1000,
            text_color="#333333",
            fg_color="#AAAAAA",
            border_color="#FFFFFF",
            scrollbar_button_color="#DDDDDD",
            scrollbar_button_hover_color="#EEEEEE",
            font=ctk.CTkFont(family="NotoSansSC-Medium", size=14, weight="normal"),
            corner_radius=3,
            border_width=1,
            border_spacing=0,
            state="disabled",
        )
        self.logbox.grid(
            row=3, column=0, padx=16, pady=(10, 5), sticky="ew", columnspan=3
        )
        self.grid_rowconfigure([3], weight=1)

        self.button = ctk.CTkButton(
            self,
            text="",
            image=ctk.CTkImage(
                light_image=Image.open(resource_path("gear.png")),
                dark_image=Image.open(resource_path("gear.png")),
                size=(18, 18),
            ),
            command=self.openconfigwindow,
            hover=False,
            font=self.font,
            fg_color=opacity(opacity=0.9),
            text_color="#FFFFFF",
            corner_radius=6,
            border_width=0,
            height=22,
            width=22,
            border_spacing=2,
        )
        self.button.grid(
            row=4, column=0, padx=(16, 16), pady=(5, 10), sticky="nws", columnspan=1
        )

        def _start():
            try:
                self.start()
            except Exception:
                sys.excepthook(*sys.exc_info())

        self.button = ctk.CTkButton(
            self,
            text="开始",
            command=_start,
            hover=False,
            font=self.font,
            fg_color=opacity(opacity=0.9),
            text_color="#FFFFFF",
            corner_radius=6,
            border_width=0,
            height=22,
            border_spacing=2,
        )
        self.button.grid(
            row=4,
            column=0,
            padx=(16 + 22 + 2 * 2 + 12, 16),
            pady=(5, 10),
            sticky="ew",
            columnspan=3,
        )

        self.log("-- 日志记录 --")

        def global_exception(exc_type, exc_value, exc_traceback):
            self.log("Error:")
            self.log(str(exc_type))
            self.log(str(exc_value))
            self.log(str(exc_traceback))

        sys.excepthook = global_exception
        self.getcache(init=True)
        self.setconfig()
        self.configwindow = None

    def file_drop(
        self,
        event,
        box: ctk.CTkTextbox,
        files: str,
        format: str = "ass",
        multiple: bool = True,
    ):
        box.configure(state="normal")
        box.delete(1.0, ctk.END)
        _files = event.data
        if "{" not in _files:
            _files = f"{{{_files}}}"
            _files = re.sub(r" ([A-Z]:)", r"} \1", _files)
            _files = re.sub(r" ([A-Z]:)", r" {\1", _files)
        _files = re.findall(r"{([^{]+)}", _files)
        setattr(
            self,
            files,
            getattr(self, files) + _files if multiple else _files,
        )
        for index, file in enumerate(getattr(self, files)):
            if not file.lower().endswith(f".{format}"):
                continue
            if not multiple and index != len(getattr(self, files)) - 1:
                continue
            box.insert(
                ctk.END, file + "\n" if index != len(getattr(self, files)) - 1 else file
            )
        box.yview(ctk.END)
        box.configure(state="disabled")

    def log(self, text: str):
        self.logbox.configure(state="normal")
        self.logbox.insert(ctk.END, text + "\n")
        self.logbox.yview(ctk.END)
        self.logbox.configure(state="disabled")

    def getassfonts(self) -> dict:
        assfont = ASSFont()
        for file in self.files:
            self.log(f"处理文件：{file}")
            _assfont = ASSFont()
            _assfont.readfile(file)
            _assfont.readstyles()
            _assfont.readdialogues()
            _assfont.collectfont()
            assfont.mergefonts(_assfont.fonts)
        assfont.remove_duplicates()
        # print(assfont.fonts)
        return assfont.fonts

    # 根据字体名称获取字体文件
    def getfontfile(self, fontname):
        for font_path, namerecord in self.cache.items():
            if fontname in namerecord:
                return font_path, os.path.basename(font_path)
        return None, None

    # 生成字体信息缓存
    def generatecache(self):
        self.cache = {}

        font_dir = os.path.join(os.environ.get("SystemRoot", "C:\\"), "Fonts")
        font_paths = []
        for root, _, files in os.walk(font_dir):  # 有一些字体是在子文件夹中
            for file in files:
                file_path = os.path.join(root, file)
                font_paths.append(file_path)
        for font_path in font_paths:
            filename: str = os.path.basename(font_path)
            if filename.lower().endswith(".ttf") or filename.lower().endswith(".otf"):
                try:
                    font = TTFont(font_path)
                    names = font["name"]
                    names = [  # 所有可能的名称
                        names.getName(1, 3, 1),
                        names.getName(4, 3, 1),
                        names.getName(1, 1, 25),
                        names.getName(4, 1, 25),
                    ]
                    self.cache[font_path] = [
                        name.toStr() for name in names if name is not None
                    ]
                    font.close()
                except Exception as e:
                    self.log(f"字体读取错误：{e}")

        self.cache_check.toggle(master=self, value=True)
        self.cache_check.getself().configure(state="normal")
        # print(self.cache)

    # 读取字体信息缓存
    def getcache(self, init: bool = False):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as json_file:
                self.cache = json.load(json_file)
        else:
            if init:
                self.cache_check.toggle(master=self, value=False)
                self.cache_check.getself().configure(state="disabled")

    # 保存字体信息
    def savecache(self):
        if not os.path.exists(f"{self.folder}\\data"):
            os.makedirs(f"{self.folder}\\data")
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        with open(self.cache_file, "w", encoding="utf-8") as json_file:
            json.dump(self.cache, json_file, ensure_ascii=False)

    # 初始化程序设置
    def initconfig(self, _return: bool = False):
        config = {
            "mkvmerge_path": "D:/path/to/mkvmerge.exe",
            "filename_ext": "[1080P][WEBRip][HEVC 10bit]",
            "mkvoutputdir": "",
            "videotrack_lang": "ja",
            "videotrack_name": "WEBRip by KyokuSaiYume",
            "videotrack_resolution": "1920x1080",
            "audiotrack_delay": "0",
            "audiotrack_lang": "ja",
            "audiotrack_name": "WEB-DL",
            "asschsjpntrack_symbol": "[CHS_JPN]",
            "asschsjpntrack_lang": "zh",
            "asschsjpntrack_name": "简日双语-CHS_JPN",
            "asschtjpntrack_symbol": "[CHT_JPN]",
            "asschtjpntrack_lang": "zh",
            "asschtjpntrack_name": "繁日雙語-CHT_JPN",
            "assjpntrack_symbol": "[JPN]",
            "assjpntrack_lang": "ja",
            "assjpntrack_name": "日本語-JPN",
            "asstrackname_separator": " - ",
            "assmultistyle_defaulttrack": "kawaii",
            "fontsubset_warning": "请勿安装此子集化字体 - ",
        }
        if _return:
            return config
        self.config = config
        self.saveconfig()

    # 读取程序设置
    def setconfig(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as json_file:
                self.config = json.load(json_file)
        else:
            self.initconfig()

    # 获取程序设置
    def getconfig(self, key):
        if key not in self.config:
            defaultconfig = self.initconfig(_return=True)
            mergedconfig = dict(self.config)
            for _key, _value in defaultconfig.items():
                if _key not in mergedconfig:
                    mergedconfig[_key] = _value
            self.config = mergedconfig
            self.saveconfig()
        return self.config[key]

    # 保存程序设置
    def saveconfig(self):
        if not os.path.exists(f"{self.folder}\\data"):
            os.makedirs(f"{self.folder}\\data")
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        with open(self.config_file, "w", encoding="utf-8") as json_file:
            json.dump(self.config, json_file, ensure_ascii=False)

    # 打开设置窗口
    def openconfigwindow(self):
        if self.configwindow is None or not self.configwindow.winfo_exists():
            self.configwindow = ConfigWindow(self)
        else:
            self.configwindow.focus()

    # 子集化字体
    def subset(self, fontfile: str, characters: str, newname: str, outputpath: str):
        subsetoptions = subset.Options(
            name_languages="*",
            # recalc_timestamp=True,
        )
        font = subset.load_font(fontfile, options=subsetoptions)  # 读取字体

        # 子集化字体
        subsetter = subset.Subsetter(options=subsetoptions)
        subsetter.populate(text=characters)
        subsetter.subset(font)

        # 修改字体名称
        name_table = font["name"]
        for record in name_table.names:
            if record.nameID == 1:
                record.string = newname.encode("utf-16be")
            elif record.nameID == 4:
                record.string = newname.encode("utf-16be")

        # 转为ttf保存
        font.flavor = "woff2"
        subset.save_font(font, outputpath, subset.Options())
        font.close()

    # 修改字幕中使用的字体名称（为子集化后的名称）
    def asssubsetfix(self, filepath: str, outputpath: str, replacedict: dict):
        self.asss.append(outputpath)
        with open(filepath, "r", encoding="utf-8") as file:
            file_content = file.read()

        for key, value in replacedict.items():
            file_content = file_content.replace(key, value)

        with open(outputpath, "w", encoding="utf-8") as file:
            file.write(file_content)

    # 开始
    def start(self):
        # print(self.files)
        self.log(f"当前设置：{self.values}")
        if self.values["usecache"]:
            self.log(f"使用缓存数据")
            self.getcache()
        else:
            self.log(f"读取字体……")
            self.generatecache()
            self.savecache()
        fonts = self.getassfonts()
        if os.path.exists(f"{self.folder}\\result"):
            shutil.rmtree(f"{self.folder}\\result")
        os.makedirs(f"{self.folder}\\result")
        real_fontpaths = []
        if self.values["subset"]:
            fontsubset_warning = self.getconfig("fontsubset_warning")
            replacedict = {}
            for font, content in fonts.items():
                self.log(f"查找字体：{font}")
                font_path, font_file = self.getfontfile(font)
                if font_path:
                    self.log(f"子集化字体：{font}")
                    randomstr = "".join(
                        random.choice(string.ascii_letters + string.digits)
                        for _ in range(8)
                    )
                    replacedict[font] = f"{fontsubset_warning}{randomstr}"
                    self.subset(
                        font_path,
                        content,
                        replacedict[font],
                        f"{self.folder}\\result\\{font} - {randomstr}.ttf",
                    )
                    real_fontpaths.append(
                        f"{self.folder}\\result\\{font} - {randomstr}.ttf"
                    )
                else:
                    self.log(f'※"{font}" 的字体文件未能找到。')
                    return
            for file in self.files:
                filename = os.path.basename(file)
                self.asssubsetfix(
                    file, f"{self.folder}\\result\\{filename}", replacedict
                )
            self.log(f"字幕字体处理完毕。共 {len(fonts)} 个字体。")
        else:
            self.asss = self.files
            for font, _ in fonts.items():
                self.log(f"查找字体：{font}")
                font_path, font_file = self.getfontfile(font)
                if font_path:
                    shutil.copy(font_path, f"{self.folder}\\result\\{font_file}")
                    real_fontpaths.append(f"{self.folder}\\result\\{font_file}")
                else:
                    self.log(f'※"{font}" 的字体文件未能找到。')
                    return
            self.log(f"字幕字体处理完毕。共 {len(fonts)} 个字体。")
        if len(self.mkv) != 0:
            self.asss = sorted(self.asss, key=lambda x: os.path.basename(x))
            self.log(f"开始自动混流")
            mkv = self.mkv[0]
            mkvmerge_path = self.getconfig("mkvmerge_path")
            title = re.sub(r"\.mkv$", "", os.path.basename(mkv))
            filename_ext = self.getconfig("filename_ext")
            outputdir = self.getconfig("mkvoutputdir")
            if len(outputdir) == 0:
                outputdir = os.path.dirname(mkv)
            if not outputdir.endswith("\\"):
                outputdir = f"{outputdir}\\"
            outputfile = f"{title} {filename_ext}.mkv"
            videotrack_lang = self.getconfig("videotrack_lang")
            videotrack_name = self.getconfig("videotrack_name")
            videotrack_resolution = self.getconfig("videotrack_resolution")
            audiotrack_delay = self.getconfig("audiotrack_delay")
            audiotrack_lang = self.getconfig("audiotrack_lang")
            audiotrack_name = self.getconfig("audiotrack_name")
            asschsjpntrack_symbol = self.getconfig("asschsjpntrack_symbol")
            asschsjpntrack_lang = self.getconfig("asschsjpntrack_lang")
            asschsjpntrack_name = self.getconfig("asschsjpntrack_name")
            asschtjpntrack_symbol = self.getconfig("asschtjpntrack_symbol")
            asschtjpntrack_lang = self.getconfig("asschtjpntrack_lang")
            asschtjpntrack_name = self.getconfig("asschtjpntrack_name")
            assjpntrack_symbol = self.getconfig("assjpntrack_symbol")
            assjpntrack_lang = self.getconfig("assjpntrack_lang")
            assjpntrack_name = self.getconfig("assjpntrack_name")
            asstrackname_separator = self.getconfig("asstrackname_separator")
            assmultistyle_defaulttrack = self.getconfig("assmultistyle_defaulttrack")
            fontsubset_warning = self.getconfig("fontsubset_warning")
            asstrack = {
                asschsjpntrack_symbol: [asschsjpntrack_lang, asschsjpntrack_name],
                asschtjpntrack_symbol: [asschtjpntrack_lang, asschtjpntrack_name],
                assjpntrack_symbol: [assjpntrack_lang, assjpntrack_name],
            }
            cmd = f'start "mkvmux" "{mkvmerge_path}" --ui-language zh_CN --priority lower '
            cmd += f'--output ^"{outputdir}{outputfile}^" '
            cmd += f"--no-subtitles --no-attachments "
            cmd += f'--language 0:{videotrack_lang} --track-name ^"0:{videotrack_name}^" --display-dimensions 0:{videotrack_resolution} '
            if int(audiotrack_delay) == 0:
                audiotrack_delay = ""
            else:
                audiotrack_delay = f"--sync 1:{audiotrack_delay} "
            cmd += f'{audiotrack_delay}--language 1:{audiotrack_lang} --track-name ^"1:{audiotrack_name}^" ^"^(^" ^"{mkv}^" ^"^)^" '
            asstrackorder = ""
            for _index, ass in enumerate(self.asss):
                asstrackorder += "," + str(_index + 1) + ":0"
                track_lang = "zh"
                track_name = ""
                track_isdefault = "--default-track-flag 0:no "
                for _symbol, _value in asstrack.items():
                    if _symbol in os.path.basename(ass):
                        track_lang = _value[0]
                        track_name = _value[1]
                        is_unique = sum(_symbol in _item for _item in self.asss)
                        if is_unique < 2:
                            track_isdefault = ""
                realtrack_name = track_name
                assstyle = os.path.splitext(os.path.basename(ass))[0].split(".")
                if len(assstyle) < 2:
                    assstyle = ""
                else:
                    assstyle = assstyle[-1]
                if len(assstyle) != 0:
                    realtrack_name = (
                        f"{realtrack_name}{asstrackname_separator}{assstyle}"
                    )
                if assmultistyle_defaulttrack == assstyle:
                    track_isdefault = ""
                cmd += f'--language 0:{track_lang} --track-name ^"0:{realtrack_name}^" {track_isdefault}^"^(^" ^"{ass}^" ^"^)^" '
            if not fontsubset_warning.endswith(" ") and not fontsubset_warning.endswith(
                "-"
            ):
                fontsubset_warning = f"{fontsubset_warning}-"
            for real_fontpath in real_fontpaths:
                cmd += f'--attachment-name ^"{fontsubset_warning}{os.path.basename(real_fontpath)}^" --attachment-mime-type font/{os.path.splitext(real_fontpath)[1][1:].lower()} --attach-file ^"{real_fontpath}^" '
            cmd += f'--title ^"{title}^" '
            cmd += f"--track-order 0:0,0:1"  # 音视频轨道
            cmd += asstrackorder  # 字幕轨道
            self.log("混流命令：")
            self.log(cmd)
            os.system(cmd)
        self.mkv = []
        self.mkvbox.configure(state="normal")
        self.mkvbox.delete(1.0, ctk.END)
        self.mkvbox.insert(ctk.END, "拖入mkv文件(如果要混流)")
        self.mkvbox.yview(ctk.END)
        self.mkvbox.configure(state="disabled")
        self.asss = []
        self.files = []
        self.filebox.configure(state="normal")
        self.filebox.delete(1.0, ctk.END)
        self.filebox.insert(ctk.END, "拖入字幕文件")
        self.filebox.yview(ctk.END)
        self.filebox.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
