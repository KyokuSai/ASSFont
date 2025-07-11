from pathlib import Path
from tkinterdnd2 import TkinterDnD, DND_ALL
import customtkinter as ctk
import tkinter
import re, json
from functools import partial
import os, sys
import shutil
from fontTools.ttLib import TTFont, TTCollection
from fontTools import subset
import random
from PIL import Image
import requests, subprocess
import io, threading
from pymediainfo import MediaInfo


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
    new_rgb_color = (int(c * opacity + 255 * (1 - opacity)) for c in rgb_color)
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

        if isinstance(master.getconfig(self.key), bool):
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
            self.labelbox.grid(row=0, column=0, padx=(10, 10), pady=(8, 8), sticky="nw")
            self.variable = ctk.StringVar(
                value="True" if master.getconfig(self.key) else "False"
            )
            self.inputbox = ctk.CTkCheckBox(
                master=self,
                text="",
                command=self.update,
                variable=self.variable,
                onvalue="True",
                offvalue="False",
                height=24,
                width=24,
                fg_color=opacity(opacity=0.8),
                corner_radius=4,
                hover=False,
            )
            self.inputbox.grid(row=0, column=0, padx=(10, 10), pady=(8, 8), sticky="ne")
        elif isinstance(master.getconfig(self.key), str):
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
            if "\n" in master.getconfig(self.key):
                self.inputbox = ctk.CTkTextbox(
                    master=self,
                    height=24
                    * (len(re.findall(r"\n", master.getconfig(self.key))) + 1),
                    width=1000,
                    text_color="#FFFFFF",
                    fg_color="#666666",
                    border_color="#EEEEEE",
                    font=master.font,
                    corner_radius=4,
                    border_width=1,
                )
                self.inputbox.insert(ctk.END, master.getconfig(self.key))
            else:
                self.variable = ctk.StringVar(value=master.getconfig(self.key))
                self.inputbox = ctk.CTkEntry(
                    master=self,
                    textvariable=self.variable,
                    height=24,
                    width=1000,
                    text_color="#FFFFFF",
                    fg_color="#666666",
                    border_color="#EEEEEE",
                    font=master.font,
                    corner_radius=4,
                    border_width=1,
                )
            self.inputbox.grid(
                row=1, column=0, padx=(10, 10), pady=(0, 5), sticky="nsw"
            )
            self.inputbox.bind("<KeyRelease>", self.update)

    def update(self, _=None):
        value = (
            self.inputbox.get("1.0", ctk.END)
            if isinstance(self.inputbox, ctk.CTkTextbox)
            else self.inputbox.get()
        )
        if isinstance(self.master.getconfig(self.key), bool):
            if value == "True":
                self.master.config[self.key] = True
            else:
                self.master.config[self.key] = False
            self.master.saveconfig()
        elif isinstance(self.master.getconfig(self.key), str):
            self.master.config[self.key] = value
            self.master.saveconfig()


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
            "assengtrack_symbol": "混流字幕轨道判定为英文的标识符",
            "assengtrack_lang": "[ENG]混流字幕轨道的语言(英文为en)",
            "assengtrack_name": "[ENG]混流字幕轨道的名称",
            "asstrackname_separator": "混流字幕轨道名称分割符\n(在字幕文件名有.style.ass时在名称后添加/分割符style/)",
            "assmultistyle_defaulttrack": "混流字幕轨道有多style时判定默认轨道的style名",
            "optional_styles": "特殊样式保留，指定样式在清理样式时保留，用,分割",
            "fontsubset_warning": "子集化字体之后添加的警告标识(作用于字体名称及附件名称)",
            "clean_scriptinfo": "开启后按照设置清理 Script Info 信息",
            "scriptinfo": "在清理 Script Info 时，要设置为什么值\n如果你需要的话可以使用{LANGUAGE}来表示语言信息",
            "scriptinfo_language": "Script Info 中语言信息的替换值\n用,分割，即：简中信息,繁中信息,日语信息",
            "clean_garbage": "开启后清除 Aegisub 生成的 Project Garbage 信息",
            "clean_furigana": "开启后清除在应用卡拉OK模板时生成的不需要的 furigana 样式",
            "clean_space": "开启后清除字幕中行末空格",
            "clean_all_space": "开启后清除字幕中所有重复空格",
            "unicode_to_utf8": '开启后将字幕中所有 Unicode 码点转换为 UTF-8 字节\n例如将"\\u{3000}"转换为"\\xE3\\x80\\x80"\n如果不清楚有什么用处也可以打开，可以避免非常极端情况下的一些小问题',
            "generate_cht": "生成字幕时是否生成繁中字幕\n使用 繁化姬 进行处理",
            "generate_cht_styles": "繁化只对此设置项指定的样式生效\n用,分割，留空则全部生效",
            "generate_cht_keep_comment": "开启后对于一些不显示的行(例如翻译注释)不进行繁化",
            "zhconvert_json": "生成繁中字幕时请求 繁化姬 的 json 数据\n使用{ASSCONTENT}来表示字幕内容",
            "generate_jpn": "生成字幕时是否生成日语字幕",
            "jpn_convert": "在生成日语字幕时是否删除所有中文行",
            "jpn_convert_styles_to_delete": "在生成日语字幕时删除的中文行的指定样式\n可删除多个样式及其内容，用,分割",
            "generate_multistyle": "是否要生成多样式字幕",
            "generate_karaoke": "是否要对生成出的字幕进行应用卡拉OK模板",
            "aegisub_cli_path": "应用卡拉OK使用的 aegisub-cli 路径",
            "aegisub_cli_loglevel": "aegisub-cli 的 loglevel\n0 = exception; 1 = assert; 2 = warning; 3 = info; 4 = debug",
            "generate_language": "生成字幕及原始文件名中的语言标识\n用,分割，即：简中标识,繁中标识,日语标识",
            # "assstyles": "生成多样式字幕所需要用到的样式表\n请查看说明填写此项或者关闭字幕多样式生成",
            "proxy": "http代理端口，0则为禁用",
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
        self.geometry("800x600")
        self.minsize(800, 600)
        self.title("ASSFont 设置 - KyokuSai")
        self.after(250, lambda: self.iconbitmap(resource_path("favicon.ico")))
        self.after(150, lambda: self.focus())
        self.font = master.font
        self.config = master.config
        self.getconfig = master.getconfig
        self.saveconfig = master.saveconfig
        self.after(10, self._create_widgets)

    def _create_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.configwindowframe = ConfigWindowFrame(
            master=self, corner_radius=0, fg_color="transparent"
        )
        self.configwindowframe.grid(row=0, column=0, sticky="nsew")


class CTkRadioButton(ctk.CTkRadioButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=4, border_width_checked=3, **kwargs)
        self._text_label.grid(row=0, column=0, sticky=ctk.NSEW)
        self._canvas.grid(row=0, column=2, sticky=ctk.E)

    def _create_bindings(self, sequence=None):
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Enter>", self._on_enter)
            self._bg_canvas.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            self._text_label.bind("<Leave>", self._on_leave)
            self._bg_canvas.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self.invoke)
            self._text_label.bind("<Button-1>", self.invoke)
            self._bg_canvas.bind("<Button-1>", self.invoke)

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring_1 = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._radiobutton_width),
            self._apply_widget_scaling(self._radiobutton_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width_checked),
        )
        if self._check_state is True:
            requires_recoloring_2 = self._draw_engine.draw_checkmark(
                self._apply_widget_scaling(self._radiobutton_width),
                self._apply_widget_scaling(self._radiobutton_height),
                self._apply_widget_scaling(self._radiobutton_height * 0.58),
            )
        else:
            requires_recoloring_2 = False
            self._canvas.delete("checkmark")
        if no_color_updates is False or requires_recoloring_1 or requires_recoloring_2:
            self._bg_canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            if self._check_state is True:
                self._canvas.itemconfig(
                    "inner_parts",
                    outline=self._apply_appearance_mode(self._fg_color),
                    fill=self._apply_appearance_mode(self._fg_color),
                )
                self._canvas.itemconfig(
                    "border_parts",
                    outline=self._apply_appearance_mode(self._fg_color),
                    fill=self._apply_appearance_mode(self._fg_color),
                )
                if "create_line" in self._canvas.gettags("checkmark"):
                    self._canvas.itemconfig(
                        "checkmark",
                        fill=self._apply_appearance_mode(self._border_color),
                    )
                else:
                    self._canvas.itemconfig(
                        "checkmark",
                        fill=self._apply_appearance_mode(self._border_color),
                    )
            else:
                self._canvas.itemconfig(
                    "inner_parts",
                    outline=self._apply_appearance_mode(self._bg_color),
                    fill=self._apply_appearance_mode(self._bg_color),
                )
                self._canvas.itemconfig(
                    "border_parts",
                    outline=self._apply_appearance_mode(self._border_color),
                    fill=self._apply_appearance_mode(self._border_color),
                )
            if self._state == tkinter.DISABLED:
                self._text_label.configure(
                    fg=(self._apply_appearance_mode(self._text_color_disabled))
                )
            else:
                self._text_label.configure(
                    fg=self._apply_appearance_mode(self._text_color)
                )
            self._text_label.configure(bg=self._apply_appearance_mode(self._bg_color))


class SelectWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        title="",
        selects=[],
        default=None,
    ):
        super().__init__(master)
        self.title(title)
        self.after(250, lambda: self.iconbitmap(resource_path("favicon.ico")))
        self.after(150, lambda: self.focus())
        self.font = master.font
        self.selects = list(selects)
        self.default = 0 if default is None else self.selects.index(default)
        self.result = None
        self.after(10, self._create_widgets)
        self.resizable(False, False)
        self.grab_set()

    def _create_widgets(self):
        self.grid_columnconfigure((0, 1), weight=1)
        self.rowconfigure(0, weight=1)

        self.radio_var = ctk.IntVar(value=self.default)
        row = 0
        for index in range(0, len(self.selects)):
            _radio = CTkRadioButton(
                self,
                text=self.selects[index],
                variable=self.radio_var,
                value=index,
                font=self.font,
                fg_color=opacity(opacity=0.9),
                text_color="#FFFFFF",
                hover_color=opacity(opacity=0.7),
                border_color="#FFFFFF",
            )
            _radio.grid(row=row, column=0, padx=(20, 20), pady=(10, 0), sticky=ctk.NSEW)
            row = row + 1

        self._ok_button = ctk.CTkButton(
            master=self,
            width=200,
            border_width=0,
            text="确认",
            font=self.font,
            command=self._ok_event,
            hover=False,
            fg_color=opacity(opacity=0.9),
            text_color="#FFFFFF",
            corner_radius=6,
            height=22,
            border_spacing=2,
        )
        self._ok_button.grid(
            row=row, column=0, columnspan=1, padx=20, pady=(10, 20), sticky="ew"
        )

    def _ok_event(self):
        self.result = self.selects[self.radio_var.get()]
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self.grab_release()
        self.destroy()

    def _cancel_event(self):
        self.grab_release()
        self.destroy()

    def get_result(self):
        self.master.wait_window(self)
        return self.result


class ASSGenerate:
    def __init__(self, master):
        self.assoriginal_filename = ""
        self.asseng_filename = ""
        self.assoriginal = ""
        self.assoriginal_cht = ""
        self.assoriginal_jpn = ""
        self.assengoriginal = ""
        self.asschss = []
        self.asschts = []
        self.assjpns = []
        self.master: ASSFunUI = master
        self.results: list[Path] = []

    # 读取字幕文件
    def readfile(self, assfile: Path):
        self.assoriginal_filename = os.path.basename(assfile)
        with open(assfile, "r", encoding="utf-8-sig") as file:
            self.assoriginal = file.read()

    # 读取英语字幕文件
    def readengfile(self, assfile: Path):
        self.asseng_filename = os.path.basename(assfile)
        with open(assfile, "r", encoding="utf-8-sig") as file:
            self.assengoriginal = file.read()

    # 清理 Script Info
    def clean_scriptinfo(self, content: str, language: str = "") -> str:
        _clean_scriptinfo = self.master.getconfig("clean_scriptinfo")
        zhconvertcomment = re.search(
            r"^(Comment\: Processed by 繁化姬.+)$",
            content,
            flags=re.MULTILINE,
        )  # 繁化姬注释
        if zhconvertcomment:
            zhconvertcomment = re.sub(
                r"@[^\|]+", "", zhconvertcomment.group(1)
            )  # 去掉时间信息
        content = re.sub(
            r"^Comment\: Processed by 繁化姬.*\n", "", content, flags=re.MULTILINE
        )
        if not _clean_scriptinfo:
            self.master.log("跳过 Script Info 清理")
            if zhconvertcomment:
                content = re.sub(
                    r"\[Script Info\]",
                    f"[Script Info]\n{zhconvertcomment}",
                    content,
                )  # 重新加上繁化姬注释
            return content
        scriptinfo = self.master.getconfig("scriptinfo")
        if "{LANGUAGE}" in scriptinfo:
            scriptinfo_language: str = self.master.getconfig("scriptinfo_language")
            scriptinfo_language = scriptinfo_language.split(",")
            if "CHS" in language.upper():
                language = scriptinfo_language[0]
            elif "CHT" in language.upper():
                language = scriptinfo_language[1]
            elif "JPN" in language.upper():
                language = scriptinfo_language[2]
            scriptinfo = re.sub(r"\{LANGUAGE\}", language, scriptinfo)
        content = re.sub(
            r"\[Script Info\][\s\S\n]+?\n(?=\[)",
            f"{scriptinfo}\n\n",
            content,
            flags=re.IGNORECASE,
        )
        if zhconvertcomment:
            content = re.sub(
                r"\[Script Info\]",
                f"[Script Info]\n{zhconvertcomment}",
                content,
            )  # 重新加上繁化姬注释
        return content

    # 清除 Aegisub Project Garbage 信息
    def clean_garbage(self, content: str) -> str:
        _clean_garbage = self.master.getconfig("clean_garbage")
        if not _clean_garbage:
            self.master.log("跳过 Aegisub Project Garbage 清理")
            return content
        content = re.sub(
            r"\[Aegisub Project Garbage\][\s\S\n]+?\n(?=\[)",
            "",
            content,
            flags=re.IGNORECASE,
        )
        return content

    # 清除未使用的 furigana 样式
    def clean_furigana(self, content: str) -> str:
        _clean_furigana = self.master.getconfig("clean_furigana")
        if not _clean_furigana:
            self.master.log("跳过 furigana 清理")
            return content
        furiganastyles = re.findall(
            r"Style: ?([^,]+?-furigana),", content, re.MULTILINE
        )
        for furiganastyle in furiganastyles:
            match = re.match(f"Dialogue:.*{furiganastyle}", content)
            if match is None:
                content = re.sub(r"Style: ?[^,]+?-furigana.+\n", "", content)
        return content

    # 清除无效空格
    def clean_space(self, content: str) -> str:
        _clean_space = self.master.getconfig("clean_space")
        if not _clean_space:
            self.master.log("跳过空格清理")
            return content
        content = re.sub(r" +$", "", content, flags=re.MULTILINE)  # 清除行末空格
        _clean_all_space = self.master.getconfig("clean_all_space")
        if _clean_all_space:
            content = re.sub(
                r" +", " ", content, flags=re.MULTILINE
            )  # 清除所有重复空格
        return content

    # Unicode码点转UTF-8字节
    def unicode_to_utf8(self, content: str) -> str:
        _unicode_to_utf8 = self.master.getconfig("unicode_to_utf8")
        if not _unicode_to_utf8:
            self.master.log("跳过Unicode码点转UTF-8字节")
            return content
        unicodes = re.findall(r"\\u\{([0-9a-fA-F]+)\}", content, re.MULTILINE)
        for unicode in unicodes:
            utf8 = "".join(
                f"\\\\x{byte:02X}" for byte in eval(f"'\\u{unicode}'").encode("utf-8")
            )
            content = re.sub(r"\\u\{[0-9a-fA-F]+\}", utf8, content)
        return content

    # 获取 style 名
    def getstyle(self, content: str) -> str | None:
        stylestring = re.search(
            r"^(Style:[\s\S\n]+?)\n(?=\[)", content, re.MULTILINE
        ).group(1)
        assstyles = self.master.getconfig("assstyles")
        for _, _assstyles in assstyles.items():
            for assstyle, assstylestring in _assstyles.items():
                assstylestrings = assstylestring.split("\n")
                if all(
                    _assstylestring in stylestring
                    for _assstylestring in assstylestrings
                ):
                    return assstyle
        return None

    # 设置字幕样式
    def setstyle(self, content: str, style: str, lang: str = "CHS_JPN") -> str:
        stylestring = "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        assstyles = self.master.getconfig("assstyles")
        if "CHS" in lang.upper():
            lang = "CHS_JPN"
        elif "CHT" in lang.upper():
            lang = "CHT_JPN"
        elif "JPN" in lang.upper():
            lang = "JPN"
        stylestring += assstyles[lang][style]
        optional_styles: str = self.master.getconfig("optional_styles")
        optional_styles = optional_styles.split(",")
        for optional_style in optional_styles:
            _stylestring = re.search(
                f"^(Style: ?{re.escape(optional_style)},.+?)$",
                content,
                flags=re.MULTILINE,
            )
            if _stylestring:
                stylestring += f"\n{_stylestring.group(1)}"
        stylestring += "\n\n"
        content = re.sub(
            r"^\[V4\+ Styles\][\s\S\n]+?\n(?=\[)",
            f"{stylestring}\n",
            content,
            flags=re.MULTILINE,
        )
        return content

    # 保存简中信息
    def chsconfirm(self):
        self.asschss.append(self.assoriginal)

    # 繁化姬
    def zhconvert(self):
        generate_cht = self.master.getconfig("generate_cht")
        if not generate_cht:
            self.master.log("跳过繁化")
            return
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN",
            "content-type": "application/json",
            "origin": "https://zhconvert.org",
            "priority": "u=1, i",
            "referer": "https://zhconvert.org/",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        json_data = self.master.getconfig("zhconvert_json")
        asscontent = self.assoriginal
        json_data = json.loads(json_data)
        for _key, _value in json_data.items():
            if isinstance(_value, str) and "{ASSCONTENT}" in _value:
                json_data[_key] = json_data[_key].replace("{ASSCONTENT}", asscontent)
        response = requests.post(
            "https://api.zhconvert.org/convert", headers=headers, json=json_data
        )
        data = response.text
        self.assoriginal_cht = json.loads(data)["data"]["text"]
        self.assoriginal_cht = self.clean_scriptinfo(self.assoriginal_cht, "CHT_JPN")

        generate_cht_styles: str = self.master.getconfig("generate_cht_styles")
        generate_cht_styles = generate_cht_styles.split(",")
        generate_cht_keep_comment = self.master.getconfig("generate_cht_keep_comment")
        chs_lines = (
            re.search(r"\[Events\]\n([\s\S\n]+)", self.assoriginal).group(1).split("\n")
        )
        cht_lines = (
            re.search(r"\[Events\]\n([\s\S\n]+)", self.assoriginal_cht)
            .group(1)
            .split("\n")
        )
        chs_lines = [x for x in chs_lines if x.strip()]
        cht_lines = [x for x in cht_lines if x.strip()]
        format = re.search(
            r"^(Format:.+)$",
            "\n".join(chs_lines),
            re.MULTILINE,
        ).group(1)
        for index, _ in enumerate(chs_lines):
            chs_line = chs_lines[index]
            cht_line = cht_lines[index]
            if len(generate_cht_styles) > 0:
                _stylename = self.master.get_assformat_by_key(format, chs_line, "Name")
                if _stylename in generate_cht_styles:
                    cht_lines[index] = chs_lines[index]
            if generate_cht_keep_comment:
                if (
                    cht_line.startswith("Comment:")
                    and self.master.get_assformat_by_key(
                        format, chs_line, "Effect"
                    ).lower()
                    != "karaoke"
                ):
                    cht_lines[index] = chs_lines[index]
        cht_lines = "\n".join(cht_lines)
        cht_lines = f"{cht_lines}\n".replace("\\", "\\\\")
        self.assoriginal_cht = re.sub(
            r"\[Events\]\n[\s\S\n]+",
            f"[Events]\n{cht_lines}",
            self.assoriginal_cht,
        )

        self.asschts.append(self.assoriginal_cht)

    # 日文字幕生成
    def jpconvert(self):
        generate_jpn = self.master.getconfig("generate_jpn")
        if not generate_jpn:
            self.master.log("跳过日文字幕生成")
            return
        jpn_convert = self.master.getconfig("jpn_convert")
        jpn_convert_styles_to_delete: str = self.master.getconfig(
            "jpn_convert_styles_to_delete"
        )
        jpn_convert_styles_to_delete = jpn_convert_styles_to_delete.split(",")
        self.assoriginal_jpn = self.assoriginal
        self.assoriginal_jpn = self.clean_scriptinfo(
            self.assoriginal_jpn, "JPN"
        )  # 修改 Script Info 中的 Language
        if jpn_convert:
            for jpn_convert_style_to_delete in jpn_convert_styles_to_delete:
                self.assoriginal_jpn = re.sub(
                    f"Style: ?{jpn_convert_style_to_delete},.+\n",
                    "",
                    self.assoriginal_jpn,
                )
                self.assoriginal_jpn = re.sub(
                    f"Style: ?{jpn_convert_style_to_delete}-furigana,.+\n",
                    "",
                    self.assoriginal_jpn,
                )
                self.assoriginal_jpn = re.sub(
                    f"\nDialogue:.*,{jpn_convert_style_to_delete},.*$",
                    "",
                    self.assoriginal_jpn,
                    flags=re.MULTILINE,
                )

        self.assjpns.append(self.assoriginal_jpn)

    # 多样式生成
    def generate_multistyle(self):
        _generate_multistyle = self.master.getconfig("generate_multistyle")
        if not _generate_multistyle:
            self.master.log("跳过多样式生成")
            return
        assstyles = self.master.getconfig("assstyles")
        for lang, ass in {
            "asschss": self.asschss[0],
            "asschts": self.asschts[0],
            "assjpns": self.assjpns[0],
        }.items():
            _lang = ""
            if "CHS" in lang.upper():
                _lang = "CHS_JPN"
            elif "CHT" in lang.upper():
                _lang = "CHT_JPN"
            elif "JPN" in lang.upper():
                _lang = "JPN"
            for style, _ in assstyles[_lang].items():
                if style == self.getstyle(ass):
                    continue
                generated = self.setstyle(ass, style, lang)
                getattr(self, lang).append(generated)

    # 卡拉OK模板化
    def generate_karaoke(self):
        _generate_karaoke = self.master.getconfig("generate_karaoke")
        if not _generate_karaoke:
            self.master.log("跳过卡拉OK模板化")
            return
        _nomkv = False
        if len(self.master.mkv) == 0:
            # self.master.log("未指定mkv文件，跳过卡拉OK模板化")
            # return
            _nomkv = True
        if os.path.exists(self.master.folder / "ass"):
            shutil.rmtree(self.master.folder / "ass")
        os.makedirs(self.master.folder / "ass")

        generate_language: str = self.master.getconfig("generate_language")
        generate_language = generate_language.split(",")
        scriptinfo_language: str = self.master.getconfig("scriptinfo_language")
        scriptinfo_language = scriptinfo_language.split(",")
        if not _nomkv:
            mkv_tmp = "".join(
                random.choice(
                    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                )
                for _ in range(8)
            )
            mkv_tmp = self.master.folder / "ass" / f"{mkv_tmp}.mkv"
            shutil.copy(self.master.mkv[0], mkv_tmp)
        for index, asss in enumerate([self.asschss, self.asschts, self.assjpns]):
            for ass in asss:
                filename = re.sub(
                    generate_language[0],
                    generate_language[index],
                    self.assoriginal_filename,
                )
                filename = re.sub(
                    "." + self.getstyle(self.assoriginal) + ".",
                    "." + self.getstyle(ass) + ".",
                    filename,
                )
                self.master.log(f"生成{filename}")
                karaoke_tmp = "".join(
                    random.choice(
                        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                    )
                    for _ in range(8)
                )
                karaoke_out = f"{karaoke_tmp}.out.ass"
                karaoke_tmp = f"{karaoke_tmp}.ass"
                with open(
                    self.master.folder / "ass" / f".{karaoke_tmp}",
                    "w",
                    encoding="utf-8-sig",
                ) as file:
                    file.write(ass)
                aegisub_cli_path: str = self.master.getconfig("aegisub_cli_path")
                aegisub_cli_loglevel: str = self.master.getconfig(
                    "aegisub_cli_loglevel"
                )
                command = [aegisub_cli_path]
                if not _nomkv:
                    command += [
                        "--video",
                        mkv_tmp,
                    ]
                command += [
                    "--automation",
                    "kara-templater.lua",
                    "--loglevel",
                    aegisub_cli_loglevel,
                    str(self.master.folder / "ass" / f".{karaoke_tmp}"),
                    str(self.master.folder / "ass" / f".{karaoke_out}"),
                    "Apply karaoke template",
                ]
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    universal_newlines=True,
                )
                for line in process.stdout:
                    self.master.log(line.rstrip())
                    print(line, end="")
                process.wait()
                self.clean_karaoke(
                    self.master.folder / "ass" / f".{karaoke_out}",
                    self.master.folder / "ass" / filename,
                    scriptinfo_language[index],
                )
                os.remove(self.master.folder / "ass" / f".{karaoke_tmp}")
                os.remove(self.master.folder / "ass" / f".{karaoke_out}")
                self.results.append(self.master.folder / "ass" / filename)
        if not _nomkv:
            os.remove(mkv_tmp)

    def clean_karaoke(
        self, file_path: str, output_path: str, script_info_language: str
    ):
        content = ""
        with open(file_path, "r", encoding="utf-8-sig") as file:
            content = file.read()
        content = self.clean_scriptinfo(content, script_info_language)
        content = self.clean_garbage(content)
        content = self.clean_furigana(content)
        with open(output_path, "w", encoding="utf-8-sig") as file:
            file.write(content)

    # 保存文件
    def savefiles(self):
        if len(self.assengoriginal) > 0:
            filename = self.asseng_filename
            with open(
                self.master.folder / "ass" / filename,
                "w",
                encoding="utf-8-sig",
            ) as file:
                file.write(self.assengoriginal)
            self.results.append(self.master.folder / "ass" / filename)

        _generate_karaoke = self.master.getconfig("generate_karaoke")
        if _generate_karaoke:
            return

        if os.path.exists(self.master.folder / "ass"):
            shutil.rmtree(self.master.folder / "ass")
        os.makedirs(self.master.folder / "ass")

        generate_language: str = self.master.getconfig("generate_language")
        generate_language = generate_language.split(",")
        for index, asss in enumerate([self.asschss, self.asschts, self.assjpns]):
            for ass in asss:
                filename = re.sub(
                    generate_language[0],
                    generate_language[index],
                    self.assoriginal_filename,
                )
                filename = re.sub(
                    "." + self.getstyle(self.assoriginal) + ".",
                    "." + self.getstyle(ass) + ".",
                    filename,
                )
                with open(
                    self.master.folder / "ass" / filename,
                    "w",
                    encoding="utf-8-sig",
                ) as file:
                    file.write(ass)
                self.results.append(self.master.folder / "ass" / filename)


class ASSFont:
    def __init__(self, master):
        self.styles = {}
        self.dialogues = []
        self.fonts = {}
        self.filecontent = ""
        self.get_assformat_by_key = master.get_assformat_by_key

    # 读取字幕文件
    def readfile(self, assfile: Path):
        with open(assfile, "r", encoding="utf-8-sig") as file:
            self.filecontent = file.read()

    # 读取字幕样式
    def readstyles(self):
        styles = re.findall(r"^(Style:.+)$", self.filecontent, re.MULTILINE)
        for style in styles:
            match = re.search(r"^Style: ?([^,]*),([^,]*)", style)
            self.styles[match.group(1)] = match.group(2)

    # 读取字幕行
    def readdialogues(self):
        format = re.search(
            r"^(Format:.+)$",
            re.search(r"\[Events\]\n([\s\S\n]+)", self.filecontent).group(1),
            re.MULTILINE,
        ).group(1)
        dialogues = re.findall(r"^(Dialogue:.+)$", self.filecontent, re.MULTILINE)
        for dialogue in dialogues:
            self.dialogues.append(
                {
                    "style": self.get_assformat_by_key(format, dialogue, "Style"),
                    "content": self.get_assformat_by_key(format, dialogue, "Text"),
                }
            )

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

    # 收集字体
    def collectfont(self):
        for dialogue in self.dialogues:
            default_style = dialogue["style"]
            content = dialogue["content"]
            if r"\p1" in content:
                content = self.cleandraw(content)
            if r"\fn" in content:
                self.collectfontbypart(self.styles[default_style], content)
                continue
            self.addfont(self.styles[default_style], content)


class ASSFunUI(Tk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        self.geometry("600x500")
        self.minsize(600, 500)
        self.title("ASSFont - KyokuSai")
        self.iconbitmap(resource_path("favicon.ico"))

        self.grid_columnconfigure([0, 1, 2], weight=1)

        if getattr(sys, "frozen", False):
            self.folder = os.path.abspath(os.path.dirname(sys.executable))
        else:
            self.folder = os.path.abspath(os.path.dirname(__file__))
        self.folder: Path = Path(self.folder)
        self.cache = {}
        self.cache_file = self.folder / "data" / "cache.json"
        self.config = {}
        self.config_file = self.folder / "data" / "config.json"
        self.assstyles = {}
        ctk.FontManager.load_font(resource_path("NotoSansSC-Medium.otf"))
        self.font = ctk.CTkFont(family="NotoSansSC-Medium", size=18, weight="normal")
        self.mkv: list[Path] = []
        self.files: list[Path] = []
        self.asss: list[Path] = []
        self.eng: list[Path] = []
        self.values = {}
        self.configwindow = None

        self.style_CTkTextbox = dict(
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
        self.after(10, self._create_widgets)
        self.after(250, self._init)

    def _create_widgets(self):
        row = 0

        self.mkvbox = ctk.CTkTextbox(self, height=25, **self.style_CTkTextbox)
        self.mkvbox.grid(
            row=row, column=0, padx=16, pady=(10, 5), sticky="ew", columnspan=3
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
        row = row + 1

        self.filebox = ctk.CTkTextbox(self, height=175, **self.style_CTkTextbox)
        self.filebox.grid(
            row=row, column=0, padx=16, pady=(5, 5), sticky="ew", columnspan=3
        )
        self.filebox.drop_target_register(DND_ALL)
        self.filebox.dnd_bind(
            "<<Drop>>", partial(self.file_drop, box=self.filebox, files="files")
        )
        self.filebox.insert(ctk.END, "拖入字幕文件")
        self.filebox.configure(state="disabled")
        row = row + 1

        self.engbox = ctk.CTkTextbox(self, height=25, **self.style_CTkTextbox)
        self.engbox.grid(
            row=row, column=0, padx=16, pady=(10, 5), sticky="ew", columnspan=3
        )
        self.engbox.drop_target_register(DND_ALL)
        self.engbox.dnd_bind(
            "<<Drop>>",
            partial(
                self.file_drop,
                box=self.engbox,
                format="ass",
                files="eng",
                multiple=False,
            ),
        )
        self.engbox.insert(ctk.END, "拖入单独英语字幕文件(如果有)")
        self.engbox.configure(state="disabled")
        row = row + 1

        _check = Check(self, key="assgenerate", label="字幕生成", default=False)
        self.assgenerate_check = _check
        _check.grid(row=row, column=0, padx=(16, 2), pady=(5, 0), sticky=ctk.N)
        _check = Check(self, key="subset", label="子集化字体", default=True)
        _check.grid(row=row, column=1, padx=(2, 2), pady=(5, 0), sticky=ctk.N)
        _check = Check(self, key="usecache", label="使用缓存", default=True)
        _check.grid(row=row, column=2, padx=(2, 16), pady=(5, 0), sticky=ctk.N)
        self.cache_check = _check
        row = row + 1

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
            row=row, column=0, padx=16, pady=(10, 5), sticky="ew", columnspan=3
        )
        self.grid_rowconfigure([row], weight=1)
        row = row + 1

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
            row=row, column=0, padx=(16, 16), pady=(5, 10), sticky="nws", columnspan=1
        )

        self.button = ctk.CTkButton(
            self,
            text="开始",
            command=self.startbythreading,
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
            row=row,
            column=0,
            padx=(16 + 22 + 2 * 2 + 12, 16),
            pady=(5, 10),
            sticky="ew",
            columnspan=3,
        )

    def _init(self):
        self.log("-- 日志记录 --")

        def global_exception(exc_type, exc_value, exc_traceback):
            self.log("Error:")
            self.log(str(exc_type))
            self.log(str(exc_value))
            self.log(str(exc_traceback))
            print(exc_type)
            print(exc_value)
            print(exc_traceback)

        sys.excepthook = global_exception
        self.getcache(init=True)
        self.setconfig()

        proxy_port = self.getconfig("proxy")
        if proxy_port != "0":
            proxy_address = f"http://127.0.0.1:{proxy_port}"
            os.environ["HTTP_PROXY"] = proxy_address
            os.environ["HTTPS_PROXY"] = proxy_address
            self.log(f"使用代理：{proxy_address}")

    def startbythreading(self):
        def _start():
            self.start()
            # try:
            #     self.start()
            # except Exception as e:
            #     print(e)
            #     sys.excepthook(*sys.exc_info())

        task_thread = threading.Thread(target=_start)
        task_thread.start()

    def get_assformat_by_key(self, format: str, content: str, key: str) -> str:
        format = format.replace(" ", "").split(",")
        index = format.index(key)
        content = content.split(",")
        value = content[index]
        if key == "Text":
            value = ",".join(content[index:])
        value = re.sub(r"^ ", "", value)
        return value

    def file_drop(
        self,
        event,
        box: ctk.CTkTextbox,
        files: str,
        format: str = "ass",
        multiple: bool = True,
    ):
        box.configure(state="normal")
        matches = re.findall(r"\{(.*?)\}|([^\s]+)", event.data)
        _files = [m[0] if m[0] else m[1] for m in matches]
        for index, file in enumerate(_files):
            if not file.lower().endswith(f".{format}"):
                continue
            if not multiple and index != len(_files) - 1:
                continue
            if not multiple:
                setattr(self, files, [])
            getattr(self, files).append(Path(file))
        box.delete(1.0, ctk.END)
        box.insert(ctk.END, "\n".join(map(str, getattr(self, files))))
        box.yview(ctk.END)
        box.configure(state="disabled")

        if len(self.files) == 1:
            self.assgenerate_check.toggle(master=self, value=True)
            self.assgenerate_check.getself().configure(state="normal")
        elif len(self.files) > 1:
            self.assgenerate_check.toggle(master=self, value=False)
            self.assgenerate_check.getself().configure(state="disabled")

    def log(self, text: str):
        self.logbox.configure(state="normal")
        self.logbox.insert(ctk.END, text + "\n")
        self.logbox.yview(ctk.END)
        self.logbox.configure(state="disabled")
        print(text)

    def getassfonts(self) -> dict:
        assfont = ASSFont(master=self)
        for file in self.files:
            self.log(f"处理文件：{file}")
            _assfont = ASSFont(master=self)
            _assfont.readfile(file)
            _assfont.readstyles()
            _assfont.readdialogues()
            _assfont.collectfont()
            assfont.mergefonts(_assfont.fonts)
        assfont.remove_duplicates()
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

        def getName(names, nameID, platformID, platEncID, langID=None):
            namerecords = []
            for namerecord in names.names:
                if (
                    namerecord.nameID == nameID
                    and namerecord.platformID == platformID
                    and namerecord.platEncID == platEncID
                ):
                    if langID is None or namerecord.langID == langID:
                        namerecords.append(namerecord)
            return namerecords

        font_dir = os.path.join(os.environ.get("SystemRoot", "C:\\"), "Fonts")
        font_paths = []
        for root, _, files in os.walk(font_dir):  # 有一些字体是在子文件夹中
            for file in files:
                file_path = os.path.join(root, file)
                font_paths.append(file_path)
        for font_path in font_paths:
            filename: str = os.path.basename(font_path)
            if filename.lower().endswith((".ttf", ".otf", ".ttc")):
                try:
                    fonts = []
                    if filename.lower().endswith(".ttc"):
                        fonts = TTCollection(font_path).fonts
                    else:
                        font = TTFont(font_path)
                        fonts = [font]
                    for font in fonts:
                        names = font["name"]
                        names = [
                            name.toStr()
                            for name in [
                                *getName(names, 1, 3, 1),
                                *getName(names, 4, 3, 1),
                                *getName(names, 1, 1, 25),
                                *getName(names, 4, 3, 25),
                            ]
                            if name is not None
                        ]
                        names = list({name for name in names if name is not None})
                        if font_path in self.cache:
                            self.cache[font_path].extend(names)
                        else:
                            self.cache[font_path] = names
                    if not filename.lower().endswith(".ttc"):
                        font.close()
                except Exception as e:
                    self.log(f"字体读取错误：{e}")

        self.cache_check.toggle(master=self, value=True)
        self.cache_check.getself().configure(state="normal")

    # 读取字体信息缓存
    def getcache(self, init: bool = False):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8-sig") as json_file:
                self.cache = json.load(json_file)
        else:
            if init:
                self.cache_check.toggle(master=self, value=False)
                self.cache_check.getself().configure(state="disabled")

    # 保存字体信息
    def savecache(self):
        if not os.path.exists(self.folder / "data"):
            os.makedirs(self.folder / "data")
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        with open(self.cache_file, "w", encoding="utf-8-sig") as json_file:
            json.dump(self.cache, json_file, ensure_ascii=False)

    # 初始化程序设置
    def initconfig(self, _return: bool = False):
        config = {
            "mkvmerge_path": "D:/path/to/mkvmerge.exe",
            "filename_ext": "[{res}P][WEBRip][HEVC 10bit]",
            "mkvoutputdir": "",
            "videotrack_lang": "ja",
            "videotrack_name": "WEBRip by KyokuSaiYume",
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
            "assengtrack_symbol": "[ENG]",
            "assengtrack_lang": "en",
            "assengtrack_name": "English-ENG",
            "asstrackname_separator": " - ",
            "assmultistyle_defaulttrack": "kawaii",
            "fontsubset_warning": "请勿安装此子集化字体 - ",
            "clean_scriptinfo": True,
            "clean_garbage": True,
            "clean_furigana": True,
            "clean_space": True,
            "clean_all_space": False,
            "unicode_to_utf8": True,
            "scriptinfo": "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nLayoutResX: 1920\nLayoutResY: 1080\nWrapStyle: 0\nScaledBorderAndShadow: yes\nYCbCr Matrix: TV.709\nOriginal Script: 極彩花夢\nLanguage: {LANGUAGE}",
            "scriptinfo_language": "CHS_JPN,CHT_JPN,JPN",
            # "assstyles": {},
            "optional_styles": "Sx-en,Ex-lrc | op_jp,Ex-lrc | op_zh,Ex-lrc | op_en,Ex-lrc | ed_jp,Ex-lrc | ed_zh,Ex-lrc | ed_en",
            "generate_cht": True,
            "generate_cht_styles": "Sx-zh,Rx-annotation",
            "generate_cht_keep_comment": True,
            "zhconvert_json": '{"text":"{ASSCONTENT}","apiKey":"","ignoreTextStyles":"Ex-KSY,Ex-invisible","jpTextStyles":"Sx-jp,*noAutoJpTextStyles","jpTextConversionStrategy":"protectOnlySameOrigin","jpStyleConversionStrategy":"protectOnlySameOrigin","modules":"{\\"ChineseVariant\\":\\"0\\",\\"Computer\\":\\"0\\",\\"EllipsisMark\\":\\"0\\",\\"EngNumFWToHW\\":\\"0\\",\\"GanToZuo\\":\\"-1\\",\\"Gundam\\":\\"0\\",\\"HunterXHunter\\":\\"0\\",\\"InternetSlang\\":\\"-1\\",\\"Mythbusters\\":\\"0\\",\\"Naruto\\":\\"0\\",\\"OnePiece\\":\\"0\\",\\"Pocketmon\\":\\"0\\",\\"ProperNoun\\":\\"-1\\",\\"QuotationMark\\":\\"0\\",\\"RemoveSpaces\\":\\"0\\",\\"Repeat\\":\\"-1\\",\\"RepeatAutoFix\\":\\"-1\\",\\"Smooth\\":\\"-1\\",\\"TengTong\\":\\"0\\",\\"TransliterationToTranslation\\":\\"0\\",\\"Typo\\":\\"-1\\",\\"Unit\\":\\"-1\\",\\"VioletEvergarden\\":\\"0\\"}","userPostReplace":"","userPreReplace":"","userProtectReplace":"","diffCharLevel":0,"diffContextLines":1,"diffEnable":0,"diffIgnoreCase":0,"diffIgnoreWhiteSpaces":0,"diffTemplate":"Inline","cleanUpText":0,"ensureNewlineAtEof":0,"translateTabsToSpaces":-1,"trimTrailingWhiteSpaces":0,"unifyLeadingHyphen":0,"converter":"Traditional"}',
            "generate_jpn": True,
            "jpn_convert": False,
            "jpn_convert_styles_to_delete": "Sx-zh,Rx-annotation",
            "generate_multistyle": True,
            "generate_karaoke": True,
            "generate_language": "CHS_JPN,CHT_JPN,JPN",
            "aegisub_cli_path": "D:/path/to/aegisub-cli.exe",
            "aegisub_cli_loglevel": "2",
            "proxy": "0",
        }
        if _return:
            return config
        self.config = config
        self.saveconfig()

    # 读取程序设置
    def setconfig(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8-sig") as json_file:
                self.config = json.load(json_file)
        else:
            self.initconfig()

    # 获取程序设置
    def getconfig(self, key):
        if key == "assstyles":
            if len(self.assstyles) != 0:
                return self.assstyles
            else:
                assstyles = {}
                for root, _, files in os.walk(self.folder / "assstyles"):
                    for file in files:
                        if file.endswith(".json"):
                            assstyles[file] = os.path.join(root, file)
                if len(assstyles) == 0:
                    self.log("※样式表文件不存在")
                    return {}
                _select = SelectWindow(
                    self,
                    title="选择样式表",
                    selects=[assstyle for assstyle, _ in assstyles.items()],
                )
                assstyles_file = assstyles[_select.get_result()]
                with open(assstyles_file, "r", encoding="utf-8-sig") as json_file:
                    self.assstyles = json.load(json_file)
                for _lang, _ in self.assstyles.items():
                    for _style, _ in self.assstyles[_lang].items():
                        if len(self.assstyles[_lang][_style]) == 0:
                            self.assstyles[_lang][_style] = self.assstyles["CHS_JPN"][
                                _style
                            ]
                return self.assstyles
        elif key not in self.config:
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
        if not os.path.exists(self.folder / "data"):
            os.makedirs(self.folder / "data")
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        with open(self.config_file, "w", encoding="utf-8-sig") as json_file:
            json.dump(self.config, json_file, ensure_ascii=False)

    # 打开设置窗口
    def openconfigwindow(self):
        if self.configwindow is None or not self.configwindow.winfo_exists():
            self.configwindow = ConfigWindow(self)
        else:
            self.configwindow.focus()

    # 子集化字体
    def subset(
        self,
        fontname: str,
        fontfile: str,
        characters: str,
        newname: str,
        outputpath: str,
    ):
        subsetoptions = subset.Options(
            name_languages="*",
            # recalc_timestamp=True,
        )
        if fontfile.lower().endswith(".ttc"):
            ttc = TTCollection(fontfile)
            ttfs = ttc.fonts
            for ttf in ttfs:
                names = ttf["name"]
                names = [
                    names.getName(1, 3, 1),
                    names.getName(4, 3, 1),
                    names.getName(1, 1, 25),
                    names.getName(4, 1, 25),
                ]
                names = [name.toStr() for name in names if name is not None]
                if fontname in names:
                    fontfile = io.BytesIO()
                    ttf.save(fontfile)
                    fontfile.seek(0)
                    break
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
        with open(filepath, "r", encoding="utf-8-sig") as file:
            file_content = file.read()

        part1 = re.search(r"([\s\S]+)\n\[Events\]\n", file_content, re.MULTILINE)
        part1 = part1.group(1)
        part2 = re.search(r"\n\[Events\]\n([\s\S]+)", file_content, re.MULTILINE)
        part2 = part2.group(1)
        for key in sorted(replacedict, key=lambda n: len(n), reverse=True):
            part1 = part1.replace(key, replacedict[key])
            part2 = part2.replace(f"\\fn{key}", f"\\fn{replacedict[key]}")
            file_content = f"{part1}\n[Events]\n{part2}"

        with open(outputpath, "w", encoding="utf-8-sig") as file:
            file.write(file_content)

    def get_resolution(self, mkv: Path) -> tuple[int, int]:
        media_info = MediaInfo.parse(mkv)
        for track in media_info.tracks:
            if track.track_type == "Video":
                return track.width, track.height
        return None, None

    # 开始
    def start(self):
        self.log(f"当前设置：{self.values}")
        mkv = self.mkv[0] if len(self.mkv) > 0 else ""
        self.log(f"mkv: {mkv}")
        self.log(f"ass: {self.files}")
        if self.values["usecache"]:
            self.log(f"使用缓存数据")
            self.getcache()
        else:
            self.log(f"读取字体……")
            self.generatecache()
            self.savecache()
        # 字幕生成
        if self.values["assgenerate"]:
            self.log("开始字幕生成")
            assgenerate = ASSGenerate(master=self)
            self.log("读取原始字幕文件")
            assgenerate.readfile(self.files[0])
            self.log("清理 Script Info")
            assgenerate.assoriginal = assgenerate.clean_scriptinfo(
                assgenerate.assoriginal, language="CHS_JPN"
            )
            self.log("清理 Aegisub Project Garbage")
            assgenerate.assoriginal = assgenerate.clean_garbage(assgenerate.assoriginal)
            self.log("清理 furigana")
            assgenerate.assoriginal = assgenerate.clean_furigana(
                assgenerate.assoriginal
            )
            self.log("清理空格")
            assgenerate.assoriginal = assgenerate.clean_space(assgenerate.assoriginal)
            self.log("Unicode 码点转换 UTF-8")
            assgenerate.assoriginal = assgenerate.unicode_to_utf8(
                assgenerate.assoriginal
            )
            self.log("完成简中处理")
            assgenerate.chsconfirm()
            self.log("进行繁化")
            assgenerate.zhconvert()
            self.log("进行日文字幕生成")
            assgenerate.jpconvert()
            self.log("进行多样式生成")
            assgenerate.generate_multistyle()
            self.log("进行卡拉OK模板化")
            assgenerate.generate_karaoke()
            if len(self.eng) > 0:
                self.log("处理英语字幕")
                assgenerate.readengfile(self.eng[0])
                assgenerate.assengoriginal = assgenerate.clean_scriptinfo(
                    assgenerate.assengoriginal, language="ENG"
                )
                assgenerate.assengoriginal = assgenerate.clean_garbage(
                    assgenerate.assengoriginal
                )
                assgenerate.assengoriginal = assgenerate.clean_furigana(
                    assgenerate.assengoriginal
                )
                assgenerate.assengoriginal = assgenerate.clean_space(
                    assgenerate.assengoriginal
                )
                assgenerate.assengoriginal = assgenerate.unicode_to_utf8(
                    assgenerate.assengoriginal
                )
            self.log("保存生成字幕")
            assgenerate.savefiles()
            self.files = assgenerate.results
        # 字体处理
        fonts = self.getassfonts()
        if os.path.exists(self.folder / "result"):
            shutil.rmtree(self.folder / "result")
        os.makedirs(self.folder / "result")
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
                        random.choice(
                            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                        )
                        for _ in range(8)
                    )
                    replacedict[font] = f"{fontsubset_warning}{randomstr}"
                    real_fontpath = self.folder / "result" / f"{font} - {randomstr}.ttf"
                    self.subset(
                        font,
                        font_path,
                        content,
                        replacedict[font],
                        real_fontpath,
                    )
                    real_fontpaths.append(real_fontpath)
                    with open(
                        self.folder / "result" / f".{font}.txt",
                        "w",
                        encoding="utf-8-sig",
                    ) as file:
                        file.write(content)
                else:
                    self.log(f'※"{font}" 的字体文件未能找到。')
                    return
            for file in self.files:
                filename = os.path.basename(file)
                self.asssubsetfix(file, self.folder / "result" / filename, replacedict)
            self.log(f"字幕字体处理完毕。共 {len(fonts)} 个字体。")
        else:
            self.asss = self.files
            for font, _ in fonts.items():
                self.log(f"查找字体：{font}")
                font_path, font_file = self.getfontfile(font)
                if font_path:
                    shutil.copy(font_path, self.folder / "result" / font_file)
                    real_fontpaths.append(self.folder / "result" / font_file)
                else:
                    self.log(f'※"{font}" 的字体文件未能找到。')
                    return
            self.log(f"字幕字体处理完毕。共 {len(fonts)} 个字体。")
        # 混流
        if mkv:
            self.asss = sorted(self.asss, key=lambda x: os.path.basename(x))
            self.log(f"开始自动混流")
            mkvmerge_path = self.getconfig("mkvmerge_path")
            title = re.sub(r"\.mkv$", "", os.path.basename(mkv))
            videotrack_resolution = self.get_resolution(mkv)
            filename_ext = self.getconfig("filename_ext")
            filename_ext = re.sub(
                r"\{res\}", str(videotrack_resolution[1]), filename_ext
            )
            outputdir = self.getconfig("mkvoutputdir")
            if len(outputdir) == 0:
                outputdir = os.path.dirname(mkv)
            if not outputdir.endswith("\\"):
                outputdir = f"{outputdir}\\"
            outputfile = f"{title} {filename_ext}.mkv"
            if title.endswith("]"):
                outputfile = f"{title}{filename_ext}.mkv"
            videotrack_lang: str = self.getconfig("videotrack_lang")
            videotrack_name: str = self.getconfig("videotrack_name")
            audiotrack_delay: str = self.getconfig("audiotrack_delay")
            audiotrack_lang: str = self.getconfig("audiotrack_lang")
            audiotrack_name: str = self.getconfig("audiotrack_name")
            asschsjpntrack_symbol: str = self.getconfig("asschsjpntrack_symbol")
            asschsjpntrack_lang: str = self.getconfig("asschsjpntrack_lang")
            asschsjpntrack_name: str = self.getconfig("asschsjpntrack_name")
            asschtjpntrack_symbol: str = self.getconfig("asschtjpntrack_symbol")
            asschtjpntrack_lang: str = self.getconfig("asschtjpntrack_lang")
            asschtjpntrack_name: str = self.getconfig("asschtjpntrack_name")
            assjpntrack_symbol: str = self.getconfig("assjpntrack_symbol")
            assjpntrack_lang: str = self.getconfig("assjpntrack_lang")
            assjpntrack_name: str = self.getconfig("assjpntrack_name")
            assengtrack_symbol: str = self.getconfig("assengtrack_symbol")
            assengtrack_lang: str = self.getconfig("assengtrack_lang")
            assengtrack_name: str = self.getconfig("assengtrack_name")
            asstrackname_separator: str = self.getconfig("asstrackname_separator")
            assmultistyle_defaulttrack: str = self.getconfig(
                "assmultistyle_defaulttrack"
            )
            _select = SelectWindow(
                self,
                title="选择默认字幕样式",
                selects=set().union(*(v.keys() for v in self.assstyles.values())),
                default=assmultistyle_defaulttrack,
            )
            assmultistyle_defaulttrack = _select.get_result()
            fontsubset_warning: str = self.getconfig("fontsubset_warning")
            asstrack: dict[str, list[str, str]] = {
                asschsjpntrack_symbol: [asschsjpntrack_lang, asschsjpntrack_name],
                asschtjpntrack_symbol: [asschtjpntrack_lang, asschtjpntrack_name],
                assjpntrack_symbol: [assjpntrack_lang, assjpntrack_name],
            }
            if len(self.eng) > 0:
                asstrack[assengtrack_symbol] = [assengtrack_lang, assengtrack_name]
            cmd = f'start "mkvmux" "{mkvmerge_path}" --ui-language zh_CN --priority lower '
            cmd += f'--output ^"{outputdir}{outputfile}^" '
            cmd += f"--no-subtitles --no-attachments "
            cmd += f'--language 0:{videotrack_lang} --track-name ^"0:{videotrack_name}^" --display-dimensions 0:{videotrack_resolution[0]}x{videotrack_resolution[1]} '
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
                        is_unique = sum(_symbol in str(_item) for _item in self.asss)
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
                if track_lang == assengtrack_symbol:
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
        self.eng = []
        self.engbox.configure(state="normal")
        self.engbox.delete(1.0, ctk.END)
        self.engbox.insert(ctk.END, "拖入单独英语字幕文件(如果有)")
        self.engbox.yview(ctk.END)
        self.engbox.configure(state="disabled")
        self.assstyles = {}


if __name__ == "__main__":
    ui = ASSFunUI()
    ui.mainloop()
