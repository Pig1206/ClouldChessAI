import tkinter as tk
import json
import datetime as dt
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import random as rd
import files.CCS_Core_Code2 as C3
from files.CCS_CEI import eng_chn_li
from tkinter import ttk
import socket
import threading
from tkinter import font
from PIL import ImageFont
from files.hash_PSD import hash
from tkinter import simpledialog

#字体初始化
prf, prz, prh = ImageFont.truetype('fonts\\simfang.TTF'), ImageFont.truetype('fonts\\simzhong.ttf'), ImageFont.truetype('fonts\\simhei.ttf')
pf, pz, ph = prf.getname()[0], prz.getname()[0], prh.getname()[0]

jd_st=0
def start_win():
    def start_main_program():
        start_window.destroy()  # 关闭启动界面
        FQAI_all_code()  # 启动主程序
    def cheng_jd():
        global jd_st
        jd_st+=2
        version_label.config(text='-  '+str(jd_st) +' %  -')
        if jd_st>=100:
            start_main_program()
        else:
            start_window.after(30, cheng_jd)
    # 创建启动界面
    start_window = tk.Tk()
    start_window.geometry('250x100+500+300')
    start_window.configure(bg='light cyan')
    start_window.resizable(False, False)
    start_window.overrideredirect(True)
    img = Image.open('images\\云棋AI-PNG.png')
    img2 = ImageTk.PhotoImage(img)
    bg1 = tk.Label(start_window, image=img2, bg='light cyan')
    bg1.place(x=0, y=-1)
    # 欢迎信息
    welcome_label = tk.Label(start_window, text='云棋AI(v2.5.1)', bg='light cyan', font=font.Font(family=pf,size=15))
    welcome_label.place(x=90, y=20)

    # 版本信息
    version_label = tk.Label(start_window, text='-  0 %  -', bg='light cyan',font=font.Font(family=pf,size=13))
    version_label.place(x=120, y=55)
    cheng_jd()
    # 运行启动界面
    start_window.mainloop()

#核心算法
class CCScore(C3.CCScore):
    def __init__(self, chess, difficulty=3, ai_player=2):
        super().__init__(chess, difficulty)
        self.ai_player = ai_player  # AI的棋子颜色
        self.human_player = 1

def check(board):
    board_size = len(board)
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 水平、垂直、对角线

    # 遍历整个棋盘
    for y in range(board_size):
        for x in range(board_size):
            if board[y][x] == 0:
                continue

            player = board[y][x]
            # 检查四个方向
            for dx, dy in directions:
                count = 1
                # 正向检查
                for i in range(1, 5):
                    nx, ny = x + dx * i, y + dy * i
                    if 0 <= nx < board_size and 0 <= ny < board_size and board[ny][nx] == player:
                        count += 1
                    else:
                        break
                # 如果找到五连珠，直接返回获胜方
                if count >= 5:
                    return player
    return None

#读取用户数据
f1 = open('images\\YQ_DataBase.json', 'r')
ms = json.loads(f1.read())
f1.close()

# 全局变量初始化
bg = 'yellow'    # 背景色
num = 0          # 步数计数器
q = [[0 for _ in range(11)] for _ in range(11)]     # 棋盘状态（16位字符串，0为空，1为玩家，2为AI）
s_n = 4          # 剩余登录尝试次数
play_num = 1     # 游戏模式（1-AI先手，2-AI后手，3-双人）
play_state = 0   # 游戏状态（0-未开始，1-进行中）
num2_state = 0   # 双人模式回合状态
up_state = 0     # 界面状态（0-主界面，1-个人信息，2-关于）
eng_chn = 0      # 语言切换
person = {}      # 当前登录用户信息
model = 'MTCS 1.0(中等)'  #模型选择
multiplayer_mode = 0  # 0-线下对战, 1-联机对战(主机), 2-联机对战(客户端)
connection = None  # 网络连接对象
server='12345'

d = eng_chn_li[2][eng_chn]    # 密码显示状态
d2 = eng_chn_li[2][eng_chn]   # 密码显示状态

def FQAI_all_code():
    win = tk.Tk()
    win.geometry('320x370+120+120')
    win.title(eng_chn_li[0][eng_chn])
    win.config(background='light cyan')
    win.resizable(False,False)
    win.iconbitmap('images\\云棋AI.ico')
    img = Image.open(eng_chn_li[1][eng_chn])
    img2 = ImageTk.PhotoImage(img)
    bg1 = tk.Label(win, image=img2, bg='light cyan')
    bg1.place(x=-1, y=-3)

    def change():
        global d
        if d == eng_chn_li[2][eng_chn]:
            d = eng_chn_li[3][eng_chn]
            de.config(text=d)
            mm.config(show='')
        elif d == eng_chn_li[3][eng_chn]:
            d = eng_chn_li[2][eng_chn]
            de.config(text=d)
            mm.config(show='•')

    def eng_chn_chg():
        global eng_chn, d, d2
        if eng_chn == 0:
            eng_chn = 1
        elif eng_chn == 1:
            eng_chn = 0
        d = eng_chn_li[2][eng_chn]    # 密码显示状态
        d2 = eng_chn_li[2][eng_chn]   # 密码显示状态
        win.destroy()
        FQAI_all_code()

    def cstart():
        global s_n, ms, person
        if name2.get() != '' and mm.get() != '':
            if name2.get() in ms.keys():
                sal, has = ms[name2.get()]['password'].split(':')
                if hash(mm.get(), sal)[1] == has:
                    person = ms[name2.get()]
                    def run_CCS():
                        def change_C(n):
                            global num, play_num, play_state, q, num2_state, person, connection, multiplayer_mode

                            if play_state == 1:
                                if eval('cn'+str(n))['text'] != '○' and eval('cn'+str(n))['text'] != '●':
                                    if play_num == 1 or play_num==2:
                                        ns = n - 1
                                        row = ns // 11
                                        col = ns % 11
                                        q[row][col] = 1  # 玩家落子
                                        eval('cn' + str(n)).config(text='●')
                                        if check(q) == 1:
                                            messagebox.showinfo('获胜结果', '您获胜!')
                                            play_state = 0
                                            num2_state = 0
                                            f1 = open('images\\YQ_DataBase.json', 'r')
                                            rt = json.loads(f1.read())
                                            f1.close()
                                            rt[person['name']]['win_num'] += 1
                                            with open('images\\YQ_DataBase.json', 'w') as f2:
                                                f2.writelines(json.dumps(rt))
                                            person['win_num'] += 1
                                        if play_state == 1:
                                            #算法调用
                                            if model == 'MNX 1.3(较简单)':
                                                loc = CCScore(q, difficulty=6).find_best_move()
                                                q[loc[1]][loc[0]] = 2
                                                eval('cn' + str(loc[1]*11+loc[0]+1)).config(text='○')
                                            elif model == 'MTCS 1.0(中等)':
                                                loc = CCScore(q, difficulty=7).find_best_move()
                                                q[loc[1]][loc[0]] = 2
                                                eval('cn' + str(loc[1]*11+loc[0]+1)).config(text='○')
                                            elif model == 'PBS 2.1(较难)':
                                                loc = CCScore(q, difficulty=9).find_best_move()
                                                q[loc[1]][loc[0]] = 2
                                                eval('cn' + str(loc[1]*11+loc[0]+1)).config(text='○')
                                            elif model == 'RDM 1.1(简单)':
                                                loc = CCScore(q, difficulty=4).find_best_move()
                                                q[loc[1]][loc[0]] = 2
                                                eval('cn' + str(loc[1]*11+loc[0]+1)).config(text='○')
                                        if check(q) == 2:
                                            messagebox.showinfo('获胜结果', 'AI获胜!')

                                            #双人对战
                                    if play_num == 3:
                                        if multiplayer_mode == 0:  # 线下对战
                                            if num % 2 == 0:
                                                ns = n - 1
                                                q[ns // 11][n % 11-1] = 1
                                                eval('cn' + str(n)).config(text='○')
                                                if check(q) == 1:
                                                    messagebox.showinfo('获胜结果', '玩家1获胜!')
                                                    play_state = 0
                                            else:
                                                ns = n - 1
                                                q[ns // 11][n % 11-1] = 2
                                                eval('cn' + str(n)).config(text='●')
                                                if check(q) == 2:
                                                    messagebox.showinfo('获胜结果', '玩家2获胜!')
                                                    play_state = 0
                                            num += 1

                                        elif multiplayer_mode == 1:  # 联机对战(主机)
                                            if num % 2 == 0:  # 主机回合
                                                ns = n - 1
                                                q[ns // 11][n % 11-1] = 1
                                                eval('cn' + str(n)).config(text='○')
                                                if check(q) == 1:
                                                    messagebox.showinfo('获胜结果', '您获胜!')
                                                    play_state = 0
                                                    f1 = open('images\\YQ_DataBase.json', 'r')
                                                    rt = json.loads(f1.read())
                                                    f1.close()
                                                    rt[person['name']]['win_num'] += 1
                                                    with open('images\\YQ_DataBase.json', 'w') as f2:
                                                        f2.writelines(json.dumps(rt))
                                                    person['win_num'] += 1
                                                try:
                                                    connection.send(str(n).encode())
                                                except:
                                                    messagebox.showerror("错误", "连接已断开")
                                                    play_state = 0
                                            num += 1

                                        elif multiplayer_mode == 2:  # 联机对战(客户端)
                                            if num % 2 == 1:  # 客户端回合
                                                ns = n - 1
                                                q[ns // 11][n % 11-1] = 2
                                                eval('cn' + str(n)).config(text='●')
                                                if check(q) == 2:
                                                    messagebox.showinfo('获胜结果', '您获胜!')
                                                    play_state = 0
                                                    f1 = open('images\\YQ_DataBase.json', 'r')
                                                    rt = json.loads(f1.read())
                                                    f1.close()
                                                    rt[person['name']]['win_num'] += 1
                                                    with open('images\\YQ_DataBase.json', 'w') as f2:
                                                        f2.writelines(json.dumps(rt))
                                                    person['win_num'] += 1
                                                try:
                                                    connection.send(str(n).encode())
                                                except:
                                                    messagebox.showerror("错误", "连接已断开")
                                                    play_state = 0
                                            num += 1

                        def receive_move():
                            global num, q, play_state, connection
                            while play_state == 1 and play_num == 3 and multiplayer_mode in [1, 2]:
                                try:
                                    data = connection.recv(1024).decode()
                                    if not data:
                                        break
                                    n = int(data)
                                    ns = n - 1
                                    if multiplayer_mode == 1:  # 主机接收客户端的移动
                                        q[ns // 11][n % 11-1] = 2
                                        eval('cn' + str(n)).config(text='●')
                                        if check(q) == 2:
                                            messagebox.showinfo('获胜结果', '对方获胜!')
                                            play_state = 0
                                    elif multiplayer_mode == 2:  # 客户端接收主机的移动
                                        q[ns // 11][n % 11-1] = 1
                                        eval('cn' + str(n)).config(text='○')
                                        if check(q) == 1:
                                            messagebox.showinfo('获胜结果', '对方获胜!')
                                            play_state = 0
                                    num += 1
                                except:
                                    if play_state == 1:
                                        messagebox.showerror("错误", "连接已断开")
                                        play_state = 0
                                    break

                        win3 = tk.Tk()
                        win3.geometry('360x550+100+100')
                        win3.title('云棋AI')
                        win3.configure(bg='light cyan')
                        win3.resizable(False,False)
                        win3.iconbitmap('images\\云棋AI.ico')

                        img = Image.open('images\\云棋AI-BG1.png')
                        img2 = ImageTk.PhotoImage(img)
                        bg1 = tk.Label(win3, image=img2)
                        bg1.place(x=-1, y=-3)

                        def change_nums(n):
                            global play_num, up_state
                            play_num = n
                            for i in range(1,6):
                                if i != n:
                                    globals()['de'+str(i)].config(activebackground='deepskyblue',bg='deepskyblue')
                            globals()['de'+str(n)].config(activebackground='whitesmoke',bg='whitesmoke')
                            if n <= 3:
                                if up_state != 0:
                                    if up_state == 2:
                                        for i in range(15):
                                            eval('abo' + str(i)).destroy()
                                    if up_state == 1:
                                        for i in range(23):  #Θ◎
                                            eval('d'+str(i)).destroy()
                                    up_state = 0
                                    rc_y = 150
                                    for j in range(1, 12):
                                        for i in range(1, 12):
                                            globals()['cn'+str((j-1)*11+i)] = tk.Button(win3,width=2,height=1,activebackground='yellow', command=lambda arg=(j-1)*11+i:change_C(arg),font=font.Font(family=ph,size=13),bg='yellow')
                                            eval('cn'+str((j-1)*11+i)).place(x=(i-1)*30+20,y=rc_y)
                                        rc_y+=30
                                    globals()['cn122'] = tk.Label(win3,text=eng_chn_li[23][eng_chn],font=font.Font(family=pz,size=13),bg='light cyan')
                                    eval('cn122').place(x=60,y=125)#Θ◎
                                    globals()['cn123'] = tk.Button(win3, command=start, width=10,height=1, text=eng_chn_li[23][eng_chn], font=font.Font(family=pz,size=15),activebackground='yellow',bg='yellow')
                                    eval('cn123').place(x=110, y=488)
                                if n == 1:
                                    eval('cn122').config(text=eng_chn_li[24][eng_chn])
                                if n == 2:
                                    eval('cn122').config(text=eng_chn_li[25][eng_chn])
                                if n == 3:
                                    eval('cn122').config(text=eng_chn_li[26][eng_chn])
                            elif n == 4:
                                if up_state != 1:
                                    def change_des():
                                        global person, up_state, ms
                                        ask_yn = messagebox.askyesno('注销账号 提示', '确认要注销账号'+person['name']+'(ID号 '+person['ID']+')吗？注销后您的所有数据将永久删除，无法恢复!')
                                        if ask_yn:
                                            f1 = open('YQ_DataBase.json', 'r')
                                            cst = json.loads(f1.read())
                                            f1.close()
                                            f2 = open('YQ_DataBase.json', 'w')
                                            del cst[person['name']]
                                            f2.write(json.dumps(cst))
                                            f2.close()
                                            messagebox.showinfo('注销账号 提示', '注销账号成功，已为您重新启动程序。')
                                            if up_state == 0:
                                                for i in range(1, 124):  #Θ◎
                                                    eval('cn'+str(i)).destroy()
                                            if up_state == 2:
                                                for i in range(15):
                                                    eval('abo' + str(i)).destroy()
                                            if up_state == 1:
                                                for i in range(23):  #Θ◎
                                                    eval('d'+str(i)).destroy()
                                            up_state=0
                                            person={}
                                            win3.destroy()
                                            f1 = open('YQ_DataBase.json', 'r')
                                            ms = json.loads(f1.read())
                                            f1.close()
                                            FQAI_all_code()
                                    if up_state == 0:
                                        for i in range(1, 124):  #Θ◎
                                            eval('cn'+str(i)).destroy()
                                    if up_state == 2:
                                        for i in range(15):
                                            eval('abo' + str(i)).destroy()
                                    up_state = 1
                                    str_list = eng_chn_li[27][eng_chn].split()
                                    lir = ['name', 'YH_number', 'ID', 'password', 'level', 'win_num']
                                    for i in range(13, 20):
                                        globals()['d'+str(i)] = tk.Canvas(win3,width=500,height=1, bd=0, bg='light gray', highlightbackground='light cyan')
                                        eval('d'+str(i)).place(x=0,y=150+(i-13)*45)
                                    for i in range(7):
                                        globals()['d'+str(i)] = tk.Label(win3,text=str_list[i],font=font.Font(family=pf,size=15),bg='light cyan')
                                        eval('d'+str(i)).place(x=20,y=120+i*45)
                                    for i in range(7, 13):
                                        globals()['d'+str(i)] = tk.Label(win3,text=person[lir[i-7]],font=font.Font(family=pf,size=15),bg='light cyan')
                                        eval('d'+str(i)).place(x=195,y=165+(i-7)*45)
                                    globals()['d'+str(20)] = tk.Button(win3, text='注销账号',width=13,font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke', command=change_des)
                                    eval('d'+str(20)).place(x=30, y=435)
                                    globals()['d'+str(21)] = tk.Button(win3, text='修改信息',width=13, font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
                                    eval('d'+str(21)).place(x=190, y=435)
                                    globals()['d'+'22'] = tk.Canvas(win3,width=1,height=310, bd=0, bg='light gray', highlightbackground='light cyan')
                                    eval('d'+'22').place(x=130,y=110)

                            elif n == 5:
                                if up_state != 2:
                                    if up_state == 0:
                                        for i in range(1,124):  #Θ◎
                                            eval('cn'+str(i)).destroy()
                                    if up_state == 1:
                                        for i in range(23):
                                            eval('d'+str(i)).destroy()
                                    up_state = 2
                                    al= '      云棋AI 智能AI棋手\n版本:v2.8.1\n版本发布时间：2025年8月21日\n前端设计:李丰毅\n后端程序:李丰毅\n赞助商：山西广寰工程技术有限公司\n赞助人：李*良,陈*\n技术支持：CSDN社区' \
                                        '\n参考文献：Python3程序设计实例教程\n特别鸣谢： [双击查看]\n玩法规则： [双击查看]'
                                    al2 = al.split('\n')
                                    y=120
                                    for i in range(11):
                                        globals()['abo'+str(i)] = tk.Label(win3, text=al2[i],bg='light cyan', font=font.Font(family=pf,size=15))
                                        eval('abo'+str(i)).place(x=10, y=y)
                                        y+=25
                                    def function1(arg):
                                        messagebox.showinfo('特别鸣谢', '1.李*良，陈*(开发支持)\n2.宫城老师，孙*燕老师(技术支持)\n3.CSDN社区(技术支持)\n4.JetBrain(环境支持)\n5.deepseek深度求索(技术支持)\n6.沈涵飞，刘正(技术支持)')
                                    def function2(arg):
                                        messagebox.showinfo('玩法规则', '1. 游戏名为五子棋，即连成5子者获胜。')
                                    eval('abo9').bind('<Double-Button-1>', function1)
                                    eval('abo10').bind('<Double-Button-1>', function2)
                                    def close():
                                        win3.destroy()
                                    def re_start():
                                        global up_state, ms, st
                                        if up_state == 0:
                                            for i in range(1,124):  #Θ◎
                                                eval('cn'+str(i)).destroy()
                                        if up_state == 2:
                                            for i in range(15):
                                                eval('abo' + str(i)).destroy()
                                        if up_state == 1:
                                            for i in range(23):  #Θ◎
                                                eval('d'+str(i)).destroy()
                                        up_state=0
                                        win3.destroy()
                                        f1 = open('images\\YQ_DataBase.json', 'r')
                                        ms = json.loads(f1.read())
                                        f1.close()
                                        FQAI_all_code()
                                    globals()['abo11'] = tk.Label(win3, text='--------版权所有，禁止转用--------',bg='light cyan', font=font.Font(family=pf,size=15), fg='red')
                                    eval('abo11').place(x=10, y=400)
                                    globals()['abo12'] = tk.Button(win3, command=re_start, width=10, text='重新启动', font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
                                    eval('abo12').place(x=50, y=435)
                                    globals()['abo13'] = tk.Button(win3, command=close, width=10, text='关闭应用', font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
                                    eval('abo13').place(x=200, y=435)
                                    global img, img2
                                    img = Image.open(os.path.abspath('images\\山西广寰图片.png'))
                                    img2 = ImageTk.PhotoImage(img)
                                    globals()['abo14'] = tk.Label(win3, image=img2, bg='light cyan')
                                    eval('abo14').place(x=250, y=112)

                        def start():
                            global play_state, q, play_num, model, num, multiplayer_mode, connection

                            if play_num == 3:  # 双人对战
                                # 创建选择对战模式的窗口
                                win6 = tk.Toplevel(win3)
                                win6.geometry('200x180+100+100')
                                win6.title('选择对战模式')
                                win6.resizable(False, False)
                                win6.configure(bg='light cyan')

                                def select_local():
                                    global multiplayer_mode
                                    multiplayer_mode = 0
                                    win6.destroy()
                                    start_game()

                                def select_host():
                                    global multiplayer_mode, connection, hos
                                    multiplayer_mode = 1
                                    try:
                                        # 创建服务器
                                        aski = simpledialog.askstring('端口号', '端口号')
                                        if aski != '' and ' ' not in aski:
                                            messagebox.showinfo("等待连接", "等待客户端连接...")
                                            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                            server.bind(('0.0.0.0', int(aski)))
                                            server.listen(1)
                                            win6.destroy()
                                            # 在新线程中接受连接
                                            def accept_connection():
                                                global connection
                                                connection, addr = server.accept()
                                                messagebox.showinfo("连接成功", f"已连接到 {addr}")
                                                start_game()
                                                threading.Thread(target=receive_move, daemon=True).start()

                                            threading.Thread(target=accept_connection, daemon=True).start()
                                        else:
                                            messagebox.showerror('error', '端口号不能为空')
                                    except Exception as e:
                                        messagebox.showerror("错误", f"创建服务器失败: {e}")
                                        multiplayer_mode = 0

                                def select_client():
                                    global multiplayer_mode, connection
                                    multiplayer_mode = 2
                                    # 创建连接窗口
                                    win5 = tk.Toplevel(win6)
                                    win5.geometry('380x280+150+200')
                                    win5.title('连接到主机')
                                    win5.resizable(False, False)
                                    win5.configure(bg='light grey')
                                    post, host = '', ''
                                    def connect():
                                        try:
                                            global connection, post, host
                                            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                            connection.connect((post, host))
                                            win5.destroy()
                                            win6.destroy()
                                            messagebox.showinfo("连接成功", "已连接到主机")
                                            start_game()
                                            threading.Thread(target=receive_move, daemon=True).start()
                                        except Exception as e:
                                            messagebox.showerror("错误", f"连接失败: {e}")
                                    fr = tk.Frame(win5)
                                    fr.place(x=340, y=15, width=20, height=225)
                                    sl = tk.Scrollbar(fr, orient='vertical')
                                    sl.pack(side=tk.RIGHT, fill = tk.Y)

                                    tree=ttk.Treeview(win5, height = 10,yscrollcommand=sl.set)#表格
                                    tree["columns"]=("名称","ip","端口")
                                    sl['command'] = tree.yview
                                    tree.column("#0", width=0)
                                    tree.column("名称",width=100)
                                    tree.column("ip",width=120)
                                    tree.column("端口",width=110)

                                    tree.heading("名称",text="名称")
                                    tree.heading("ip",text="ip")
                                    tree.heading("端口",text="端口")
                                    tree.place(x=10, y=15)
                                    def check_ip(ip):
                                        try:
                                            for i in [int(ip.split('.')[i]) for i in range(4)]:
                                                if i > 255 or i < 0:
                                                    return False
                                            return True
                                        except Exception:
                                            return False
                                    tree.insert("",0,text='',values=('', '( 空 )', '( 双击添加 )'))
                                    if len(person['connect_list']) != 0:
                                        for i in person['connect_list']:
                                            tree.insert("",0,text='',values=(i[0], i[1], i[2]))
                                    def print_selected_row(event):
                                        sitem = tree.selection()
                                        if sitem:
                                            item = sitem[0]
                                            values = tree.item(item, 'values')
                                            if values[-1] == '( 双击添加 )':
                                                win7=tk.Toplevel(win5)
                                                win7.geometry('270x300+100+100')
                                                win7.resizable(False, False)
                                                win7.configure(bg='light grey')
                                                win7.title('连接到主机 > 添加常用用户')
                                                def mk():
                                                    if list(mm.get()).count('.') == 3 and check_ip(mm.get()):
                                                        tree.insert("",0,text='',values=(name2.get(), mm.get(), mm2.get()))
                                                        f1 = open('images\\YQ_DataBase.json', 'r')
                                                        rt = json.loads(f1.read())
                                                        f1.close()
                                                        rt[person['name']]['connect_list'].append([name2.get(), mm.get(), mm2.get()])
                                                        with open('images\\YQ_DataBase.json', 'w') as f2:
                                                            f2.writelines(json.dumps(rt))
                                                        person['connect_list'].append([name2.get(), mm.get(), mm2.get()])
                                                        win7.destroy()
                                                    else:
                                                        messagebox.showwarning('警告', 'ipv4地址格式错误')
                                                name = tk.Label(win7, text='用户名',bg='light grey', font=font.Font(family=pf,size=16))
                                                name.place(x=15, y=10)
                                                name2 = tk.Entry(win7,width=15,font=font.Font(family=pf,size=16))
                                                name2.place(x=15, y=50)
                                                name = tk.Label(win7, text='ip地址',bg='light grey', font=font.Font(family=pf,size=16))
                                                name.place(x=15, y=90)
                                                mm = tk.Entry(win7,width=20, font=font.Font(family=pf,size=16))
                                                mm.place(x=15, y=130)
                                                name = tk.Label(win7, text='端口',bg='light grey', font=font.Font(family=pf,size=16))
                                                name.place(x=15, y=170)
                                                mm2 = tk.Entry(win7,width=15, font=font.Font(family=pf,size=16))
                                                mm2.place(x=15, y=210)
                                                get = tk.Button(win7, command=mk, width=15, text='确认添加', font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
                                                get.place(x=50, y=250)
                                                win7.mainloop()
                                            else:
                                                global post, host
                                                post = values[1]
                                                host = int(values[-1])
                                                connect()
                                    def dele(null_input):
                                        sitem = tree.selection()
                                        if sitem:
                                            item = sitem[0]
                                            values = tree.item(item, 'values')
                                        if values[-1] != '( 双击添加 )':
                                            ask = messagebox.askyesno('删除用户', '确定要删除用户'+values[0]+'(ip: '+values[1]+')吗?')
                                            if ask:
                                                tree.delete(item)
                                                messagebox.showinfo('提示', '已删除用户'+values[0]+'(ip: '+values[1]+')')
                                    tree.bind('<Double-1>',print_selected_row)
                                    tree.bind('<Button-3>',dele)

                                    win5.mainloop()

                                ch = tk.Label(win6, text='请选择对战模式:', bg='light cyan',font=font.Font(family=pf,size=15))
                                ch.place(x=30, y=10)
                                up= tk.Button(win6, text='线下对战', width=15,command=select_local, height=1, font=font.Font(family=pz,size=12),activebackground='whitesmoke',bg='deepskyblue')
                                up.place(x=20, y=50)
                                mak = tk.Button(win6, text='联机对战(创建主机)', width=15, command=select_host, height=1, font=font.Font(family=pz,size=12),activebackground='whitesmoke',bg='deepskyblue')
                                mak.place(x=20, y=90)
                                ino = tk.Button(win6, text='联机对战(加入游戏)', width=15, command=select_client, height=1, font=font.Font(family=pz,size=12),activebackground='whitesmoke',bg='deepskyblue')
                                ino.place(x=20, y=130)
                                win6.mainloop()
                            else:
                                start_game()

                        def start_game():
                            global play_state, q, play_num, model, num
                            model = combo.get()
                            for i in range(1,122):
                                eval('cn'+str(i)).config(text='')
                                q = [[0 for _ in range(11)] for _ in range(11)]
                            play_state = 1
                            num = 0
                            if play_num == 2:
                                num = rd.choice([[5, 5], [4, 4], [4, 6], [6, 4], [6, 6], [5, 5], [5, 5], [5, 5]])
                                q[num[0]][num[1]] = 2
                                print(q)
                                eval('cn' + str(num[0]*11+num[1]+1)).config(text='○')
                            if play_num == 3 and multiplayer_mode == 2:  # 客户端先等待主机下棋
                                eval('cn122').config(text='等待对方下棋...')

                        def ECH2():
                            global eng_chn
                            if eng_chn == 0:
                                eng_chn = 1
                            elif eng_chn == 1:
                                eng_chn = 0
                            if up_state == 2:
                                for i in range(15):
                                    eval('abo' + str(i)).destroy()
                            if up_state == 1:
                                for i in range(23):  #Θ◎
                                    eval('d'+str(i)).destroy()
                            for i in range(1, 124):  #Θ◎
                                eval('cn'+str(i)).destroy()
                            win3.destroy()
                            run_CCS()

                        fs= tk.Canvas(win3,width=500,height=4,bg='black', highlightbackground='light cyan')
                        fs.place(x=-5,y=38+65)
                        globals()['de'+str(1)] = tk.Button(win3, command=lambda arg=1:change_nums(arg), width=9,height=2, text='AI对战\n(您是先手)', font=font.Font(family=ph,size=10),activebackground='whitesmoke',bg='whitesmoke')
                        globals()['de'+str(1)].place(x=0, y=70)
                        globals()['de'+str(2)] = tk.Button(win3, command=lambda arg=2:change_nums(arg), width=9,height=2, text='AI对战\n(您是后手)', font=font.Font(family=ph,size=10),activebackground='deepskyblue',bg='deepskyblue')
                        globals()['de'+str(2)].place(x=73, y=70)
                        globals()['de'+str(3)] = tk.Button(win3, command=lambda arg=3:change_nums(arg), width=9,height=2, text='双人对战', font=font.Font(family=ph,size=10),activebackground='deepskyblue',bg='deepskyblue')
                        globals()['de'+str(3)].place(x=73*2, y=70)
                        globals()['de'+str(4)] = tk.Button(win3, command=lambda arg=4:change_nums(arg), width=9,height=2, text='个人信息', font=font.Font(family=ph,size=10),activebackground='deepskyblue',bg='deepskyblue')
                        globals()['de'+str(4)].place(x=73*3, y=70)
                        globals()['de'+str(5)] = tk.Button(win3, command=lambda arg=5:change_nums(arg), width=9,height=2, text='i 关于', font=font.Font(family=ph,size=10),activebackground='deepskyblue',bg='deepskyblue')
                        globals()['de'+str(5)].place(x=73*4, y=70)

                        combo = ttk.Combobox(win3, width=15, values=['MNX 1.3(较简单)', 'MTCS 1.0(中等)', 'PBS 2.1(较难)', 'RDM 1.1(简单)'])
                        combo.place(x=230, y=5)
                        combo.current(1)
                        rc_y = 150
                        for j in range(1, 12):
                            for i in range(1, 12):
                                globals()['cn'+str((j-1)*11+i)] = tk.Button(win3,width=2,height=1,activebackground='yellow', command=lambda arg=(j-1)*11+i:change_C(arg),font=font.Font(family=ph,size=13),bg='yellow')
                                eval('cn'+str((j-1)*11+i)).place(x=(i-1)*30+20,y=rc_y)
                            rc_y+=30
                        globals()['cn122'] = tk.Label(win3,text=eng_chn_li[24][eng_chn],font=font.Font(family=pz,size=13),bg='light cyan')
                        eval('cn122').place(x=60,y=125)
                        globals()['cn123'] = tk.Button(win3, command=start, width=10,height=1, text=eng_chn_li[23][eng_chn], font=font.Font(family=pz,size=15),activebackground='yellow',bg='yellow')
                        eval('cn123').place(x=110, y=488)
                        about_me= tk.Label(win3, text='◎'+eng_chn_li[0][eng_chn],bg='light cyan',fg='gray', font=font.Font(family=pf,size=10))
                        about_me.place(x=10, y=530)
                        chg = tk.Button(win3, command=ECH2, width=8, text=eng_chn_li[4][eng_chn], font=font.Font(family=pf,size=10),activebackground='whitesmoke',bg='whitesmoke')
                        chg.place(x=290, y=525)
                        win3.mainloop()
                    win.destroy()
                    run_CCS()
                else:
                    if s_n != 1:
                        s_n -= 1
                        messagebox.showerror(eng_chn_li[14][eng_chn], eng_chn_li[21][eng_chn]+str(s_n)+eng_chn_li[22][eng_chn])
                    else:
                        win.destroy()
            else:
                messagebox.showinfo(eng_chn_li[14][eng_chn], eng_chn_li[20][eng_chn])
        else:
            messagebox.showwarning(eng_chn_li[14][eng_chn], eng_chn_li[17][eng_chn])

    def make_new():
        win4 = tk.Toplevel()
        win4.geometry('320x390+100+100')
        win4.title(eng_chn_li[12][eng_chn])
        win4.configure(bg='light cyan')
        win4.resizable(False,False)
        win4.iconbitmap('images\\云棋AI.ico')

        global img, img2
        img = Image.open(eng_chn_li[13][eng_chn])
        img2 = ImageTk.PhotoImage(img)
        bg1 = tk.Label(win4, image=img2, bg='light cyan')
        bg1.place(x=-1, y=-3)
        def change1():
            global d
            if d == eng_chn_li[2][eng_chn]:
                d = eng_chn_li[3][eng_chn]
                de1.config(text=d)
                mm.config(show='')
            elif d == eng_chn_li[3][eng_chn]:
                d = eng_chn_li[2][eng_chn]
                de1.config(text=d)
                mm.config(show='•')
        def change2():
            global d2
            if d2 == eng_chn_li[2][eng_chn]:
                d2 = eng_chn_li[3][eng_chn]
                de2.config(text=d2)
                mm2.config(show='')
            elif d2 == eng_chn_li[3][eng_chn]:
                d2 = eng_chn_li[2][eng_chn]
                de2.config(text=d2)
                mm2.config(show='•')
        def make_new():
            global ms,rfp
            if not(name2.get =='' or mm.get() == '' or mm2.get() == ''):
                if name2.get() not in ms.keys():
                    if mm.get() == mm2.get():
                        if mm.get().isnumeric() or mm.get().isalpha() or len(mm.get()) <5 or not mm.get().isalnum():
                            messagebox.showwarning(eng_chn_li[14][eng_chn], eng_chn_li[19][eng_chn])
                        else:
                            f1 = open('images\\YQ_DataBase.json', 'w')
                            t1, t2 = str(dt.datetime.now())[:10], str(dt.datetime.now())[-6:]
                            t3 = ''.join(t1.split('-'))
                            t4 = "YH"+t3+t2
                            sal, pasw = hash(mm.get())
                            ms[name2.get()] = {'name':name2.get(),'password':f'{sal}:{pasw}','ID':t4,'win_num':0, 'YH_number':0,'level':1,'english_type':eng_chn,'connect_list':[]}
                            f1.writelines(json.dumps(ms))
                            messagebox.showinfo(eng_chn_li[14][eng_chn], eng_chn_li[18][eng_chn])
                            win4.destroy()
                            f1.close()
                    else:
                        messagebox.showinfo(eng_chn_li[14][eng_chn], eng_chn_li[15][eng_chn])
                else:
                    messagebox.showinfo(eng_chn_li[14][eng_chn], eng_chn_li[16][eng_chn])
            else:
                messagebox.showwarning(eng_chn_li[14][eng_chn], eng_chn_li[17][eng_chn])
        name = tk.Label(win4, text=eng_chn_li[6][eng_chn],bg='light cyan', font=font.Font(family=pf,size=16))
        name.place(x=25, y=80)
        name2 = tk.Entry(win4,width=20,font=font.Font(family=pf,size=16))
        name2.place(x=25, y=120)
        name = tk.Label(win4, text=eng_chn_li[7][eng_chn],bg='light cyan', font=font.Font(family=pf,size=16))
        name.place(x=25, y=160)
        mm = tk.Entry(win4,width=15, font=font.Font(family=pf,size=16), show='•')
        mm.place(x=25, y=200)
        name = tk.Label(win4, text=eng_chn_li[10][eng_chn],bg='light cyan', font=font.Font(family=pf,size=16))
        name.place(x=25, y=240)
        mm2 = tk.Entry(win4,width=15, font=font.Font(family=pf,size=16), show='•')
        mm2.place(x=25, y=280)
        de1 = tk.Button(win4, command=change1, width=5, text=eng_chn_li[2][eng_chn], font=font.Font(family=pf,size=10),activebackground='whitesmoke',bg='whitesmoke')
        de1.place(x=205, y=200)
        de2 = tk.Button(win4, command=change2, width=5, text=eng_chn_li[2][eng_chn], font=font.Font(family=pf,size=10),activebackground='whitesmoke',bg='whitesmoke')
        de2.place(x=205, y=280)
        get = tk.Button(win4, command=make_new, width=20, text=eng_chn_li[11][eng_chn], font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
        get.place(x=55, y=320)
        about_me = tk.Label(win4, text='◎'+eng_chn_li[0][eng_chn],bg='light cyan',fg='grey', font=font.Font(family=pf,size=9))
        about_me.place(x=5, y=365)
        win4.mainloop()
    ask = tk.Label(win, text=eng_chn_li[5][eng_chn],bg='light cyan', font=font.Font(family=pf,size=15))
    ask.place(x=20, y=80)
    name = tk.Label(win, text=eng_chn_li[6][eng_chn],bg='light cyan', font=font.Font(family=pf,size=16))
    name.place(x=20, y=130)
    name2 = tk.Entry(win,width=20,font=font.Font(family=pf,size=16))
    name2.place(x=20, y=170)
    name = tk.Label(win, text=eng_chn_li[7][eng_chn],bg='light cyan', font=font.Font(family=pf,size=16))
    name.place(x=20, y=210)
    mm = tk.Entry(win,width=15, font=font.Font(family=pf,size=16), show='•')
    mm.place(x=20, y=250)
    de = tk.Button(win, command=change, width=5, text=eng_chn_li[2][eng_chn], font=font.Font(family=pf,size=10),activebackground='whitesmoke',bg='whitesmoke')
    de.place(x=200, y=250)
    get = tk.Button(win, command=cstart, width=10, text=eng_chn_li[8][eng_chn], font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
    get.place(x=35, y=290)
    get2 = tk.Button(win, command=make_new, width=10,height=1, text=eng_chn_li[9][eng_chn], font=font.Font(family=pf,size=15),activebackground='whitesmoke',bg='whitesmoke')
    get2.place(x=155, y=290)
    about_me = tk.Label(win, text='◎'+eng_chn_li[0][eng_chn],bg='light cyan',fg='grey', font=font.Font(family=pf,size=9))
    about_me.place(x=5, y=340)
    chg = tk.Button(win, command=eng_chn_chg, width=8, text=eng_chn_li[4][eng_chn], font=font.Font(family=pf,size=10),activebackground='whitesmoke',bg='whitesmoke')
    chg.place(x=250, y=345)
    win.mainloop()

if __name__ == "__main__":
    start_win()