import yaml
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

config_dict = yaml.safe_load(
    open('Source/config.yaml')
)

def initPallet(window):
    # 导入准备在托盘化显示上使用的图标
    icons = config_dict['Icon']

    # 新建一个菜单项控件
    menu = QMenu(window)

    # 设置托盘菜单项
    actions = {
        "quit": QAction('退出', window, triggered=window.quit), # 菜单项退出，点击后调用quit函数
        "show": QAction('显示', window, triggered=lambda: window.setWindowOpacity(1)), # 菜单项显示，点击后调用showing函数
        "hide": QAction('隐藏', window, triggered=lambda: window.setWindowOpacity(0)), # 菜单项隐藏，点击后调用hide函数
    }

    # 设置点击选项的图片
    # quit_action.setIcon(QIcon(icons))

    # 将菜单项添加到菜单中
    for key in actions:
        action = actions[key]
        menu.addAction(action)

    # 配置图标并展示
    menu_icon = QSystemTrayIcon(window)
    menu_icon.setIcon(QIcon(icons)) # 设置托盘图标
    menu_icon.setContextMenu(menu) # 设置托盘菜单
    menu_icon.show() # 展示