# AutoTypist

这是一个 Windows 图形界面工具，可输入多行文字，设置启动等待时间和逐字符打字间隔，并在倒计时结束后向当前活动窗口模拟键盘输入。程序不使用剪贴板；等待时间和打字间隔可通过输入框旁的上下箭头调节。等待时间范围为 0 到 86400 秒，步进 1 秒；打字间隔范围为 0.01 到 10 秒，步进 0.01 秒。

界面采用黑白灰配色，并在启动 Tk 窗口前启用 Windows 高 DPI 感知；默认窗口尺寸约为之前的一半，并随显示 DPI 缩放。等待时间和打字间隔用数值旁边上下排列的 ▲/▼ 按钮调节，分别按 1 秒和 0.01 秒步进。

## 运行源码

```powershell
python -m pip install -r requirements.txt
python type_text.py
```

## 打包为单文件 EXE

```powershell
python -m PyInstaller --clean --noconfirm --onefile --windowed --name AutoTypist type_text.py
```

生成的程序位于 `dist\AutoTypist.exe`。启动后点击“开始输入”，并在倒计时内切换到需要输入文字的窗口。输入期间将鼠标移到屏幕左上角可紧急停止。模拟键盘输入是逐字符发送的，输入期间目标窗口必须保持可接收键盘输入。
